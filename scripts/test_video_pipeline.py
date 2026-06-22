"""
Smoke test for the video analysis pipeline (OpenCV + GPT-4o Vision).

Tests the current pipeline without Content Understanding:
  1. probe_video_duration — OpenCV reads the video and returns duration
  2. build_time_windowed_segments — synthesizes overlapping windows
  3. run_video_phase2 — GPT-4o Vision compliance field extraction (optional, costs ~$0.02/window)

Usage:
    python scripts/test_video_pipeline.py --url "https://your-sas-url..."
    python scripts/test_video_pipeline.py --url "https://..." --phase2
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
logger = logging.getLogger(__name__)

SAMPLE_VIDEO_URL = (
    "https://raw.githubusercontent.com/Azure-Samples"
    "/azure-ai-content-understanding-python/main/data/sample_video.mp4"
)


def parse_args():
    parser = argparse.ArgumentParser(description="ProcedureGuard video pipeline smoke test")
    parser.add_argument("--url", default=SAMPLE_VIDEO_URL, help="Video URL (public HTTPS or Blob SAS)")
    parser.add_argument("--run-id", default="run-smoke-test-001")
    parser.add_argument("--window-seconds", type=float, default=25.0)
    parser.add_argument("--overlap-seconds", type=float, default=6.0)
    parser.add_argument(
        "--phase2",
        action="store_true",
        help="Run GPT-4o Phase 2 field extraction (costs ~$0.02/window)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    from src.ingestion.video_analyzer import build_time_windowed_segments, probe_video_duration, run_video_phase2

    print("ProcedureGuard — Video Pipeline Smoke Test")
    print(f"Video : {args.url[:80]}...")
    print(f"run_id: {args.run_id}")

    print("\n" + "=" * 60)
    print("STEP 1: Duration probe (OpenCV)")
    print("=" * 60)
    duration = probe_video_duration(args.url)
    if duration <= 0:
        print("❌ Could not open video — check URL and network access")
        sys.exit(1)
    print(f"✅ Duration: {duration:.1f}s")

    print("\n" + "=" * 60)
    print("STEP 2: Time-windowed segmentation")
    print("=" * 60)
    segments = build_time_windowed_segments(
        duration, window_seconds=args.window_seconds, overlap_seconds=args.overlap_seconds
    )
    print(f"✅ {len(segments)} window(s) ({args.window_seconds:.0f}s each, {args.overlap_seconds:.0f}s overlap)")
    for seg in segments:
        print(f"   {seg['segment_id']}: {seg['start_time_seconds']:.1f}s – {seg['end_time_seconds']:.1f}s")

    if not args.phase2:
        print("\nSkipping Phase 2 (pass --phase2 to run GPT-4o Vision field extraction)")
        sys.exit(0)

    print("\n" + "=" * 60)
    print("STEP 3: GPT-4o Phase 2 — compliance field extraction")
    print("=" * 60)
    observations = {
        "run_id": args.run_id,
        "video_url": args.url,
        "video_duration_seconds": duration,
        "segments": segments,
        "total_segments": len(segments),
    }
    try:
        run_video_phase2(observations, args.run_id, video_url=args.url)
        print(f"\n✅ Phase 2 complete")
        print("\nObservations JSON:")
        print("-" * 40)
        print(json.dumps(observations, indent=2, default=str))
    except Exception as exc:
        print(f"❌ Phase 2 failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
