"""
Tests for src/reasoning/sequence_timing.py

No Azure dependencies — fully testable offline.
This should be the first module with passing tests.

Owner: Person C (storage + orchestration)
"""
import pytest

from src.reasoning.sequence_timing import find_matching_segments, validate_sequence_and_timing


# ── validate_sequence_and_timing ─────────────────────────────────────────────

def test_correct_sequence_passes(sample_checklist, sample_observations):
    """Steps executed in order should all return sequence_ok=True."""
    results = validate_sequence_and_timing(sample_checklist, sample_observations)
    assert len(results) == 2
    assert all(r.sequence_ok for r in results)


def test_out_of_order_step_fails(sample_checklist, sample_observations_out_of_order):
    """A step that occurs before its predecessor should return sequence_ok=False."""
    results = validate_sequence_and_timing(sample_checklist, sample_observations_out_of_order)
    step2 = next(r for r in results if r.item_id == "check-002")
    assert step2.sequence_ok is False


def test_duration_check_passes_when_long_enough(sample_checklist, sample_observations):
    """A duration step with sufficient observed time should return duration_ok=True."""
    results = validate_sequence_and_timing(sample_checklist, sample_observations)
    duration_result = next(r for r in results if r.item_id == "check-002")
    assert duration_result.duration_ok is True
    # seg-002 is 40.0–75.0 = 35s, expected 30s
    assert (duration_result.observed_end - duration_result.observed_start) >= 30


def test_duration_check_fails_when_too_short(sample_checklist, sample_observations_too_short):
    """A duration step shorter than expected should return duration_ok=False."""
    results = validate_sequence_and_timing(sample_checklist, sample_observations_too_short)
    duration_result = next(r for r in results if r.item_id == "check-002")
    assert duration_result.duration_ok is False
    # seg-002 is 40.0–50.0 = 10s, expected 30s
    assert (duration_result.observed_end - duration_result.observed_start) < 30


def test_missing_segment_returns_sequence_false(sample_checklist, empty_observations):
    """Steps with no video segments should all return sequence_ok=False."""
    results = validate_sequence_and_timing(sample_checklist, empty_observations)
    assert len(results) == 2
    assert all(r.sequence_ok is False for r in results)


def test_returns_one_result_per_checklist_item(sample_checklist, sample_observations):
    """Output must have exactly one TimingResult per checklist item."""
    results = validate_sequence_and_timing(sample_checklist, sample_observations)
    assert len(results) == len(sample_checklist["items"])


def test_first_step_always_passes_sequence(sample_checklist, sample_observations):
    """The first checklist item must always pass the sequence check."""
    results = validate_sequence_and_timing(sample_checklist, sample_observations)
    first = next(r for r in results if r.item_id == "check-001")
    assert first.sequence_ok is True


def test_presence_step_has_null_duration_ok(sample_checklist, sample_observations):
    """Non-duration checklist items must have duration_ok=None."""
    results = validate_sequence_and_timing(sample_checklist, sample_observations)
    presence_result = next(r for r in results if r.item_id == "check-001")
    assert presence_result.duration_ok is None


def test_observed_timestamps_populated(sample_checklist, sample_observations):
    """TimingResult must carry the matched segment's start and end timestamps."""
    results = validate_sequence_and_timing(sample_checklist, sample_observations)
    first = next(r for r in results if r.item_id == "check-001")
    assert first.observed_start == 0.0
    assert first.observed_end == 40.0


def test_out_of_order_note_contains_timestamps(
    sample_checklist, sample_observations_out_of_order
):
    """The note on an out-of-order result must mention both timestamps."""
    results = validate_sequence_and_timing(sample_checklist, sample_observations_out_of_order)
    step2 = next(r for r in results if r.item_id == "check-002")
    assert "0.0" in step2.note or "order" in step2.note.lower()


# ── find_matching_segments ────────────────────────────────────────────────────

_SEGMENTS_FOR_MATCH = [
    {
        "segment_id": "seg-001",
        "start_time_seconds": 0.0,
        "end_time_seconds": 40.0,
        "action_observed": "attaching motor bracket to frame",
        "description": "",
    },
    {
        "segment_id": "seg-002",
        "start_time_seconds": 40.0,
        "end_time_seconds": 75.0,
        "action_observed": "waiting for adhesive to cure",
        "description": "",
    },
    {
        "segment_id": "seg-003",
        "start_time_seconds": 75.0,
        "end_time_seconds": 100.0,
        "action_observed": "tightening belt tensioner screws",
        "description": "",
    },
]


def test_find_matching_segments_returns_correct_segment():
    """Keyword match must return the segment whose action best matches the description."""
    results = find_matching_segments("motor bracket installation", _SEGMENTS_FOR_MATCH)
    assert len(results) >= 1
    assert results[0]["segment_id"] == "seg-001"


def test_find_matching_segments_respects_top_n():
    """Result count must not exceed top_n."""
    results = find_matching_segments("motor adhesive screws", _SEGMENTS_FOR_MATCH, top_n=2)
    assert len(results) <= 2


def test_find_matching_segments_sorted_chronologically():
    """Returned segments must be ordered by start_time_seconds ascending."""
    results = find_matching_segments("motor adhesive screws", _SEGMENTS_FOR_MATCH, top_n=3)
    starts = [s["start_time_seconds"] for s in results]
    assert starts == sorted(starts)


def test_find_matching_segments_empty_input_returns_empty():
    """Empty segment list must return an empty list without raising."""
    assert find_matching_segments("motor bracket", []) == []


def test_find_matching_segments_no_match_returns_empty():
    """A description with no keyword overlap must return an empty list."""
    results = find_matching_segments("xyz123 qqqq", _SEGMENTS_FOR_MATCH)
    assert results == []


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_checklist():
    return {
        "run_id": "run-test-001",
        "items": [
            {"item_id": "check-001", "step_id": "step-001", "sequence": 1,
             "check_type": "presence", "expected_duration_seconds": None,
             "criterion": "Worker attaches motor to frame"},
            {"item_id": "check-002", "step_id": "step-002", "sequence": 2,
             "check_type": "duration", "expected_duration_seconds": 30,
             "criterion": "Worker waits for adhesive to cure"},
        ],
    }


@pytest.fixture
def sample_observations():
    return {
        "run_id": "run-test-001",
        "segments": [
            {"segment_id": "seg-001", "start_time_seconds": 0.0,
             "end_time_seconds": 40.0, "action_observed": "attaching motor to frame"},
            {"segment_id": "seg-002", "start_time_seconds": 40.0,
             "end_time_seconds": 75.0, "action_observed": "waiting for adhesive to cure"},
        ],
    }


@pytest.fixture
def sample_observations_out_of_order():
    return {
        "run_id": "run-test-001",
        "segments": [
            {"segment_id": "seg-001", "start_time_seconds": 50.0,
             "end_time_seconds": 90.0, "action_observed": "attaching motor to frame"},
            {"segment_id": "seg-002", "start_time_seconds": 0.0,
             "end_time_seconds": 30.0, "action_observed": "waiting for adhesive"},
        ],
    }


@pytest.fixture
def sample_observations_too_short():
    return {
        "run_id": "run-test-001",
        "segments": [
            {"segment_id": "seg-001", "start_time_seconds": 0.0,
             "end_time_seconds": 40.0, "action_observed": "attaching motor"},
            {"segment_id": "seg-002", "start_time_seconds": 40.0,
             "end_time_seconds": 50.0, "action_observed": "waiting"},  # only 10s, needs 30s
        ],
    }


@pytest.fixture
def empty_observations():
    return {"run_id": "run-test-001", "segments": []}
