"""
Error-clip validation: run the GT-SOP + A1-enabled pipeline on a local video
and report verdicts with expected-deviation annotations.

Purpose: verify A1 (checklist-aware Phase 2) still catches real deviations —
i.e., that "fewer false positives" didn't accidentally mean "fewer true positives".

Usage:
    python scripts/validate_error_clip.py <video_path> [--window 25] [--overlap 6]

Example:
    python scripts/validate_error_clip.py industreal_selected/videos/candidates/23_assy_1_2.mp4
"""
import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.ingestion.video_analyzer import (
    build_time_windowed_segments,
    probe_video_duration,
    run_video_phase2,
)
from src.reasoning.compliance_engine import (
    apply_absence_inference,
    enforce_unique_evidence,
    reason_step,
)
from src.reasoning.sequence_timing import validate_sequence_and_timing

_ROOT = Path(__file__).parent.parent
_CHECKLIST_PATH = _ROOT / "experiments" / "sop_gt" / "_checklist_gtgrounded.json"
_SOP_STEPS_PATH = _ROOT / "experiments" / "sop_gt" / "_sop_steps_gtgrounded.json"

# Known deviations for clips from demo_candidate_rankings.csv
KNOWN_DEVIATIONS = {
    "23_assy_1_2": {
        "check-005": "missing/reduced fit_wheel and fit_wing (GT delta: fit_wheel:-1; fit_wing:-1)",
    },
    "22_assy_2_3": {
        "check-004": "missing fit_wing_beam (GT delta: fit_wing_beam:-1)",
        "check-006": "missing fit_pulley (GT delta: fit_pulley:-1)",
    }
}


def _verdict_symbol(verdict: str) -> str:
    return {"Compliant": "✓", "Deviation Detected": "✗", "Unable to Verify": "?", "Requires Inspection": "!"}.get(
        verdict, verdict
    )


