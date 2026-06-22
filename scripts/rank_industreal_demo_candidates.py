"""
Rank IndustReal recordings for a ProcedureGuard-style demo using only the
small action-recognition label bundle.

Why this exists:
- The full IndustReal dataset is large.
- ProcedureGuard currently struggles with fine-detail errors (pins, screws,
  washers, seating/orientation).
- We want a cheap, local first pass that prioritizes clips whose error is more
  likely to be visible at coarse video resolution.

Heuristic:
- Start from the action-recognition labels in train.csv / val.csv / test.csv.
- Treat recordings with a middle index of 0 (e.g. 03_assy_0_1) as the clean
  baseline for the same participant + task mode.
- Compare each error recording against its clean baseline.
- Prefer recordings whose large-part "fit_*" actions are missing or reduced
  (wheel / pulley / wing / wing beam), because those are more likely to create
  a visibly wrong final state than fine-detail fastener errors.
- Explicitly demote the two known-problem demo clips already investigated in
  ProcedureGuard: 03_assy_1_3 and 08_assy_2_4.

This script does NOT prove that an error is visually obvious. It produces a
ranked shortlist for manual frame inspection.
"""
from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path


_ID_RE = re.compile(r"^(?P<participant>\d+)_(?P<mode>assy|main)_(?P<variant>\d+)_(?P<trial>\d+)$")

# Large visible parts / assemblies are weighted higher than fine-detail acts.
_VISIBLE_ACTION_WEIGHTS = {
    "fit_wheel": 4,
    "fit_pulley": 4,
    "fit_wing": 3,
    "fit_wing_beam": 3,
    "put_wheel": 1,
    "put_pulley": 1,
}

# These two are already known bad demo choices from local ProcedureGuard work:
# - 03_assy_1_3: front chassis issue not honestly catchable from the current setup
# - 08_assy_2_4: wrong-pin substitution, too fine-grained
_KNOWN_SUBTLE_CLIPS = {
    "03_assy_1_3": "Known front-chassis clip; already found not honestly catchable.",
    "08_assy_2_4": "Known wrong-pin clip; fine-detail substitution, not a good demo.",
}

_DELTA_KEYS = (
    "fit_wheel",
    "fit_pulley",
    "fit_wing",
    "fit_wing_beam",
    "put_wheel",
    "put_pulley",
    "pull_wheel",
)


def _load_records(labels_dir: Path) -> dict[str, dict]:
    records: dict[str, dict] = {}
    for split in ("train", "val", "test"):
        csv_path = labels_dir / f"{split}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Missing labels file: {csv_path}")

        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                recording_id, action_name = row[0], row[2]
                rec = records.setdefault(
                    recording_id,
                    {"split": split, "counts": Counter()},
                )
                rec["counts"][action_name] += 1
    return records


def _score_candidate(recording_id: str, split: str, deltas: dict[str, int], mode: str) -> tuple[int, str]:
    score = 0
    notes: list[str] = []

    for action_name, weight in _VISIBLE_ACTION_WEIGHTS.items():
        delta = deltas.get(action_name, 0)
        if delta < 0:
            score += (-delta) * weight
            notes.append(f"missing/reduced {action_name} ({delta})")

    if deltas.get("pull_wheel", 0) > 0:
        score += deltas["pull_wheel"] * 3
        notes.append(f"repair/rework signal pull_wheel (+{deltas['pull_wheel']})")

    if mode == "assy":
        score += 3
        notes.append("assembly clip")

    if split == "test":
        score += 2
        notes.append("test split")
    elif split == "val":
        score += 1
        notes.append("validation split")

    if recording_id in _KNOWN_SUBTLE_CLIPS:
        score -= 100
        notes.append(_KNOWN_SUBTLE_CLIPS[recording_id])

    return score, "; ".join(notes)


def rank_candidates(labels_dir: Path) -> list[dict]:
    records = _load_records(labels_dir)
    ranked: list[dict] = []

    for recording_id, rec in sorted(records.items()):
        match = _ID_RE.match(recording_id)
        if not match:
            continue

        mode = match.group("mode")
        variant = match.group("variant")
        if variant == "0":
            continue

        participant = match.group("participant")
        baseline_id = f"{participant}_{mode}_0_1"
        if baseline_id not in records:
            continue

        baseline_counts = records[baseline_id]["counts"]
        error_counts = rec["counts"]
        all_actions = set(baseline_counts) | set(error_counts)
        deltas = {action: error_counts[action] - baseline_counts[action] for action in all_actions}

        score, note = _score_candidate(recording_id, rec["split"], deltas, mode)
        visible_deltas = {k: deltas[k] for k in _DELTA_KEYS if deltas.get(k)}

        if recording_id in _KNOWN_SUBTLE_CLIPS:
            recommendation = "avoid"
        elif score >= 10:
            recommendation = "high"
        elif score >= 6:
            recommendation = "medium"
        else:
            recommendation = "low"

        ranked.append(
            {
                "recording_id": recording_id,
                "split": rec["split"],
                "mode": mode,
                "baseline_id": baseline_id,
                "score": score,
                "recommendation": recommendation,
                "visible_deltas": visible_deltas,
                "note": note,
            }
        )

    ranked.sort(key=lambda row: (-row["score"], row["recording_id"]))
    return ranked


def write_csv(rows: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "recording_id",
                "split",
                "mode",
                "baseline_id",
                "score",
                "recommendation",
                "visible_deltas",
                "note",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **row,
                    "visible_deltas": "; ".join(f"{k}:{v}" for k, v in row["visible_deltas"].items()),
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank IndustReal clips for demo-worthiness.")
    parser.add_argument(
        "--labels-dir",
        type=Path,
        default=Path("industreal_meta/action_recognition_labels"),
        help="Directory containing train.csv, val.csv, and test.csv from action_recognition_labels.zip",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("industreal_meta/demo_candidate_rankings.csv"),
        help="CSV output path",
    )
    args = parser.parse_args()

    rows = rank_candidates(args.labels_dir)
    write_csv(rows, args.output)

    print(f"Wrote {len(rows)} ranked recordings to {args.output}")
    print("\nTop candidates:")
    for row in rows[:10]:
        print(
            f"  {row['recording_id']:12s} | {row['recommendation']:6s} | "
            f"score={row['score']:>3} | split={row['split']:>5s} | {row['visible_deltas']}"
        )


if __name__ == "__main__":
    main()
