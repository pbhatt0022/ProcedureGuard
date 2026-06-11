# ProcedureGuard — Project Context

> Paste this file at the start of every new conversation to give full project context.

---

## What is this project

ProcedureGuard is an AI-powered manufacturing procedure verification system built on Microsoft Azure. It reads a Standard Operating Procedure (SOP) document and analyses a video recording of a manufacturing process, producing a structured quality verification report that confirms which steps were executed correctly and where deviations occurred.

Built as a 4-week internship MVP. Team of 4 people. Demo-ready dashboard required by end of Week 4.

---

## Internship constraints

- **Azure-native only** — all services must be Microsoft Azure. No third-party APIs.
- **Supervised academic project** — decisions must be justifiable to a supervisor
- **4-week timeline** — scope must be ruthlessly managed
- **Demo deliverable** — the output is a working Streamlit dashboard, not a production system

---

## Pilot persona

**Vikram Nair** — Quality Assurance Manager, mid-sized medical device contract manufacturer. Subject to FDA, CE Mark, and ISO 13485 audits. Pain point: paper checklists cover only 5% of production volume; deviations go unrecorded between inspector visits.

---

## Tech stack

| Service | Role |
|---|---|
| Azure Content Understanding (`2025-11-01` GA) | Custom video analyzer — per-segment compliance field extraction |
| Azure Document Intelligence (Layout Model v4.0) | SOP PDF ingestion — text, tables, numbered steps |
| Azure OpenAI GPT-4o / GPT-4.1 | Checklist generation + per-step compliance reasoning |
| Azure Foundry Agent Service | Agent orchestration (3 agents) |
| Azure Cosmos DB | Compliance checklists, verdicts, keyed by `run_id` |
| Azure Blob Storage | SOP PDFs, videos, keyframes (`{run_id}/{step_id}.jpg`) |
| Python + Streamlit | Quality verification dashboard |
| GitHub Actions | CI/CD |

---

## Three agents (Layer 3)

- **Agent 1 — SOP Ingestion Agent**: Converts Document Intelligence JSON into a compliance checklist (presence / sequence / duration checks). Writes to Cosmos DB. Runs once per SOP.
- **Agent 2 — Compliance Reasoning Agent**: Per-step verdict (Compliant / Deviation Detected / Unable to Verify) with confidence score and evidence reference. Calls GPT-4o. Low confidence → retry with adjacent segments. Also triggers Python sequence + timing engine.
- **Agent 3 — Q&A Chat Agent**: On-demand conversational interface over run history. Calls Cosmos DB and Blob Storage via MCP tools at `mcp.ai.azure.com`.

---

## Success criteria

- SOP-to-checklist extraction: >90% of verifiable steps correctly identified
- Compliance verdict accuracy: >80% agreement vs manual benchmark on IndustReal dataset
- End-to-end pipeline latency: <5 minutes per video
- Streamlit dashboard demo-ready by end of Week 4

---

## Datasets

- **IndustReal (WACV 2024)** — primary dataset. 6 hours of egocentric procedural assembly videos, 27 participants, Apache 2.0. Available at `https://data.4tu.nl/datasets/b008dd74-020d-4ea4-a8ba-7bb60769d224`
- **Prusa MK3S+ assembly** — secondary demo SOP-video pair. OPENMARCIE availability unconfirmed — verify before Week 1 ends. Fallback: self-record a short assembly video.

---

## Key technical constraints to remember

- Content Understanding: 1 fps frame sampling, 512×512 px — fine motor actions at risk
- Content Understanding video: must use Blob Storage URL reference for files >200 MB / >30 min
- Content Understanding base analyzer for video: `prebuilt-video` (not `prebuilt-videoSearch`)
- A2A protocol: **not used** — pipeline is linear and Azure-native
- MCP: used only for Agent 3 Q&A — Cosmos DB + Blob as MCP tools

---

## Current status

> **Update this every week.**

Week: 2 (complete as of June 11, 2026)
Status: Core pipeline implemented and tested. `sop_extractor`, `checklist_generator`, `compliance_engine`, `sequence_timing`, and `pipeline.py` are all working with 73 tests passing. Agent Service wrappers and Cosmos DB / Blob Storage persistence are stubs — deferred to Week 3. Streamlit UI build starts June 12, demo target June 15.
Current blocker: None.
