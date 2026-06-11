"""
Tests for src/ingestion/video_analyzer.py

Phase 1 (Content Understanding) and Phase 2 (GPT-4o compliance fields).

Run smoke test against a real video:
  python scripts/test_video_pipeline.py
  python scripts/test_video_pipeline.py --phase2   # also runs GPT-4o extraction

Owner: Priya (video pipeline)
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from src.ingestion.video_analyzer import (
    COMPLIANCE_FIELD_SCHEMA,
    extract_compliance_fields,
    parse_observations,
    run_video_phase2,
)


# ── Unit tests (no Azure required) ──────────────────────────────────────────

def test_compliance_schema_has_required_fields():
    """Compliance field schema must define all 5 required fields."""
    required = {"ppe_status", "tool_in_use", "component_contact",
                "visible_safety_concern", "action_observed"}
    assert required == set(COMPLIANCE_FIELD_SCHEMA.fields.keys())


def test_parse_observations_returns_required_keys(mock_analysis_result, sample_run_id):
    """parse_observations output must contain all top-level schema keys."""
    result = parse_observations(mock_analysis_result, sample_run_id, "https://example.com/video.mp4")
    assert set(result.keys()) == {
        "run_id", "video_file", "analyzer_id", "analyzed_at", "total_segments", "segments"
    }


def test_parse_observations_segment_keys(mock_analysis_result, sample_run_id):
    """Each segment must contain all required field keys including description."""
    result = parse_observations(mock_analysis_result, sample_run_id, "https://example.com/video.mp4")
    assert result["total_segments"] == 1
    seg = result["segments"][0]
    assert set(seg.keys()) == {
        "segment_id", "start_time_seconds", "end_time_seconds",
        "description",
        "ppe_status", "tool_in_use", "component_contact",
        "visible_safety_concern", "action_observed",
    }


def test_parse_observations_timestamps(mock_analysis_result, sample_run_id):
    """Segment timestamps must be correctly converted from milliseconds to seconds."""
    result = parse_observations(mock_analysis_result, sample_run_id, "https://example.com/video.mp4")
    seg = result["segments"][0]
    assert seg["start_time_seconds"] == 0.0
    assert seg["end_time_seconds"] == 45.2


def test_parse_observations_skips_non_audiovisual(mock_non_audiovisual_result, sample_run_id):
    """Non-audio-visual content items must be skipped."""
    result = parse_observations(mock_non_audiovisual_result, sample_run_id, "https://example.com/video.mp4")
    assert result["total_segments"] == 0


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_run_id():
    return "run-test-00000001"


class _MockContent:
    """Minimal stand-in for AudioVisualContent returned by the SDK."""
    def __init__(self, kind, start_ms, end_ms, fields=None, markdown=None):
        self.kind = kind
        self.start_time_ms = start_ms
        self.end_time_ms = end_ms
        self.fields = fields or {}
        self.markdown = markdown


class _MockResult:
    def __init__(self, contents):
        self.contents = contents


@pytest.fixture
def mock_analysis_result():
    from azure.ai.contentunderstanding.models import AnalysisContentKind
    content = _MockContent(
        kind=AnalysisContentKind.AUDIO_VISUAL,
        start_ms=0,
        end_ms=45200,
    )
    return _MockResult(contents=[content])


@pytest.fixture
def mock_non_audiovisual_result():
    content = _MockContent(kind="image", start_ms=0, end_ms=5000)
    return _MockResult(contents=[content])


@pytest.fixture
def mock_analysis_result_with_markdown():
    """Analysis result where the segment has a Content Understanding description."""
    from azure.ai.contentunderstanding.models import AnalysisContentKind
    content = _MockContent(
        kind=AnalysisContentKind.AUDIO_VISUAL,
        start_ms=0,
        end_ms=45200,
        markdown="Worker uses an Allen key to tighten three M3 screws on the motor bracket.",
    )
    return _MockResult(contents=[content])


def _make_openai_mock(response_json: dict) -> MagicMock:
    """Return a mock AzureOpenAI client that returns a canned JSON completion."""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps(response_json)
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


# ── Phase 2: parse_observations description capture ──────────────────────────

def test_parse_observations_description_from_markdown(
    mock_analysis_result_with_markdown, sample_run_id
):
    """description must be populated from content.markdown when present."""
    result = parse_observations(
        mock_analysis_result_with_markdown, sample_run_id, "https://example.com/video.mp4"
    )
    assert result["segments"][0]["description"] == (
        "Worker uses an Allen key to tighten three M3 screws on the motor bracket."
    )


def test_parse_observations_description_empty_when_no_markdown(
    mock_analysis_result, sample_run_id
):
    """description must be empty string when content has no markdown attribute."""
    result = parse_observations(mock_analysis_result, sample_run_id, "https://example.com/video.mp4")
    assert result["segments"][0]["description"] == ""


# ── Phase 2: extract_compliance_fields ───────────────────────────────────────

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


def test_extract_compliance_fields_empty_description_skips_api():
    """Empty description with no image URL must return null fields without calling OpenAI."""
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


def test_extract_compliance_fields_vision_mode_sends_image_url():
    """When keyframe_image_url is provided, the request must include image_url content."""
    canned = {
        "ppe_status": "compliant",
        "tool_in_use": None,
        "component_contact": None,
        "visible_safety_concern": False,
        "action_observed": "Worker inspects completed assembly.",
    }
    mock_client = _make_openai_mock(canned)
    image_url = "https://pgstorepriya2026.blob.core.windows.net/keyframes/run-001/seg-001.jpg?sv=..."

    with patch("src.ingestion.video_analyzer.get_openai_client", return_value=mock_client):
        extract_compliance_fields(
            description="Worker inspects assembly.",
            segment_id="seg-001",
            run_id="run-test-001",
            keyframe_image_url=image_url,
        )

    call_kwargs = mock_client.chat.completions.create.call_args
    messages = call_kwargs.kwargs.get("messages") or call_kwargs[1]["messages"]
    user_message = next(m for m in messages if m["role"] == "user")
    # User content must be a list containing an image_url item
    assert isinstance(user_message["content"], list)
    image_items = [c for c in user_message["content"] if c.get("type") == "image_url"]
    assert len(image_items) == 1
    assert image_items[0]["image_url"]["url"] == image_url


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


# ── Phase 2: run_video_phase2 ────────────────────────────────────────────────

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

    with patch(
        "src.ingestion.video_analyzer.extract_compliance_fields",
        return_value=canned_fields,
    ) as mock_ecf:
        result = run_video_phase2(observations, sample_run_id)

    assert mock_ecf.call_count == 2
    for seg in result["segments"]:
        assert seg["ppe_status"] == "compliant"
        assert seg["action_observed"] == "Worker tightens screws."


def test_run_video_phase2_passes_keyframe_url_to_extractor(sample_run_id):
    """keyframe_urls dict must be forwarded to extract_compliance_fields per segment."""
    observations = {
        "run_id": sample_run_id,
        "segments": [
            {
                "segment_id": "seg-001",
                "description": "Worker attaches motor.",
                "ppe_status": None,
                "tool_in_use": None,
                "component_contact": None,
                "visible_safety_concern": False,
                "action_observed": None,
            }
        ],
        "total_segments": 1,
    }
    keyframe_urls = {"seg-001": "https://example.com/keyframes/seg-001.jpg"}

    with patch(
        "src.ingestion.video_analyzer.extract_compliance_fields",
        return_value={
            "ppe_status": None,
            "tool_in_use": None,
            "component_contact": None,
            "visible_safety_concern": False,
            "action_observed": None,
        },
    ) as mock_ecf:
        run_video_phase2(observations, sample_run_id, keyframe_urls=keyframe_urls)

    _, kwargs = mock_ecf.call_args
    assert kwargs.get("keyframe_image_url") == "https://example.com/keyframes/seg-001.jpg"
