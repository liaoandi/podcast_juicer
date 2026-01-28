#!/usr/bin/env python3
"""
高级转录脚本 - 支持更强模型和说话人识别

功能：
1. 使用 Whisper large-v3（最强模型）
2. 支持说话人识别（pyannote.audio）
3. 输出带说话人标记的转录

依赖安装：
    pip install openai-whisper pyannote.audio

使用方法：
    python transcribe_advanced.py <audio_file> [model_size]

    model_size: base, large-v3 (default: large-v3)

说明：
    - large-v3: 最准确，但最慢（约 4-5 倍于 base）
    - 说话人识别需要额外的 Hugging Face token（可选）
"""

import whisper
import json
import sys
import os
import torch
import subprocess

def preprocess_audio(audio_file):
    """
    预处理音频：转换为 16kHz 单声道 WAV
    这样可以提升 Whisper 和 pyannote 的性能和准确度

    Args:
        audio_file: 原始音频文件路径

    Returns:
        预处理后的 WAV 文件路径
    """
    # 如果已经是处理过的 WAV，直接返回
    if audio_file.endswith('_16k.wav'):
        return audio_file

    base_name = audio_file.rsplit('.', 1)[0]
    output_file = f"{base_name}_16k.wav"

    # 如果已经存在，直接使用
    if os.path.exists(output_file):
        print(f"✓ 使用已存在的预处理音频: {output_file}")
        return output_file

    print(f"🔄 预处理音频: {audio_file}")
    print(f"   转换为 16kHz 单声道 WAV...")

    try:
        # 使用 ffmpeg 转换
        cmd = [
            'ffmpeg',
            '-i', audio_file,
            '-ar', '16000',  # 采样率 16kHz
            '-ac', '1',       # 单声道
            '-y',             # 覆盖已存在的文件
            output_file
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )

        print(f"✓ 预处理完成: {output_file}")
        return output_file

    except subprocess.CalledProcessError as e:
        print(f"⚠️  音频预处理失败，使用原文件")
        print(f"   错误: {e.stderr.decode()}")
        return audio_file
    except FileNotFoundError:
        print(f"⚠️  未找到 ffmpeg，使用原文件")
        print(f"   安装: brew install ffmpeg (macOS) 或 apt install ffmpeg (Linux)")
        return audio_file

def transcribe_with_whisper(audio_file, model_size='large-v3'):
    """
    使用 Whisper 转录音频

    Args:
        audio_file: 音频文件路径
        model_size: 模型大小 (base, small, medium, large, large-v3)

    Returns:
        转录结果（JSON 格式）
    """
    print(f"🎙️  加载 Whisper 模型: {model_size}")
    print(f"   注意：large-v3 模型下载较大（约 3GB），首次使用需要时间")

    try:
        model = whisper.load_model(model_size)
    except Exception as e:
        print(f"❌ 加载模型失败: {e}")
        print(f"   尝试使用 base 模型...")
        model = whisper.load_model("base")
        model_size = "base"

    print(f"\n🔊 转录音频: {audio_file}")
    print(f"   使用模型: {model_size}")
    print(f"   预计时间: {'10-15 分钟' if model_size == 'large-v3' else '2-3 分钟'}")

    result = model.transcribe(
        audio_file,
        language="zh",
        verbose=True,
        word_timestamps=True  # 获取词级时间戳（用于后续说话人分离）
    )

    return result

