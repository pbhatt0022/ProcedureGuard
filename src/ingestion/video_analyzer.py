"""
Layer 2 — Video Analyzer

GPT-4o Vision compliance field extraction from time-windowed video segments.

Duration probed via OpenCV. Segments are synthesized by build_time_windowed_segments()
(25s windows, 6s overlap), then GPT-4o Vision fills compliance fields per window.

Input:  Blob Storage SAS URL or public HTTPS URL to a manufacturing video
Output: dict matching schemas/video_observations.json
Azure:  Azure OpenAI GPT-4o (compliance field extraction)
Owner:  Priya (video pipeline)
"""
import base64
import json
import logging
import math

import cv2
from tenacity import retry, stop_after_attempt, wait_exponential

from config import cfg
from src.openai_client import get_openai_client

logger = logging.getLogger(__name__)

_PHASE2_MAX_FRAMES = 6   # frames sent to GPT-4o per segment
_PHASE2_FRAME_SIZE = 768  # resize longest edge before encoding (detail:high tiles it for finer parts)


def _encode_frame(frame) -> bytes:
    """Resize a frame to _PHASE2_FRAME_SIZE on its longest edge and JPEG-encode it."""
    h, w = frame.shape[:2]
    scale = _PHASE2_FRAME_SIZE / max(h, w)
    if scale < 1.0:
        frame = cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return buf.tobytes()


def extract_keyframes_batch(video_url: str, targets: list[dict]) -> dict[str, bytes]:
    """
    Extract keyframes for multiple steps in a single open-capture pass.
    targets is a list of {"step_id": str, "timestamp_s": float}.
    Returns a dict of {step_id: jpeg_bytes}.
    """
    if not targets:
        return {}

    # Sort targets by timestamp ascending for reliable sequential seeking in FFmpeg/OpenCV
    valid_targets = [t for t in targets if t.get("timestamp_s") is not None and t["timestamp_s"] >= 0]
    sorted_targets = sorted(valid_targets, key=lambda x: x["timestamp_s"])
    if not sorted_targets:
        return {}

    cap = cv2.VideoCapture(video_url)
    if not cap.isOpened():
        logger.warning(f"Batch extraction: OpenCV could not open video URL: {video_url[:60]}")
        return {}

    results: dict[str, bytes] = {}
    for target in sorted_targets:
        step_id = target["step_id"]
        ts_s = target["timestamp_s"]
        ts_ms = ts_s * 1000.0

        cap.set(cv2.CAP_PROP_POS_MSEC, ts_ms)
        ret, frame = cap.read()
        if not ret or frame is None:
            logger.warning(f"Batch extraction: Failed to read frame at {ts_s}s ({ts_ms}ms) for {step_id}")
            continue

        results[step_id] = _encode_frame(frame)

    cap.release()
    logger.info(f"Batch keyframe extraction complete | extracted={len(results)}/{len(targets)}")
    return results



# ── Phase 2: GPT-4o compliance field extraction ──────────────────────────────

PHASE2_SYSTEM_PROMPT = """You are a manufacturing compliance field extractor analyzing
frames from one short video window of a manual assembly task.

Return a JSON object with exactly these fields:
{
  "ppe_status": "<compliant|non-compliant|not-visible>",
  "tool_in_use": "<tool name or null>",
  "component_contact": "<specific component description or null>",
  "visible_safety_concern": <true|false>,
  "action_observed": "<one or two sentences describing the assembly action in concrete physical detail>"
}

For action_observed and component_contact, be CONCRETE and SPECIFIC about what is actually
visible — a downstream step matches these descriptions against assembly instructions, so
generic phrases like "assembling components by hand" are useless. In particular:
- Name parts by visible attributes: colour, rough shape, kind (e.g. "a black pin",
  "a white perforated beam", "a pink connector", "a wheel", "a screw", "an acorn nut").
- Describe how parts are JOINED: inserting a pin through aligned holes, sliding a beam onto
  a peg, pressing two brackets together, threading a nut onto a screw, mounting a wheel onto
  an axle, aligning bores before insertion.
- Note counts and positions when visible ("two beams", "the leftmost hole", "the rear axle").
- If a fastener (pin / screw / nut) is being placed, say so explicitly and what it connects.

Definitions:
- ppe_status: "compliant" = required safety equipment visible and worn correctly;
  "non-compliant" = missing or incorrectly worn PPE; "not-visible" = cannot assess.
- tool_in_use: name the specific tool (e.g. "Allen key", "screwdriver") or null if hands only.
- visible_safety_concern: true only if a clear hazard is observable.

Describe only what is genuinely visible — do not invent detail you cannot see.
Respond with the JSON object only. No explanation.""".strip()


