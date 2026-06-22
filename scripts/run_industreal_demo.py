"""
Run the live pipeline (Phase 2 + reasoning) on an IndustReal clip, reusing the
STEMFIE checklist verbatim from an existing demo report — that checklist is
already verifiability-tiered and was generated from the same SOP (the STEMFIE
manual) that IndustReal participants are following on camera, so no
re-extraction or hand-built checklist is needed.

Usage:
    python scripts/run_industreal_demo.py baseline <sas_url>
    python scripts/run_industreal_demo.py candidate <sas_url>
"""
import argparse
import json
import sys
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.ingestion.video_analyzer import build_time_windowed_segments, probe_video_duration, run_video_phase2
from src.reasoning.compliance_engine import apply_absence_inference, enforce_unique_evidence, reason_step
from src.reasoning.sequence_timing import validate_sequence_and_timing

_ROOT = Path(__file__).parent.parent
_DEMO_RESULTS = _ROOT / "demo_results"
# Reuse the verifiability-tiered STEMFIE checklist from any existing demo report.
# All IndustReal demo runs share this same checklist (same SOP).
_SOURCE = _DEMO_RESULTS / "demo_results_industreal_23_assy_0_1_baseline.json"
_NAMES = {
    "baseline": "demo_results_industreal_23_assy_0_1_baseline",
    "candidate": "demo_results_industreal_22_assy_2_3_candidate",
}


def main():
    p = argparse.ArgumentParser(description="Run live pipeline on an IndustReal clip, reusing the STEMFIE checklist")
    p.add_argument("which", choices=list(_NAMES))
    p.add_argument("video_url", help="SAS URL of the clip in Blob Storage")
    p.add_argument("--window-seconds", type=float, default=25.0)
    p.add_argument("--overlap-seconds", type=float, default=6.0)
    args = p.parse_args()

    source = json.loads(_SOURCE.read_text(encoding="utf-8"))
    sop_steps = source["sop_steps"]
    checklist = source["checklist"]
    tiers = Counter(i.get("verifiability") for i in checklist.get("items", []))
    print(f"Reusing checklist from {_SOURCE.name}: {len(checklist['items'])} items, tiers={dict(tiers)}")

    run_id = f"run-{datetime.now(timezone.utc):%Y%m%d}-{uuid.uuid4().hex[:8]}"
    out = _DEMO_RESULTS / f"{_NAMES[args.which]}.json"

    print(f"\nClip       : {args.which}")
    print(f"run_id     : {run_id}")

    duration = probe_video_duration(args.video_url)
    print(f"Duration   : {duration:.0f}s")

    observations = {
        "run_id": run_id,
        "video_url": args.video_url,
        "video_duration_seconds": duration,
        "segments": build_time_windowed_segments(
            duration, window_seconds=args.window_seconds, overlap_seconds=args.overlap_seconds
        ),
    }
    observations["total_segments"] = len(observations["segments"])
    print(
        f"Windows    : {observations['total_segments']} "
        f"({args.window_seconds:.0f}s each, {args.overlap_seconds:.0f}s overlap)\n"
    )

    run_video_phase2(observations, run_id, video_url=args.video_url)

    timing = {r.item_id: r for r in validate_sequence_and_timing(checklist, observations)}
    verdicts = []
    for item in checklist.get("items", []):
        v = reason_step(item, observations, run_id)
        t = timing.get(item.get("item_id"))
        if t:
            v["sequence_ok"] = t.sequence_ok
            v["duration_ok"] = t.duration_ok
        verdicts.append(v)

    verdicts = enforce_unique_evidence(verdicts)
    verdicts = apply_absence_inference(verdicts, observations, checklist.get("items", []))

    compliant = sum(1 for v in verdicts if v["verdict"] == "Compliant")
    deviation = sum(1 for v in verdicts if v["verdict"] == "Deviation Detected")
    unable = sum(1 for v in verdicts if v["verdict"] == "Unable to Verify")
    inspection = sum(1 for v in verdicts if v["verdict"] == "Requires Inspection")
    denom = compliant + deviation
    score = round(compliant / denom, 3) if denom else None

    data = {
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
    out.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    print("\n" + "=" * 58)
    print(f"  {args.which}  —  industreal live run")
    print("=" * 58)
    print(f"  Compliant          : {compliant}")
    print(f"  Deviation Detected : {deviation}")
    print(f"  Unable to Verify   : {unable}")
    print(f"  Requires Inspection: {inspection}")
    print(f"  Adherence Score    : {f'{score:.1%}' if score is not None else 'N/A'}  (of {denom} video-verifiable steps)")
    print(f"  Written            : {out.name}")
    print("=" * 58)


if __name__ == "__main__":
    main()
