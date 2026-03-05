from transcript_utils import format_timestamp, match_speakers_to_segments


def test_format_timestamp_basic():
    assert format_timestamp(0) == "00:00:00"
    assert format_timestamp(59) == "00:00:59"
    assert format_timestamp(61) == "00:01:01"
    assert format_timestamp(3661) == "01:01:01"


def test_match_speakers_to_segments_assigns():
    segments = [
        {"start_seconds": 0.0, "end_seconds": 2.0, "text": "A"},
        {"start_seconds": 2.0, "end_seconds": 4.0, "text": "B"},
        {"start_seconds": 4.0, "end_seconds": 6.0, "text": "C"},
    ]
    timeline = [
        {"start": 0.0, "end": 3.0, "speaker": "SPEAKER_00"},
        {"start": 3.0, "end": 10.0, "speaker": "SPEAKER_01"},
    ]
    out = match_speakers_to_segments(segments, timeline)
    assert out[0]["speaker"] == "SPEAKER_00"
    assert out[1]["speaker"] == "SPEAKER_00"
    assert out[2]["speaker"] == "SPEAKER_01"


def test_match_speakers_to_segments_unknown_when_no_match():
    segments = [
        {"start_seconds": 10.0, "end_seconds": 12.0, "text": "A"},
    ]
    timeline = [
        {"start": 0.0, "end": 5.0, "speaker": "SPEAKER_00"},
    ]
    out = match_speakers_to_segments(segments, timeline)
    assert out[0]["speaker"] == "Unknown"
