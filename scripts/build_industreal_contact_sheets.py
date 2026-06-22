"""
Build side-by-side contact sheets for shortlisted IndustReal clips.

This is a purely local inspection tool:
- no Azure
- no GPT
- no ProcedureGuard pipeline calls

For each candidate clip and its clean baseline, the script samples frames
evenly across the full clip and near the end of the clip, then creates:
- a full-clip comparison strip
- an end-state comparison strip

These images are meant for quick human triage of whether the error looks
grossly visible enough for a ProcedureGuard demo.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import cv2
import numpy as np


PAIR_IDS = [
    "22_assy",
    "18_assy",
    "23_assy",
    "17_assy",
    "16_main",
    "10_assy",
]

PAIR_MAP = {
    "22_assy": ("22_assy_2_3.mp4", "22_assy_0_1.mp4"),
    "18_assy": ("18_assy_2_5.mp4", "18_assy_0_1.mp4"),
    "23_assy": ("23_assy_1_2.mp4", "23_assy_0_1.mp4"),
    "17_assy": ("17_assy_1_5.mp4", "17_assy_0_1.mp4"),
    "16_main": ("16_main_3_3.mp4", "16_main_0_1.mp4"),
    "10_assy": ("10_assy_3_2.mp4", "10_assy_0_1.mp4"),
}


def _open_video(path: Path) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {path}")
    return cap


def _video_duration_seconds(cap: cv2.VideoCapture) -> float:
    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
    return frames / fps if fps > 0 else 0.0


def _read_frame_at(cap: cv2.VideoCapture, t_s: float) -> np.ndarray:
    cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, t_s) * 1000.0)
    ok, frame = cap.read()
    if not ok or frame is None:
        raise RuntimeError(f"Could not read frame at {t_s:.2f}s")
    return frame


def _resize_keep_aspect(frame: np.ndarray, *, target_h: int) -> np.ndarray:
    h, w = frame.shape[:2]
    scale = target_h / h
    new_w = max(1, int(round(w * scale)))
    return cv2.resize(frame, (new_w, target_h), interpolation=cv2.INTER_AREA)


def _label_frame(frame: np.ndarray, label: str) -> np.ndarray:
    out = frame.copy()
    cv2.rectangle(out, (0, 0), (out.shape[1], 28), (255, 255, 255), -1)
    cv2.putText(
        out,
        label,
        (8, 19),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        (0, 0, 0),
        1,
        cv2.LINE_AA,
    )
    return out


def _stack_rows(candidate: np.ndarray, baseline: np.ndarray) -> np.ndarray:
    width = max(candidate.shape[1], baseline.shape[1])

    def pad(img: np.ndarray) -> np.ndarray:
        if img.shape[1] == width:
            return img
        pad_w = width - img.shape[1]
        return cv2.copyMakeBorder(img, 0, 0, 0, pad_w, cv2.BORDER_CONSTANT, value=(245, 245, 245))

    return np.vstack([pad(candidate), pad(baseline)])


def _build_sheet(
    candidate_path: Path,
    baseline_path: Path,
    *,
    out_path: Path,
    mode: str,
    samples: int,
    target_h: int,
) -> None:
    cand_cap = _open_video(candidate_path)
    base_cap = _open_video(baseline_path)
    try:
        cand_dur = _video_duration_seconds(cand_cap)
        base_dur = _video_duration_seconds(base_cap)
        pair_duration = min(cand_dur, base_dur)
        if pair_duration <= 0:
            raise RuntimeError("Could not determine video duration")

        if mode == "full":
            times = np.linspace(0.08 * pair_duration, 0.92 * pair_duration, samples)
        elif mode == "end":
            start = max(0.0, pair_duration * 0.7)
            times = np.linspace(start, 0.98 * pair_duration, samples)
        else:
            raise ValueError(f"Unsupported mode: {mode}")

        columns: list[np.ndarray] = []
        for t_s in times:
            cand = _read_frame_at(cand_cap, float(t_s))
            base = _read_frame_at(base_cap, float(t_s))
            cand = _resize_keep_aspect(cand, target_h=target_h)
            base = _resize_keep_aspect(base, target_h=target_h)
            cand = _label_frame(cand, f"candidate {t_s:5.1f}s")
            base = _label_frame(base, f"baseline  {t_s:5.1f}s")
            pair = _stack_rows(cand, base)
            columns.append(pair)

        spacer = np.full((columns[0].shape[0], 12, 3), 255, dtype=np.uint8)
        sheet = columns[0]
        for col in columns[1:]:
            sheet = np.hstack([sheet, spacer, col])

        title_h = 42
        title = np.full((title_h, sheet.shape[1], 3), 250, dtype=np.uint8)
        name = f"{candidate_path.stem} vs {baseline_path.stem} ({mode})"
        cv2.putText(title, name, (10, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2, cv2.LINE_AA)
        sheet = np.vstack([title, sheet])
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_path), sheet)
    finally:
        cand_cap.release()
        base_cap.release()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build IndustReal comparison contact sheets.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("industreal_selected/videos"),
        help="Folder containing candidates/ and baselines/",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("industreal_selected/inspection"),
        help="Output folder for generated contact sheets",
    )
    parser.add_argument("--samples", type=int, default=8, help="Frames per strip")
    parser.add_argument("--height", type=int, default=180, help="Per-frame display height")
    args = parser.parse_args()

    candidate_dir = args.root / "candidates"
    baseline_dir = args.root / "baselines"

    for pair_id in PAIR_IDS:
        candidate_name, baseline_name = PAIR_MAP[pair_id]
        candidate_path = candidate_dir / candidate_name
        baseline_path = baseline_dir / baseline_name
        _build_sheet(
            candidate_path,
            baseline_path,
            out_path=args.out / f"{pair_id}_full.png",
            mode="full",
            samples=args.samples,
            target_h=args.height,
        )
        _build_sheet(
            candidate_path,
            baseline_path,
            out_path=args.out / f"{pair_id}_end.png",
            mode="end",
            samples=args.samples,
            target_h=args.height,
        )
        print(f"Built sheets for {pair_id}")


if __name__ == "__main__":
    main()
