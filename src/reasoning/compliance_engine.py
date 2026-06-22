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
import re
from datetime import datetime, timezone
from typing import Literal

from tenacity import retry, stop_after_attempt, wait_exponential

from config import cfg
from src.openai_client import get_openai_client

logger = logging.getLogger(__name__)

Verdict = Literal["Compliant", "Deviation Detected", "Unable to Verify", "Requires Inspection"]
_VALID_VERDICTS = frozenset({"Compliant", "Deviation Detected", "Unable to Verify"})

# Words too generic to count as a lexical match signal for candidate-window prefiltering.
_STOPWORDS = frozenset({
    "the", "and", "for", "with", "that", "this", "from", "into", "onto", "than",
    "then", "have", "has", "had", "are", "was", "were", "been", "being", "not",
    "step", "ensure", "verify", "confirm", "check", "correct", "correctly",
    "properly", "should", "must", "shall", "will", "can", "may",
    "pin", "pins", "beam", "beams", "connector", "connectors", "perforated",
    "assembly", "assembler", "worker", "user", "screw", "screws", "fastener",
    "fasteners", "attachment", "attaching", "attached", "install", "installed",
    "installing", "mounting", "mounted", "mount", "bracket", "brackets",
})

# Emitted without a GPT-4o call for fine-detail criteria the video cannot resolve.
REQUIRES_INSPECTION = "Requires Inspection"

SYSTEM_PROMPT = """You are a manufacturing compliance reasoning engine.
You are given ONE observable action from an SOP step and a list of video segment
observations. Each segment is a short (~24s) window with a description of what the
worker did in that window. Decide whether the observable action was performed.

First identify which window(s) best match the observable action by reading each
segment's action_observed and description. Then render a verdict.

The window descriptions use generic visual vocabulary (colours, shapes, "connector",
"beam") rather than SOP part names. Match by the physical nature of the action and the
components' appearance, not exact terminology — e.g. "a black pin pushed through aligned
holes joining two beams" satisfies "insert the chassis pin through the bores". Still
abstain when no window plausibly shows the action.

Return a JSON object with exactly these fields:
{
  "verdict": "<Compliant|Deviation Detected|Unable to Verify>",
  "confidence": <float 0.0–1.0>,
  "evidence_segment_id": "<segment_id of the best-matching window, or null>",
  "reasoning": "<one sentence explaining the verdict, citing the window>"
}

Verdict rules:
- "Compliant": a window clearly shows the observable action being performed with the
  expected component(s).
- "Deviation Detected": a window POSITIVELY shows one of:
    (a) this action done with a clearly wrong component, or in a clearly wrong order; or
    (b) a GROSS VISIBLE CONTRADICTION — a later window shows the assembly at a point past
        where this component must already be attached, the spot it should occupy is plainly
        and fully visible in that window, and it is clearly empty or wrong (e.g. an axle
        assembly shown with no wheel mounted on it, a frame shown with no pulley where one
        must be present, a part installed backwards/upside-down when orientation is grossly
        obvious without fine inspection).
  Only when a SPECIFIC window shows something actually, visibly wrong — name that window.
- "Unable to Verify": no window shows anything relevant to this action, OR no window gives a
  clear, unobstructed view of the spot where the component should be — so you cannot confirm
  presence or absence either way.

CRITICAL: Judge ONLY the observable action described. Do NOT return "Deviation Detected"
merely because fine detail (torque, seating, orientation, "rotates freely") is unconfirmable
— that detail has already been filtered out and is handled elsewhere. Absence of evidence is
"Unable to Verify", never a deviation. The difference between (b) and "Unable to Verify" is
whether you can point to one specific window that plainly shows the empty/wrong location —
never infer absence from a window that simply doesn't address that area, and never infer
absence from silence across all windows alone. (Confirmed-absence-over-a-complete-recording
is handled deterministically downstream by apply_absence_inference(), not here.)

A checklist-aware vision pass (A1) may have already scanned the frames for this specific step.
The payload includes a top-level "vision_flagged_segments" list — read it FIRST before scanning the windows.

If "vision_flagged_segments" is NON-EMPTY:
  - A dedicated vision pass confirmed this step's action in those windows with high confidence.
  - Return "Compliant" citing the first listed segment as evidence.
  - Only override to "Deviation Detected" if another window EXPLICITLY shows a gross contradiction
    (missing component in an unobstructed view). Do NOT override based on vocabulary mismatch —
    generic Phase 2 descriptions ("white beam", "gray pin") are expected and do not contradict A1.

If "vision_flagged_segments" is EMPTY (A1 ran but found nothing for this step):
  - Be strict: default to "Unable to Verify".
  - Only return "Compliant" if a segment's description or action_observed explicitly and unambiguously
    names the unique key objects of this step (e.g. "pulley", "wing beam" — not generic "beam" or "pin").
  - Do NOT generalize generic component handling actions to satisfy this step.

If "vision_flagged_segments" is absent from the payload (A1 did not run):
  - Apply normal vocabulary-matching judgment as described above.

Respond with the JSON object only. No explanation outside the JSON.""".strip()


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


