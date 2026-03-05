from gemini_utils import clean_json
from step2_identify_speakers import GeminiSpeakerIdentifier


def test_clean_json_strips_fences():
    text = "```json\n{\"ok\": true}\n```"
    assert clean_json(text) == {"ok": True}


def test_step2_clean_json_handles_truncation():
    # truncated speaker_labels array should be repaired
    text = "{\"speaker_labels\": [{\"index\": 0, \"speaker\": \"A\"}"
    result = GeminiSpeakerIdentifier._clean_json(text)
    assert result is not None
    assert "speaker_labels" in result
    assert isinstance(result["speaker_labels"], list)