def main():
    p = argparse.ArgumentParser(description="Error-clip deviation detection validation")
    p.add_argument("video_path", help="Local path to the candidate video file")
    p.add_argument("--window", type=float, default=25.0, help="Time window seconds (default 25)")
    p.add_argument("--overlap", type=float, default=6.0, help="Overlap seconds (default 6)")
    p.add_argument("--out", type=str, default=None, help="Output JSON path (default: auto)")
    args = p.parse_args()

    video_path = Path(args.video_path).resolve()
    if not video_path.exists():
        sys.exit(f"Video not found: {video_path}")

    clip_id = video_path.stem  # e.g. "23_assy_1_2"
    expected_deviations = KNOWN_DEVIATIONS.get(clip_id, {})

    checklist = json.loads(_CHECKLIST_PATH.read_text(encoding="utf-8"))
    sop_steps = json.loads(_SOP_STEPS_PATH.read_text(encoding="utf-8"))

    print("=" * 62)
    print(f"  ProcedureGuard — Error Clip Validation")
    print(f"  Clip        : {clip_id}")
    print(f"  Checklist   : {len(checklist['items'])} items (all presence-tier)")
    print(f"  A1 enabled  : YES (checklist passed to Phase 2)")
    if expected_deviations:
        print(f"  Known errors: {', '.join(expected_deviations.keys())}")
    print("=" * 62)

    run_id = f"validate-{datetime.now(timezone.utc):%Y%m%d}-{uuid.uuid4().hex[:6]}"
    video_url = str(video_path)

    duration = probe_video_duration(video_url)
    print(f"\nDuration   : {duration:.0f}s")

    observations = {
        "run_id": run_id,
        "video_url": video_url,
        "video_duration_seconds": duration,
        "segments": build_time_windowed_segments(
            duration, window_seconds=args.window, overlap_seconds=args.overlap
        ),
    }
    observations["total_segments"] = len(observations["segments"])
    print(f"Windows    : {observations['total_segments']} ({args.window:.0f}s / {args.overlap:.0f}s overlap)\n")

    print("Running Phase 2 vision extraction (A1-enabled)...")
    run_video_phase2(observations, run_id, video_url=video_url, checklist=checklist)
    print("Phase 2 done.\n")

    timing_map = {r.item_id: r for r in validate_sequence_and_timing(checklist, observations)}

    print("Running compliance reasoning per step...")
    verdicts = []
    for item in checklist.get("items", []):
        v = reason_step(item, observations, run_id)
        t = timing_map.get(item.get("item_id"))
        if t:
            v["sequence_ok"] = t.sequence_ok
            v["duration_ok"] = t.duration_ok
        verdicts.append(v)

    verdicts = enforce_unique_evidence(verdicts)
    verdicts = apply_absence_inference(verdicts, observations, checklist.get("items", []))

    # ── Results ────────────────────────────────────────────────────────────────
    compliant = sum(1 for v in verdicts if v["verdict"] == "Compliant")
    deviation = sum(1 for v in verdicts if v["verdict"] == "Deviation Detected")
    unable = sum(1 for v in verdicts if v["verdict"] == "Unable to Verify")
    inspection = sum(1 for v in verdicts if v["verdict"] == "Requires Inspection")
    denom = compliant + deviation
    score = round(compliant / denom, 3) if denom else None

    print("\n" + "=" * 62)
    print(f"  VERDICT SUMMARY  —  {clip_id}")
    print("=" * 62)
    for v in verdicts:
        item_id = v.get("item_id", "?")
        verdict = v.get("verdict", "?")
        conf = v.get("confidence", 0.0)
        sym = _verdict_symbol(verdict)
        expected_note = ""
        if item_id in expected_deviations:
            expected_note = f"  ← EXPECTED DEVIATION ({expected_deviations[item_id][:40]}...)"
        print(f"  {sym} {item_id}  {verdict:<22}  conf={conf:.2f}{expected_note}")

    print()
    print(f"  Compliant          : {compliant}")
    print(f"  Deviation Detected : {deviation}")
    print(f"  Unable to Verify   : {unable}")
    print(f"  Requires Inspection: {inspection}")
    print(f"  Adherence Score    : {f'{score:.1%}' if score is not None else 'N/A'}")

    # ── True/False positive accounting ────────────────────────────────────────
    print()
    print("  DETECTION ACCURACY:")
    tp = fp = fn = 0
    for v in verdicts:
        item_id = v.get("item_id", "?")
        is_non_compliant = v["verdict"] in ("Deviation Detected",)
        is_known_deviation = item_id in expected_deviations
        if is_non_compliant and is_known_deviation:
            tp += 1
            print(f"    TP: {item_id} correctly flagged as Deviation")
        elif is_non_compliant and not is_known_deviation:
            fp += 1
            print(f"    FP: {item_id} flagged as Deviation but NOT in known errors")
        elif not is_non_compliant and is_known_deviation:
            fn += 1
            print(f"    FN: {item_id} is a known deviation but got {v['verdict']}")

    if tp + fp + fn == 0:
        print("    (No deviations detected and no expected deviations defined for this clip)")
    else:
        precision = tp / (tp + fp) if (tp + fp) > 0 else None
        recall = tp / (tp + fn) if (tp + fn) > 0 else None
        print(f"\n    Precision: {f'{precision:.0%}' if precision is not None else 'N/A'}  "
              f"Recall: {f'{recall:.0%}' if recall is not None else 'N/A'}  "
              f"(TP={tp} FP={fp} FN={fn})")

    print("=" * 62)

    # ── Save ──────────────────────────────────────────────────────────────────
    out_path = Path(args.out) if args.out else _ROOT / f"validate_{clip_id}_result.json"
    out_data = {
        "run_id": run_id,
        "clip_id": clip_id,
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
        "known_deviations": expected_deviations,
    }
    out_path.write_text(json.dumps(out_data, indent=2, default=str), encoding="utf-8")
    print(f"\n  Saved: {out_path.name}")


if __name__ == "__main__":
    main()
