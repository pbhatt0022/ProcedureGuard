"""
Layer 2 — SOP Extractor

Sends an SOP PDF to Azure AI Document Intelligence (Layout Model v4.0)
and returns a structured Steps JSON representing each procedural step
with sequence order and timing constraints.

Input:  Blob Storage URL pointing to an SOP PDF (or local file path)
Output: dict matching schemas/sop_steps.json
Azure:  Azure AI Document Intelligence (API version 2024-11-30 GA, SDK 1.0.x)
Owner:  Person A (SOP pipeline)

Key constraints (see docs/KNOWN_ISSUES.md):
  - Same resource + key as Content Understanding (regional endpoint, API key auth)
  - Large manuals (200+ pages): pass `pages="1-20"` to limit scope during testing
  - Step parsing is heuristic (v1) — Agent 1 refines the raw steps into a
    compliance checklist downstream, so over-extraction is acceptable here
"""
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from tenacity import retry, stop_after_attempt, wait_exponential

from config import cfg

logger = logging.getLogger(__name__)

LAYOUT_MODEL_ID = "prebuilt-layout"

# Paragraph roles that are page furniture, not procedural content.
_SKIP_ROLES = {"pageHeader", "pageFooter", "pageNumber", "footnote", "formulaBlock"}

# Roles that mark the start of a new document section.
_SECTION_ROLES = {"title", "sectionHeading"}

# Paragraphs shorter than this are part labels / captions, not step instructions.
_MIN_STEP_CHARS = 20

# Sections whose body content is navigation, not procedure (e.g. the Prusa
# manual's table of contents spans 10+ pages of step titles).
_NON_PROCEDURE_SECTION_RE = re.compile(r"\b(table of contents|contents|index)\b", re.IGNORECASE)

# A step is a timed ("duration") check when it contains a waiting/curing cue
# AND a time quantity. A time quantity alone (e.g. "tighten for 2 seconds at
# the end") is treated as presence — timing is incidental, not the check.
_DURATION_CUE_RE = re.compile(
    r"\b(wait|cure|curing|allow|let\s+it|leave|hold|rest|dry|cool|pause|settle)\b",
    re.IGNORECASE,
)
_TIME_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?)\b",
    re.IGNORECASE,
)
_UNIT_TO_SECONDS = {"sec": 1, "min": 60, "hou": 3600, "hr": 3600}


