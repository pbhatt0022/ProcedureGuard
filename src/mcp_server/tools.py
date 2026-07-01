from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from src.config import get_config
from src.providers.sqlite_data_store import SQLiteDataStore


def create_mcp_server(data_store: Any | None = None) -> FastMCP:
    config = get_config()
    store = data_store or SQLiteDataStore(db_path=config.sqlite_db_path)
    server = FastMCP(
        name="procedureguard-agent4",
        instructions=(
            "Read-only MCP server for ProcedureGuard Agent 4. "
            "It exposes read-only verdict, evidence, checklist, run summary, incident, ticket, "
            "and audit log retrieval tools only."
        ),
    )

    @server.tool(
        description="Retrieve the stored run-level compliance summary, adherence score, overall status, and deterministic sequence/timing results for a run."
    )
    def retrieve_run_summary(run_id: str) -> dict[str, Any]:
        return {"run_summary": store.retrieve_run_summary(run_id=run_id)}

    @server.tool(
        description="Retrieve verdict records for a run, or narrow to a single SOP step."
    )
    def query_verdicts(run_id: str, step_id: str | None = None) -> dict[str, Any]:
        return {"verdicts": store.query_verdicts(run_id=run_id, step_id=step_id)}

    @server.tool(
        description="Retrieve the SOP checklist metadata for a single step in a run."
    )
    def retrieve_checklist_step(run_id: str, step_id: str) -> dict[str, Any]:
        return {"checklist_step": store.retrieve_checklist_step(run_id=run_id, step_id=step_id)}

    @server.tool(
        description="Fetch keyframe evidence records for a run, optionally filtered by step or timestamp."
    )
    def fetch_keyframes(
        run_id: str,
        step_id: str | None = None,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        return {
            "keyframes": store.fetch_keyframes(
                run_id=run_id,
                step_id=step_id,
                timestamp=timestamp,
            )
        }

    @server.tool(
        description="Fetch video clip evidence records for a run, optionally filtered by step or timestamp."
    )
    def fetch_video_clips(
        run_id: str,
        step_id: str | None = None,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        return {
            "video_clips": store.fetch_video_clips(
                run_id=run_id,
                step_id=step_id,
                timestamp=timestamp,
            )
        }

    @server.tool(
        description="Retrieve the status and metadata for a single existing incident ticket."
    )
    def retrieve_ticket_status(ticket_id: str) -> dict[str, Any]:
        return {"ticket": store.retrieve_ticket_status(ticket_id=ticket_id)}

    @server.tool(
        description="Retrieve incident tickets associated with a run, or narrow to a single SOP step."
    )
    def query_tickets(run_id: str, step_id: str | None = None) -> dict[str, Any]:
        return {"tickets": store.query_tickets(run_id=run_id, step_id=step_id)}

    @server.tool(
        description="Retrieve incident records for a run, optionally filtered by step, severity, or status."
    )
    def query_incidents(
        run_id: str,
        step_id: str | None = None,
        severity: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        return {
            "incidents": store.query_incidents(
                run_id=run_id,
                step_id=step_id,
                severity=severity,
                status=status,
            )
        }

    @server.tool(
        description="Retrieve a single incident record by incident ID."
    )
    def retrieve_incidents(incident_id: str) -> dict[str, Any]:
        return {"incident": store.retrieve_incident(incident_id=incident_id)}

    @server.tool(
        description="Retrieve audit log events for a production run, optionally narrowed to a step or ticket."
    )
    def query_audit_logs(
        run_id: str,
        step_id: str | None = None,
        ticket_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "audit_logs": store.query_audit_logs(
                run_id=run_id,
                step_id=step_id,
                ticket_id=ticket_id,
            )
        }

    return server
