"""
VLM Stability Probe: run Phase 2 vision analysis on the clean baseline 3 times
and report naming and checklist-flagging stability.
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.video_analyzer import (
    build_time_windowed_segments,
    probe_video_duration,
    run_video_phase2,
)

_ROOT = Path(__file__).parent.parent
_CHECKLIST_PATH = _ROOT / "experiments" / "sop_gt" / "_checklist_gtgrounded.json"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    # Add caching for extract_compliance_fields to avoid re-running slow vision calls on crash
    import src.ingestion.video_analyzer as va
    original_extract = va.extract_compliance_fields
    cache_path = _ROOT / "experiments" / "sop_gt" / "vlm_cache.json"

    if cache_path.exists():
        try:
            vlm_cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            vlm_cache = {}
    else:
        vlm_cache = {}

    def cached_extract(description, segment_id, run_id, keyframe_images=None, checklist_items=None):
        key = f"{run_id}:{segment_id}"
        if key in vlm_cache:
            return vlm_cache[key]
        res = original_extract(description, segment_id, run_id, keyframe_images=keyframe_images, checklist_items=checklist_items)
        vlm_cache[key] = res
        try:
            cache_path.write_text(json.dumps(vlm_cache, indent=2), encoding="utf-8")
        except Exception:
            pass
        return res

    va.extract_compliance_fields = cached_extract

    video_path = _ROOT / "industreal_selected/videos/baselines/23_assy_0_1.mp4"
    if not video_path.exists():
        sys.exit(f"Video not found: {video_path}")

    checklist = json.loads(_CHECKLIST_PATH.read_text(encoding="utf-8"))
    video_url = str(video_path)
    duration = probe_video_duration(video_url)

    print("=" * 65)
    print("  ProcedureGuard — VLM Naming Stability Probe")
    print(f"  Clip        : {video_path.name}")
    print(f"  Checklist   : {len(checklist['items'])} items")
    print(f"  Duration    : {duration:.1f}s")
    print("=" * 65)

    base_segments = build_time_windowed_segments(duration, window_seconds=25.0, overlap_seconds=6.0)
    print(f"Generated {len(base_segments)} segments. Running Phase 2 three times sequentially...")

    runs = []
    for run_idx in range(1, 4):
        print(f"\n--- RUN {run_idx}/3 ---")
        obs = {
            "run_id": f"probe-run-{run_idx}",
            "video_url": video_url,
            "video_duration_seconds": duration,
            "segments": copy.deepcopy(base_segments),
        }
        run_video_phase2(obs, f"probe-run-{run_idx}", video_url=video_url, checklist=checklist)
        runs.append(obs)
        print(f"RUN {run_idx} complete.")

    # Analyse flagging consistency per segment, per checklist item
    all_items = [it["item_id"] for it in checklist["items"]]
    segment_ids = [seg["segment_id"] for seg in base_segments]

    print("\n" + "=" * 65)
    print("  FLAGGING CONSISTENCY RESULTS")
    print("=" * 65)
    print(f"  {'Step':<10} | {'Segment':<10} | {'Run 1':<6} | {'Run 2':<6} | {'Run 3':<6} | {'Status':<10}")
    print("-" * 65)

    unstable_count = 0
    stable_count = 0

    for item_id in all_items:
        for seg_id in segment_ids:
            flags = []
            for run_idx, run_data in enumerate(runs):
                seg = next(s for s in run_data["segments"] if s["segment_id"] == seg_id)
                observed = {e["item_id"] for e in seg.get("observed_items") or []}
                flags.append(item_id in observed)

            # If it was never flagged, skip showing it to avoid spamming empty rows
            if not any(flags):
                continue

            # Check if all runs agree (either all True or all False)
            is_stable = all(f == flags[0] for f in flags)
            status = "STABLE" if is_stable else "UNSTABLE (X)"
            if is_stable:
                stable_count += 1
            else:
                unstable_count += 1

            r1 = "FLAG" if flags[0] else "-"
            r2 = "FLAG" if flags[1] else "-"
            r3 = "FLAG" if flags[2] else "-"
            print(f"  {item_id:<10} | {seg_id:<10} | {r1:<6} | {r2:<6} | {r3:<6} | {status}")

    print("-" * 65)
    print(f"  Summary: Stable flags = {stable_count}, Unstable flags = {unstable_count}")
    print("=" * 65)

    # Save detailed data for inspection
    out_path = _ROOT / "experiments/sop_gt/vlm_stability_probe_results.json"
    out_path.write_text(json.dumps(runs, indent=2, default=str), encoding="utf-8")
    print(f"Detailed logs saved to {out_path.name}")


if __name__ == "__main__":
    main()
