"""
Tests for src/ingestion/video_analyzer.py

Phase 2 only — GPT-4o Vision compliance field extraction from time-windowed
segments. Phase 1 (Content Understanding) was removed June 18; duration is now
probed via OpenCV and segments are synthesized by build_time_windowed_segments().

Run smoke test against a real video:
  python scripts/test_video_pipeline.py
  python scripts/test_video_pipeline.py --phase2   # also runs GPT-4o extraction

Owner: Priya (video pipeline)
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from src.ingestion.video_analyzer import (
    build_time_windowed_segments,
    extract_compliance_fields,
    run_video_phase2,
)


# ── build_time_windowed_segments (no Azure required) ─────────────────────────

def test_windows_cover_full_duration():
    """Windows must tile from 0 to the clip end with no trailing gap."""
    segs = build_time_windowed_segments(300.0, window_seconds=25.0, overlap_seconds=6.0)
    assert segs[0]["start_time_seconds"] == 0.0
    assert segs[-1]["end_time_seconds"] >= 300.0 - 0.01


def test_windows_respect_max_cap():
    """Window count never exceeds max_windows, even on long clips."""
    segs = build_time_windowed_segments(3600.0, window_seconds=25.0, overlap_seconds=6.0, max_windows=20)
    assert len(segs) <= 20


def test_windows_empty_for_zero_duration():
    """A non-positive duration yields no windows."""
    assert build_time_windowed_segments(0.0) == []


def test_window_segments_have_null_compliance_fields():
    """Fresh segment stubs must carry nulled compliance fields for Phase 2 to fill."""
    seg = build_time_windowed_segments(60.0)[0]
    assert seg["ppe_status"] is None
    assert seg["action_observed"] is None
    assert seg["visible_safety_concern"] is False


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_run_id():
    return "run-test-00000001"


def _make_openai_mock(response_json: dict) -> MagicMock:
    """Return a mock AzureOpenAI client that returns a canned JSON completion."""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps(response_json)
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


# ── extract_compliance_fields ────────────────────────────────────────────────

def test_extract_compliance_fields_returns_all_keys():
    """Must return all 5 compliance field keys with correct types."""
    canned = {
        "ppe_status": "compliant",
        "tool_in_use": "Allen key",
        "component_contact": "M3 screw on motor bracket",
        "visible_safety_concern": False,
        "action_observed": "Worker tightens three screws on the motor bracket.",
    }
    mock_client = _make_openai_mock(canned)

    with patch("src.ingestion.video_analyzer.get_openai_client", return_value=mock_client):
        result = extract_compliance_fields(
            description="Worker tightens motor bracket screws with an Allen key.",
            segment_id="seg-001",
            run_id="run-test-001",
        )

    assert set(result.keys()) == {
        "ppe_status", "tool_in_use", "component_contact",
        "visible_safety_concern", "action_observed",
    }
    assert result["ppe_status"] == "compliant"
    assert result["tool_in_use"] == "Allen key"
    assert result["visible_safety_concern"] is False
    assert isinstance(result["action_observed"], str)


def test_extract_compliance_fields_empty_description_and_no_images_skips_api():
    """Empty description with no frames must return null fields without calling OpenAI."""
    mock_client = MagicMock()

    with patch("src.ingestion.video_analyzer.get_openai_client", return_value=mock_client):
        result = extract_compliance_fields(
            description="",
            segment_id="seg-002",
            run_id="run-test-001",
        )

    mock_client.chat.completions.create.assert_not_called()
    assert result["ppe_status"] is None
    assert result["tool_in_use"] is None
    assert result["action_observed"] is None
    assert result["visible_safety_concern"] is False


def test_extract_compliance_fields_vision_mode_sends_image_content():
    """When keyframe_images is provided, the request must include image_url content items."""
    canned = {
        "ppe_status": "compliant",
        "tool_in_use": None,
        "component_contact": None,
        "visible_safety_concern": False,
        "action_observed": "Worker inspects completed assembly.",
    }
    mock_client = _make_openai_mock(canned)
    frames = [
        "data:image/jpeg;base64,AAAA",
        "data:image/jpeg;base64,BBBB",
    ]

    with patch("src.ingestion.video_analyzer.get_openai_client", return_value=mock_client):
        extract_compliance_fields(
            description="",
            segment_id="seg-001",
            run_id="run-test-001",
            keyframe_images=frames,
        )

    call_kwargs = mock_client.chat.completions.create.call_args
    messages = call_kwargs.kwargs.get("messages") or call_kwargs[1]["messages"]
    user_message = next(m for m in messages if m["role"] == "user")
    # User content must be a list containing one image_url item per frame
    assert isinstance(user_message["content"], list)
    image_items = [c for c in user_message["content"] if c.get("type") == "image_url"]
    assert len(image_items) == len(frames)
    assert image_items[0]["image_url"]["url"] == frames[0]
    assert image_items[0]["image_url"]["detail"] == "high"


def test_extract_compliance_fields_bad_json_returns_nulls():
    """A malformed GPT-4o response must return null fields rather than raise."""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "not json at all"
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("src.ingestion.video_analyzer.get_openai_client", return_value=mock_client):
        result = extract_compliance_fields(
            description="Some description.",
            segment_id="seg-001",
            run_id="run-test-001",
        )

    assert result["ppe_status"] is None
    assert result["action_observed"] is None


# ── run_video_phase2 ─────────────────────────────────────────────────────────

def test_run_video_phase2_fills_all_segments(sample_run_id):
    """run_video_phase2 must call extract_compliance_fields for every segment."""
    observations = {
        "run_id": sample_run_id,
        "segments": [
            {
                "segment_id": "seg-001",
                "start_time_seconds": 0.0,
                "end_time_seconds": 30.0,
                "description": "Worker attaches motor.",
                "ppe_status": None,
                "tool_in_use": None,
                "component_contact": None,
                "visible_safety_concern": False,
                "action_observed": None,
            },
            {
                "segment_id": "seg-002",
                "start_time_seconds": 30.0,
                "end_time_seconds": 60.0,
                "description": "Worker threads belt.",
                "ppe_status": None,
                "tool_in_use": None,
                "component_contact": None,
                "visible_safety_concern": False,
                "action_observed": None,
            },
        ],
        "total_segments": 2,
    }

    canned_fields = {
        "ppe_status": "compliant",
        "tool_in_use": "Allen key",
        "component_contact": "motor bracket",
        "visible_safety_concern": False,
        "action_observed": "Worker tightens screws.",
    }

    # No video_url → text-only mode, so no OpenCV. Patch the field extractor.
    with patch(
        "src.ingestion.video_analyzer.extract_compliance_fields",
        return_value=canned_fields,
    ) as mock_ecf:
        result = run_video_phase2(observations, sample_run_id)

    assert mock_ecf.call_count == 2
    for seg in result["segments"]:
        assert seg["ppe_status"] == "compliant"
        assert seg["action_observed"] == "Worker tightens screws."
