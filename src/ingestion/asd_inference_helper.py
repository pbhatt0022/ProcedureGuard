"""
Inference helper for Assembly State Detection (ASD).
Runs in the isolated virtual environment (venv_asd) and outputs frame-level detections as JSON.
"""
import argparse
import json
import sys
from pathlib import Path
import cv2

try:
    from ultralytics import YOLO
except ImportError:
    print(json.dumps({"error": "ultralytics not installed in this environment."}))
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, help="Path to video file")
    parser.add_argument("--weights", required=True, help="Path to YOLOv8 weights (.pt)")
    parser.add_argument("--fps", type=float, default=1.0, help="Sampling frequency (frames per second)")
    args = parser.parse_args()

    video_path = Path(args.video)
    weights_path = Path(args.weights)

    if not video_path.exists():
        print(json.dumps({"error": f"Video not found: {video_path}"}))
        sys.exit(1)
    if not weights_path.exists():
        print(json.dumps({"error": f"Weights not found: {weights_path}"}))
        sys.exit(1)

    # Load model
    model = YOLO(str(weights_path))

    # Open video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(json.dumps({"error": f"Could not open video: {video_path}"}))
        sys.exit(1)

    video_fps = cap.get(cv2.CAP_PROP_FPS) or 10.0
    frame_step = max(1, round(video_fps / args.fps))

    detections = []
    frame_idx = 0

    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret or frame is None:
            break

        timestamp_s = frame_idx / video_fps
        results = model.predict(source=frame, device="cpu", conf=0.05, verbose=False)
        boxes = results[0].boxes

        frame_dets = [
            {
                "state_code": model.names[int(box.cls[0].item())],
                "confidence": round(float(box.conf[0].item()), 4),
            }
            for box in boxes
        ]

        detections.append({
            "timestamp_seconds": round(timestamp_s, 2),
            "detections": frame_dets
        })

        frame_idx += frame_step

    cap.release()

    # Output JSON results to stdout
    print(json.dumps({
        "video_file": video_path.name,
        "detections": detections
    }, indent=2))

if __name__ == "__main__":
    main()
