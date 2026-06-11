"""
Layer 2 — Video Analyzer

Two-phase manufacturing video analysis pipeline:

Phase 1:  Azure AI Content Understanding (prebuilt-video) — segment detection,
          timestamps, and natural language description of each scene.
Phase 2:  GPT-4o compliance field extraction — ppe_status, tool_in_use,
          component_contact, visible_safety_concern, action_observed.

Input:  Blob Storage SAS URL or public HTTPS URL to a manufacturing video
Output: dict matching schemas/video_observations.json
Azure:  Azure AI Content Understanding (API 2025-11-01 GA)
        Azure OpenAI GPT-4o (Phase 2 compliance field extraction)
Owner:  Priya (video pipeline)

Key constraints (see docs/KNOWN_ISSUES.md):
  - Frame sampling: ~1 fps — fast transitions may be missed
  - Frame resolution: 512x512 px — fine motor detail unreliable
  - Use Blob URL reference, NOT binary upload (4GB/2hr vs 200MB limit)
  - Base analyzer: prebuilt-video (NOT prebuilt-videoSearch)
  - Minimum segment length ~15s for reliable field extraction
"""
import json
import logging
from datetime import datetime, timezone

from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.ai.contentunderstanding.models import (
    AnalysisContentKind,
    AnalysisInput,
    ContentAnalyzer,
    ContentFieldDefinition,
    ContentFieldSchema,
    ContentFieldType,
    GenerationMethod,
)
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceExistsError
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from config import cfg

logger = logging.getLogger(__name__)


def _get_field(fields: dict, name: str):
    """Extract a string value from a Content Understanding fields dict. Returns None if absent."""
    f = fields.get(name)
    return f.value if f else None


# ── Compliance field schema ──────────────────────────────────────────────────
# Extends prebuilt-video with compliance-specific fields.
# See docs/ARCHITECTURE.md for design rationale.
# NOTE: If you update these fields, re-run create_or_update_analyzer().
COMPLIANCE_FIELD_SCHEMA = ContentFieldSchema(
    fields={
        "ppe_status": ContentFieldDefinition(
            type=ContentFieldType.STRING,
            method=GenerationMethod.CLASSIFY,
            description="PPE compliance status of the worker in this segment",
            enum=["compliant", "non-compliant", "not-visible"],
        ),
        "tool_in_use": ContentFieldDefinition(
            type=ContentFieldType.STRING,
            method=GenerationMethod.GENERATE,
            description="Identify the tool currently being used by the worker. Return null if no tool is visible.",
        ),
        "component_contact": ContentFieldDefinition(
            type=ContentFieldType.STRING,
            method=GenerationMethod.GENERATE,
            description="Describe which component or part the worker is contacting or assembling. Return null if unclear.",
        ),
        "visible_safety_concern": ContentFieldDefinition(
            type=ContentFieldType.STRING,
            method=GenerationMethod.CLASSIFY,
            description="Whether a visible safety concern is present in this segment",
            enum=["true", "false"],
        ),
        "action_observed": ContentFieldDefinition(
            type=ContentFieldType.STRING,
            method=GenerationMethod.GENERATE,
            description="Natural language description of the primary action performed by the worker in this segment.",
        ),
    }
)


# ── Phase 2: GPT-4o compliance field extraction ──────────────────────────────

PHASE2_SYSTEM_PROMPT = """You are a manufacturing compliance field extractor.
Analyze the provided video segment and extract structured compliance observations.

Return a JSON object with exactly these fields:
{
  "ppe_status": "<compliant|non-compliant|not-visible>",
  "tool_in_use": "<tool name or null>",
  "component_contact": "<component description or null>",
  "visible_safety_concern": <true|false>,
  "action_observed": "<one sentence describing the worker's primary action>"
}

Definitions:
- ppe_status: "compliant" = required safety equipment visible and worn correctly;
  "non-compliant" = missing or incorrectly worn PPE; "not-visible" = cannot assess.
- tool_in_use: name the specific tool (e.g. "Allen key", "pliers") or null if none used.
- component_contact: identify the specific part being handled
  (e.g. "M3 screw on X-axis motor bracket") or null if unclear.
- visible_safety_concern: true only if a clear hazard is observable
  (e.g. exposed wiring, dropped component, improper tool grip, hand near sharp edge).
- action_observed: one concise sentence describing the primary manufacturing action.

Respond with the JSON object only. No explanation.""".strip()


def get_openai_client() -> AzureOpenAI:
    """Initialise AzureOpenAI client for Phase 2 compliance field extraction."""
    return AzureOpenAI(
        azure_endpoint=cfg.openai_endpoint,
        api_version=cfg.openai_api_version,
        api_key=cfg.openai_api_key or None,
    )


# ── Phase 1: Content Understanding client ────────────────────────────────────

