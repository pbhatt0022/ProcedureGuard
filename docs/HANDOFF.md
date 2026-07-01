# Handoff

## Purpose

This repository is a standalone implementation of Procedure Guard Agent 4: a read-only Q&A agent for compliance, evidence, incident, ticket, and audit-trail questions.

The intended role in the larger Procedure Guard solution is:

`main app / dashboard -> Agent 4 adapter -> QAAgent -> Azure OpenAI -> MCP client -> local MCP server -> read-only data tools`

This repo is useful as:
- a reference implementation for Agent 4 behavior
- a local development harness for QA chat flows
- a contract definition for read-only compliance investigation features

## What Agent 4 Does

Agent 4 answers questions about:
- run summaries
- SOP step verdicts
- deviation explanations
- keyframe and clip retrieval
- incident lookups
- ticket status
- audit trail history
- QA handoff summaries

Agent 4 is intentionally read-only.

It must not:
- create or update tickets
- assign or escalate tickets
- create incidents
- generate new compliance verdicts
- re-score runs beyond stored data
- trigger workflows or pipelines

## Main Entry Points

- `src/agents/qa_agent.py`
  - Primary application-facing entrypoint.
  - Use `QAAgent.answer(question, run_id=..., session_id=...)`.
- `src/mcp_server/tools.py`
  - Defines the MCP-exposed read-only tools.
- `src/providers/sqlite_data_store.py`
  - Local SQLite-backed record store seeded from dummy JSON.
- `src/providers/conversation_state_store.py`
  - Session context storage using Redis with in-memory fallback.
- `src/agents/query_resolution.py`
  - Resolves run/step/ticket/incident context and detects query intent.
- `src/config.py`
  - Centralized environment/config loading.

## Current Runtime Model

The current implementation uses:
- Azure OpenAI chat completions via the OpenAI Python SDK
- official Python MCP client/server libraries
- stdio transport for MCP
- SQLite local storage at `src/local_data/procedureguard.db`
- dummy seed data from `src/dummy_data/*.json`
- Redis for lightweight session memory when available

Important: this is not yet wired to production data sources.

## Public Integration Contract

From the perspective of the main Procedure Guard solution, the simplest contract is:

1. Construct `QAAgent`.
2. Pass in a user question.
3. Pass in a stable `session_id`.
4. Pass in the relevant default `run_id`.
5. Render the returned answer string.

Minimal usage pattern:

```python
from src.agents.qa_agent import QAAgent

agent = QAAgent()
answer = agent.answer(
    "Why was STEP-03 marked deviation?",
    run_id="RUN-102",
    session_id="web-user-123",
)
```

Expected behavior:
- Returns a final grounded answer string.
- Returns a clarification question if context is missing.
- Returns a friendly configuration/runtime error string if dependencies are unavailable.

## Session Behavior

Agent 4 keeps lightweight session context so follow-up questions work.

Stored context includes:
- current run ID
- current step ID
- current incident ID
- current ticket ID
- current evidence IDs
- last intent
- short answer summary metadata

This means the main app should preserve a stable `session_id` per user conversation.

If the main solution creates a fresh `session_id` on every message, follow-up questions like "show the clip" or "who owns it" will lose context.

## Query Resolution Notes

`src/agents/query_resolution.py` currently handles:
- run extraction like `RUN-102`
- step extraction like `STEP-03`
- incident/ticket extraction like `INC-2045`
- simple intent detection
- fallback to prior session context
- clarification when a follow-up is too vague

This is helpful for integration because the caller does not need to resolve every ID itself before calling the agent.

## MCP Tools Exposed

The MCP server currently exposes these read-only tools:

1. `retrieve_run_summary(run_id)`
2. `query_verdicts(run_id, step_id=None)`
3. `retrieve_checklist_step(run_id, step_id)`
4. `fetch_keyframes(run_id, step_id=None, timestamp=None)`
5. `fetch_video_clips(run_id, step_id=None, timestamp=None)`
6. `retrieve_ticket_status(ticket_id)`
7. `query_tickets(run_id, step_id=None)`
8. `query_incidents(run_id, step_id=None, severity=None, status=None)`
9. `retrieve_incidents(incident_id)`
10. `query_audit_logs(run_id, step_id=None, ticket_id=None)`