# Appended to PHASE2_SYSTEM_PROMPT only when run_video_phase2 is given the checklist
# (A1: checklist-aware Phase 2). Grounds the vision pass in the actual SOP steps so the
# downstream reasoner gets a direct item→window signal instead of guessing via vocabulary.
PHASE2_CHECKLIST_INSTRUCTION = """
ADDITIONALLY, you are given a numbered CHECKLIST of specific assembly steps. For THIS window's
frames, decide which checklist steps are positively shown — the named component(s) being placed,
joined, or fastened as described. Add one extra field to your JSON:
  "observed_items": [ {"item_id": "<id>", "confidence": <0.0-1.0>} ]
Include an entry ONLY for steps you can actually see in these frames (confidence >= 0.5); omit
the rest. Match by physical appearance and action, not exact wording (e.g. a white perforated
beam pressed onto pegs can satisfy "mount the short braces onto the base frame"). If no checklist
step is visible in this window, return "observed_items": [].""".strip()


def _format_checklist_for_vision(checklist_items: list[dict]) -> str:
    """Render checklist items as a compact prompt block for the vision pass."""
    lines = ["CHECKLIST — which of these steps are visible in THIS window:"]
    for it in checklist_items:
        keys = it.get("key_objects") or []
        key_str = f"  (key objects: {', '.join(keys)})" if keys else ""
        action = it.get("observable_action") or it.get("criterion") or ""
        lines.append(f"- {it.get('item_id')}: {action}{key_str}")
    return "\n".join(lines)


def probe_video_duration(video_url: str) -> float:
    """
    Best-effort video duration in seconds via OpenCV.

    Drives time-windowed segmentation (build_time_windowed_segments).
    Returns 0.0 if the video can't be opened.
    """
    cap = cv2.VideoCapture(video_url)
    if not cap.isOpened():
        logger.warning("probe_video_duration: OpenCV could not open video URL")
        return 0.0
    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
    cap.release()
    return round(frames / fps, 1) if fps > 0 else 0.0


def build_time_windowed_segments(
    total_duration_s: float,
    *,
    window_seconds: float = 25.0,
    overlap_seconds: float = 6.0,
    max_windows: int = 20,
) -> list[dict]:
    """
    Synthesize overlapping fixed-duration segment stubs spanning the whole video.

    The prebuilt-video base analyzer segments by shot/scene cut. Continuous
    single-take assembly footage has no cuts, so it collapses to one segment
    covering the entire clip — which destroys evidence localization and forces
    mass abstention downstream (every criterion is judged against the same
    4-minute blob). This replaces that single segment with overlapping time
    windows, each carrying real start/end timestamps. The overlap means an
    action straddling what would otherwise be a hard cut still falls fully
    inside at least one window. run_video_phase2() then fills the compliance
    fields per window via GPT-4o Vision.

    Args:
        total_duration_s: Total video duration in seconds.
        window_seconds:   Target window length. ~25s clears the ~15s minimum
                          for reliable field extraction (see KNOWN_ISSUES) while
                          keeping evidence localized to a tight slice.
        overlap_seconds:  Overlap between consecutive windows. Clamped to at
                          most half of window_seconds.
        max_windows:      Ceiling on window count — caps GPT-4o cost on long clips.
                          When the target window/overlap would exceed this, both
                          are stretched proportionally so the cap always holds.

    Returns:
        List of segment dicts matching schemas/video_observations.json, with
        compliance fields nulled out for run_video_phase2() to populate.
    """
    if total_duration_s <= 0:
        return []

    overlap_seconds = max(0.0, min(overlap_seconds, window_seconds / 2))
    stride = window_seconds - overlap_seconds

    if total_duration_s <= window_seconds:
        n = 1
    else:
        n = 1 + math.ceil((total_duration_s - window_seconds) / stride)

    if n > max_windows:
        # Too many windows at the target size/overlap — stretch both
        # proportionally so the cap holds while keeping the same overlap ratio.
        n = max_windows
        stride = total_duration_s / n
        window_seconds = stride + overlap_seconds

    segments = []
    for i in range(n):
        start = i * stride
        segments.append({
            "segment_id": f"seg-{str(i + 1).zfill(3)}",
            "start_time_seconds": round(start, 1),
            "end_time_seconds": round(min(start + window_seconds, total_duration_s), 1),
            "description": "",
            "ppe_status": None,
            "tool_in_use": None,
            "component_contact": None,
            "visible_safety_concern": False,
            "action_observed": None,
        })
    return segments


