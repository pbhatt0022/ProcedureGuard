"""
ProcedureGuard — Flow 1 Pipeline Orchestrator

Chains all Layer 2 and Layer 3 modules into a single end-to-end run.
Deterministic control flow — no LLM agents, just direct module calls.

Flow:
  1. Extract SOP steps (Document Intelligence)
  2. Generate compliance checklist (GPT-4o)
  3. Probe video duration (OpenCV) → time-windowed segments → GPT-4o Vision field extraction
  4. Validate sequence and timing (deterministic)
  5. Reason each checklist item against observations (GPT-4o)
  6. Merge timing into verdicts, apply absence inference, compute adherence score

Returns a full results dict for the dashboard.
"""
import logging
import os
import uuid
from datetime import datetime, timezone

from config import cfg
from src.ingestion.sop_extractor import extract_sop_steps
from src.ingestion.video_analyzer import (
    build_time_windowed_segments,
    probe_video_duration,
    run_video_phase2,
    extract_keyframes_batch,
)
from src.storage.blob_client import write_keyframe
from src.reasoning.checklist_generator import generate_checklist
from src.reasoning.compliance_engine import (
    apply_absence_inference,
    build_verdict_record,
    enforce_unique_evidence,
    reason_step,
)
from src.reasoning.sequence_timing import validate_sequence_and_timing

logger = logging.getLogger(__name__)


def generate_run_id() -> str:
    """Generate a unique run_id. Format: run-YYYYMMDD-<short-uuid>"""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    short_id = str(uuid.uuid4())[:8]
    return f"run-{date_str}-{short_id}"


def _adherence_score(verdicts: list[dict]) -> float | None:
    """
    Compliant ÷ (Compliant + Deviation Detected).
    Returns None when no scoreable verdicts exist.
    Unable to Verify is excluded from the denominator.
    """
    compliant = sum(1 for v in verdicts if v["verdict"] == "Compliant")
    deviation = sum(1 for v in verdicts if v["verdict"] == "Deviation Detected")
    denominator = compliant + deviation
    return round(compliant / denominator, 3) if denominator > 0 else None


