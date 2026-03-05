#!/usr/bin/env python3
"""
润色转录文本：添加标点符号 + 轻度书面化
使用 Gemini Flash 进行智能润色（并发加速）
"""

import re
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.genai import types
from gemini_utils import get_gemini_client

# 润色用 flash 模型（轻量任务，不需要 thinking）
POLISH_MODEL = "gemini-2.5-flash"
POLISH_LOCATION = "us-central1"
MAX_WORKERS = 5  # 并发数

# 初始化 Gemini 客户端
client = None
_client_lock = threading.Lock()

def get_client():
    """获取或初始化 Gemini 客户端"""
    global client
    if client is None:
        with _client_lock:
            if client is None:  # double-check
                client = get_gemini_client(location=POLISH_LOCATION)
    return client

SYSTEM_PROMPT = """你是专业的播客转录润色专家，负责为转录添加标点并轻度书面化。

任务：添加标点、适当断句、删除口头禅

**关键要求**：
1. 添加标点符号（逗号、句号、问号等），适当断句

2. 轻度书面化（删除明显口头禅）：
   - 删除纯填充词："就是说"、"那个"、"这个"（当作填充词时）、"怎么讲"、"说白了"
   - 删除语气词："啊"、"呀"、句末的"吧"、"呢"
   - 简化连接词："然后" 可适当删除或改为句号

3. **必须保留概率词和观点表达**（这些是分析的核心）：
   - 保留："我觉得"、"我认为"、"我会觉得"
   - 保留："相对来说"、"比较"、"一定程度上"、"可能"、"大概"、"应该"
   - 保留："有点"、"略微"、"稍微"
   - 这些词表达了说话人的不确定性判断，必须保留

4. 适当断句：
   - 长句（>50字）拆分为短句
   - 用句号代替过多的逗号

5. 保持核心信息完整：
   - 所有数字、数据必须保留（如：14 倍、27 倍、90%）
   - 核心观点和逻辑不变
   - 专业术语和生动比喻保留

6. 数字和英文专有名词后加空格

7. 直接输出润色后的文本，不要解释

示例：
输入：我会觉得其实Google其实是对我来说一个被市场教育的过程吧因为我们相对来说一直都比较对Google偏悲观
输出：我会觉得 Google 对我来说是一个被市场教育的过程，因为我们相对来说一直都比较对 Google 偏悲观。"""


def polish_with_llm(text, max_retries=3):
    """使用 Gemini Flash 添加标点符号和轻度书面化"""
    for attempt in range(max_retries):
        try:
            full_prompt = f"{SYSTEM_PROMPT}\n\n要润色的文本：\n{text}"

            response = get_client().models.generate_content(
                model=POLISH_MODEL,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=max(2000, len(text) * 3)
                )
            )

            polished = (response.text or "").strip()
            if not polished:
                return text

            # 清理可能的说明性文字
            if polished.startswith('润色后') or polished.startswith('以下是'):
                lines = polished.split('\n')
                polished = '\n'.join([l for l in lines if l and not l.startswith(('润色', '以下', '原文'))])

            return polished

        except Exception as e:
            if attempt == max_retries - 1:
                print(f"⚠️ API 调用失败，使用原文: {e}")
                return text
            import time
            time.sleep(2 * (attempt + 1))
            continue

    return text


def _polish_one_segment(idx, seg, total):
    """润色单个 segment（供并发调用）"""
    text = re.sub(r'[ \t]+', ' ', seg['text']).strip()
    polished_text = polish_with_llm(text)
    result = {
        'id': seg['id'],
        'start': seg['start'],
        'end': seg['end'],
        'start_seconds': seg['start_seconds'],
        'end_seconds': seg['end_seconds'],
        'text': polished_text,
        'speaker': seg['speaker'],
        'speaker_role': seg.get('speaker_role', 'unknown'),
        'speaker_confidence': seg.get('speaker_confidence', 'low'),
    }
    print(f"   [{idx}/{total}] {seg['start']} - {seg['end']} ({len(text)}字) ✓ ({len(polished_text)}字)")
    return idx, result