@retry(stop=stop_after_attempt(6), wait=wait_exponential(multiplier=2, min=5, max=90))
def extract_compliance_fields(
    description: str,
    segment_id: str,
    run_id: str,
    *,
    keyframe_images: list[str] | None = None,
    checklist_items: list[dict] | None = None,
) -> dict:
    """
    Phase 2: extract structured compliance fields using GPT-4o.

    Sends an optional text hint plus a list of keyframe images (base64 data
    URIs) to GPT-4o. Vision mode is used whenever keyframe_images is non-empty;
    in practice run_video_phase2() always supplies frames, so text-only mode is
    a defensive fallback for when OpenCV cannot open the clip.

    Args:
        description:     Optional text hint for this segment (usually empty —
                         the frames are the primary signal).
        segment_id:      Segment identifier for logging (e.g. "seg-001").
        run_id:          Pipeline run identifier for logging.
        keyframe_images: List of base64 JPEG data URIs sampled by
                         run_video_phase2(). When provided, GPT-4o sees the
                         actual frames alongside the text description.

    Returns:
        dict with keys: ppe_status, tool_in_use, component_contact,
                        visible_safety_concern, action_observed
    """
    _null_result: dict = {
        "ppe_status": None,
        "tool_in_use": None,
        "component_contact": None,
        "visible_safety_concern": False,
        "action_observed": None,
    }

    has_images = bool(keyframe_images)
    if not description.strip() and not has_images:
        logger.warning(f"Phase 2: no description or images for {segment_id} | run_id={run_id}")
        return _null_result

    # Build user message — text-only or multimodal (vision)
    if has_images:
        user_content: list = [
            {
                "type": "text",
                "text": (
                    f"Segment: {segment_id}\n\n"
                    f"The following {len(keyframe_images)} frames are evenly sampled "
                    f"from this video segment. Analyze them to extract compliance fields."
                ),
            },
        ]
        for img_data_uri in keyframe_images:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": img_data_uri, "detail": "high"},
            })
        logger.debug(f"Phase 2 vision mode | {segment_id} | frames={len(keyframe_images)} | run_id={run_id}")
    else:
        user_content = (
            f"Segment: {segment_id}\n\n"
            f"Text hint (no frames available):\n{description}"
        )
        logger.debug(f"Phase 2 text mode | {segment_id} | run_id={run_id}")

    # A1: checklist-aware mode — append the SOP steps to the prompt and ask the
    # vision pass which ones are visible here. Only active when checklist_items given,
    # so default (text-asserting) callers see the unchanged 5-field behaviour.
    system_prompt = PHASE2_SYSTEM_PROMPT
    if checklist_items:
        system_prompt = f"{PHASE2_SYSTEM_PROMPT}\n\n{PHASE2_CHECKLIST_INSTRUCTION}"
        checklist_text = _format_checklist_for_vision(checklist_items)
        if isinstance(user_content, list):
            user_content.append({"type": "text", "text": checklist_text})
        else:
            user_content = f"{user_content}\n\n{checklist_text}"

    client = get_openai_client()
    response = client.chat.completions.create(
        model=cfg.openai_deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
        max_tokens=500 if checklist_items else 300,
        temperature=0,
    )

    raw = response.choices[0].message.content
    try:
        fields = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error(f"Phase 2 JSON parse error | {segment_id} | {exc} | raw={raw[:200]}")
        return _null_result

    result = {
        "ppe_status": fields.get("ppe_status"),
        "tool_in_use": fields.get("tool_in_use"),
        "component_contact": fields.get("component_contact"),
        "visible_safety_concern": bool(fields.get("visible_safety_concern", False)),
        "action_observed": fields.get("action_observed"),
    }
    # Only surface observed_items in checklist-aware mode — keeps the default 5-key contract.
    if checklist_items:
        raw_items = fields.get("observed_items") or []
        observed = []
        for entry in raw_items:
            if isinstance(entry, dict) and entry.get("item_id"):
                try:
                    conf = float(entry.get("confidence", 0.0))
                except (TypeError, ValueError):
                    conf = 0.0
                if conf >= 0.5:
                    observed.append({"item_id": entry["item_id"], "confidence": round(conf, 2)})
        result["observed_items"] = observed
    return result


