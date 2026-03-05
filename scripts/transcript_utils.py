#!/usr/bin/env python3
"""
Transcript helper utilities shared by steps and tests.
"""

import json


def format_timestamp(seconds):
    """将秒数转换为 HH:MM:SS 格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


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

    speaker_timeline = sorted(speaker_timeline, key=lambda x: x["start"])
    j = 0
    n = len(speaker_timeline)

    for seg in segments:
        seg_mid = (seg["start_seconds"] + seg["end_seconds"]) / 2.0

        while j + 1 < n and speaker_timeline[j]["end"] < seg_mid:
            j += 1

        if speaker_timeline[j]["start"] <= seg_mid <= speaker_timeline[j]["end"]:
            seg["speaker"] = speaker_timeline[j]["speaker"]
        else:
            seg["speaker"] = "Unknown"

    speakers = {}
    for seg in segments:
        speaker = seg.get("speaker", "Unknown")
        speakers[speaker] = speakers.get(speaker, 0) + 1

    print("   说话人分布:")
    for speaker, count in sorted(speakers.items()):
        print(f"     {speaker}: {count} 段")

    return segments


def save_transcript(result, output_file, speaker_timeline=None):
    """保存转录结果为 JSON"""

    segments = []
    for i, seg in enumerate(result["segments"]):
        segments.append({
            "id": i,
            "start": format_timestamp(seg["start"]),
            "end": format_timestamp(seg["end"]),
            "start_seconds": seg["start"],
            "end_seconds": seg["end"],
            "text": seg["text"].strip(),
            "speaker": seg.get("speaker", "Unknown"),
        })

    if speaker_timeline:
        segments = match_speakers_to_segments(segments, speaker_timeline)

    output = {
        "language": result["language"],
        "segments": segments,
    }

    print(f"\n💾 保存转录: {output_file}")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\n✅ 完成！")
    print(f"   文件: {output_file}")
    print(f"   片段: {len(segments)}")
    if segments:
        print(f"   总时长: {segments[-1]['end']}")