def _flush_chunk(merged, chunk):
    """Flush a chunk of segments into a merged segment."""
    combined_text = ''.join([seg['text'].strip() for seg in chunk])
    speaker = chunk[0].get('speaker', 'Unknown')
    merged.append({
        'id': len(merged),
        'start': chunk[0].get('start', '00:00:00'),
        'end': chunk[-1].get('end', '00:00:00'),
        'start_seconds': chunk[0].get('start_seconds', 0),
        'end_seconds': chunk[-1].get('end_seconds', 0),
        'text': combined_text,
        'speaker': speaker,
        'speaker_role': chunk[0].get('speaker_role', 'unknown'),
        'speaker_confidence': chunk[0].get('speaker_confidence', 'low'),
        'original_ids': [seg.get('id', i) for i, seg in enumerate(chunk)]
    })


def merge_segments_for_polishing(segments, merge_count=15):
    """将相邻 segments 合并成段落（speaker 变化时强制分割）"""
    merged = []
    current_chunk = []

    for seg in segments:
        if current_chunk and seg.get('speaker', 'Unknown') != current_chunk[-1].get('speaker', 'Unknown'):
            _flush_chunk(merged, current_chunk)
            current_chunk = []

        current_chunk.append(seg)

        if len(current_chunk) >= merge_count:
            _flush_chunk(merged, current_chunk)
            current_chunk = []

    if current_chunk:
        _flush_chunk(merged, current_chunk)

    return merged


def polish_full_transcript(input_file, output_file, merge_count=15):
    """润色整个转录文件（并发加速）"""
    print(f"📖 读取原始转录: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        transcript = json.load(f)

    segments = transcript['segments']
    print(f"   总片段数: {len(segments)}")

    # 合并 segments
    print(f"\n🔗 合并 segments (每 {merge_count} 个合并，speaker 变化强制分割)")
    merged = merge_segments_for_polishing(segments, merge_count)
    print(f"   合并后段落数: {len(merged)}")

    # 并发润色
    print(f"\n✨ 开始润色 (模型: {POLISH_MODEL}, 并发: {MAX_WORKERS})...")
    polished_segments = [None] * len(merged)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        for i, seg in enumerate(merged):
            future = executor.submit(_polish_one_segment, i + 1, seg, len(merged))
            futures[future] = i

        for future in as_completed(futures):
            try:
                idx, result = future.result()
                polished_segments[idx - 1] = result
            except Exception as e:
                i = futures[future]
                print(f"   [{i+1}/{len(merged)}] ✗ 失败: {e}")
                seg = merged[i]
                polished_segments[i] = {
                    'id': seg['id'],
                    'start': seg['start'],
                    'end': seg['end'],
                    'start_seconds': seg['start_seconds'],
                    'end_seconds': seg['end_seconds'],
                    'text': seg['text'],
                    'speaker': seg['speaker'],
                    'speaker_role': seg.get('speaker_role', 'unknown'),
                    'speaker_confidence': seg.get('speaker_confidence', 'low'),
                }

    # Filter out any None entries (shouldn't happen but safety)
    polished_segments = [s for s in polished_segments if s is not None]

    # 保存
    output = {
        'language': transcript.get('language', 'zh'),
        'segments': polished_segments
    }

    print(f"\n💾 保存润色后文件: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 完成！")
    print(f"   原始片段: {len(segments)}")
    print(f"   润色段落: {len(polished_segments)}")
    print(f"   输出文件: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python step3_polish_transcript.py <input_json> [output_json] [merge_count]")
        print("")
        print("参数:")
        print("  input_json   : 输入的转录 JSON 文件")
        print("  output_json  : 输出的润色后 JSON 文件（可选，默认为 input_polished.json）")
        print("  merge_count  : 每几个 segments 合并一次（可选，默认 15）")
        sys.exit(1)

    input_file = sys.argv[1]

    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_polished.json"

    merge_count = int(sys.argv[3]) if len(sys.argv) > 3 else 15

    polish_full_transcript(input_file, output_file, merge_count)
