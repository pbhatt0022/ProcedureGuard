"""
Smoke test for the video analysis pipeline.

Tests Content Understanding against a real video without needing the full
pipeline or Streamlit. Runs two passes:
  1. Quick API check with Microsoft's sample video (public URL, no upload needed)
  2. Full compliance analyzer test with the same or your own video

Usage:
    # Quickest test — uses Microsoft's public sample video
    python scripts/test_video_pipeline.py

    # Test with your own video URL (already in Blob Storage)
    python scripts/test_video_pipeline.py --url "https://your-sas-url..."

    # Skip step 1 and go straight to the compliance analyzer
    python scripts/test_video_pipeline.py --skip-prebuilt

What to look for in the output:
    - If step 1 fails: likely an auth or endpoint issue (fix before step 2)
    - If step 2 fails at analyzer creation: check KNOWN_ISSUES.md for current constraints
    - If fields return null: expected in Phase 1 — GPT-4o vision pass not yet wired in
    - If segments = 0: custom field schema issue — see KNOWN_ISSUES.md

Owner: Priya (video pipeline)
"""
import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure project root is on sys.path so `config` and `src` are importable
# when running this script directly (e.g. `python scripts/test_video_pipeline.py`)
sys.path.insert(0, str(Path(__file__).parent.parent))

# Force UTF-8 stdout so emoji in print statements work on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Microsoft's public sample video — no upload needed for quick testing.
# Using raw.githubusercontent.com (direct CDN, no redirect) instead of
# github.com/raw/... which Azure services can't follow due to redirects.
SAMPLE_VIDEO_URL = (
    "https://raw.githubusercontent.com/Azure-Samples"
    "/azure-ai-content-understanding-python/main/data/sample_video.mp4"
)


def parse_args():
    parser = argparse.ArgumentParser(description="ProcedureGuard video pipeline smoke test")
    parser.add_argument(
        "--url",
        default=SAMPLE_VIDEO_URL,
        help="Video URL to test (public HTTPS or Blob SAS URL). Defaults to Microsoft sample video.",
    )
    parser.add_argument(
        "--run-id",
        default="run-smoke-test-001",
        help="run_id for this test run (default: run-smoke-test-001)",
    )
    parser.add_argument(
        "--skip-prebuilt",
        action="store_true",
        help="Skip the prebuilt-videoSearch test and go straight to the custom compliance analyzer",
    )
    parser.add_argument(
        "--phase2",
        action="store_true",
        help=(
            "Run the GPT-4o compliance field extraction pass (Phase 2) after Phase 1. "
            "Requires AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in .env. "
            "Incurs a small Azure OpenAI cost (~$0.01 per segment)."
        ),
    )
    return parser.parse_args()


def step1_prebuilt_check(video_url: str, run_id: str) -> bool:
    """
    Quick API reachability check using prebuilt-videoSearch.
    If this fails, there is an auth or endpoint issue to fix first.
    """
    from azure.ai.contentunderstanding import ContentUnderstandingClient
    from azure.ai.contentunderstanding.models import AnalysisInput
    from azure.core.credentials import AzureKeyCredential
    from azure.identity import DefaultAzureCredential
    from config import cfg

    print("\n" + "=" * 60)
    print("STEP 1: Prebuilt analyzer check (prebuilt-videoSearch)")
    print("=" * 60)
    print(f"Endpoint : {cfg.content_understanding_endpoint}")
    print(f"Video URL: {video_url[:80]}...")

    try:
        credential = (
            AzureKeyCredential(cfg.content_understanding_key)
            if cfg.content_understanding_key
            else DefaultAzureCredential()
        )
        client = ContentUnderstandingClient(
            endpoint=cfg.content_understanding_endpoint,
            credential=credential,
        )
        poller = client.begin_analyze(
            analyzer_id="prebuilt-videoSearch",
            inputs=[AnalysisInput(url=video_url)],
        )
        result = poller.result()
        print(f"\n✅ Step 1 passed — API reachable, {len(result.contents)} content segment(s) returned")

        # Print a snippet of the markdown to see what prebuilt gives us
        if result.contents:
            content = result.contents[0]
            md = getattr(content, "markdown", None)
            if md:
                print("\nFirst 500 chars of markdown output:")
                print("-" * 40)
                print(md[:500])
        return True

    except Exception as e:
        print(f"\n❌ Step 1 failed: {e}")
        print("\nCommon causes:")
        print("  - RBAC role not propagated yet (wait 2 min and retry)")
        print("  - Wrong endpoint in .env — check AZURE_CONTENT_UNDERSTANDING_ENDPOINT")
        print("  - az login session expired — run `az login --tenant <tenant-id>`")
        return False


