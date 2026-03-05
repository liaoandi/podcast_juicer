import json
import os

from step0b_search_transcript import convert_to_segments


def test_convert_to_segments_estimates_timing(tmp_path, monkeypatch):
    transcript_text = "第一段内容。\n\n第二段内容更长一些。"
    out_file = tmp_path / "official.json"
    monkeypatch.setenv("TRANSCRIPT_CHARS_PER_SEC", "4.0")

    convert_to_segments(transcript_text, str(out_file), audio_path=None)

    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["is_official_transcript"] is True
    assert data["timing_estimated"] is True
    assert len(data["segments"]) >= 2
    # monotonic timestamps
    starts = [s["start_seconds"] for s in data["segments"]]
    ends = [s["end_seconds"] for s in data["segments"]]
    assert all(s2 >= s1 for s1, s2 in zip(starts, starts[1:]))
    assert all(e2 >= e1 for e1, e2 in zip(ends, ends[1:]))
