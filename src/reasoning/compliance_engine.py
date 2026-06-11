"""
Layer 3 — Compliance Engine (GPT-4o)

Pure reasoning module — no Foundry dependency, fully unit-testable locally.
For each SOP step, compares the compliance criterion against all video
segment observations and produces a structured verdict.

Matching strategy (decided June 2026):
  GPT-4o receives the full observations dict and identifies the best-matching
  segment itself. This is the correct approach for Week 2 (short clips, 1–5
  segments). Week 3 upgrade: pass pre-filtered candidate segments from
  Azure AI Search instead of all segments — reason_step signature stays the same.

Verdict values: Compliant | Deviation Detected | Unable to Verify
  Unable to Verify is returned when observations are insufficient — never forced.

Input:  One checklist item + full video observations dict
Output: dict matching schemas/verification_record.json (single step)
Azure:  Azure OpenAI GPT-4o
Owner:  Person B (video pipeline)
"""
import json
import logging
from datetime import datetime, timezone
from typing import Literal

from openai import AzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from config import cfg

logger = logging.getLogger(__name__)

Verdict = Literal["Compliant", "Deviation Detected", "Unable to Verify"]
_VALID_VERDICTS = frozenset({"Compliant", "Deviation Detected", "Unable to Verify"})

SYSTEM_PROMPT = """You are a manufacturing compliance reasoning engine.
Given an SOP compliance criterion and a list of video segment observations,
determine whether the step was performed correctly.

First identify which segment best matches the criterion by reading each
segment's action_observed and description. Then render a verdict.

Return a JSON object with exactly these fields:
{
  "verdict": "<Compliant|Deviation Detected|Unable to Verify>",
  "confidence": <float 0.0–1.0>,
  "evidence_segment_id": "<segment_id of the best-matching segment, or null>",
  "reasoning": "<one sentence explaining the verdict>"
}

Verdict rules:
- "Compliant": the criterion is clearly satisfied by the observed action.
- "Deviation Detected": the action was observed but does not satisfy the criterion
  (wrong tool, skipped component, incorrect order, insufficient duration).
- "Unable to Verify": no segment clearly shows this step, or video resolution is
  insufficient to confirm (1fps/512px limitation — fine motor detail unreliable).
  Use this when in doubt. Never fabricate confidence.

Respond with the JSON object only. No explanation outside the JSON.""".strip()


def get_openai_client() -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint=cfg.openai_endpoint,
        api_version=cfg.openai_api_version,
        api_key=cfg.openai_api_key or None,
    )


def _lookup_segment_timestamps(
    segment_id: str | None,
    segments: list[dict],
) -> tuple[float | None, float | None]:
    """Return (start, end) seconds for segment_id, or (None, None) if not found."""
    if not segment_id:
        return None, None
    for seg in segments:
        if seg.get("segment_id") == segment_id:
            return seg.get("start_time_seconds"), seg.get("end_time_seconds")
    logger.warning(f"evidence_segment_id '{segment_id}' not found in segments list")
    return None, None


def _null_verdict(checklist_item: dict, run_id: str, reason: str = "") -> dict:
    """Return an Unable to Verify verdict without calling GPT-4o."""
    return {
        "run_id": run_id,
        "item_id": checklist_item.get("item_id", ""),
        "step_id": checklist_item.get("step_id", ""),
        "sequence": checklist_item.get("sequence"),
        "criterion": checklist_item.get("criterion", ""),
        "verdict": "Unable to Verify",
        "confidence": 0.0,
        "evidence_segment_id": None,
        "evidence_timestamp_start": None,
        "evidence_timestamp_end": None,
        "keyframe_blob_path": None,
        "reasoning": reason or "No video segments were available to evaluate this step.",
        "sequence_ok": None,
        "duration_ok": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def reason_step(
    checklist_item: dict,
    observations: dict,
    run_id: str,
) -> dict:
    """
    Produce a compliance verdict for one SOP step.

    GPT-4o receives all video segments and identifies the best-matching one
    alongside the verdict. No pre-filtering required for short clips.

    Week 3 upgrade path: swap `observations` for pre-filtered candidate
    segments from Azure AI Search — this function signature stays the same.

    Args:
        checklist_item: One item from schemas/compliance_checklist.json.
        observations:   Full output of video_analyzer.parse_observations()
                        (schemas/video_observations.json). GPT-4o selects
                        the relevant segment internally.
        run_id:         Pipeline run identifier.

    Returns:
        dict matching schemas/verification_record.json.
        sequence_ok and duration_ok are None — filled by sequence_timing
        (Week 2 Step 4) before writing to Cosmos DB.
    """
    segments = observations.get("segments", [])
    step_id = checklist_item.get("step_id", "")

    if not segments:
        logger.warning(f"reason_step: no segments | run_id={run_id} | step={step_id}")
        return _null_verdict(checklist_item, run_id)

    logger.info(f"Reasoning step | run_id={run_id} | step={step_id} | segments={len(segments)}")

    user_payload = {
        "criterion": checklist_item.get("criterion", ""),
        "check_type": checklist_item.get("check_type", "presence"),
        "sop_section": checklist_item.get("sop_section", ""),
        "expected_duration_seconds": checklist_item.get("expected_duration_seconds"),
        "video_segments": [
            {
                "segment_id": s.get("segment_id"),
                "start_time_seconds": s.get("start_time_seconds"),
                "end_time_seconds": s.get("end_time_seconds"),
                "description": s.get("description", ""),
                "ppe_status": s.get("ppe_status"),
                "tool_in_use": s.get("tool_in_use"),
                "component_contact": s.get("component_contact"),
                "visible_safety_concern": s.get("visible_safety_concern"),
                "action_observed": s.get("action_observed"),
            }
            for s in segments
        ],
    }

    client = get_openai_client()
    response = client.chat.completions.create(
        model=cfg.openai_deployment,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_payload, indent=2)},
        ],
        response_format={"type": "json_object"},
        max_tokens=300,
        temperature=0,
    )

    raw = response.choices[0].message.content
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error(f"reason_step JSON parse error | {step_id} | {exc} | raw={raw[:300]}")
        return _null_verdict(checklist_item, run_id, "GPT-4o returned unparseable response.")

    verdict = parsed.get("verdict", "Unable to Verify")
    if verdict not in _VALID_VERDICTS:
        logger.warning(f"Invalid verdict '{verdict}' for {step_id} — defaulting to Unable to Verify")
        verdict = "Unable to Verify"

    confidence = max(0.0, min(1.0, float(parsed.get("confidence", 0.0))))
    evidence_seg_id = parsed.get("evidence_segment_id")
    ts_start, ts_end = _lookup_segment_timestamps(evidence_seg_id, segments)

    # Keyframe path follows blob storage convention; blob_client uploads here in Week 5.
    keyframe_path = f"keyframes/{run_id}/{step_id}.jpg" if evidence_seg_id else None

    return {
        "run_id": run_id,
        "item_id": checklist_item.get("item_id", ""),
        "step_id": step_id,
        "sequence": checklist_item.get("sequence"),
        "criterion": checklist_item.get("criterion", ""),
        "verdict": verdict,
        "confidence": confidence,
        "evidence_segment_id": evidence_seg_id,
        "evidence_timestamp_start": ts_start,
        "evidence_timestamp_end": ts_end,
        "keyframe_blob_path": keyframe_path,
        "reasoning": parsed.get("reasoning", ""),
        "sequence_ok": None,  # filled by pipeline.py after validate_sequence_and_timing()
        "duration_ok": None,  # filled by pipeline.py after validate_sequence_and_timing()
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