def run_pipeline(
    sop_source: str,
    video_url: str,
    *,
    sop_pages: str | None = None,
    sop_granularity: str = "section",
) -> dict:
    """
    Execute the full compliance verification pipeline.

    Args:
        sop_source:      Local path or Blob URL to the SOP PDF.
        video_url:       HTTPS URL or Blob SAS URL to the manufacturing video.
        sop_pages:       Page range to extract (e.g. "1-30"). None = all pages.
        sop_granularity: "section" (one step per heading) or "paragraph".
                         Use "section" for the Prusa manual.

    Returns:
        {
          "run_id":          str,
          "sop_steps":       dict,   # schemas/sop_steps.json
          "checklist":       dict,   # schemas/compliance_checklist.json
          "observations":    dict,   # schemas/video_observations.json (Phase 2 filled)
          "verdicts":        list,   # list of schemas/verification_record.json
          "adherence_score": float | None,
          "summary": {
            "total": int, "compliant": int,
            "deviation": int, "unable_to_verify": int,
          },
        }
    """
    run_id = generate_run_id()
    logger.info(f"Pipeline started | run_id={run_id}")

    # ── Step 1: SOP extraction ────────────────────────────────────────────────
    logger.info(f"[1/5] Extracting SOP steps | source={sop_source[:60]}")
    sop_steps = extract_sop_steps(
        sop_source, run_id,
        pages=sop_pages,
        granularity=sop_granularity,
    )
    logger.info(f"[1/5] Done — {sop_steps['total_steps']} steps extracted")

    # ── Step 2: Compliance checklist ──────────────────────────────────────────
    logger.info(f"[2/5] Generating compliance checklist | steps={sop_steps['total_steps']}")
    checklist = generate_checklist(sop_steps, run_id)
    logger.info(f"[2/5] Done — {checklist['total_items']} checklist items")

    # ── Step 3: Video analysis (time-windowed Phase 2) ────────────────────────
    logger.info(f"[3/5] Analyzing video | url={video_url[:60]}")
    duration = probe_video_duration(video_url)
    observations = {
        "run_id": run_id,
        "video_url": video_url,
        "video_duration_seconds": duration,
        "segments": [],
        "total_segments": 0,
    }
    observations["segments"] = build_time_windowed_segments(duration, window_seconds=25.0)
    observations["total_segments"] = len(observations["segments"])
    logger.info(
        f"[3/5] Duration={duration:.0f}s — segmented into {observations['total_segments']} "
        f"time window(s)"
    )

    logger.info(f"[3/5] Running GPT-4o Phase 2 compliance field extraction")
    run_video_phase2(observations, run_id, video_url=video_url, checklist=checklist)
    logger.info(f"[3/5] Phase 2 done")

    # ── Step 4: Sequence and timing validation ────────────────────────────────
    logger.info(f"[4/5] Validating sequence and timing")
    timing_results = validate_sequence_and_timing(checklist, observations)
    timing_by_item = {r.item_id: r for r in timing_results}
    logger.info(f"[4/5] Done — {len(timing_results)} timing result(s)")

    # ── Step 5: Per-step compliance reasoning ─────────────────────────────────
    items = checklist.get("items", [])
    logger.info(f"[5/5] Reasoning {len(items)} checklist item(s)")
    verdicts: list[dict] = []

    for item in items:
        item_id = item.get("item_id", "?")
        try:
            verdict = reason_step(item, observations, run_id)
        except Exception as exc:
            logger.error(f"reason_step failed | {item_id} | {exc}")
            verdict = build_verdict_record(item, run_id, reasoning=f"Reasoning engine error: {exc}")

        # Merge timing results into verdict
        timing = timing_by_item.get(item_id)
        if timing:
            verdict["sequence_ok"] = timing.sequence_ok
            verdict["duration_ok"] = timing.duration_ok

        verdicts.append(verdict)
        logger.info(
            f"[5/5] {item_id} → {verdict['verdict']} "
            f"(confidence={verdict['confidence']:.2f})"
        )

    # Honesty guard: one window can't back multiple distinct Compliant steps.
    verdicts = enforce_unique_evidence(verdicts)

    # Absence inference: upgrade UTV → Deviation Detected for presence-tier steps
    # where no window showed any key-object signal and the clip is fully covered.
    verdicts = apply_absence_inference(verdicts, observations, checklist.get("items", []))

    # ── Step 6: Extract and save real keyframe images in batch ────────────────
    logger.info(f"[6/6] Batch extracting evidence keyframe images from video...")
    targets = []
    for v in verdicts:
        if v.get("verdict") in ("Compliant", "Deviation Detected"):
            start_time = v.get("evidence_timestamp_start")
            if start_time is not None:
                targets.append({"step_id": v.get("step_id", "step"), "timestamp_s": start_time})

    if targets:
        try:
            batch_results = extract_keyframes_batch(video_url, targets)
            for v in verdicts:
                step_id = v.get("step_id")
                if step_id in batch_results:
                    keyframe_path = write_keyframe(batch_results[step_id], run_id, step_id)
                    v["keyframe_blob_path"] = keyframe_path
        except Exception as exc:
            logger.error(f"Failed during batch keyframe extraction: {exc}")

    # ── Summary ───────────────────────────────────────────────────────────────
    compliant = sum(1 for v in verdicts if v["verdict"] == "Compliant")
    deviation = sum(1 for v in verdicts if v["verdict"] == "Deviation Detected")
    unable = sum(1 for v in verdicts if v["verdict"] == "Unable to Verify")
    inspection = sum(1 for v in verdicts if v["verdict"] == "Requires Inspection")
    score = _adherence_score(verdicts)

    logger.info(
        f"Pipeline complete | run_id={run_id} | "
        f"compliant={compliant} deviation={deviation} unable={unable} "
        f"adherence={score}"
    )

    result_dict = {
        "run_id": run_id,
        "sop_steps": sop_steps,
        "checklist": checklist,
        "observations": observations,
        "verdicts": verdicts,
        "adherence_score": score,
        "summary": {
            "total": len(verdicts),
            "compliant": compliant,
            "deviation": deviation,
            "unable_to_verify": unable,
            "requires_inspection": inspection,
        },
    }

    # ── Step 7: Auto-save run record to runs store ────────────────────────────
    # Wrapped in a safe try/except so that write failures (e.g. read-only file systems in tests)
    # never crash the pipeline run.
    try:
        run_file = os.path.join(cfg.runs_dir, f"{run_id}.json")
        os.makedirs(cfg.runs_dir, exist_ok=True)
        import json
        with open(run_file, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Auto-saved run record to runs store: {run_file}")
    except Exception as exc:
        logger.error(f"Guarded auto-save failed | {run_id} | {exc}")

    return result_dict
