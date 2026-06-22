"""
Tests for src/reasoning/checklist_generator.py

All tests are unit tests — no Azure required. The OpenAI client is mocked
so these run in CI without any credentials.

Owner: Priya (reasoning pipeline)
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from src.reasoning.checklist_generator import (
    _validate_items,
    generate_checklist,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_run_id():
    return "run-test-00000001"


@pytest.fixture
def sample_sop_steps():
    """Three-step SOP matching schemas/sop_steps.json."""
    return {
        "run_id": "run-test-00000001",
        "sop_document": "prusa-mk3s-assembly-v2.pdf",
        "extracted_at": "2026-06-11T10:00:00Z",
        "total_steps": 3,
        "steps": [
            {
                "step_id": "step-001",
                "sequence": 1,
                "description": "Attach the Y-axis motor to the frame using M3x10 screws. Torque to 0.4 Nm.",
                "check_type": "presence",
                "expected_duration_seconds": None,
                "section": "2.1 Y-Axis Assembly",
                "visual_references": ["figure-2a"],
            },
            {
                "step_id": "step-002",
                "sequence": 2,
                "description": "Thread the Y-axis belt through the motor pulley. Belt must be taut with no slack.",
                "check_type": "presence",
                "expected_duration_seconds": None,
                "section": "2.2 Y-Axis Belt",
                "visual_references": [],
            },
            {
                "step_id": "step-003",
                "sequence": 3,
                "description": "Allow adhesive to cure for minimum 30 seconds before proceeding.",
                "check_type": "duration",
                "expected_duration_seconds": 30,
                "section": "2.3 Adhesive Application",
                "visual_references": [],
            },
        ],
    }


@pytest.fixture
def canned_gpt_response():
    """Minimal valid GPT-4o response for the three-step SOP."""
    return {
        "items": [
            {
                "item_id": "check-001",
                "step_id": "step-001",
                "sequence": 1,
                "criterion": "Worker attaches Y-axis motor to frame using M3x10 screws",
                "observable_action": "The Y-axis motor is mounted onto the frame.",
                "verifiability": "presence",
                "key_objects": [],
                "check_type": "presence",
                "expected_duration_seconds": None,
                "sop_section": "2.1 Y-Axis Assembly",
            },
            {
                "item_id": "check-002",
                "step_id": "step-002",
                "sequence": 2,
                "criterion": "Worker threads belt through pulley with no visible slack",
                "observable_action": "The belt is threaded through the motor pulley.",
                "verifiability": "sequence",
                "key_objects": [],
                "check_type": "sequence",
                "expected_duration_seconds": None,
                "sop_section": "2.2 Y-Axis Belt",
            },
            {
                "item_id": "check-003",
                "step_id": "step-003",
                "sequence": 3,
                "criterion": "Worker waits at least 30 seconds after adhesive application",
                "observable_action": None,
                "verifiability": "fine_detail",
                "key_objects": [],
                "check_type": "duration",
                "expected_duration_seconds": 30,
                "sop_section": "2.3 Adhesive Application",
            },
        ]
    }


def _make_openai_mock(response_dict: dict) -> MagicMock:
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps(response_dict)
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


# ── generate_checklist: top-level schema ─────────────────────────────────────

def test_generate_checklist_top_level_keys(
    sample_sop_steps, sample_run_id, canned_gpt_response
):
    """Output must contain all top-level schema keys."""
    mock_client = _make_openai_mock(canned_gpt_response)
    with patch("src.reasoning.checklist_generator.get_openai_client", return_value=mock_client):
        result = generate_checklist(sample_sop_steps, sample_run_id)

    assert set(result.keys()) == {
        "run_id", "sop_document", "created_at", "total_items", "items"
    }
    assert result["run_id"] == sample_run_id
    assert result["sop_document"] == "prusa-mk3s-assembly-v2.pdf"


def test_generate_checklist_item_count_matches_steps(
    sample_sop_steps, sample_run_id, canned_gpt_response
):
    """total_items must equal the number of items in the list."""
    mock_client = _make_openai_mock(canned_gpt_response)
    with patch("src.reasoning.checklist_generator.get_openai_client", return_value=mock_client):
        result = generate_checklist(sample_sop_steps, sample_run_id)

    assert result["total_items"] == 3
    assert len(result["items"]) == 3


def test_generate_checklist_item_keys(
    sample_sop_steps, sample_run_id, canned_gpt_response
):
    """Every item must contain all 7 required keys."""
    required = {
        "item_id", "step_id", "sequence", "criterion",
        "check_type", "expected_duration_seconds", "sop_section",
    }
    mock_client = _make_openai_mock(canned_gpt_response)
    with patch("src.reasoning.checklist_generator.get_openai_client", return_value=mock_client):
        result = generate_checklist(sample_sop_steps, sample_run_id)

    for item in result["items"]:
        assert set(item.keys()) >= required, f"Item missing keys: {required - set(item.keys())}"


def test_generate_checklist_step_ids_preserved(
    sample_sop_steps, sample_run_id, canned_gpt_response
):
    """step_ids in checklist items must match the input SOP step_ids."""
    mock_client = _make_openai_mock(canned_gpt_response)
    with patch("src.reasoning.checklist_generator.get_openai_client", return_value=mock_client):
        result = generate_checklist(sample_sop_steps, sample_run_id)

    output_step_ids = [item["step_id"] for item in result["items"]]
    assert output_step_ids == ["step-001", "step-002", "step-003"]


def test_generate_checklist_duration_item_has_seconds(
    sample_sop_steps, sample_run_id, canned_gpt_response
):
    """Duration check items must carry a numeric expected_duration_seconds."""
    mock_client = _make_openai_mock(canned_gpt_response)
    with patch("src.reasoning.checklist_generator.get_openai_client", return_value=mock_client):
        result = generate_checklist(sample_sop_steps, sample_run_id)

    duration_item = next(i for i in result["items"] if i["check_type"] == "duration")
    assert duration_item["expected_duration_seconds"] == 30


# ── generate_checklist: edge cases ───────────────────────────────────────────

def test_generate_checklist_empty_steps_skips_api(sample_run_id):
    """Zero steps must return an empty checklist without calling OpenAI."""
    empty_sop = {"sop_document": "test.pdf", "steps": []}
    mock_client = MagicMock()

    with patch("src.reasoning.checklist_generator.get_openai_client", return_value=mock_client):
        result = generate_checklist(empty_sop, sample_run_id)

    mock_client.chat.completions.create.assert_not_called()
    assert result["total_items"] == 0
    assert result["items"] == []


def test_generate_checklist_passes_temperature_zero(
    sample_sop_steps, sample_run_id, canned_gpt_response
):
    """GPT-4o must be called with temperature=0 for determinism."""
    mock_client = _make_openai_mock(canned_gpt_response)
    with patch("src.reasoning.checklist_generator.get_openai_client", return_value=mock_client):
        generate_checklist(sample_sop_steps, sample_run_id)

    call_kwargs = mock_client.chat.completions.create.call_args
    kwargs = call_kwargs.kwargs if call_kwargs.kwargs else call_kwargs[1]
    assert kwargs.get("temperature") == 0


# ── _validate_items: item validation ─────────────────────────────────────────

def test_validate_items_drops_item_with_missing_key(sample_run_id):
    """Items missing required keys must be dropped rather than propagated."""
    items = [
        {
            "item_id": "check-001",
            "step_id": "step-001",
            "sequence": 1,
            # criterion missing
            "check_type": "presence",
            "expected_duration_seconds": None,
            "sop_section": "1.1",
        }
    ]
    result = _validate_items(items, sample_run_id)
    assert result == []


def test_validate_items_invalid_check_type_defaults_to_presence(sample_run_id):
    """check_type values outside the allowed set must be coerced to 'presence'."""
    items = [
        {
            "item_id": "check-001",
            "step_id": "step-001",
            "sequence": 1,
            "criterion": "Some criterion",
            "observable_action": "A visible component is placed.",
            "verifiability": "presence",
            "check_type": "verify",  # invalid
            "expected_duration_seconds": None,
            "sop_section": "1.1",
        }
    ]
    result = _validate_items(items, sample_run_id)
    assert len(result) == 1
    assert result[0]["check_type"] == "presence"


def test_validate_items_duration_coerced_from_string(sample_run_id):
    """expected_duration_seconds returned as a string must be coerced to float."""
    items = [
        {
            "item_id": "check-001",
            "step_id": "step-001",
            "sequence": 1,
            "criterion": "Worker waits at least 30 seconds",
            "observable_action": None,
            "verifiability": "fine_detail",
            "check_type": "duration",
            "expected_duration_seconds": "30",  # GPT-4o sometimes returns strings
            "sop_section": "1.1",
        }
    ]
    result = _validate_items(items, sample_run_id)
    assert result[0]["expected_duration_seconds"] == 30.0


def test_validate_items_non_numeric_duration_set_to_null(sample_run_id):
    """Non-numeric expected_duration_seconds must be set to null rather than raising."""
    items = [
        {
            "item_id": "check-001",
            "step_id": "step-001",
            "sequence": 1,
            "criterion": "Worker waits",
            "observable_action": None,
            "verifiability": "fine_detail",
            "check_type": "duration",
            "expected_duration_seconds": "about 30 seconds",
            "sop_section": "1.1",
        }
    ]
    result = _validate_items(items, sample_run_id)
    assert result[0]["expected_duration_seconds"] is None
