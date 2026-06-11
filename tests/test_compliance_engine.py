"""
Tests for src/reasoning/compliance_engine.py

All unit tests — no Azure required. OpenAI client is mocked throughout.

Owner: Priya (reasoning pipeline)
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from src.reasoning.compliance_engine import (
    _lookup_segment_timestamps,
    _null_verdict,
    reason_step,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_run_id():
    return "run-test-00000001"


@pytest.fixture
def sample_checklist_item():
    return {
        "item_id": "check-001",
        "step_id": "step-001",
        "sequence": 1,
        "criterion": "Worker attaches Y-axis motor to frame using M3x10 screws",
        "check_type": "presence",
        "expected_duration_seconds": None,
        "sop_section": "2.1 Y-Axis Assembly",
    }


@pytest.fixture
def sample_observations():
    """Two-segment observations dict matching schemas/video_observations.json."""
    return {
        "run_id": "run-test-00000001",
        "video_file": "https://example.com/video.mp4",
        "analyzer_id": "procedureguard_compliance_v1",
        "analyzed_at": "2026-06-11T10:00:00Z",
        "total_segments": 2,
        "segments": [
            {
                "segment_id": "seg-001",
                "start_time_seconds": 0.0,
                "end_time_seconds": 45.2,
                "description": "Worker picks up screwdriver and attaches motor bracket.",
                "ppe_status": "compliant",
                "tool_in_use": "screwdriver",
                "component_contact": "Y-axis motor bracket",
                "visible_safety_concern": False,
                "action_observed": "Worker secures Y-axis motor to frame using a screwdriver.",
            },
            {
                "segment_id": "seg-002",
                "start_time_seconds": 45.2,
                "end_time_seconds": 82.7,
                "description": "Worker threads belt through pulley.",
                "ppe_status": "compliant",
                "tool_in_use": None,
                "component_contact": "Y-axis belt",
                "visible_safety_concern": False,
                "action_observed": "Worker threads the belt through the motor pulley.",
            },
        ],
    }


def _make_openai_mock(response_dict: dict) -> MagicMock:
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps(response_dict)
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


# ── reason_step: output schema ────────────────────────────────────────────────

def test_reason_step_returns_all_schema_keys(
    sample_checklist_item, sample_observations, sample_run_id
):
    """Output must contain every key in schemas/verification_record.json."""
    expected_keys = {
        "run_id", "item_id", "step_id", "sequence", "criterion",
        "verdict", "confidence", "evidence_segment_id",
        "evidence_timestamp_start", "evidence_timestamp_end",
        "keyframe_blob_path", "reasoning",
        "sequence_ok", "duration_ok", "created_at",
    }
    mock_client = _make_openai_mock({
        "verdict": "Compliant",
        "confidence": 0.91,
        "evidence_segment_id": "seg-001",
        "reasoning": "Segment 1 shows the motor being attached.",
    })
    with patch("src.reasoning.compliance_engine.get_openai_client", return_value=mock_client):
        result = reason_step(sample_checklist_item, sample_observations, sample_run_id)

    assert set(result.keys()) == expected_keys


def test_reason_step_checklist_fields_passed_through(
    sample_checklist_item, sample_observations, sample_run_id
):
    """item_id, step_id, sequence, and criterion must be copied from the checklist item."""
    mock_client = _make_openai_mock({
        "verdict": "Compliant", "confidence": 0.9,
        "evidence_segment_id": "seg-001", "reasoning": "Looks good.",
    })
    with patch("src.reasoning.compliance_engine.get_openai_client", return_value=mock_client):
        result = reason_step(sample_checklist_item, sample_observations, sample_run_id)

    assert result["item_id"] == "check-001"
    assert result["step_id"] == "step-001"
    assert result["sequence"] == 1
    assert result["criterion"] == sample_checklist_item["criterion"]
    assert result["run_id"] == sample_run_id


# ── reason_step: verdict parsing ──────────────────────────────────────────────

@pytest.mark.parametrize("verdict", ["Compliant", "Deviation Detected", "Unable to Verify"])
def test_reason_step_valid_verdicts(
    verdict, sample_checklist_item, sample_observations, sample_run_id
):
    """All three valid verdict strings must be accepted and passed through."""
    mock_client = _make_openai_mock({
        "verdict": verdict, "confidence": 0.8,
        "evidence_segment_id": "seg-001", "reasoning": "Test.",
    })
    with patch("src.reasoning.compliance_engine.get_openai_client", return_value=mock_client):
        result = reason_step(sample_checklist_item, sample_observations, sample_run_id)

    assert result["verdict"] == verdict


def test_reason_step_invalid_verdict_coerced_to_unable(
    sample_checklist_item, sample_observations, sample_run_id
):
    """An unrecognised verdict string must be coerced to 'Unable to Verify'."""
    mock_client = _make_openai_mock({
        "verdict": "Inconclusive", "confidence": 0.5,
        "evidence_segment_id": None, "reasoning": "Not sure.",
    })
    with patch("src.reasoning.compliance_engine.get_openai_client", return_value=mock_client):
        result = reason_step(sample_checklist_item, sample_observations, sample_run_id)

    assert result["verdict"] == "Unable to Verify"


def test_reason_step_confidence_clamped_to_unit_interval(
    sample_checklist_item, sample_observations, sample_run_id
):
    """Confidence values outside [0.0, 1.0] must be clamped."""
    mock_client = _make_openai_mock({
        "verdict": "Compliant", "confidence": 1.5,  # over 1.0
        "evidence_segment_id": "seg-001", "reasoning": "Definitely.",
    })
    with patch("src.reasoning.compliance_engine.get_openai_client", return_value=mock_client):
        result = reason_step(sample_checklist_item, sample_observations, sample_run_id)

    assert result["confidence"] == 1.0


# ── reason_step: evidence segment resolution ─────────────────────────────────

def test_reason_step_timestamps_resolved_from_evidence_segment(
    sample_checklist_item, sample_observations, sample_run_id
):
    """Timestamps must be looked up from the matched segment, not fabricated."""
    mock_client = _make_openai_mock({
        "verdict": "Compliant", "confidence": 0.91,
        "evidence_segment_id": "seg-001",
        "reasoning": "Motor bracket attached in segment 1.",
    })
    with patch("src.reasoning.compliance_engine.get_openai_client", return_value=mock_client):
        result = reason_step(sample_checklist_item, sample_observations, sample_run_id)

    assert result["evidence_segment_id"] == "seg-001"
    assert result["evidence_timestamp_start"] == 0.0
    assert result["evidence_timestamp_end"] == 45.2


def test_reason_step_null_timestamps_when_no_evidence_segment(
    sample_checklist_item, sample_observations, sample_run_id
):
    """When evidence_segment_id is null, timestamps must be None."""
    mock_client = _make_openai_mock({
        "verdict": "Unable to Verify", "confidence": 0.1,
        "evidence_segment_id": None, "reasoning": "Step not visible.",
    })
    with patch("src.reasoning.compliance_engine.get_openai_client", return_value=mock_client):
        result = reason_step(sample_checklist_item, sample_observations, sample_run_id)

    assert result["evidence_segment_id"] is None
    assert result["evidence_timestamp_start"] is None
    assert result["evidence_timestamp_end"] is None
    assert result["keyframe_blob_path"] is None


def test_reason_step_keyframe_path_constructed_when_evidence_present(
    sample_checklist_item, sample_observations, sample_run_id
):
    """keyframe_blob_path must follow the convention keyframes/{run_id}/{step_id}.jpg."""
    mock_client = _make_openai_mock({
        "verdict": "Compliant", "confidence": 0.85,
        "evidence_segment_id": "seg-001", "reasoning": "Seen in seg-001.",
    })
    with patch("src.reasoning.compliance_engine.get_openai_client", return_value=mock_client):
        result = reason_step(sample_checklist_item, sample_observations, sample_run_id)

    assert result["keyframe_blob_path"] == f"keyframes/{sample_run_id}/step-001.jpg"


# ── reason_step: edge cases ───────────────────────────────────────────────────

def test_reason_step_no_segments_skips_api(
    sample_checklist_item, sample_run_id
):
    """Empty observations must return Unable to Verify without calling OpenAI."""
    empty_observations = {"segments": []}
    mock_client = MagicMock()

    with patch("src.reasoning.compliance_engine.get_openai_client", return_value=mock_client):
        result = reason_step(sample_checklist_item, empty_observations, sample_run_id)

    mock_client.chat.completions.create.assert_not_called()
    assert result["verdict"] == "Unable to Verify"
    assert result["confidence"] == 0.0


def test_reason_step_bad_json_returns_null_verdict(
    sample_checklist_item, sample_observations, sample_run_id
):
    """A malformed GPT-4o response must return Unable to Verify rather than raising."""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "not valid json"
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("src.reasoning.compliance_engine.get_openai_client", return_value=mock_client):
        result = reason_step(sample_checklist_item, sample_observations, sample_run_id)

    assert result["verdict"] == "Unable to Verify"


def test_reason_step_sequence_ok_and_duration_ok_are_none(
    sample_checklist_item, sample_observations, sample_run_id
):
    """sequence_ok and duration_ok must be None — they are filled by sequence_timing."""
    mock_client = _make_openai_mock({
        "verdict": "Compliant", "confidence": 0.9,
        "evidence_segment_id": "seg-001", "reasoning": "OK.",
    })
    with patch("src.reasoning.compliance_engine.get_openai_client", return_value=mock_client):
        result = reason_step(sample_checklist_item, sample_observations, sample_run_id)

    assert result["sequence_ok"] is None
    assert result["duration_ok"] is None


def test_reason_step_sends_all_segments_in_user_message(
    sample_checklist_item, sample_observations, sample_run_id
):
    """The user message sent to GPT-4o must contain all segments from observations."""
    mock_client = _make_openai_mock({
        "verdict": "Compliant", "confidence": 0.9,
        "evidence_segment_id": "seg-001", "reasoning": "OK.",
    })
    with patch("src.reasoning.compliance_engine.get_openai_client", return_value=mock_client):
        reason_step(sample_checklist_item, sample_observations, sample_run_id)

    call_kwargs = mock_client.chat.completions.create.call_args
    kwargs = call_kwargs.kwargs if call_kwargs.kwargs else call_kwargs[1]
    messages = kwargs["messages"]
    user_msg = next(m for m in messages if m["role"] == "user")
    payload = json.loads(user_msg["content"])
    assert len(payload["video_segments"]) == 2


# ── _lookup_segment_timestamps ────────────────────────────────────────────────

def test_lookup_returns_correct_timestamps():
    segments = [
        {"segment_id": "seg-001", "start_time_seconds": 0.0, "end_time_seconds": 30.0},
        {"segment_id": "seg-002", "start_time_seconds": 30.0, "end_time_seconds": 60.0},
    ]
    assert _lookup_segment_timestamps("seg-002", segments) == (30.0, 60.0)


def test_lookup_returns_none_for_missing_id():
    segments = [{"segment_id": "seg-001", "start_time_seconds": 0.0, "end_time_seconds": 30.0}]
    assert _lookup_segment_timestamps("seg-999", segments) == (None, None)


def test_lookup_returns_none_for_null_id():
    segments = [{"segment_id": "seg-001", "start_time_seconds": 0.0, "end_time_seconds": 30.0}]
    assert _lookup_segment_timestamps(None, segments) == (None, None)


# ── _null_verdict ─────────────────────────────────────────────────────────────

def test_null_verdict_has_all_required_keys(sample_checklist_item, sample_run_id):
    result = _null_verdict(sample_checklist_item, sample_run_id)
    required = {
        "run_id", "item_id", "step_id", "sequence", "criterion",
        "verdict", "confidence", "evidence_segment_id",
        "evidence_timestamp_start", "evidence_timestamp_end",
        "keyframe_blob_path", "reasoning", "sequence_ok", "duration_ok", "created_at",
    }
    assert set(result.keys()) == required
    assert result["verdict"] == "Unable to Verify"
    assert result["confidence"] == 0.0
