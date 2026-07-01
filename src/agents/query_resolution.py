from __future__ import annotations

from dataclasses import dataclass, field
import re

from src.providers.conversation_state_store import ConversationState


STEP_PATTERN = re.compile(r"\bstep[\s-]*0*(\d+)\b", re.IGNORECASE)
RUN_PATTERN = re.compile(r"\brun[\s-]*0*(\d+)\b", re.IGNORECASE)
INCIDENT_PATTERN = re.compile(r"\b(?:inc|incident|ticket)[\s-]*0*(\d+)\b", re.IGNORECASE)
ORDINAL_STEP_PATTERNS = {
    re.compile(r"\bfirst step\b", re.IGNORECASE): "STEP-01",
    re.compile(r"\bsecond step\b", re.IGNORECASE): "STEP-02",
    re.compile(r"\bthird step\b", re.IGNORECASE): "STEP-03",
    re.compile(r"\bfourth step\b", re.IGNORECASE): "STEP-04",
    re.compile(r"\bfifth step\b", re.IGNORECASE): "STEP-05",
}
VAGUE_REFERENCE_PATTERNS = [
    re.compile(r"\bit\b", re.IGNORECASE),
    re.compile(r"\bthat step\b", re.IGNORECASE),
    re.compile(r"\bthe issue\b", re.IGNORECASE),
    re.compile(r"\bthe ticket\b", re.IGNORECASE),
    re.compile(r"\bthe evidence\b", re.IGNORECASE),
    re.compile(r"\bwho owns it\b", re.IGNORECASE),
]


@dataclass
class QueryResolution:
    session_id: str
    original_question: str
    normalized_question: str
    explicit_run_id: str | None
    explicit_step_id: str | None
    explicit_incident_id: str | None
    explicit_ticket_id: str | None
    run_id: str | None
    step_id: str | None
    incident_id: str | None
    ticket_id: str | None
    evidence_ids: list[str] = field(default_factory=list)
    severity_filters: list[str] = field(default_factory=list)
    intent: str = "general_help"
    needs_clarification: bool = False
    clarification_prompt: str | None = None
    used_session_state: bool = False
    debug_notes: list[str] = field(default_factory=list)


def resolve_query(
    question: str,
    *,
    session_id: str,
    default_run_id: str,
    state: ConversationState,
) -> QueryResolution:
    normalized_question = question.strip()
    lowered = normalized_question.lower()

    explicit_run_id = _extract_run_id(normalized_question)
    explicit_step_id = _extract_step_id(normalized_question)
    explicit_incident_id = _extract_incident_id(normalized_question)
    explicit_ticket_id = explicit_incident_id
    intent = _detect_intent(lowered)
    severity_filters = _extract_severity_filters(lowered)

    run_id = explicit_run_id or state.current_run_id or default_run_id
    step_id = explicit_step_id
    incident_id = explicit_incident_id
    ticket_id = explicit_ticket_id
    evidence_ids: list[str] = []
    debug_notes: list[str] = []
    used_session_state = False

    if explicit_run_id:
        debug_notes.append(f"explicit run resolved to {explicit_run_id}")
    if explicit_step_id:
        debug_notes.append(f"explicit step resolved to {explicit_step_id}")
    if explicit_incident_id:
        debug_notes.append(f"explicit incident resolved to {explicit_incident_id}")

    vague_reference = _has_vague_reference(lowered) or intent in {
        "deviation_reason",
        "evidence_request",
        "keyframe_request",
        "clip_request",
        "incident_query",
        "ticket_query",
        "reviewer_history",
    }
    if step_id is None and _step_context_relevant(intent, lowered):
        if state.current_step_id:
            step_id = state.current_step_id
            used_session_state = True
            debug_notes.append(f"step context inherited from session: {step_id}")

    if incident_id is None and _incident_context_relevant(intent, lowered):
        if state.current_incident_id:
            incident_id = state.current_incident_id
            used_session_state = True
            debug_notes.append(f"incident context inherited from session: {incident_id}")

    if ticket_id is None and _ticket_context_relevant(intent, lowered):
        if state.current_ticket_id:
            ticket_id = state.current_ticket_id
            used_session_state = True
            debug_notes.append(f"ticket context inherited from session: {ticket_id}")

    if not evidence_ids and intent in {"evidence_request", "keyframe_request", "clip_request"} and state.current_evidence_ids:
        evidence_ids = list(state.current_evidence_ids)
        used_session_state = True
        debug_notes.append("evidence context inherited from session")

    if vague_reference and not any([explicit_step_id, explicit_incident_id, explicit_ticket_id]) and not used_session_state:
        return QueryResolution(
            session_id=session_id,
            original_question=question,
            normalized_question=normalized_question,
            explicit_run_id=explicit_run_id,
            explicit_step_id=explicit_step_id,
            explicit_incident_id=explicit_incident_id,
            explicit_ticket_id=explicit_ticket_id,
            run_id=run_id,
            step_id=None,
            incident_id=None,
            ticket_id=None,
            evidence_ids=[],
            severity_filters=severity_filters,
            intent=intent,
            needs_clarification=True,
            clarification_prompt="Which run, step, or ticket should I look up?",
            used_session_state=False,
            debug_notes=["clarification required because the question depends on missing session context"],
        )

    return QueryResolution(
        session_id=session_id,
        original_question=question,
        normalized_question=normalized_question,
        explicit_run_id=explicit_run_id,
        explicit_step_id=explicit_step_id,
        explicit_incident_id=explicit_incident_id,
        explicit_ticket_id=explicit_ticket_id,
        run_id=run_id,
        step_id=step_id,
        incident_id=incident_id,
        ticket_id=ticket_id,
        evidence_ids=evidence_ids,
        severity_filters=severity_filters,
        intent=intent,
        needs_clarification=False,
        clarification_prompt=None,
        used_session_state=used_session_state,
        debug_notes=debug_notes,
    )


