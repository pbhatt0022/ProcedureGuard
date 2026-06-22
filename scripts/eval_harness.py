"""
ProcedureGuard — Presence-tier evaluation harness.

Compares pipeline verdicts against IndustReal ground truth labels
(industreal_meta/demo_candidate_rankings.csv visible_deltas) for all
clips that have existing results JSON files.

Usage:
    python scripts/eval_harness.py               # evaluate all available clips
    python scripts/eval_harness.py --verbose      # show per-item detail

Output:
    Per-clip verdict table + aggregate precision/recall on the presence tier.

Ground truth methodology
------------------------
IndustReal ground truth comes from action-recognition labels (train/test/val
CSVs) expressed as per-clip deltas versus a matched clean baseline:
    fit_wheel:-1  means 1 fewer fit_wheel event vs baseline
    fit_pulley:-1 means 1 fewer fit_pulley event vs baseline

We map these deltas onto our 10 presence-tier checklist items (which cover the
STEMFIE SOP steps we extract from pages 1–10). Mapping confidence is noted
explicitly for each entry; uncertain mappings are marked UNRESOLVED and excluded
from precision/recall to avoid contaminating the metric.

Checklist presence-tier items (for reference):
    check-007  Hands removed from assembly after each step
    check-011  [fine_detail in current checklist — listed for completeness]
    check-012  Front chassis mounted onto base
    check-013  Pin through aligned bores of front chassis
    check-016  Long braces mounted onto rear interface of base
    check-017  Pin through forward bore of rear chassis
    check-018  Pin through rearmost bore of rear chassis
    check-021  Front bracket mounted onto front chassis interface
    check-022  Screw installed onto front bracket
    check-024  Front wheel assembly mounted onto axle
    check-025  Rear wheel assembly + pulley on rear axle
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Literal

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ── Ground truth ──────────────────────────────────────────────────────────────
# Per-clip, per-item expected outcome for presence-tier checklist items.
# True  = SHOULD fire Deviation Detected (step was skipped/wrong in this clip)
# False = SHOULD NOT fire Deviation Detected (step was done correctly)
# Absent key = unknown/unresolved → excluded from metrics
#
# Derivation notes
# ────────────────
# 22_assy_2_3 (candidate vs 22_assy_0_1 baseline)
#   fit_wheel:-1  + fit_pulley:-1 → rear wheel assembly (check-025) missing.
#   When fit_pulley is also missing the rear axle group is the skip.
#   fit_wing_beam:-1 → possibly check-016 but STEMFIE "wing beam" vs "long brace"
#   nomenclature is ambiguous without comparing SOP to IndustReal part names →
#   UNRESOLVED; excluded.
#   fit_wing:+1 → extra wing fit, not a deviation for our checklist → excluded.
#
# 23_assy_1_2 (candidate vs 23_assy_0_1 baseline)
#   fit_wheel:-1  (no fit_pulley missing) → rear axle assembly seems complete;
#   front wheel (check-024) is more likely the skip when pulley is present.
#   fit_wing:-1  → no matching presence-tier item in our checklist → UNRESOLVED.
#   fit_wing_beam:+1 → extra, not a deviation → excluded.
#
# 16_main_3_3 (candidate vs 16_main_0_1 baseline, "main" assembly mode)
#   fit_wheel:-2 + put_wheel:-1 → both wheel assemblies (check-024, check-025)
#   appear to be missing. NOTE: this is a "main" mode clip; the STEMFIE
#   subassembly coverage of our SOP extraction may not align perfectly →
#   confidence is MEDIUM rather than HIGH.
#
# 23_assy_0_1 (clean baseline)
#   All presence-tier items should NOT fire.
#   Any Deviation Detected verdict here is a definite false positive.

GT_ITEM_LEVEL: dict[str, dict[str, bool]] = {
    "22_assy_2_3": {
        "check-024": False,  # front wheel — done (fit_wheel:-1 accounted for by rear assembly)
        "check-025": True,   # rear wheel + pulley — missing (fit_wheel:-1 + fit_pulley:-1)
        # check-016: UNRESOLVED (fit_wing_beam:-1, nomenclature ambiguity)
    },
    "23_assy_1_2": {
        "check-024": True,   # front wheel — likely missing (fit_wheel:-1 without fit_pulley)
        "check-025": False,  # rear axle + pulley — likely present (no fit_pulley delta)
        # check-016: UNRESOLVED (fit_wing_beam:+1 is extra, not a skip)
    },
    "16_main_3_3": {
        "check-024": True,   # front wheel — missing (fit_wheel:-2, medium confidence)
        "check-025": True,   # rear wheel — missing (fit_wheel:-2 + put_wheel:-1, medium confidence)
    },
    "23_assy_0_1": {
        "check-012": False,
        "check-013": False,
        "check-016": False,
        "check-017": False,
        "check-018": False,
        "check-021": False,
        "check-022": False,
        "check-024": False,
        "check-025": False,
    },
    # 17_assy_1_5 (candidate vs 17_assy_0_1 baseline)
    #   fit_pulley:-1 → rear axle pulley missing (check-025 FAIL)
    #   no fit_wheel delta → front wheel present (check-024 PASS)
    #   NOTE: clip not yet uploaded to Blob Storage; results file pending
    "17_assy_1_5": {
        "check-024": False,
        "check-025": True,
    },
    # 18_assy_2_5 (candidate vs 18_assy_0_1 baseline)
    #   fit_pulley:-1 → rear axle pulley missing (check-025 FAIL)
    #   no fit_wheel delta → front wheel present (check-024 PASS)
    #   NOTE: clip not yet uploaded to Blob Storage; results file pending
    "18_assy_2_5": {
        "check-024": False,
        "check-025": True,
    },
}

# Maps clip_id → result JSON filename (relative to project root)
RESULT_FILES: dict[str, str] = {
    "22_assy_2_3":  "demo_results_industreal_22_assy_2_3_candidate.json",
    "23_assy_1_2":  "demo_results_industreal_23_assy_1_2_candidate.json",
    "16_main_3_3":  "demo_results_industreal_16_main_3_3_candidate.json",
    "23_assy_0_1":  "demo_results_industreal_23_assy_0_1_baseline.json",
    "17_assy_1_5":  "demo_results_industreal_17_assy_1_5_candidate.json",
    "18_assy_2_5":  "demo_results_industreal_18_assy_2_5_candidate.json",
}

VerdictLabel = Literal["Compliant", "Deviation Detected", "Unable to Verify",
                        "Requires Inspection"]

_ROOT = Path(__file__).parent.parent


# ── Core evaluation ───────────────────────────────────────────────────────────

def load_results(clip_id: str) -> dict | None:
    fname = RESULT_FILES.get(clip_id)
    if not fname:
        return None
    path = _ROOT / "demo_results" / fname
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def verdicts_by_item(results: dict) -> dict[str, dict]:
    """Return {item_id: verdict_dict} for all verdicts in a results file."""
    return {v["item_id"]: v for v in results.get("verdicts", [])}


def classify_verdict(
    pipeline_verdict: VerdictLabel,
    expected_fail: bool,
) -> str:
    """
    Classify a single (pipeline, ground_truth) pair.

    Returns: "TP" | "FP" | "FN" | "TN"
    Only Deviation Detected counts as a positive prediction.
    Unable to Verify on a known-fail step is a False Negative.
    """
    predicted_positive = pipeline_verdict == "Deviation Detected"
    if expected_fail and predicted_positive:
        return "TP"
    if not expected_fail and predicted_positive:
        return "FP"
    if expected_fail and not predicted_positive:
        return "FN"
    return "TN"


def evaluate_clip(
    clip_id: str,
    verbose: bool = False,
) -> dict | None:
    """
    Evaluate one clip against its ground truth.

    Returns a dict with:
        clip_id, run_id, counts (TP/FP/FN/TN), precision, recall,
        items (list of per-item detail dicts)
    Returns None if the results file is missing.
    """
    results = load_results(clip_id)
    if results is None:
        print(f"  [skip] {clip_id} — results file not found")
        return None

    gt = GT_ITEM_LEVEL.get(clip_id, {})
    if not gt:
        print(f"  [skip] {clip_id} — no ground truth defined")
        return None

    vdict = verdicts_by_item(results)
    counts = {"TP": 0, "FP": 0, "FN": 0, "TN": 0}
    items = []

    for item_id, expected_fail in gt.items():
        v = vdict.get(item_id, {})
        pipeline_verdict: VerdictLabel = v.get("verdict", "Unable to Verify")
        conf = v.get("confidence", 0.0)
        not_obs = v.get("not_observed", False)
        cls = classify_verdict(pipeline_verdict, expected_fail)
        counts[cls] += 1
        items.append({
            "item_id": item_id,
            "expected_fail": expected_fail,
            "pipeline_verdict": pipeline_verdict,
            "confidence": conf,
            "not_observed": not_obs,
            "classification": cls,
        })

    denom_p = counts["TP"] + counts["FP"]
    denom_r = counts["TP"] + counts["FN"]
    precision = counts["TP"] / denom_p if denom_p > 0 else None
    recall    = counts["TP"] / denom_r if denom_r > 0 else None

    return {
        "clip_id":   clip_id,
        "run_id":    results.get("run_id", "?"),
        "counts":    counts,
        "precision": precision,
        "recall":    recall,
        "items":     items,
    }


# ── Reporting ─────────────────────────────────────────────────────────────────

_CLS_SYMBOL = {"TP": "OK", "TN": " .", "FP": "FP", "FN": "FN"}
_CLS_LABEL  = {"TP": "TRUE  POS", "TN": "TRUE  NEG", "FP": "FALSE POS", "FN": "FALSE NEG"}


def print_report(results: list[dict], verbose: bool) -> None:
    sep = "=" * 68

    print(f"\n{sep}")
    print("  ProcedureGuard — Presence-tier Evaluation Report")
    print(sep)

    all_counts = {"TP": 0, "FP": 0, "FN": 0, "TN": 0}

    for r in results:
        c = r["counts"]
        denom_p = c["TP"] + c["FP"]
        denom_r = c["TP"] + c["FN"]
        p_str = f"{r['precision']:.0%}" if r["precision"] is not None else " N/A"
        rc_str = f"{r['recall']:.0%}"   if r["recall"]    is not None else " N/A"

        print(f"\n  {r['clip_id']}  ({r['run_id']})")
        print(f"  {'-'*62}")
        print(f"  TP={c['TP']}  FP={c['FP']}  FN={c['FN']}  TN={c['TN']}  "
              f"|  Precision={p_str}  Recall={rc_str}")

        if verbose:
            for item in r["items"]:
                sym   = _CLS_SYMBOL[item["classification"]]
                label = _CLS_LABEL[item["classification"]]
                gt_str = "FAIL" if item["expected_fail"] else "PASS"
                obs = " [not_observed]" if item.get("not_observed") else ""
                print(f"    {sym} {item['item_id']}  GT={gt_str:<4}  "
                      f"pipeline={item['pipeline_verdict']:<22}  "
                      f"conf={item['confidence']:.2f}  {label}{obs}")

        for k in all_counts:
            all_counts[k] += c[k]

    total_p_denom = all_counts["TP"] + all_counts["FP"]
    total_r_denom = all_counts["TP"] + all_counts["FN"]
    agg_p  = all_counts["TP"] / total_p_denom if total_p_denom > 0 else None
    agg_rc = all_counts["TP"] / total_r_denom if total_r_denom > 0 else None

    agg_p_str  = f"{agg_p:.0%}"  if agg_p  is not None else "N/A"
    agg_rc_str = f"{agg_rc:.0%}" if agg_rc is not None else "N/A"

    print(f"\n{sep}")
    print(f"  AGGREGATE  (across {len(results)} clip(s), {sum(all_counts.values())} evaluated items)")
    print(f"  TP={all_counts['TP']}  FP={all_counts['FP']}  FN={all_counts['FN']}  TN={all_counts['TN']}")
    print(f"  Precision = {agg_p_str}   Recall = {agg_rc_str}")
    print(sep)
    print()
    print("  Coverage note: only items with high-confidence GT mappings are")
    print("  included. Unmapped actions (fit_wing, fit_wing_beam) are excluded.")
    print("  Extend GT_ITEM_LEVEL in this script to add more clips/mappings.")
    print()


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate presence-tier accuracy against IndustReal GT")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show per-item classification detail")
    parser.add_argument("--clip", help="Evaluate a single clip (e.g. 22_assy_2_3)")
    args = parser.parse_args()

    clips = [args.clip] if args.clip else list(GT_ITEM_LEVEL.keys())
    evaluated = []
    for clip_id in clips:
        r = evaluate_clip(clip_id, verbose=args.verbose)
        if r:
            evaluated.append(r)

    if evaluated:
        print_report(evaluated, verbose=args.verbose)
    else:
        print("No clips could be evaluated — check that result JSON files exist.")


if __name__ == "__main__":
    main()