def _significant_tokens(text: str | None) -> set[str]:
    """Lowercased, stopword-filtered word set used for lexical overlap scoring."""
    if not text:
        return set()
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if len(w) > 2 and w not in _STOPWORDS}


def _vision_flagged_map(item_id: str | None, segments: list[dict]) -> dict[str, float]:
    """
    Map {segment_id: confidence} for windows whose checklist-aware Phase 2 pass
    (A1) positively reported this item_id as visible. Empty when Phase 2 ran in
    the default (non-checklist) mode, so this is a no-op on legacy observations.
    """
    if not item_id:
        return {}
    flagged: dict[str, float] = {}
    for seg in segments:
        for entry in seg.get("observed_items") or []:
            if entry.get("item_id") == item_id:
                flagged[seg.get("segment_id")] = entry.get("confidence", 0.5)
                break
    return flagged


def build_verdict_record(
    checklist_item: dict,
    run_id: str,
    *,
    verdict: str = "Unable to Verify",
    confidence: float = 0.0,
    evidence_segment_id: str | None = None,
    evidence_timestamp_start: float | None = None,
    evidence_timestamp_end: float | None = None,
    keyframe_blob_path: str | None = None,
    reasoning: str = "",
    sequence_ok: bool | None = None,
    duration_ok: bool | None = None,
) -> dict:
    """Build a verification_record dict (schemas/verification_record.json)."""
    return {
        "run_id": run_id,
        "item_id": checklist_item.get("item_id", ""),
        "step_id": checklist_item.get("step_id", ""),
        "sequence": checklist_item.get("sequence"),
        "criterion": checklist_item.get("criterion", ""),
        "verdict": verdict,
        "confidence": confidence,
        "evidence_segment_id": evidence_segment_id,
        "evidence_timestamp_start": evidence_timestamp_start,
        "evidence_timestamp_end": evidence_timestamp_end,
        "keyframe_blob_path": keyframe_blob_path,
        "reasoning": reasoning,
        "sequence_ok": sequence_ok,
        "duration_ok": duration_ok,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _null_verdict(checklist_item: dict, run_id: str, reason: str = "") -> dict:
    """Return an Unable to Verify verdict without calling GPT-4o."""
    return build_verdict_record(
        checklist_item, run_id,
        reasoning=reason or "No video segments were available to evaluate this step.",
    )


def _inspection_verdict(checklist_item: dict, run_id: str) -> dict:
    """
    Return a 'Requires Inspection' verdict for a fine-detail criterion, without
    calling GPT-4o. These steps (torque, seating, orientation, rotation checks,
    small-part counts, measurements, inspection-only acts) genuinely cannot be
    confirmed from overhead 1 fps / 512 px video, so the honest outcome is to
    route them to manual inspection rather than guess or fabricate a verdict.
    """
    return build_verdict_record(
        checklist_item, run_id,
        verdict=REQUIRES_INSPECTION,
        confidence=1.0,
        reasoning=(
            "Fine-detail QC criterion (torque, seating, orientation, rotation, small-part "
            "count, or an inspection-only act) — not assessable from overhead 1 fps / 512 px "
            "video. Routed to manual inspection."
        ),
    )


# Hardened retry to ride out sustained GPT-4o 429 rate-limit windows (matches
# extract_compliance_fields). 6 attempts, backoff 5s→90s — up to ~5 min before giving up.
@retry(stop=stop_after_attempt(6), wait=wait_exponential(multiplier=2, min=5, max=90))
def reason_step(
    checklist_item: dict,
    observations: dict,
    run_id: str,
) -> dict:
    """
    Produce a compliance verdict for one SOP step.

    GPT-4o receives all video segments and identifies the best-matching one
    alongside the verdict. No pre-filtering required for short clips.

    Verdicts are positive-evidence only: Compliant or Deviation Detected require
    a specific cited window; otherwise Unable to Verify. Confirmed-absence over a
    fully-covered clip is handled separately by apply_absence_inference().

    Week 3 upgrade path: swap `observations` for pre-filtered candidate
    segments from Azure AI Search — this function signature stays the same.

    Args:
        checklist_item: One item from schemas/compliance_checklist.json.
        observations:   Video observations dict (schemas/video_observations.json),
                        segments filled by run_video_phase2(). GPT-4o selects
                        the relevant segment internally.
        run_id:         Pipeline run identifier.

    Returns:
        dict matching schemas/verification_record.json.
        sequence_ok and duration_ok are None — filled by sequence_timing
        (Week 2 Step 4) before writing to Cosmos DB.
    """
    segments = observations.get("segments", [])
    step_id = checklist_item.get("step_id", "")

    # Fine-detail criteria the video cannot resolve are routed to inspection without
    # a GPT-4o call — honest, deterministic, and free. (verifiability is set by the
    # checklist generator; missing/invalid values were normalised to "fine_detail".)
    verifiability = checklist_item.get("verifiability", "fine_detail")
    observable_action = checklist_item.get("observable_action")
    if verifiability == "fine_detail" or not observable_action:
        logger.info(f"Routing to inspection | run_id={run_id} | step={step_id} | verifiability={verifiability}")
        return _inspection_verdict(checklist_item, run_id)

    if not segments:
        logger.warning(f"reason_step: no segments | run_id={run_id} | step={step_id}")
        return _null_verdict(checklist_item, run_id)

    flagged = _vision_flagged_map(checklist_item.get("item_id"), segments)

    # Detect whether A1 ran at all (any segment has observed_items field).
    # Three-way distinction for the prompt:
    #   A1 flagged this item  → non-empty list (GPT-4o: trust it → Compliant)
    #   A1 ran, saw nothing   → empty list    (GPT-4o: be strict → UTV default)
    #   A1 never ran          → key absent    (GPT-4o: normal vocabulary matching)
    a1_ran = any("observed_items" in s for s in segments)

    logger.info(
        f"Reasoning step | run_id={run_id} | step={step_id} | "
        f"segments={len(segments)} | vision_flagged={len(flagged)} | a1_ran={a1_ran}"
    )

    user_payload: dict = {
        "observable_action": observable_action,
        "full_criterion_for_context": checklist_item.get("criterion", ""),
        "sop_section": checklist_item.get("sop_section", ""),
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
                "vision_flagged_this_action": s.get("segment_id") in flagged,
            }
            for s in segments
        ],
    }
    if a1_ran:
        # Explicit top-level summary so GPT-4o doesn't have to scan per-segment booleans.
        user_payload["vision_flagged_segments"] = sorted(flagged.keys())

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

    # sequence_ok / duration_ok left None — filled by pipeline.py after validate_sequence_and_timing().
    return build_verdict_record(
        checklist_item, run_id,
        verdict=verdict,
        confidence=confidence,
        evidence_segment_id=evidence_seg_id,
        evidence_timestamp_start=ts_start,
        evidence_timestamp_end=ts_end,
        keyframe_blob_path=keyframe_path,
        reasoning=parsed.get("reasoning", ""),
    )


