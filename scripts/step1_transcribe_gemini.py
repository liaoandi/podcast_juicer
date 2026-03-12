#!/usr/bin/env python3
"""
使用 Gemini 3.1 Pro 直接转录音频（替代 Whisper + 说话人识别 + 润色）

优势：
- 一步到位：转录 + 说话人标注 + 书面化
- 质量更高：英文名/专业术语识别更准
- 速度更快：~7分钟/集（vs Whisper方案 ~27分钟）

使用方法：
    python step1_transcribe_gemini.py <audio_file> [participants_json] [output_file]
"""

import json
import os
import sys
import time
from gemini_utils import get_gemini_client, DEFAULT_MODEL, clean_json
from google.genai import types


# Gemini 音频转录配置
TRANSCRIBE_MODEL = DEFAULT_MODEL
TRANSCRIBE_LOCATION = "global"
# 每段音频最大时长（秒），超过则分段处理
MAX_CHUNK_SECONDS = 180  # 3 分钟（thinking 模型最佳长度）
MAX_WORKERS = 1  # 串行转录（避免 API 499 取消）


def get_audio_duration(audio_path):
    """获取音频时长（秒）"""
    import subprocess
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True, text=True, check=True
        )
        return float(result.stdout.strip())
    except Exception:
        return None


SKIP_INTRO_SECONDS = 120  # 跳过前2分钟片头（音乐/广告/固定介绍）


def split_audio(audio_path, chunk_seconds=MAX_CHUNK_SECONDS, skip_intro=SKIP_INTRO_SECONDS):
    """将长音频分割为多个片段，返回 [(chunk_path, start_sec, end_sec), ...]"""
    duration = get_audio_duration(audio_path)
    if duration is None:
        print(f"   ⚠️ 无法获取音频时长，尝试整体转录")
        return [(audio_path, 0, None)]

    print(f"   音频时长: {duration/60:.1f} 分钟")

    if skip_intro and duration > skip_intro + chunk_seconds:
        print(f"   跳过前 {skip_intro}s 片头")

    effective_start = skip_intro if (skip_intro and duration > skip_intro + chunk_seconds) else 0

    if duration - effective_start <= chunk_seconds:
        return [(audio_path, effective_start, duration)]

    import subprocess, glob
    base = os.path.splitext(audio_path)[0]

    # 清理旧的 chunk 文件（防止上次崩溃残留）
    for old_chunk in glob.glob(f"{base}_chunk*.mp3"):
        os.remove(old_chunk)

    chunks = []
    start = effective_start
    chunk_idx = 0

    while start < duration:
        end = min(start + chunk_seconds, duration)
        chunk_path = f"{base}_chunk{chunk_idx}.mp3"

        subprocess.run([
            'ffmpeg', '-i', audio_path,
            '-ss', str(start), '-t', str(end - start),
            '-y', chunk_path
        ], capture_output=True, check=True)

        chunks.append((chunk_path, start, end))
        start = end
        chunk_idx += 1

    print(f"   分割为 {len(chunks)} 个片段")
    return chunks


def build_transcribe_prompt(participants_info=None, chunk_note=None):
    """构建转录 prompt"""
    participants_str = ""
    if participants_info:
        hosts = participants_info.get('host', [])
        guests = participants_info.get('guests', [])
        bg = participants_info.get('guest_background', {})

        if hosts:
            participants_str += f"\n主持人: {', '.join(hosts)}"
        if guests:
            participants_str += f"\n嘉宾: {', '.join(guests)}"
        if bg:
            for name, info in bg.items():
                participants_str += f"\n  - {name}: {info}"

    chunk_str = f"\n注意: {chunk_note}" if chunk_note else ""

    return f"""请转录这段播客音频。要求：

1. 标注每个说话人（用真实姓名，如果提供了参与者信息）
2. 格式: 每个说话人的一段连续发言作为一个段落
3. 保留完整内容，不要省略任何部分
4. 适度书面化：添加标点符号，删除明显的口头禅（"就是说"、"那个"等）
5. 保留概率词和观点表达（"我觉得"、"可能"、"相对来说"）
6. 数字和英文专有名词后加空格
7. 输出 JSON 格式

{f"参与者信息:{participants_str}" if participants_str else "请根据对话内容推断说话人身份。"}
{chunk_str}

输出 JSON 格式：
{{
  "segments": [
    {{
      "speaker": "说话人姓名",
      "text": "说话内容（完整的一段发言）",
      "start_approx": "绝对开始时间 HH:MM:SS"
    }}
  ]
}}

直接输出 JSON，不要其他说明。"""


def transcribe_chunk(client, audio_bytes, participants_info=None, chunk_note=None):
    """转录单个音频片段"""
    prompt = build_transcribe_prompt(participants_info, chunk_note)

    response = client.models.generate_content(
        model=TRANSCRIBE_MODEL,
        contents=[
            types.Part(inline_data=types.Blob(data=audio_bytes, mime_type='audio/mpeg')),
            prompt
        ],
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=65536,
        )
    )

    raw_text = ""
    try:
        raw_text = response.text or ""
    except Exception:
        raw_text = ""

    return clean_json(raw_text)


