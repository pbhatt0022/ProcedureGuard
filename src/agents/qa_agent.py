from __future__ import annotations

import asyncio
import json
import logging
import shlex
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

from src.agents.query_resolution import QueryResolution, resolve_query
from src.config import Config, get_config
from src.providers.conversation_state_store import ConversationStateStore


SYSTEM_PROMPT = (
    "You are Agent 4, the ProcedureGuard Q&A Chat Agent. You are read-only. "
    "You can retrieve stored run summaries, verdicts, SOP checklist steps, keyframes, "
    "video clips, incident records, ticket status, tickets, and audit logs using MCP tools. "
    "Your job is to answer run-level compliance questions, step-level verdict explanations, "
    "evidence retrieval requests, deviation investigations, incident/ticket questions, audit trail "
    "questions, and QA handoff questions. Use stored tool outputs only. "
    "For run-level summaries, rely on retrieve_run_summary plus verdict records. "
    "For step explanations, combine query_verdicts with retrieve_checklist_step and relevant evidence tools. "
    "For timing and sequence questions, use only deterministic sequence or timing results returned by tools; "
    "do not guess from timestamps unless the stored summary explicitly supports that comparison. "
    "For vague risk-oriented questions, default to a concise summary of run status, deviations, high or critical "
    "incidents, and evidence references. "
    "Prefer these intent-to-tool mappings: run_summary/compliance_summary/qa_review_summary/sequence_query/timing_query -> retrieve_run_summary; "
    "step_explanation/deviation_reason -> query_verdicts plus retrieve_checklist_step; "
    "evidence_request/keyframe_request -> fetch_keyframes; clip_request -> fetch_video_clips; "
    "incident_query -> query_incidents or retrieve_incidents; ticket_query -> retrieve_ticket_status or query_tickets; "
    "audit_query/reviewer_history -> query_audit_logs. "
    "You must not create new compliance verdicts, re-score a run, override Agent 2 or Agent 3 outputs, "
    "create or update tickets, assign tickets, escalate tickets, create incidents, classify severity, or invent "
    "data. If evidence, clips, keyframes, or records are missing, say not found or insufficient evidence."
)

LOGGER = logging.getLogger(__name__)


@dataclass
class MCPToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]


class AgentConfigurationError(RuntimeError):
    pass


class MCPConnectionError(RuntimeError):
    pass


class MCPToolDiscoveryError(RuntimeError):
    pass


class MCPToolExecutionError(RuntimeError):
    pass


class AzureChatCompletionError(RuntimeError):
    pass


class ToolSchemaConversionError(RuntimeError):
    pass