def get_document_intelligence_client() -> DocumentIntelligenceClient:
    """
    Initialise Document Intelligence client.

    Credential priority:
      1. API key (AZURE_DOCUMENT_INTELLIGENCE_KEY in .env) — required when the
         resource has no custom subdomain (regional endpoint only).
      2. DefaultAzureCredential (az login) — requires a custom subdomain endpoint.

    NOTE: procedureguard-ai uses the regional endpoint with API key auth.
    Same resource and key as Content Understanding. See docs/KNOWN_ISSUES.md.
    """
    if cfg.doc_intelligence_key:
        return DocumentIntelligenceClient(
            endpoint=cfg.doc_intelligence_endpoint,
            credential=AzureKeyCredential(cfg.doc_intelligence_key),
        )
    return DocumentIntelligenceClient(
        endpoint=cfg.doc_intelligence_endpoint,
        credential=DefaultAzureCredential(),
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def analyze_sop_layout(source: str, pages: str | None = None) -> object:
    """
    Run the Layout model over an SOP PDF and return the raw AnalyzeResult.

    Args:
        source: HTTPS/SAS URL to the PDF in Blob Storage, or a local file path.
        pages:  Optional page range (e.g. "1-20") — strongly recommended for
                large manuals during testing. None analyzes the whole document.

    Returns:
        Raw AnalyzeResult from the SDK. Pass to parse_sop_steps().
    """
    client = get_document_intelligence_client()

    if source.lower().startswith(("http://", "https://")):
        # NOTE: URL reference (not binary upload) so file size is not limited.
        body = AnalyzeDocumentRequest(url_source=source)
    else:
        body = AnalyzeDocumentRequest(bytes_source=Path(source).read_bytes())

    logger.info(f"Submitting SOP to Layout model | pages={pages or 'all'}")
    poller = client.begin_analyze_document(LAYOUT_MODEL_ID, body, pages=pages)
    result = poller.result()
    logger.info(
        f"Layout analysis complete | pages={len(result.pages or [])} "
        f"| paragraphs={len(result.paragraphs or [])} "
        f"| figures={len(result.figures or [])}"
    )
    return result


def _classify_check(text: str) -> tuple[str, int | None]:
    """
    Determine check_type and expected_duration_seconds for a step description.

    Returns ("duration", seconds) when the step is a timed wait/cure
    instruction, otherwise ("presence", None).
    """
    time_match = _TIME_RE.search(text)
    if time_match and _DURATION_CUE_RE.search(text):
        value = float(time_match.group(1))
        unit_key = time_match.group(2).lower()[:3]
        seconds = int(value * _UNIT_TO_SECONDS.get(unit_key, 1))
        return "duration", seconds
    return "presence", None


def _figures_by_page(raw_result: object) -> dict[int, list[str]]:
    """Map page number -> list of figure reference ids (e.g. 'figure-2.1')."""
    by_page: dict[int, list[str]] = {}
    for figure in raw_result.figures or []:
        if not figure.bounding_regions:
            continue
        page = figure.bounding_regions[0].page_number
        by_page.setdefault(page, []).append(f"figure-{figure.id}")
    return by_page


def _paragraph_page(paragraph: object) -> int | None:
    if paragraph.bounding_regions:
        return paragraph.bounding_regions[0].page_number
    return None


def _document_name(source: str) -> str:
    """Filename from a URL (SAS query stripped) or local path."""
    if source.lower().startswith(("http://", "https://")):
        return Path(urlparse(source).path).name
    return Path(source).name


def _make_step(sequence: int, description: str, section: str | None,
               visual_references: list[str]) -> dict:
    check_type, duration = _classify_check(description)
    return {
        "step_id": f"step-{str(sequence).zfill(3)}",
        "sequence": sequence,
        "description": description,
        "check_type": check_type,
        "expected_duration_seconds": duration,
        "section": section,
        "visual_references": visual_references,
    }


def parse_sop_steps(raw_result: object, run_id: str, source: str,
                    granularity: str = "paragraph") -> dict:
    """
    Convert a raw Layout AnalyzeResult into the standardised Steps JSON
    (schemas/sop_steps.json).

    Heuristic v1:
      - title/sectionHeading paragraphs set the current `section`
      - page furniture roles (header/footer/page number/footnote) are skipped
      - body content under navigation sections (table of contents, index)
        is skipped — TOC entries are step *titles*, not instructions
      - remaining body paragraphs of >= _MIN_STEP_CHARS are kept, in
        reading order
      - figures on the same page as a step become its visual_references
      - wait/cure instructions with a time quantity become "duration" checks

    Granularity:
      - "paragraph": each kept paragraph is one step. Right for SOPs where
        one paragraph = one instruction (the schema example).
      - "section": consecutive paragraphs under one section heading merge
        into a single step. Right for instruction-manual style documents
        like the Prusa manual, where the procedural unit is the
        "STEP N <title>" heading and paragraphs are bullets beneath it.

    Args:
        raw_result:  AnalyzeResult from analyze_sop_layout().
        run_id:      Pipeline run identifier — included for traceability.
        source:      PDF URL or path — recorded as sop_document.
        granularity: "paragraph" (default) or "section".

    Returns:
        dict matching schemas/sop_steps.json
    """
    if granularity not in ("paragraph", "section"):
        raise ValueError(f"granularity must be 'paragraph' or 'section', got {granularity!r}")

    figures_by_page = _figures_by_page(raw_result)
    current_section = None
    # (section, text, page) per kept paragraph, in reading order
    kept: list[tuple[str | None, str, int | None]] = []

    for paragraph in raw_result.paragraphs or []:
        role = paragraph.role
        if role in _SKIP_ROLES:
            continue

        text = (paragraph.content or "").strip()
        if role in _SECTION_ROLES:
            if text:
                current_section = text
            continue

        if len(text) < _MIN_STEP_CHARS:
            continue

        if current_section and _NON_PROCEDURE_SECTION_RE.search(current_section):
            continue

        kept.append((current_section, text, _paragraph_page(paragraph)))

    steps = []
    if granularity == "paragraph":
        for section, text, page in kept:
            steps.append(_make_step(
                len(steps) + 1, text, section,
                list(figures_by_page.get(page, [])) if page else [],
            ))
    else:
        for section, text, page in kept:
            figures = figures_by_page.get(page, []) if page else []
            if steps and steps[-1]["section"] == section:
                steps[-1]["description"] += "\n" + text
                merged = steps[-1]["visual_references"]
                merged.extend(f for f in figures if f not in merged)
            else:
                steps.append(_make_step(len(steps) + 1, text, section, list(figures)))
        # Re-classify after merging — a duration cue may span paragraphs
        for step in steps:
            check_type, duration = _classify_check(step["description"])
            step["check_type"] = check_type
            step["expected_duration_seconds"] = duration

    if not steps:
        logger.warning(
            f"No steps extracted | run_id={run_id} — check the page range and "
            "whether the document is a scanned image without OCR-able text."
        )

    return {
        "run_id": run_id,
        "sop_document": _document_name(source),
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "total_steps": len(steps),
        "steps": steps,
    }


def extract_sop_steps(sop_blob_url: str, run_id: str, pages: str | None = None,
                      granularity: str = "paragraph") -> dict:
    """
    Analyse an SOP PDF and return structured Steps JSON.

    Args:
        sop_blob_url: SAS URL to the SOP PDF in Blob Storage, or a local path.
        run_id:       Pipeline run identifier — included in output for traceability.
        pages:        Optional page range (e.g. "1-20") for large manuals.
        granularity:  "paragraph" (default) or "section" — see parse_sop_steps().
                      Use "section" for the Prusa manual.

    Returns:
        dict matching schemas/sop_steps.json
    """
    logger.info(f"Extracting SOP steps | run_id={run_id}")
    raw_result = analyze_sop_layout(sop_blob_url, pages=pages)
    return parse_sop_steps(raw_result, run_id, sop_blob_url, granularity=granularity)
