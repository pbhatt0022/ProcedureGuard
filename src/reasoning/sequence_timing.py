"""
Layer 3 — Sequence and Timing Engine

Pure Python module — no Azure SDK, no GPT-4o, fully unit-testable offline.
Deterministically validates step execution order and duration constraints
using timestamps from the video observations.

Two checks:
  1. Sequence: did each step start after the previous step started?
  2. Duration: for steps with expected_duration_seconds, did the
               observed segment last long enough?

Segment matching uses keyword overlap on action_observed + description.
When no keyword match is found, falls back to positional alignment
(step N → segment N) so short/generic action strings don't break the pipeline.

Input:  compliance checklist + video observations (both as dicts)
Output: list[TimingResult] — one entry per checklist item
Owner:  Person C (storage + orchestration)
"""
import logging
import re
from typing import NamedTuple

logger = logging.getLogger(__name__)


class TimingResult(NamedTuple):
    step_id: str
    item_id: str
    sequence_ok: bool           # True if step started after previous step
    duration_ok: bool | None    # True/False for duration steps; None otherwise
    observed_start: float | None
    observed_end: float | None
    expected_duration: float | None
    note: str


def find_matching_segments(
    step_description: str,
    segments: list[dict],
    top_n: int = 3,
) -> list[dict]:
    """
    Find video segments most likely to correspond to a given SOP step description.

    Scores each segment by counting keyword overlap between step_description
    and the segment's action_observed + description fields. Returns up to
    top_n results ordered chronologically by start_time_seconds.

    Returns an empty list when no segment scores > 0.

    Args:
        step_description: Criterion or description text for the SOP step.
        segments:         Segment dicts from schemas/video_observations.json.
        top_n:            Maximum number of candidates to return.
    """
    if not segments or not step_description.strip():
        return []

    # Tokenise: lowercase words longer than 2 chars (filters "to", "at", "is", etc.)
    query_words = {
        w.lower() for w in re.split(r"\W+", step_description) if len(w) > 2
    }

    scored: list[tuple[int, float, dict]] = []
    for seg in segments:
        text = " ".join(filter(None, [
            seg.get("action_observed") or "",
            seg.get("description") or "",
        ])).lower()
        seg_words = {w for w in re.split(r"\W+", text) if len(w) > 2}
        score = len(query_words & seg_words)
        if score > 0:
            scored.append((score, seg.get("start_time_seconds", 0.0), seg))

    # Best score first; chronological for ties
    scored.sort(key=lambda x: (-x[0], x[1]))

    # Return top_n sorted chronologically
    top = [seg for _, _, seg in scored[:top_n]]
    top.sort(key=lambda s: s.get("start_time_seconds", 0.0))
    return top


def validate_sequence_and_timing(
    checklist: dict,
    observations: dict,
) -> list[TimingResult]:
    """
    Validate step order and duration constraints against video timestamps.

    For each checklist item (sorted by sequence):
      1. Find the best matching segment via keyword overlap.
         Falls back to positional alignment (step N → segment N) when
         keyword matching produces no candidates (e.g. terse action strings).
      2. sequence_ok: current step must start at or after the previous step started.
         The first item always passes.
      3. duration_ok: for check_type="duration" items, observed segment duration
         must be >= expected_duration_seconds. Null for all other check types.

    sequence_ok and duration_ok are independent — a step can fail one and pass
    the other.

    Args:
        checklist:    Output of generate_checklist() — schemas/compliance_checklist.json
        observations: Output of parse_observations() — schemas/video_observations.json

    Returns:
        list[TimingResult] — one entry per checklist item, in sequence order.
    """
    items = sorted(checklist.get("items", []), key=lambda x: x.get("sequence", 0))
    segments = observations.get("segments", [])
    results: list[TimingResult] = []
    prev_start: float | None = None

    for idx, item in enumerate(items):
        item_id = item.get("item_id", "")
        step_id = item.get("step_id", "")
        criterion = item.get("criterion", "")
        check_type = item.get("check_type", "presence")
        expected_dur = item.get("expected_duration_seconds")

        if not segments:
            results.append(TimingResult(
                step_id=step_id,
                item_id=item_id,
                sequence_ok=False,
                duration_ok=None,
                observed_start=None,
                observed_end=None,
                expected_duration=expected_dur,
                note="No video segments available",
            ))
            continue

        # Keyword match; fall back to positional when no match
        candidates = find_matching_segments(criterion, segments, top_n=1)
        if not candidates:
            fallback_idx = min(idx, len(segments) - 1)
            candidates = [segments[fallback_idx]]
            logger.debug(
                f"No keyword match for '{criterion[:50]}' — "
                f"positional fallback to segment index {fallback_idx}"
            )

        seg = candidates[0]
        obs_start = seg.get("start_time_seconds")
        obs_end = seg.get("end_time_seconds")

        # ── Sequence check ────────────────────────────────────────────────────
        if prev_start is None:
            sequence_ok = True
            seq_note = ""
        else:
            sequence_ok = obs_start is not None and obs_start >= prev_start
            seq_note = (
                ""
                if sequence_ok
                else (
                    f"Out of order: started at {obs_start}s, "
                    f"previous step started at {prev_start}s"
                )
            )

        # ── Duration check (independent of sequence) ─────────────────────────
        if check_type == "duration" and expected_dur is not None:
            if obs_start is not None and obs_end is not None:
                observed_dur = obs_end - obs_start
                duration_ok: bool | None = observed_dur >= expected_dur
                dur_note = (
                    f"Observed {observed_dur:.1f}s, expected >= {expected_dur:.1f}s"
                )
            else:
                duration_ok = None
                dur_note = "Timestamps unavailable — cannot check duration"
        else:
            duration_ok = None
            dur_note = ""

        note = ". ".join(filter(None, [seq_note, dur_note]))

        results.append(TimingResult(
            step_id=step_id,
            item_id=item_id,
            sequence_ok=sequence_ok,
            duration_ok=duration_ok,
            observed_start=obs_start,
            observed_end=obs_end,
            expected_duration=expected_dur,
            note=note,
        ))

        prev_start = obs_start

    return results