def get_client() -> ContentUnderstandingClient:
    """
    Initialise Content Understanding client.

    Credential priority:
      1. API key (AZURE_CONTENT_UNDERSTANDING_KEY in .env) — works with the
         regional endpoint (https://eastus.api.cognitive.microsoft.com/).
         Use this for local dev when the Foundry hub lacks a custom subdomain.
      2. DefaultAzureCredential (az login) — requires a custom subdomain
         endpoint (https://<name>.cognitiveservices.azure.com/ or
         https://<name>.services.ai.azure.com/).
    """
    if cfg.content_understanding_key:
        logger.debug("Content Understanding: using AzureKeyCredential")
        return ContentUnderstandingClient(
            endpoint=cfg.content_understanding_endpoint,
            credential=AzureKeyCredential(cfg.content_understanding_key),
        )
    logger.debug("Content Understanding: using DefaultAzureCredential")
    return ContentUnderstandingClient(
        endpoint=cfg.content_understanding_endpoint,
        credential=DefaultAzureCredential(),
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def create_or_update_analyzer() -> None:
    """
    Register the custom compliance video analyzer in Content Understanding.
    Run once during setup, or whenever the field schema changes.
    Safe to call on every deploy — creates or replaces.

    NOTE: API version 2025-11-01 (GA). Never use preview versions.
    NOTE: If you get a model deployment error, you may need to deploy
          gpt-4.1-mini and text-embedding-3-large in Azure AI Foundry first.
          See docs/KNOWN_ISSUES.md.
    """
    client = get_client()
    analyzer_id = cfg.content_understanding_analyzer_id

    # NOTE: Do not specify `models` for standalone AIServices resources —
    # the service uses its own managed GPT deployment.
    # Only set models={"completion": "<deployment-name>"} when using a
    # full AI Foundry project with explicit model deployments.
    analyzer = ContentAnalyzer(
        base_analyzer_id="prebuilt-video",
        field_schema=COMPLIANCE_FIELD_SCHEMA,
    )

    logger.info(f"Creating/updating analyzer | id={analyzer_id}")
    try:
        poller = client.begin_create_analyzer(analyzer_id, analyzer)
        poller.result()
    except ResourceExistsError:
        # Analyzer already exists — delete and recreate to ensure schema is current.
        # Content Understanding API does not support in-place schema updates once
        # the analyzer is in 'succeeded' state; DELETE + PUT is the only update path.
        logger.info(f"Analyzer already exists — deleting to force schema update | id={analyzer_id}")
        client.delete_analyzer(analyzer_id)
        poller = client.begin_create_analyzer(analyzer_id, analyzer)
        poller.result()
    logger.info(f"Analyzer ready | id={analyzer_id}")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def analyze_video(video_url: str, run_id: str) -> object:
    """
    Submit a manufacturing video for segment detection (Phase 1).

    Uses prebuilt-video, which reliably returns results on a standalone
    AIServices resource. Compliance fields are populated separately by
    run_video_phase2() via a direct GPT-4o call.

    Args:
        video_url: HTTPS URL or Blob Storage SAS URL to the video.
        run_id:    Pipeline run identifier.

    Returns:
        Raw AnalysisResult object from the SDK. Pass to parse_observations().
    """
    client = get_client()
    logger.info(f"Submitting video for analysis | run_id={run_id} | url={video_url[:60]}...")

    # NOTE: Using prebuilt-video (base) instead of the custom compliance analyzer.
    # Custom GENERATE/CLASSIFY fields silently return 0 segments on standalone
    # AIServices resources without a linked Azure OpenAI deployment.
    # Compliance fields are extracted by run_video_phase2() instead.
    # See docs/KNOWN_ISSUES.md.
    poller = client.begin_analyze(
        analyzer_id="prebuilt-video",
        inputs=[AnalysisInput(url=video_url)],
    )

    logger.info(f"Polling for result | run_id={run_id}")
    result = poller.result()
    logger.info(f"Analysis complete | run_id={run_id} | segments={len(result.contents)}")
    return result


def parse_observations(raw_result: object, run_id: str, video_url: str) -> dict:
    """
    Convert a Content Understanding AnalysisResult into Observations JSON.

    Compliance fields (ppe_status, tool_in_use, etc.) will be null after this
    call. Call run_video_phase2() on the returned dict to fill them via GPT-4o.

    Args:
        raw_result:  AnalysisResult from analyze_video().
        run_id:      Pipeline run identifier.
        video_url:   Source video URL (recorded for traceability).

    Returns:
        dict matching schemas/video_observations.json (compliance fields null)
    """
    segments = []

    for i, content in enumerate(raw_result.contents):
        if content.kind != AnalysisContentKind.AUDIO_VISUAL:
            logger.warning(f"Skipping non-audio-visual content at index {i}")
            continue

        seg_id = f"seg-{str(i + 1).zfill(3)}"
        start_s = (content.start_time_ms / 1000.0) if content.start_time_ms is not None else 0.0
        end_s = (content.end_time_ms / 1000.0) if content.end_time_ms is not None else 0.0

        fields = content.fields or {}
        segment = {
            "segment_id": seg_id,
            "start_time_seconds": start_s,
            "end_time_seconds": end_s,
            # Content Understanding natural language description of the segment.
            # Used as Phase 2 input and Agent 2 reasoning context.
            "description": getattr(content, "markdown", None) or "",
            "ppe_status": _get_field(fields, "ppe_status"),
            "tool_in_use": _get_field(fields, "tool_in_use"),
            "component_contact": _get_field(fields, "component_contact"),
            # visible_safety_concern comes back as "true"/"false" string — convert to bool
            "visible_safety_concern": _get_field(fields, "visible_safety_concern") == "true",
            "action_observed": _get_field(fields, "action_observed"),
        }
        segments.append(segment)

    return {
        "run_id": run_id,
        "video_file": video_url,
        "analyzer_id": cfg.content_understanding_analyzer_id,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "total_segments": len(segments),
        "segments": segments,
    }


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def extract_compliance_fields(
    description: str,
    segment_id: str,
    run_id: str,
    *,
    keyframe_image_url: str | None = None,
) -> dict:
    """
    Phase 2: extract structured compliance fields using GPT-4o.

    Sends the Content Understanding segment description (and optionally a
    keyframe image URL) to GPT-4o and returns the 5 compliance fields.

    When keyframe_image_url is provided (Vision mode), GPT-4o sees both the
    text description and the actual frame — more accurate than text alone.
    Generate the URL with blob_client.get_keyframe_sas_url(run_id, segment_id).

    Args:
        description:        Markdown text from Content Understanding for this segment.
        segment_id:         Segment identifier for logging (e.g. "seg-001").
        run_id:             Pipeline run identifier for logging.
        keyframe_image_url: Optional Blob SAS URL to the keyframe JPG.
                            When provided, uses GPT-4o Vision mode.

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

    if not description.strip() and not keyframe_image_url:
        logger.warning(f"Phase 2: no description or image for {segment_id} | run_id={run_id}")
        return _null_result

    # Build user message — text-only or multimodal (vision)
    if keyframe_image_url:
        user_content = [
            {
                "type": "text",
                "text": (
                    f"Segment: {segment_id}\n\n"
                    f"Content Understanding description:\n{description}"
                ),
            },
            {
                "type": "image_url",
                "image_url": {"url": keyframe_image_url, "detail": "high"},
            },
        ]
        logger.debug(f"Phase 2 vision mode | {segment_id} | run_id={run_id}")
    else:
        user_content = (
            f"Segment: {segment_id}\n\n"
            f"Content Understanding description:\n{description}"
        )
        logger.debug(f"Phase 2 text mode | {segment_id} | run_id={run_id}")

    client = get_openai_client()
    response = client.chat.completions.create(
        model=cfg.openai_deployment,
        messages=[
            {"role": "system", "content": PHASE2_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
        max_tokens=300,
        temperature=0,
    )

    raw = response.choices[0].message.content
    try:
        fields = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error(f"Phase 2 JSON parse error | {segment_id} | {exc} | raw={raw[:200]}")
        return _null_result

    return {
        "ppe_status": fields.get("ppe_status"),
        "tool_in_use": fields.get("tool_in_use"),
        "component_contact": fields.get("component_contact"),
        "visible_safety_concern": bool(fields.get("visible_safety_concern", False)),
        "action_observed": fields.get("action_observed"),
    }


def run_video_phase2(
    observations: dict,
    run_id: str,
    *,
    keyframe_urls: dict | None = None,
) -> dict:
    """
    Fill compliance fields for all segments using GPT-4o (Phase 2).

    Iterates the segments in an observations dict produced by parse_observations(),
    calls extract_compliance_fields() for each, and updates the dict in place.

    Args:
        observations:   Output of parse_observations() — modified in place.
        run_id:         Pipeline run identifier.
        keyframe_urls:  Optional {segment_id: blob_sas_url} for Vision mode.
                        When provided, each segment's keyframe image is sent
                        alongside the text description (higher accuracy).
                        Generate with blob_client.get_keyframe_sas_url().
                        If omitted, uses text-only mode (Content Understanding markdown).

    Returns:
        The same observations dict with all 5 compliance fields populated.
    """
    segments = observations.get("segments", [])
    logger.info(f"Phase 2 start | run_id={run_id} | segments={len(segments)}")

    for segment in segments:
        seg_id = segment["segment_id"]
        description = segment.get("description", "")
        image_url = (keyframe_urls or {}).get(seg_id)

        fields = extract_compliance_fields(
            description, seg_id, run_id, keyframe_image_url=image_url
        )
        segment.update(fields)

        mode = "vision" if image_url else "text"
        action_preview = (fields.get("action_observed") or "")[:60]
        logger.info(f"Phase 2 {mode} done | {seg_id} | action={action_preview!r}")

    logger.info(f"Phase 2 complete | run_id={run_id}")
    return observations
