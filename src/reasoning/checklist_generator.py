"""
Layer 3 — Checklist Generator (GPT-4o)

Pure reasoning module — no Foundry dependency, fully unit-testable locally.
Sends SOP steps JSON to GPT-4o and returns a compliance checklist with one
entry per verifiable step, classified as:
  - presence:  Did the worker perform this action?
  - sequence:  Did it happen in the correct order relative to other steps?
  - duration:  Did it last long enough?

Input:  dict matching schemas/sop_steps.json
Output: dict matching schemas/compliance_checklist.json
Azure:  Azure OpenAI GPT-4o (via openai.AzureOpenAI)
Owner:  Person A (SOP pipeline)

Quick smoke test (requires Azure OpenAI in .env):
    python - <<'EOF'
    import json, sys
    sys.path.insert(0, ".")
    from src.ingestion.sop_extractor import extract_sop_steps
    from src.reasoning.checklist_generator import generate_checklist
    steps = extract_sop_steps("tests/fixtures/prusa_mk3s_plus_assembly.pdf",
                              "run-smoke-001", pages="1-10", granularity="section")
    checklist = generate_checklist(steps, "run-smoke-001")
    print(json.dumps(checklist, indent=2))
    EOF
"""
import json
import logging
from datetime import datetime, timezone

from openai import AzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from config import cfg

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a compliance checklist generator for manufacturing quality assurance.
Given a list of SOP steps, produce one compliance checklist item per step.

Each item must have exactly these fields:
- item_id: sequential ID formatted as "check-001", "check-002", etc.
- step_id: copied from input step_id
- sequence: copied from input sequence (integer)
- criterion: one clear, observable statement of what must be visually true for the step to be compliant
- check_type: one of ["presence", "sequence", "duration"]
  Use "presence" to verify the action was performed.
  Use "sequence" to verify it occurred after the preceding required step.
  Use "duration" when the step involves a timed wait or minimum hold time.
  If check_type_hint is provided, use it unless the description clearly implies a different type.
- expected_duration_seconds: a number if check_type is "duration", otherwise null
- sop_section: copied from input section field

Respond with exactly this JSON structure — no other keys, no explanation:
{"items": [<item>, <item>, ...]}""".strip()


_REQUIRED_ITEM_KEYS = frozenset({
    "item_id", "step_id", "sequence", "criterion",
    "check_type", "expected_duration_seconds", "sop_section",
})
_VALID_CHECK_TYPES = frozenset({"presence", "sequence", "duration"})


def get_openai_client() -> AzureOpenAI:
    """Initialise AzureOpenAI client."""
    return AzureOpenAI(
        azure_endpoint=cfg.openai_endpoint,
        api_version=cfg.openai_api_version,
        api_key=cfg.openai_api_key or None,
    )


def _validate_items(items: list, run_id: str) -> list:
    """
    Validate and coerce GPT-4o checklist items.
    Items missing required keys are dropped. Invalid check_type defaults to "presence".
    """
    validated = []
    for i, item in enumerate(items):
        missing = _REQUIRED_ITEM_KEYS - set(item.keys())
        if missing:
            logger.warning(
                f"Checklist item {i} missing keys {missing} | run_id={run_id} — skipping"
            )
            continue

        if item["check_type"] not in _VALID_CHECK_TYPES:
            logger.warning(
                f"Invalid check_type '{item['check_type']}' for {item.get('step_id')} "
                f"| run_id={run_id} — defaulting to presence"
            )
            item["check_type"] = "presence"

        dur = item.get("expected_duration_seconds")
        if dur is not None:
            try:
                item["expected_duration_seconds"] = float(dur)
            except (TypeError, ValueError):
                logger.warning(
                    f"Invalid expected_duration_seconds {dur!r} for {item.get('step_id')} "
                    f"| run_id={run_id} — setting null"
                )
                item["expected_duration_seconds"] = None

        validated.append(item)

    return validated


def _empty_checklist(sop_steps: dict, run_id: str) -> dict:
    return {
        "run_id": run_id,
        "sop_document": sop_steps.get("sop_document", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_items": 0,
        "items": [],
    }


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_checklist(sop_steps: dict, run_id: str) -> dict:
    """
    Generate a structured compliance checklist from SOP steps using GPT-4o.

    Sends each step's description and metadata to GPT-4o, which rewrites them
    as observable compliance criteria and classifies each as presence / sequence
    / duration. One checklist item is produced per SOP step.

    Args:
        sop_steps: Output of sop_extractor.extract_sop_steps() — matches
                   schemas/sop_steps.json.
        run_id:    Included in output for traceability.

    Returns:
        dict matching schemas/compliance_checklist.json
    """
    steps = sop_steps.get("steps", [])
    if not steps:
        logger.warning(f"generate_checklist called with 0 steps | run_id={run_id}")
        return _empty_checklist(sop_steps, run_id)

    logger.info(f"Generating checklist | run_id={run_id} | steps={len(steps)}")

    # Only send fields GPT-4o needs — drop visual_references and other noise
    step_summaries = [
        {
            "step_id": s["step_id"],
            "sequence": s["sequence"],
            "description": s["description"],
            "check_type_hint": s.get("check_type"),
            "expected_duration_seconds": s.get("expected_duration_seconds"),
            "section": s.get("section", ""),
        }
        for s in steps
    ]

    client = get_openai_client()
    response = client.chat.completions.create(
        model=cfg.openai_deployment,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Generate the compliance checklist for these SOP steps:\n\n"
                    + json.dumps(step_summaries, indent=2)
                ),
            },
        ],
        response_format={"type": "json_object"},
        max_tokens=4096,
        temperature=0,
    )

    raw = response.choices[0].message.content
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error(
            f"Checklist JSON parse error | run_id={run_id} | {exc} | raw={raw[:400]}"
        )
        raise

    items = _validate_items(parsed.get("items", []), run_id)

    return {
        "run_id": run_id,
        "sop_document": sop_steps.get("sop_document", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_items": len(items),
        "items": items,
    }