Claude should treat these tool contracts as the stable functional surface of Agent 4.

## Local Data Model

`src/local_data/procedureguard.db` is a local SQLite database file.

It is not source-of-truth production data.
It is created/used as a local durable cache/store seeded from:
- `src/dummy_data/runs.json`
- `src/dummy_data/checklist_steps.json`
- `src/dummy_data/verdicts.json`
- `src/dummy_data/incidents.json`
- `src/dummy_data/tickets.json`
- `src/dummy_data/audit_logs.json`
- `src/dummy_data/evidence.json`

For integration work, Claude should assume:
- the JSON files define the current demo dataset
- the SQLite file is local runtime state
- future production connectors should replace the provider layer, not the agent contract

## Recommended Integration Approach

Integrate this repo into the main solution in layers:

1. Wrap `QAAgent.answer(...)` behind a service boundary in the main app.
2. Map the main app's authenticated user/session to Agent 4 `session_id`.
3. Supply the active run ID from the UI context when available.
4. Keep Agent 4 responses read-only in the UI.
5. Surface clarification questions directly back to the user.
6. Log MCP/tool/runtime failures separately from user-facing responses.

Recommended first production-style adapter interface:

```python
def answer_agent4_question(
    *,
    user_message: str,
    run_id: str,
    session_id: str,
) -> str:
    agent = QAAgent()
    return agent.answer(user_message, run_id=run_id, session_id=session_id)
```

## What Claude Likely Needs To Replace

For main-solution integration, the likely swap points are:

- Replace dummy/local provider backing with real Procedure Guard data sources.
  - likely Cosmos DB or equivalent for verdicts/runs/incidents/tickets
  - likely Blob Storage or equivalent for evidence references
- Replace local process assumptions around MCP server startup if the main architecture prefers:
  - a dedicated sidecar
  - a managed worker/service
  - an internal tool host
- Replace direct CLI/demo entrypoints with app-owned API or orchestration code

Recommended rule: keep `QAAgent` behavior and tool semantics stable while swapping provider implementations underneath.

## Known Limits And Gaps

Current implementation limits:
- dummy/demo data only
- no write operations
- no real production identity/authorization model
- no real ticketing backend integration
- no real blob retrieval, only metadata/path-style references
- no advanced retrieval/ranking beyond direct tool usage
- no streaming response path
- no HTTP API wrapper in this repo

Important behavioral limit:
- timing and sequence answers must come from stored deterministic outputs, not fresh inference from raw timestamps alone

## Configuration Required

Environment variables expected by this repo:

```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.services.ai.azure.com/openai/v1
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1-mini
AZURE_OPENAI_API_VERSION=2025-04-14
PROVIDER_MODE=mcp
MCP_SERVER_COMMAND=python scripts/run_mcp_server.py
SQLITE_DB_PATH=src/local_data/procedureguard.db
REDIS_URL=redis://localhost:6379/0
SESSION_TTL_SECONDS=3600
```

## Local Verification

Useful commands before or during integration:

```bash
python scripts/run_mcp_server.py
python scripts/test_mcp_tools.py
python scripts/test_gpt_qa_agent.py
python scripts/test_gpt_qa_agent.py "Was STEP-03 compliant?"
python scripts/test_qa_memory.py
```

## Recommended Next Steps For Claude

1. Add an app-level adapter/service around `QAAgent.answer(...)`.
2. Connect the main Procedure Guard UI session model to Agent 4 `session_id`.
3. Pass real selected run context from the dashboard into `run_id`.
4. Decide whether MCP remains stdio-launched or should become a managed internal service.
5. Replace the SQLite/dummy provider path with the main solution's real data sources.
6. Preserve the read-only guardrails during integration.
7. Add end-to-end tests for follow-up question continuity across the main app session.

## File Map For Fast Navigation

- `README.md`
- `docs/QA_AGENT_INTEGRATION.md`
- `src/agents/qa_agent.py`
- `src/agents/query_resolution.py`
- `src/config.py`
- `src/mcp_server/tools.py`
- `src/providers/sqlite_data_store.py`
- `src/providers/conversation_state_store.py`
- `scripts/test_gpt_qa_agent.py`
- `scripts/test_mcp_tools.py`