def apply_absence_inference(
    verdicts: list[dict],
    observations: dict,
    checklist_items: list[dict],
    coverage_tolerance: float = 0.10,
) -> list[dict]:
    """
    Upgrade Unable to Verify → Deviation Detected for presence-tier steps where
    zero windows showed any signal and the windows tile >= 90% of the clip.

    Guards:
      1. Windows must cover >= 90% of total clip duration.
      2. At least one Compliant verdict must exist (camera sanity check).
      3. Zero token overlap between the step's observable_action and ALL windows.
    """
    segments = observations.get("segments", [])
    if not segments:
        return verdicts

    last_window_end = max((s.get("end_time_seconds", 0) for s in segments), default=0.0)
    video_duration = observations.get("video_duration_seconds", last_window_end)
    if video_duration <= 0 or (last_window_end / video_duration) < (1.0 - coverage_tolerance):
        return verdicts

    if not any(v.get("verdict") == "Compliant" for v in verdicts):
        return verdicts

    item_lookup = {item.get("item_id"): item for item in checklist_items}

    all_window_tokens = []
    for seg in segments:
        desc = " ".join([
            seg.get("action_observed") or "",
            seg.get("component_contact") or "",
            seg.get("tool_in_use") or "",
            seg.get("description") or "",
        ])
        all_window_tokens.append(_significant_tokens(desc))

    for v in verdicts:
        if v.get("verdict") != "Unable to Verify":
            continue
        if v.get("_uniqueness_demoted"):
            continue
        item_id = v.get("item_id") if v.get("item_id") is not None else v.get("step_id")
        item = item_lookup.get(item_id, {})
        if item.get("verifiability") != "presence":
            continue
        # A1 guard: never infer absence for an item the checklist-aware vision pass
        # positively saw in any window. The targeted vision signal overrides token
        # absence — at worst this stays Unable to Verify, never a confirmed-absence
        # Deviation. No-op on legacy observations that carry no observed_items.
        if _vision_flagged_map(item_id, segments):
            continue
        # Only fire absence inference for items with explicit key_objects.
        # Phase 2 uses generic visual vocabulary (colour/shape) that rarely matches
        # functional SOP terms like "screw", "bracket", or "front chassis" — falling
        # back to observable_action tokens causes false positives on every step whose
        # functional name doesn't appear in the frame descriptions.
        # key_objects should be set ONLY when Phase 2 vocabulary is known to contain
        # the discriminating token (e.g. "pulley" once Phase 2 is vocabulary-aligned).
        key_objects: list[str] = item.get("key_objects") or []
        if not key_objects:
            continue
        query_tokens: set[str] = set()
        for obj in key_objects:
            query_tokens |= _significant_tokens(obj)
        if not query_tokens:
            continue
        total_signal = sum(len(query_tokens & wt) for wt in all_window_tokens)
        if total_signal > 0:
            continue
        v["verdict"] = "Deviation Detected"
        v["not_observed"] = True
        v["confidence"] = 0.85
        v["reasoning"] = (
            f"No video window contained any signal matching this action across "
            f"{len(segments)} window(s) covering {last_window_end:.0f}s of footage. "
            f"Full-clip coverage confirmed — action was not performed."
        )

    return verdicts