def step2_compliance_analyzer(video_url: str, run_id: str):
    """
    Full test with the custom compliance field schema.
    Creates the analyzer if it doesn't exist, then analyzes the video.

    Returns:
        (True, observations) on success, (False, None) on failure.
    """
    from src.ingestion.video_analyzer import (
        create_or_update_analyzer,
        analyze_video,
        parse_observations,
    )

    print("\n" + "=" * 60)
    print("STEP 2: Custom compliance analyzer test")
    print("=" * 60)

    # 2a — Create/update the custom analyzer
    print("\n[2a] Creating/updating compliance analyzer...")
    try:
        create_or_update_analyzer()
        print("✅ Analyzer created/updated successfully")
    except Exception as e:
        print(f"❌ Analyzer creation failed: {e}")
        print("\nIf error mentions 'model deployment' or 'gpt-4.1':")
        print("  You may need to deploy gpt-4.1-mini in Azure AI Foundry first.")
        print("  See docs/KNOWN_ISSUES.md for the workaround.")
        return False, None

    # 2b — Submit video for analysis
    print(f"\n[2b] Analyzing video with compliance schema...")
    print("     (This can take 1–5 minutes depending on video length)")
    try:
        raw_result = analyze_video(video_url, run_id)
    except Exception as e:
        print(f"❌ Video analysis failed: {e}")
        return False, None

    # 2c — Parse and display observations
    print("\n[2c] Parsing observations...")
    observations = parse_observations(raw_result, run_id, video_url)

    print(f"\n✅ Analysis complete — {observations['total_segments']} segment(s)")
    print("\nObservations JSON:")
    print("-" * 40)
    print(json.dumps(observations, indent=2))

    # 2d — Quality check: flag null-heavy segments
    print("\n" + "=" * 60)
    print("QUALITY CHECK — 1fps/512px field coverage")
    print("=" * 60)
    null_segments = 0
    for seg in observations["segments"]:
        generative_fields = [seg["tool_in_use"], seg["component_contact"], seg["action_observed"]]
        null_count = sum(1 for v in generative_fields if v is None)
        status = "⚠️  ALL NULL" if null_count == 3 else f"✅ {3 - null_count}/3 fields populated"
        duration = seg["end_time_seconds"] - seg["start_time_seconds"]
        print(f"  {seg['segment_id']} ({duration:.1f}s): {status}")
        if null_count == 3:
            null_segments += 1

    if null_segments > 0:
        print(f"\n⚠️  {null_segments}/{observations['total_segments']} segments have all-null fields.")
        print("   Phase 1 (prebuilt-video base): expected — segment detection works.")
        print("   Run with --phase2 to fill compliance fields via GPT-4o.")
    else:
        print("\n✅ All segments have at least some fields populated.")
        print("   GPT-4o vision pass is active and producing compliance observations.")

    return True, observations


def step3_gpt4o_phase2(observations: dict, run_id: str) -> bool:
    """
    GPT-4o compliance field extraction (Phase 2).
    Fills ppe_status, tool_in_use, component_contact, visible_safety_concern,
    action_observed for every segment using the Content Understanding description.
    """
    from src.ingestion.video_analyzer import run_video_phase2
    from config import cfg

    print("\n" + "=" * 60)
    print("STEP 3: GPT-4o Phase 2 — compliance field extraction")
    print("=" * 60)
    print(f"OpenAI endpoint : {cfg.openai_endpoint}")
    print(f"Deployment      : {cfg.openai_deployment}")
    print(f"Segments to process: {observations['total_segments']}")

    if not cfg.openai_endpoint:
        print("\n❌ AZURE_OPENAI_ENDPOINT not set in .env — cannot run Phase 2")
        return False

    try:
        updated = run_video_phase2(observations, run_id)
        print(f"\n✅ Phase 2 complete — {updated['total_segments']} segment(s) processed")
        print("\nUpdated Observations JSON:")
        print("-" * 40)
        print(json.dumps(updated, indent=2))

        # Quality summary
        print("\n" + "=" * 60)
        print("PHASE 2 QUALITY SUMMARY")
        print("=" * 60)
        for seg in updated["segments"]:
            seg_id = seg["segment_id"]
            dur = seg.get("end_time_seconds", 0) - seg.get("start_time_seconds", 0)
            ppe = seg.get("ppe_status") or "N/A"
            action = (seg.get("action_observed") or "N/A")[:70]
            concern = "⚠️  YES" if seg.get("visible_safety_concern") else "no"
            print(f"  {seg_id} ({dur:.1f}s) | PPE: {ppe} | safety: {concern}")
            print(f"    action: {action}")
        return True

    except Exception as e:
        print(f"\n❌ Phase 2 failed: {e}")
        print("\nCommon causes:")
        print("  - AZURE_OPENAI_API_KEY missing or wrong in .env")
        print("  - gpt-4o deployment not provisioned in procedureguard-openai")
        print("  - Network/firewall blocking the OpenAI endpoint")
        return False


def main():
    args = parse_args()

    print("ProcedureGuard — Video Pipeline Smoke Test")
    print(f"Video : {args.url}")
    print(f"run_id: {args.run_id}")

    if not args.skip_prebuilt:
        ok = step1_prebuilt_check(args.url, args.run_id)
        if not ok:
            print("\nFix Step 1 before proceeding to Step 2.")
            sys.exit(1)

    ok, observations = step2_compliance_analyzer(args.url, args.run_id)

    if args.phase2:
        if not ok or observations is None:
            print("\nPhase 1 failed — skipping Phase 2.")
            sys.exit(1)
        step3_gpt4o_phase2(observations, args.run_id)


if __name__ == "__main__":
    main()