def run_video_phase2(
    observations: dict,
    run_id: str,
    *,
    video_url: str | None = None,
    checklist: dict | None = None,
) -> dict:
    """
    Fill compliance fields for all segments using GPT-4o (Phase 2).

    Iterates segments produced by build_time_windowed_segments(), extracts
    keyframes from the video using OpenCV (Vision mode), and calls GPT-4o for
    each segment. Falls back to text-only mode if keyframe extraction fails.

    Args:
        observations: Observations dict with segment stubs — modified in place.
        run_id:       Pipeline run identifier.
        video_url:    HTTPS or Blob SAS URL to the video. When provided,
                      OpenCV extracts frames for Vision mode. If omitted,
                      falls back to text-only mode (less accurate).

    Returns:
        The same observations dict with all 5 compliance fields populated.
    """
    segments = observations.get("segments", [])
    # A1: checklist-aware grounding — pass a compact item list (id + action + key_objects)
    # to each window's vision call so it reports which SOP steps it actually sees.
    checklist_items = None
    if checklist:
        checklist_items = [
            {
                "item_id": it.get("item_id"),
                "observable_action": it.get("observable_action"),
                "criterion": it.get("criterion"),
                "key_objects": it.get("key_objects"),
            }
            for it in checklist.get("items", [])
            if it.get("verifiability") != "fine_detail" and it.get("observable_action")
        ] or None
    logger.info(
        f"Phase 2 start | run_id={run_id} | segments={len(segments)} | "
        f"checklist_aware={bool(checklist_items)}"
    )

    # Pre-open the video capture once and reuse across segments to avoid
    # reconnecting for every segment on multi-segment videos.
    cap = None
    if video_url:
        cap = cv2.VideoCapture(video_url)
        if not cap.isOpened():
            logger.warning(f"Phase 2: OpenCV could not open video — falling back to text mode | run_id={run_id}")
            cap = None

    for segment in segments:
        seg_id = segment["segment_id"]
        description = segment.get("description", "")
        start_ms = (segment.get("start_time_seconds") or 0) * 1000
        end_ms = (segment.get("end_time_seconds") or 0) * 1000

        keyframe_images: list[str] = []
        if cap is not None and end_ms > start_ms:
            duration_ms = end_ms - start_ms
            num_frames = min(_PHASE2_MAX_FRAMES, max(4, round(duration_ms / 5_000)))
            step = duration_ms / max(num_frames - 1, 1) if num_frames > 1 else duration_ms / 2
            timestamps = [start_ms + i * step for i in range(num_frames)] if num_frames > 1 else [start_ms + duration_ms / 2]

            for ts_ms in timestamps:
                cap.set(cv2.CAP_PROP_POS_MSEC, ts_ms)
                ret, frame = cap.read()
                if not ret or frame is None:
                    continue
                b64 = base64.b64encode(_encode_frame(frame)).decode("ascii")
                keyframe_images.append(f"data:image/jpeg;base64,{b64}")

            logger.debug(f"Phase 2 extracted {len(keyframe_images)} frames | {seg_id}")

        fields = extract_compliance_fields(
            description, seg_id, run_id,
            keyframe_images=keyframe_images or None,
            checklist_items=checklist_items,
        )
        segment.update(fields)

        mode = "vision" if keyframe_images else "text"
        action_preview = (fields.get("action_observed") or "")[:60]
        logger.info(f"Phase 2 {mode} done | {seg_id} | action={action_preview!r}")

    if cap is not None:
        cap.release()

    logger.info(f"Phase 2 complete | run_id={run_id}")
    return observations
