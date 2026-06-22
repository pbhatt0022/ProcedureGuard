"""
End-to-end pipeline smoke test.

Runs the full Flow 1 pipeline against real Azure services and prints
a formatted compliance report. Use this to validate before the demo.

Usage:
    # Quickest: Microsoft sample video + Prusa SOP (pages 1-10, section granularity)
    python scripts/run_pipeline_demo.py

    # Custom inputs
    python scripts/run_pipeline_demo.py \\
        --sop tests/fixtures/prusa_mk3s_plus_assembly.pdf \\
        --video "https://your-sas-url..." \\
        --pages 1-30

Cost estimate: ~$0.05–0.15 per run (Document Intelligence + GPT-4o calls)
"""
import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# NOTE: the repo's video is stored in Git LFS — raw.githubusercontent.com serves
# only the LFS pointer text, which Content Understanding rejects with
# ContentSourceNotAccessible. media.githubusercontent.com serves the real binary.
SAMPLE_VIDEO_URL = (
    "https://media.githubusercontent.com/media/Azure-Samples"
    "/azure-ai-content-understanding-python/main/data/FlightSimulator.mp4"
)
DEFAULT_SOP = str(Path(__file__).parent.parent / "tests/fixtures/prusa_mk3s_plus_assembly.pdf")


def parse_args():
    p = argparse.ArgumentParser(description="ProcedureGuard end-to-end pipeline demo")
    p.add_argument("--sop", default=DEFAULT_SOP,
                   help="Path or URL to SOP PDF (default: Prusa fixture)")
    p.add_argument("--video", default=SAMPLE_VIDEO_URL,
                   help="Video URL (default: Microsoft sample video)")
    p.add_argument("--pages", default="1-10",
                   help="Page range for SOP extraction (default: 1-10)")
    p.add_argument("--granularity", default="section",
                   choices=["section", "paragraph"],
                   help="SOP parsing granularity (default: section)")
    p.add_argument("--json-out", metavar="FILE",
                   help="Write full results JSON to this file")
    return p.parse_args()


def print_report(results: dict) -> None:
    run_id = results["run_id"]
    summary = results["summary"]
    score = results["adherence_score"]
    verdicts = results["verdicts"]

    print("\n" + "=" * 65)
    print("  PROCEDUREGUARD — COMPLIANCE REPORT")
    print("=" * 65)
    print(f"  run_id   : {run_id}")
    print(f"  SOP steps: {results['sop_steps']['total_steps']}")
    print(f"  Checklist: {results['checklist']['total_items']} items")
    print(f"  Segments : {results['observations']['total_segments']}")
    print()
    print(f"  Compliant         : {summary['compliant']}")
    print(f"  Deviation Detected: {summary['deviation']}")
    print(f"  Unable to Verify  : {summary['unable_to_verify']}")
    score_str = f"{score:.1%}" if score is not None else "N/A (no scoreable steps)"
    print(f"  Adherence Score   : {score_str}")
    print("=" * 65)

    _ICONS = {
        "Compliant": "✅",
        "Deviation Detected": "❌",
        "Unable to Verify": "⚠️ ",
    }

    for v in verdicts:
        icon = _ICONS.get(v["verdict"], "?")
        conf = f"{v['confidence']:.0%}"
        seq = ""
        if v.get("sequence_ok") is False:
            seq = " [OUT OF ORDER]"
        dur = ""
        if v.get("duration_ok") is False:
            dur = " [TOO SHORT]"
        print(f"\n{icon} {v['step_id']} | {v['verdict']} ({conf}){seq}{dur}")
        print(f"   Criterion : {v['criterion'][:70]}")
        print(f"   Reasoning : {(v['reasoning'] or '')[:80]}")
        if v.get("evidence_segment_id"):
            ts = (
                f"{v['evidence_timestamp_start']:.1f}s"
                f"–{v['evidence_timestamp_end']:.1f}s"
            )
            print(f"   Evidence  : {v['evidence_segment_id']} ({ts})")

    print("\n" + "=" * 65)


def main():
    args = parse_args()

    print("ProcedureGuard — End-to-End Pipeline Demo")
    print(f"SOP   : {args.sop}")
    print(f"Video : {args.video}")
    print(f"Pages : {args.pages}  Granularity: {args.granularity}")
    print("\nRunning pipeline... (this takes 2–5 minutes)\n")

    from src.pipeline import run_pipeline

    try:
        results = run_pipeline(
            sop_source=args.sop,
            video_url=args.video,
            sop_pages=args.pages,
            sop_granularity=args.granularity,
        )
    except Exception as exc:
        print(f"\n❌ Pipeline failed: {exc}")
        raise

    print_report(results)

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nFull results written to {args.json_out}")


if __name__ == "__main__":
    main()
