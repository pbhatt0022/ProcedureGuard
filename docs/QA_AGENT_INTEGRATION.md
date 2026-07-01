# Agent 4 Integration

## Role

Agent 4 is the ProcedureGuard Q&A Chat Agent.

Agent 4 is read-only and limited to:
- evidence retrieval
- ticket queries
- compliance investigation
- run-level compliance summary retrieval
- incident lookup
- audit-trail support
- QA handoff support

Agent 4 does not:
- create tickets
- update tickets
- assign tickets
- escalate tickets
- create incidents
- classify severity
- send notifications
- modify data
- trigger pipeline execution

## Architecture

The target local architecture is:

`User / Dashboard -> QAAgent -> Azure OpenAI GPT model -> official MCP client -> official MCP server -> read-only tools -> dummy JSON backend`

Implementation files:
- `src/agents/qa_agent.py`
- `src/mcp_server/server.py`
- `src/mcp_server/tools.py`
- `src/providers/dummy_data_store.py`
- `src/dummy_data/*.json`

The MCP layer uses the official Python MCP SDK over `stdio`.

It does not use a custom `BaseHTTPRequestHandler` server or a custom `/mcp` HTTP endpoint.

## Setup

Create your local environment file:

```bash
cp .env.example .env
```

Then fill in:
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_DEPLOYMENT_NAME`
- `AZURE_OPENAI_API_VERSION`

Do not commit a real `.env` file. The repository ignores `.env`.

## Dummy Backend Meaning

The dummy JSON backend stands in for future production systems:
- `verdicts.json`: future Cosmos DB verdict records
- `evidence.json`: future Blob Storage keyframe and clip metadata
- `tickets.json`: future ticket status system
- `audit_logs.json`: future compliance audit event stream
- `runs.json`: future run/session metadata

Today, Agent 4 reads local records through a SQLite provider that seeds itself from the dummy JSON files.

Later, the MCP tool implementations can be swapped to real Cosmos, Blob, and ticket integrations without changing the dashboard-facing `QAAgent` contract.

## Conversation Memory

Agent 4 keeps short-lived conversation state per session:
- `session_id`
- `current_run_id`
- `current_step_id`
- `current_incident_id`
- `current_ticket_id`
- `current_evidence_ids`
- `last_intent`
- `last_updated_at`

Redis is used when available. If Redis is unavailable, the agent falls back to an in-memory store so the local demo still works.

The session layer stores only lightweight IDs and metadata, not full evidence blobs or full chat history.

## MCP Tools

The MCP server exposes these read-only tools:

1. `retrieve_run_summary(run_id: str)`
2. `query_verdicts(run_id: str, step_id: str | None = None)`
3. `retrieve_checklist_step(run_id: str, step_id: str)`
4. `fetch_keyframes(run_id: str, step_id: str | None = None, timestamp: str | None = None)`
5. `fetch_video_clips(run_id: str, step_id: str | None = None, timestamp: str | None = None)`
6. `retrieve_ticket_status(ticket_id: str)`
7. `query_tickets(run_id: str, step_id: str | None = None)`
8. `query_incidents(run_id: str, step_id: str | None = None, severity: str | None = None, status: str | None = None)`
9. `retrieve_incidents(incident_id: str)`
10. `query_audit_logs(run_id: str, step_id: str | None = None, ticket_id: str | None = None)`

Guardrails:
- Agent 4 must not create new compliance verdicts.
- Agent 4 must not re-score runs beyond the stored run summary.
- Agent 4 must not override Agent 2 or Agent 3 outputs.
- Agent 4 must not invent evidence if clips or keyframes are missing.
- If data is unavailable, Agent 4 should answer with `not found` or `insufficient evidence`.

## QAAgent Behavior

`QAAgent`:
- uses Azure OpenAI chat completions
- discovers MCP tools from the official MCP server
- lets GPT decide which tool to call
- executes tool calls through the MCP client
- sends tool results back to GPT
- returns a final answer grounded only in tool output

If Azure OpenAI credentials are missing, the GPT test skips cleanly.

If the MCP server cannot be started or reached through the configured stdio command, the agent returns a clear MCP availability error.

## Configuration

Agent 4 loads configuration only through `src/config.py`, which reads `.env` via `python-dotenv`.

Default `.env.example` values:

```bash
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1-mini
AZURE_OPENAI_API_VERSION=
PROVIDER_MODE=mcp
MCP_SERVER_COMMAND=python scripts/run_mcp_server.py
```

## Run Locally

Start the MCP server:

```bash
python scripts/run_mcp_server.py
```

Test MCP tools:

```bash
python scripts/test_mcp_tools.py
```

Test the GPT agent:

```bash
python scripts/test_gpt_qa_agent.py
```

Suggested questions:
- `Was STEP-03 compliant?`
- `Show keyframe for STEP-03.`
- `Fetch video clip for STEP-03.`
- `What is the status of INC-2045?`
- `Who is assigned to INC-2045?`
- `Investigate STEP-03.`
- `What happened in RUN-102?`
- `What is the adherence score?`
- `Why was STEP-04 unable to verify?`
- `Which deviation is most serious?`
- `Who reviewed this deviation?`
- `Which steps need human review?`
- `Which steps were unable to verify?`

## Future Replacement Path

When production integrations are ready, replace only the dummy backend reads inside `src/providers/dummy_data_store.py` or behind the MCP tool layer.

The Agent 4 responsibilities and read-only guarantees should stay unchanged.