def _extract_step_id(text: str) -> str | None:
    match = STEP_PATTERN.search(text)
    if match:
        return f"STEP-{int(match.group(1)):02d}"
    for pattern, step_id in ORDINAL_STEP_PATTERNS.items():
        if pattern.search(text):
            return step_id
    return None


def _extract_run_id(text: str) -> str | None:
    match = RUN_PATTERN.search(text)
    if not match:
        return None
    return f"RUN-{int(match.group(1))}"


def _extract_incident_id(text: str) -> str | None:
    match = INCIDENT_PATTERN.search(text)
    if not match:
        return None
    return f"INC-{int(match.group(1))}"


def _detect_intent(lowered: str) -> str:
    if "out of order" in lowered or "sequence" in lowered:
        return "sequence_query"
    if "cure" in lowered or "timing" in lowered or "long enough" in lowered:
        return "timing_query"
    if "what should qa review first" in lowered or "qa review" in lowered:
        return "qa_review_summary"
    if "adherence" in lowered or "what happened" in lowered or "summarize this run" in lowered:
        return "run_summary"
    if "follow the sop" in lowered or "serious issues" in lowered or "critical issue" in lowered:
        return "compliance_summary"
    if "changed after review" in lowered or "reviewed it" in lowered:
        return "reviewer_history"
    if "audit" in lowered or "history" in lowered or "show history" in lowered:
        return "audit_query"
    if "who owns" in lowered or "assigned" in lowered or "is the ticket open" in lowered:
        return "ticket_query"
    if "status" in lowered and ("inc" in lowered or "ticket" in lowered or "incident" in lowered):
        return "ticket_query"
    if "incident" in lowered or "issue" in lowered:
        return "incident_query"
    if "keyframe" in lowered:
        return "keyframe_request"
    if "clip" in lowered:
        return "clip_request"
    if "evidence" in lowered or "show me" in lowered or "show the" in lowered:
        return "evidence_request"
    if "why was" in lowered or "flagged" in lowered or "deviation" in lowered:
        return "deviation_reason"
    if "tell me about step" in lowered or "tell me about" in lowered:
        return "step_explanation"
    return "general_help"


def _extract_severity_filters(lowered: str) -> list[str]:
    if "serious issues" in lowered:
        return ["High", "Critical"]
    if "critical issue" in lowered or "critical issues" in lowered:
        return ["Critical"]
    return []


def _has_vague_reference(lowered: str) -> bool:
    return any(pattern.search(lowered) for pattern in VAGUE_REFERENCE_PATTERNS)


def _step_context_relevant(intent: str, lowered: str) -> bool:
    return intent in {
        "step_explanation",
        "deviation_reason",
        "evidence_request",
        "keyframe_request",
        "clip_request",
        "general_help",
    } or "that step" in lowered


def _incident_context_relevant(intent: str, lowered: str) -> bool:
    return intent in {"incident_query", "audit_query", "reviewer_history", "ticket_query"} or "the issue" in lowered


def _ticket_context_relevant(intent: str, lowered: str) -> bool:
    return intent in {"ticket_query", "audit_query", "reviewer_history"} or "the ticket" in lowered