def enforce_unique_evidence(verdicts: list[dict]) -> list[dict]:
    """
    Honesty guard: one video window cannot back more than one 'Compliant' verdict.

    The SOP often repeats an action at positions overhead video cannot distinguish
    (forward vs rearmost bore, front vs rear axle). Without this guard, several
    position-specific steps all match the same generic window ("a pin through aligned
    holes") and each claims Compliant — over-attributing a single observed action to
    multiple distinct steps. When that happens the video simply does not contain
    distinct evidence for each step.

    Rule: for each evidence segment, keep only the highest-confidence Compliant verdict
    (ties broken by earliest sequence). Demote the rest to 'Unable to Verify' with a note.
    Mutates and returns the same list.
    """
    by_seg: dict[str, list[dict]] = {}
    for v in verdicts:
        if v.get("verdict") == "Compliant" and v.get("evidence_segment_id"):
            by_seg.setdefault(v["evidence_segment_id"], []).append(v)

    for seg_id, group in by_seg.items():
        if len(group) <= 1:
            continue
        group.sort(key=lambda v: (-float(v.get("confidence", 0.0)), v.get("sequence") or 0))
        keeper = group[0]
        for v in group[1:]:
            v["verdict"] = "Unable to Verify"
            v["confidence"] = round(min(float(v.get("confidence", 0.0)), 0.4), 3)
            v["evidence_segment_id"] = None
            v["evidence_timestamp_start"] = None
            v["evidence_timestamp_end"] = None
            v["keyframe_blob_path"] = None
            v["reasoning"] = (
                f"Step {keeper.get('step_id')} matched the same video window ({seg_id}); "
                f"the video lacks distinct evidence to confirm this step separately. "
                f"Routed to manual verification."
            )
            # Sentinel: prevents apply_absence_inference from re-escalating this step
            # to Deviation Detected — the step had evidence, it just wasn't distinct.
            v["_uniqueness_demoted"] = True
    return verdicts