def try_speaker_diarization(audio_file):
    """
    尝试使用 pyannote.audio 进行说话人分离

    需要 Hugging Face token，从这里获取：
    https://huggingface.co/settings/tokens

    并接受模型许可：
    https://huggingface.co/pyannote/speaker-diarization

    Returns:
        说话人时间轴，或 None（如果不可用）
    """
    try:
        from pyannote.audio import Pipeline

        # 检查环境变量中的 token
        hf_token = os.environ.get('HUGGINGFACE_TOKEN')

        if not hf_token:
            print("\n⚠️  未找到 HUGGINGFACE_TOKEN 环境变量")
            print("   说话人识别需要 Hugging Face token")
            print("   获取方式：https://huggingface.co/settings/tokens")
            print("   使用: export HUGGINGFACE_TOKEN=your_token")
            print("   跳过说话人识别...\n")
            return None

        print("\n👥 加载说话人分离模型...")

        # 临时允许不安全的模型加载（pyannote 模型需要）
        import torch.serialization
        torch.serialization.add_safe_globals([torch.torch_version.TorchVersion])

        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            token=hf_token
        )

        print("   分析说话人...")
        diarization = pipeline(audio_file)

        # 转换为时间轴格式
        speaker_timeline = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            speaker_timeline.append({
                'start': turn.start,
                'end': turn.end,
                'speaker': speaker
            })

        print(f"   识别到 {len(set([s['speaker'] for s in speaker_timeline]))} 位说话人")
        return speaker_timeline

    except ImportError:
        print("\n⚠️  pyannote.audio 未安装")
        print("   安装: pip install pyannote.audio")
        print("   跳过说话人识别...\n")
        return None
    except Exception as e:
        print(f"\n⚠️  说话人识别失败: {e}")
        print("   继续使用基础转录...\n")
        return None

def match_speakers_to_segments(segments, speaker_timeline):
    """
    将说话人标记匹配到转录 segments（优化版 O(N+M)）

    Args:
        segments: Whisper 转录的 segments
        speaker_timeline: 说话人时间轴

    Returns:
        带说话人标记的 segments
    """
    if not speaker_timeline:
        return segments

    print("\n🔗 匹配说话人到转录片段...")

    # 排序 speaker_timeline，确保时间顺序
    speaker_timeline = sorted(speaker_timeline, key=lambda x: x["start"])
    j = 0
    n = len(speaker_timeline)

    for seg in segments:
        # 使用 start_seconds 和 end_seconds（数值字段），而不是格式化后的字符串
        seg_mid = (seg["start_seconds"] + seg["end_seconds"]) / 2.0

        # 双指针优化：跳过已经过期的 speaker 时间段
        while j + 1 < n and speaker_timeline[j]["end"] < seg_mid:
            j += 1

        # 检查当前 speaker 时间段是否匹配
        if speaker_timeline[j]["start"] <= seg_mid <= speaker_timeline[j]["end"]:
            seg["speaker"] = speaker_timeline[j]["speaker"]
        else:
            seg["speaker"] = "Unknown"

    # 统计说话人
    speakers = {}
    for seg in segments:
        speaker = seg.get('speaker', 'Unknown')
        speakers[speaker] = speakers.get(speaker, 0) + 1

    print(f"   说话人分布:")
    for speaker, count in sorted(speakers.items()):
        print(f"     {speaker}: {count} 段")

    return segments

def format_timestamp(seconds):
    """将秒数转换为 HH:MM:SS 格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def save_transcript(result, output_file, speaker_timeline=None):
    """保存转录结果为 JSON"""

    segments = []
    for i, seg in enumerate(result['segments']):
        segments.append({
            'id': i,
            'start': format_timestamp(seg['start']),
            'end': format_timestamp(seg['end']),
            'start_seconds': seg['start'],
            'end_seconds': seg['end'],
            'text': seg['text'].strip(),
            'speaker': seg.get('speaker', 'Unknown')
        })

    # 匹配说话人
    if speaker_timeline:
        segments = match_speakers_to_segments(segments, speaker_timeline)

    output = {
        'language': result['language'],
        'segments': segments
    }

    print(f"\n💾 保存转录: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 完成！")
    print(f"   文件: {output_file}")
    print(f"   片段: {len(segments)}")
    print(f"   总时长: {segments[-1]['end']}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python transcribe_advanced.py <audio_file> [model_size]")
        print("模型: base (快), large-v3 (准确)")
        sys.exit(1)

    audio_file = sys.argv[1]
    model_size = sys.argv[2] if len(sys.argv) > 2 else "large-v3"

    # 预处理音频（转换为 16kHz 单声道 WAV）
    processed_audio = preprocess_audio(audio_file)

    # 转录
    result = transcribe_with_whisper(processed_audio, model_size)

    # 说话人识别（可选）
    speaker_timeline = try_speaker_diarization(processed_audio)

    # 保存
    base_name = audio_file.rsplit('.', 1)[0]
    output_file = f"{base_name}_transcript_advanced.json"
    save_transcript(result, output_file, speaker_timeline)