def format_timestamp(seconds):
    """秒数转 HH:MM:SS"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def parse_approx_time(time_str, offset=0, chunk_end=None):
    """解析 LLM 返回的大约时间（MM:SS 或 HH:MM:SS），加上偏移。

    期望模型返回相对于整期音频的绝对时间；为兼容旧输出，仍接受 chunk 内相对时间。
    """
    def _clamp_to_chunk(seconds):
        seconds = max(0, int(seconds))
        chunk_start = max(0, int(offset))
        if chunk_end is None:
            return max(chunk_start, seconds)
        return max(chunk_start, min(seconds, int(chunk_end)))

    if not time_str:
        return offset
    try:
        parts = time_str.strip().split(':')
        if len(parts) == 3:
            secs = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            if offset <= 0:
                return _clamp_to_chunk(secs)

            if chunk_end is not None and offset <= secs <= chunk_end + 5:
                return secs

            relative_secs = secs + offset
            if chunk_end is not None and offset <= relative_secs <= chunk_end + 5:
                return relative_secs

            if secs >= offset:
                return _clamp_to_chunk(secs)
            return _clamp_to_chunk(relative_secs)
        elif len(parts) == 2:
            secs = int(parts[0]) * 60 + int(parts[1])
        else:
            secs = 0

        if offset <= 0:
            return _clamp_to_chunk(secs)

        if chunk_end is not None:
            chunk_duration = max(0, int(chunk_end - offset))
            if secs <= chunk_duration + 5:
                return secs + offset
            if offset <= secs <= chunk_end + 5:
                return secs

        if secs < offset:
            return _clamp_to_chunk(secs + offset)

        return _clamp_to_chunk(secs)
    except Exception:
        return offset


def transcribe_audio(audio_file, participants_file=None, output_file=None):
    """使用 Gemini 转录完整音频"""

    if not os.path.exists(audio_file):
        print(f"❌ 音频文件不存在: {audio_file}")
        sys.exit(1)

    file_size = os.path.getsize(audio_file) / (1024 * 1024)
    print(f"\n🎙️ Gemini 音频转录")
    print(f"   音频: {audio_file} ({file_size:.1f} MB)")
    print(f"   模型: {TRANSCRIBE_MODEL}")

    # 加载参与者信息
    participants_info = None
    if participants_file and os.path.exists(participants_file):
        with open(participants_file, 'r', encoding='utf-8') as f:
            participants_info = json.load(f)
        hosts = participants_info.get('host', [])
        guests = participants_info.get('guests', [])
        print(f"   主持人: {hosts}")
        print(f"   嘉宾: {guests}")

    # 分割音频
    print(f"\n📦 准备音频片段...")
    chunks = split_audio(audio_file)

    # 初始化客户端
    print(f"\n🔗 连接 Gemini...")
    client = get_gemini_client(location=TRANSCRIBE_LOCATION)

    # 并行转录
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _transcribe_one(i, chunk_path, start_sec, end_sec):
        """转录单个片段（带重试）"""
        with open(chunk_path, 'rb') as f:
            audio_bytes = f.read()

        chunk_note = None
        if len(chunks) > 1:
            chunk_note = f"这是第 {i+1}/{len(chunks)} 段，时间范围 {format_timestamp(start_sec)} - {format_timestamp(end_sec or 0)}"

        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = transcribe_chunk(client, audio_bytes, participants_info, chunk_note)
                if result and 'segments' in result:
                    return i, start_sec, end_sec, result['segments']
                # LLM 返回了非标准格式
                if result:
                    print(f"   [{i+1}] ⚠️ 返回格式异常，缺少 segments 字段: {list(result.keys())}")
                return i, start_sec, end_sec, None
            except Exception as e:
                if attempt < max_retries - 1:
                    wait = 10 * (attempt + 1)
                    print(f"   [{i+1}] ⚠️ 重试: {str(e)[:60]}...")
                    time.sleep(wait)
                else:
                    print(f"   [{i+1}] ❌ 失败: {str(e)[:60]}")
                    return i, start_sec, end_sec, None

    # ── 增量存储：每个 chunk 完成后立刻写入，支持断点续跑 ──
    if not output_file:
        base = os.path.splitext(audio_file)[0]
        output_file = f"{base}_transcript_gemini.json"

    progress_file = output_file + ".progress"

    # 加载已完成的 chunk（断点续跑）
    chunk_results = [None] * len(chunks)
    done_chunks = set()
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
            for cr in progress_data.get('chunk_results', []):
                idx = cr['chunk_index']
                # 只恢复有实际 segments 的 chunk，失败的 chunk 重试
                if idx < len(chunks) and cr.get('segments'):
                    chunk_results[idx] = (cr['start_sec'], cr['end_sec'], cr['segments'])
                    done_chunks.add(idx)
            print(f"\n📂 断点续跑: 已完成 {len(done_chunks)}/{len(chunks)} 个 chunk")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"\n⚠️ progress 文件损坏 ({e})，从头开始")
            done_chunks = set()
            chunk_results = [None] * len(chunks)

    total_start = time.time()
    workers = min(MAX_WORKERS, len(chunks))

    def _save_progress():
        """将已完成的 chunk 原子写入 progress 文件"""
        saved = []
        for idx, entry in enumerate(chunk_results):
            if entry is not None:
                start_sec, end_sec, segs = entry
                saved.append({
                    'chunk_index': idx,
                    'start_sec': start_sec,
                    'end_sec': end_sec,
                    'segments': segs,
                })
        tmp_file = progress_file + ".tmp"
        with open(tmp_file, 'w', encoding='utf-8') as f:
            json.dump({'total_chunks': len(chunks), 'chunk_results': saved}, f, ensure_ascii=False)
        os.replace(tmp_file, progress_file)

    remaining = [(i, c) for i, c in enumerate(chunks) if i not in done_chunks]
    if remaining:
        print(f"\n🚀 转录 ({len(remaining)} 个 chunk 待处理, {workers} 路)...")
    else:
        print(f"\n✅ 所有 chunk 已完成，直接合并")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {}
        for i, (chunk_path, start_sec, end_sec) in remaining:
            future = executor.submit(_transcribe_one, i, chunk_path, start_sec, end_sec)
            futures[future] = i

        for future in as_completed(futures):
            try:
                idx, start_sec, end_sec, segs = future.result()
                chunk_results[idx] = (start_sec, end_sec, segs)
                if segs:
                    print(f"   [{idx+1}/{len(chunks)}] ✓ {format_timestamp(start_sec)}-{format_timestamp(end_sec or 0)}: {len(segs)} 段")
                else:
                    print(f"   [{idx+1}/{len(chunks)}] ✗ {format_timestamp(start_sec)}-{format_timestamp(end_sec or 0)}: 无结果")
                # 每个 chunk 完成后立刻保存进度
                _save_progress()
            except Exception as e:
                i = futures[future]
                print(f"   [{i+1}/{len(chunks)}] ❌ 异常: {e}")

    # 按顺序合并结果（跳过 None 条目）
    all_segments = []
    for entry in chunk_results:
        if entry is None:
            continue
        start_sec, end_sec, segs = entry
        if not segs:
            continue
        for j, seg in enumerate(segs):
            approx_start = parse_approx_time(seg.get('start_approx', ''), offset=start_sec, chunk_end=end_sec)
            if end_sec is not None:
                approx_start = min(approx_start, int(end_sec))
            if j + 1 < len(segs):
                approx_end = parse_approx_time(
                    segs[j + 1].get('start_approx', ''),
                    offset=start_sec,
                    chunk_end=end_sec,
                )
            else:
                approx_end = end_sec or (approx_start + 30)

            if end_sec is not None:
                approx_end = min(approx_end, int(end_sec))
            approx_end = max(approx_end, approx_start)

            all_segments.append({
                'id': len(all_segments),
                'speaker': seg.get('speaker', 'Unknown'),
                'text': seg.get('text', ''),
                'start': format_timestamp(approx_start),
                'end': format_timestamp(approx_end),
                'start_seconds': approx_start,
                'end_seconds': approx_end,
            })

    total_elapsed = time.time() - total_start
    print(f"\n✅ 转录完成!")
    print(f"   总段落: {len(all_segments)}")
    print(f"   总耗时: {total_elapsed:.1f}s ({total_elapsed/60:.1f}min)")

    # 统计说话人
    speakers = {}
    for seg in all_segments:
        sp = seg['speaker']
        speakers[sp] = speakers.get(sp, 0) + 1
    print(f"   说话人: {speakers}")

    # 构建输出
    output = {
        'language': 'zh',
        'transcription_method': 'gemini_audio',
        'model': TRANSCRIBE_MODEL,
        'segments': all_segments,
    }

    print(f"\n💾 保存: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 清理临时文件（progress 完成即删，chunk 文件移到 archive）
    for f in [progress_file, progress_file + ".tmp"]:
        if os.path.exists(f):
            os.remove(f)
    for chunk_path, _, _ in chunks:
        if chunk_path != audio_file and os.path.exists(chunk_path):
            os.remove(chunk_path)

    return output_file


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python step1_transcribe_gemini.py <audio_file> [participants_json] [output_file]")
        print("")
        print("示例:")
        print("  python step1_transcribe_gemini.py 233.mp3")
        print("  python step1_transcribe_gemini.py 233.mp3 participants.json")
        print("  python step1_transcribe_gemini.py 233.mp3 participants.json output.json")
        sys.exit(1)

    audio_file = sys.argv[1]
    participants_file = sys.argv[2] if len(sys.argv) > 2 else None
    output_file = sys.argv[3] if len(sys.argv) > 3 else None

    transcribe_audio(audio_file, participants_file, output_file)