class QAAgent:
    def __init__(
        self,
        *,
        config: Config | None = None,
        state_store: ConversationStateStore | None = None,
    ) -> None:
        self.config = config or get_config()
        self.state_store = state_store or ConversationStateStore(
            redis_url=self.config.redis_url,
            ttl_seconds=self.config.session_ttl_seconds,
        )

    def answer(self, question: str, run_id: str = "RUN-102", session_id: str = "default") -> str:
        if not question.strip():
            return "Question is empty."
        if self.config.provider_mode != "mcp":
            return f"Unsupported provider mode for Agent 4: {self.config.provider_mode}"
        resolution = self.resolve_query_context(question=question.strip(), run_id=run_id, session_id=session_id)
        if resolution.needs_clarification:
            self._log_resolution(resolution)
            self._persist_resolution_state(resolution)
            return resolution.clarification_prompt or "Please clarify the run, step, or ticket."
        try:
            self.config.validate_for_gpt()
            return asyncio.run(self._answer_async(resolution=resolution))
        except ValueError as exc:
            return self._format_error("Agent configuration error", exc)
        except RuntimeError as exc:
            return self._format_error("Agent runtime error", exc)

    def resolve_query_context(self, *, question: str, run_id: str, session_id: str) -> QueryResolution:
        state = self.state_store.load(session_id)
        resolution = resolve_query(
            question,
            session_id=session_id,
            default_run_id=run_id,
            state=state,
        )
        return resolution

    async def _answer_async(self, resolution: QueryResolution) -> str:
        tool_definitions: list[MCPToolDefinition] = []
        tool_outputs: list[dict[str, Any]] = []
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Session ID: {resolution.session_id}\n"
                    f"Default run context: {resolution.run_id or 'unknown'}\n"
                    f"Resolved step context: {resolution.step_id or 'none'}\n"
                    f"Resolved incident context: {resolution.incident_id or 'none'}\n"
                    f"Resolved ticket context: {resolution.ticket_id or 'none'}\n"
                    f"Resolved evidence IDs: {', '.join(resolution.evidence_ids) or 'none'}\n"
                    f"Resolved severity filters: {', '.join(resolution.severity_filters) or 'none'}\n"
                    f"Detected intent: {resolution.intent}\n"
                    f"Question: {resolution.original_question}\n"
                    "Use MCP tools when you need run, evidence, ticket, or audit data. "
                    "Ground the final answer only in tool outputs."
                ),
            },
        ]
        self._log_resolution(resolution)

        try:
            self._validate_mcp_command()
        except RuntimeError as exc:
            raise AgentConfigurationError(str(exc)) from exc

        try:
            async with self._open_mcp_session() as session:
                try:
                    tool_definitions = await self._list_mcp_tools(session)
                except Exception as exc:
                    raise MCPToolDiscoveryError(self._describe_exception(exc)) from exc

                for _ in range(8):
                    try:
                        response = self._chat_completion(messages, tool_definitions)
                    except Exception as exc:
                        raise AzureChatCompletionError(self._describe_exception(exc)) from exc

                    assistant_message = response.choices[0].message
                    tool_calls = assistant_message.tool_calls or []

                    messages.append(self._assistant_message_payload(assistant_message))

                    if not tool_calls:
                        content = assistant_message.content or ""
                        self._persist_resolution_state(
                            resolution,
                            tool_outputs=tool_outputs,
                            final_answer=content,
                        )
                        return content.strip() or "No answer was returned."

                    for tool_call in tool_calls:
                        try:
                            tool_result = await self._call_mcp_tool(
                                session,
                                tool_name=tool_call.function.name,
                                raw_arguments=tool_call.function.arguments,
                                resolution=resolution,
                            )
                        except Exception as exc:
                            tool_name = getattr(tool_call.function, "name", "unknown_tool")
                            raise MCPToolExecutionError(
                                f"{tool_name}: {self._describe_exception(exc)}"
                            ) from exc
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(tool_result),
                            }
                        )
                        tool_outputs.append(tool_result)
        except FileNotFoundError as exc:
            raise MCPConnectionError(
                "MCP server command not found. "
                "Check MCP_SERVER_COMMAND and ensure the official MCP server can start. "
                f"Details: {self._describe_exception(exc)}"
            ) from exc
        except (MCPToolDiscoveryError, AzureChatCompletionError, MCPToolExecutionError):
            raise
        except Exception as exc:
            categorized = self._extract_categorized_error(exc)
            if categorized is not None:
                raise categorized from exc
            raise MCPConnectionError(self._describe_exception(exc)) from exc

        return "Agent 4 could not complete the response within the tool-calling limit."

    async def _list_mcp_tools(self, session: ClientSession) -> list[MCPToolDefinition]:
        result = await session.list_tools()
        tool_definitions: list[MCPToolDefinition] = []
        for tool in result.tools:
            input_schema = getattr(tool, "inputSchema", None) or getattr(tool, "input_schema", None) or {}
            if not isinstance(input_schema, dict):
                raise ToolSchemaConversionError(
                    f"Tool {tool.name} returned a non-dict input schema: {type(input_schema).__name__}"
                )
            tool_definitions.append(
                MCPToolDefinition(
                    name=tool.name,
                    description=tool.description or "",
                    input_schema=input_schema,
                )
            )
        return tool_definitions

    async def _call_mcp_tool(
        self,
        session: ClientSession,
        *,
        tool_name: str,
        raw_arguments: str,
        resolution: QueryResolution,
    ) -> dict[str, Any]:
        try:
            arguments = json.loads(raw_arguments or "{}")
        except json.JSONDecodeError:
            arguments = {}
        if not isinstance(arguments, dict):
            arguments = {}
        arguments = self._normalize_tool_arguments(tool_name, arguments, resolution)

        result = await session.call_tool(tool_name, arguments)

        structured = getattr(result, "structuredContent", None) or getattr(result, "structured_content", None)
        if isinstance(structured, dict):
            return structured

        content = getattr(result, "content", None)
        if isinstance(content, list):
            text_chunks: list[str] = []
            for item in content:
                text_value = getattr(item, "text", None)
                if isinstance(text_value, str) and text_value.strip():
                    text_chunks.append(text_value)
            if text_chunks:
                combined = "\n".join(text_chunks)
                try:
                    parsed = json.loads(combined)
                except json.JSONDecodeError:
                    return {"content": combined}
                if isinstance(parsed, dict):
                    return parsed
        return {"content": str(result)}

    def _normalize_tool_arguments(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        resolution: QueryResolution,
    ) -> dict[str, Any]:
        normalized = dict(arguments)

        for key in ("run_id", "step_id", "incident_id", "ticket_id"):
            if key in normalized and isinstance(normalized[key], str):
                normalized[key] = self._normalize_entity_value(key, normalized[key])

        if tool_name == "retrieve_run_summary":
            normalized["run_id"] = normalized.get("run_id") or resolution.run_id
        elif tool_name == "query_verdicts":
            normalized["run_id"] = normalized.get("run_id") or resolution.run_id
            normalized["step_id"] = normalized.get("step_id") or resolution.step_id
        elif tool_name == "retrieve_checklist_step":
            normalized["run_id"] = normalized.get("run_id") or resolution.run_id
            normalized["step_id"] = normalized.get("step_id") or resolution.step_id
        elif tool_name in {"fetch_keyframes", "fetch_video_clips"}:
            normalized["run_id"] = normalized.get("run_id") or resolution.run_id
            normalized["step_id"] = normalized.get("step_id") or resolution.step_id
        elif tool_name == "retrieve_ticket_status":
            normalized["ticket_id"] = normalized.get("ticket_id") or resolution.ticket_id
        elif tool_name == "query_tickets":
            normalized["run_id"] = normalized.get("run_id") or resolution.run_id
            normalized["step_id"] = normalized.get("step_id") or resolution.step_id
        elif tool_name == "query_incidents":
            normalized["run_id"] = normalized.get("run_id") or resolution.run_id
            normalized["step_id"] = normalized.get("step_id") or resolution.step_id
            if resolution.severity_filters:
                normalized["severity"] = normalized.get("severity") or resolution.severity_filters[-1]
        elif tool_name == "retrieve_incidents":
            normalized["incident_id"] = normalized.get("incident_id") or resolution.incident_id
        elif tool_name == "query_audit_logs":
            normalized["run_id"] = normalized.get("run_id") or resolution.run_id
            normalized["step_id"] = normalized.get("step_id") or resolution.step_id
            normalized["ticket_id"] = normalized.get("ticket_id") or resolution.ticket_id

        return {key: value for key, value in normalized.items() if value not in (None, "")}

    def _normalize_entity_value(self, key: str, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            return stripped
        lowered = stripped.lower()
        digits = "".join(character for character in stripped if character.isdigit())
        if key == "step_id" and digits:
            return f"STEP-{int(digits):02d}"
        if key == "run_id" and digits:
            return f"RUN-{int(digits)}"
        if key in {"incident_id", "ticket_id"} and digits:
            return f"INC-{int(digits)}"
        if key == "step_id" and lowered.startswith("step-"):
            return stripped.upper()
        if key == "run_id" and lowered.startswith("run-"):
            return stripped.upper()
        if key in {"incident_id", "ticket_id"} and lowered.startswith("inc-"):
            return stripped.upper()
        return stripped

    def _chat_completion(
        self,
        messages: list[dict[str, Any]],
        tool_definitions: list[MCPToolDefinition],
    ) -> Any:
        client = OpenAI(
            base_url=self.config.azure_openai_endpoint,
            api_key=self.config.azure_openai_api_key,
        )
        return client.chat.completions.create(
            model=self.config.azure_openai_deployment_name,
            messages=messages,
            tools=[self._tool_schema(tool) for tool in tool_definitions],
            tool_choice="auto",
            temperature=0,
        )

    def _tool_schema(self, tool: MCPToolDefinition) -> dict[str, Any]:
        if not isinstance(tool.input_schema, dict):
            raise ToolSchemaConversionError(
                f"Tool {tool.name} has invalid schema type: {type(tool.input_schema).__name__}"
            )
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema or {"type": "object", "properties": {}},
            },
        }

    def _assistant_message_payload(self, message: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "role": "assistant",
            "content": message.content or "",
        }
        if message.tool_calls:
            payload["tool_calls"] = [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                }
                for tool_call in message.tool_calls
            ]
        return payload

    def _validate_mcp_command(self) -> None:
        if not self.config.mcp_server_command.strip():
            raise RuntimeError("MCP_SERVER_COMMAND is empty.")

    def _persist_resolution_state(
        self,
        resolution: QueryResolution,
        tool_outputs: list[dict[str, Any]] | None = None,
        final_answer: str | None = None,
    ) -> None:
        patch: dict[str, Any] = {"last_intent": resolution.intent}

        if resolution.run_id is not None:
            patch["current_run_id"] = resolution.run_id
        if resolution.step_id is not None:
            patch["current_step_id"] = resolution.step_id
        if resolution.incident_id is not None:
            patch["current_incident_id"] = resolution.incident_id
        if resolution.ticket_id is not None:
            patch["current_ticket_id"] = resolution.ticket_id
        if resolution.evidence_ids:
            patch["current_evidence_ids"] = resolution.evidence_ids

        if resolution.explicit_run_id is not None and resolution.explicit_step_id is None:
            patch["current_step_id"] = None
            patch["current_incident_id"] = None
            patch["current_ticket_id"] = None
            patch["current_evidence_ids"] = []
        if resolution.explicit_step_id is not None and resolution.explicit_ticket_id is None:
            patch["current_incident_id"] = None
            patch["current_ticket_id"] = None
            patch["current_evidence_ids"] = []

        for tool_output in tool_outputs or []:
            patch.update(self._extract_state_patch(tool_output))

        if final_answer:
            patch["last_answer_summary"] = self._summarize_answer(final_answer)

        self.state_store.update(resolution.session_id, **patch)

    def _extract_state_patch(self, tool_output: dict[str, Any]) -> dict[str, Any]:
        patch: dict[str, Any] = {}

        run_summary = tool_output.get("run_summary")
        if isinstance(run_summary, dict):
            patch["current_run_id"] = run_summary.get("run_id")

        verdicts = tool_output.get("verdicts")
        if isinstance(verdicts, list) and verdicts:
            first_verdict = verdicts[0]
            if isinstance(first_verdict, dict):
                patch["current_run_id"] = first_verdict.get("run_id")
                patch["current_step_id"] = first_verdict.get("step_id")
                patch["current_ticket_id"] = first_verdict.get("ticket_id")
                evidence_ids = first_verdict.get("evidence_ids")
                if isinstance(evidence_ids, list):
                    patch["current_evidence_ids"] = evidence_ids

        checklist_step = tool_output.get("checklist_step")
        if isinstance(checklist_step, dict):
            patch["current_run_id"] = checklist_step.get("run_id")
            patch["current_step_id"] = checklist_step.get("step_id")

        for evidence_key in ("keyframes", "video_clips"):
            evidence_records = tool_output.get(evidence_key)
            if isinstance(evidence_records, list) and evidence_records:
                first_record = evidence_records[0]
                if isinstance(first_record, dict):
                    patch["current_run_id"] = first_record.get("run_id")
                    patch["current_step_id"] = first_record.get("step_id")
                    patch["current_evidence_ids"] = [
                        record.get("evidence_id")
                        for record in evidence_records
                        if isinstance(record, dict) and record.get("evidence_id")
                    ]

        ticket = tool_output.get("ticket")
        if isinstance(ticket, dict):
            patch["current_run_id"] = ticket.get("run_id")
            patch["current_step_id"] = ticket.get("step_id")
            patch["current_ticket_id"] = ticket.get("ticket_id")

        tickets = tool_output.get("tickets")
        if isinstance(tickets, list) and tickets:
            first_ticket = tickets[0]
            if isinstance(first_ticket, dict):
                patch["current_run_id"] = first_ticket.get("run_id")
                patch["current_step_id"] = first_ticket.get("step_id")
                patch["current_ticket_id"] = first_ticket.get("ticket_id")

        incident = tool_output.get("incident")
        if isinstance(incident, dict):
            patch["current_run_id"] = incident.get("run_id")
            patch["current_step_id"] = incident.get("step_id")
            patch["current_incident_id"] = incident.get("incident_id")
            patch["current_ticket_id"] = incident.get("ticket_id")

        incidents = tool_output.get("incidents")
        if isinstance(incidents, list) and incidents:
            first_incident = incidents[0]
            if isinstance(first_incident, dict):
                patch["current_run_id"] = first_incident.get("run_id")
                patch["current_step_id"] = first_incident.get("step_id")
                patch["current_incident_id"] = first_incident.get("incident_id")
                patch["current_ticket_id"] = first_incident.get("ticket_id")

        audit_logs = tool_output.get("audit_logs")
        if isinstance(audit_logs, list) and audit_logs:
            first_audit = audit_logs[0]
            if isinstance(first_audit, dict):
                patch["current_run_id"] = first_audit.get("run_id")
                patch["current_step_id"] = first_audit.get("step_id")
                patch["current_ticket_id"] = first_audit.get("ticket_id")
                patch["current_incident_id"] = first_audit.get("incident_id")

        return {key: value for key, value in patch.items() if value not in (None, [], "")}

    def _log_resolution(self, resolution: QueryResolution) -> None:
        LOGGER.debug(
            "Agent 4 resolution session=%s intent=%s run=%s step=%s incident=%s ticket=%s severities=%s used_memory=%s notes=%s",
            resolution.session_id,
            resolution.intent,
            resolution.run_id,
            resolution.step_id,
            resolution.incident_id,
            resolution.ticket_id,
            ",".join(resolution.severity_filters) or "none",
            resolution.used_session_state,
            "; ".join(resolution.debug_notes) or "none",
        )

    def _summarize_answer(self, answer: str) -> str:
        compact = " ".join(answer.split())
        if len(compact) <= 240:
            return compact
        return compact[:237].rstrip() + "..."

    def _format_error(self, prefix: str, exc: BaseException) -> str:
        return f"{prefix}: {self._describe_exception(exc)}"

    def _describe_exception(self, exc: BaseException) -> str:
        nested = getattr(exc, "exceptions", None)
        if isinstance(nested, tuple) and nested:
            nested_descriptions = "; ".join(self._describe_exception(item) for item in nested)
            return f"{type(exc).__name__}: {nested_descriptions}"
        message = str(exc).strip()
        if not message:
            return type(exc).__name__
        return f"{type(exc).__name__}: {message}"

    def _extract_categorized_error(self, exc: BaseException) -> RuntimeError | None:
        for nested in self._iter_nested_exceptions(exc):
            if isinstance(nested, (MCPToolDiscoveryError, AzureChatCompletionError, MCPToolExecutionError)):
                return nested
            if isinstance(nested, ToolSchemaConversionError):
                return MCPToolDiscoveryError(self._describe_exception(nested))
        return None

    def _iter_nested_exceptions(self, exc: BaseException) -> list[BaseException]:
        nested = getattr(exc, "exceptions", None)
        if isinstance(nested, tuple) and nested:
            flattened: list[BaseException] = []
            for item in nested:
                flattened.extend(self._iter_nested_exceptions(item))
            return flattened
        return [exc]

    @asynccontextmanager
    async def _open_mcp_session(self) -> Any:
        parts = shlex.split(self.config.mcp_server_command.strip())
        if not parts:
            raise RuntimeError("MCP_SERVER_COMMAND is empty.")
        server_params = StdioServerParameters(command=parts[0], args=parts[1:])
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield session
