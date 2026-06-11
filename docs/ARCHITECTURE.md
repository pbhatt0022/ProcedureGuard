# ProcedureGuard — Architecture

> Update this file when any layer, agent, or service decision changes.

---

## 5-Layer Architecture Overview

```
Layer 1 · Input
  SOP PDF + Manufacturing Video → uploaded via Streamlit → archived to Blob Storage

Layer 2 · Data Extraction
  SOP PDF    → Document Intelligence (Layout v4.0) → Steps JSON
             → AI Search (multimodal embeddings) → Visual SOP Index (diagrams, figures, symbols)
  Video MP4  → Content Understanding (prebuilt-video + custom schema) → Observations JSON

Layer 3 · AI Agents (Foundry Agent Service)
  Agent 1 (SOP Ingestion)      → Steps JSON → GPT-4o → Compliance checklist → Cosmos DB
  Agent 2 (Compliance Reasoning) → Checklist + Observations → GPT-4o → Per-step verdicts → Cosmos DB
                                   → Sequence + Timing Engine (Python) → Cosmos DB
  Agent 3 (Q&A Chat)           → User query → MCP tools → Cosmos DB / Blob → Response

Layer 4 · Data Management
  Azure Cosmos DB    → Checklists, verdicts, verification records (keyed by run_id)
  Azure Blob Storage → Raw SOP PDFs, videos, keyframes ({run_id}/{step_id}.jpg)

Layer 5 · Presentation
  Streamlit Dashboard
    - Compliance summary (step-by-step verdicts)
    - Adherence score (0–100%)
    - Deviation timeline (timestamps + keyframes)
    - Evidence viewer (video clips + SOP reference)
    - Chat interface (→ Agent 3 via MCP)
```

---

## Data flow

### Pipeline execution flow (triggered on upload)
1. User uploads SOP PDF + video via Streamlit
2. Both files written to Blob Storage (`run_id` assigned at this point)
3. Blob URL passed to Document Intelligence → returns Steps JSON
3a. SOP PDF indexed by Azure AI Search with multimodal embeddings → Visual SOP Index built (diagrams, figures, safety symbols)
4. Blob URL passed to Content Understanding → returns Observations JSON
5. Agent 1 receives Steps JSON + queries Visual SOP Index for visual context → GPT-4o generates compliance checklist → written to Cosmos DB
6. Agent 2 fetches checklist from Cosmos DB → per-step: fetches relevant observations, calls GPT-4o, gets verdict + confidence
7. If confidence < threshold → Agent 2 fetches adjacent video segments and re-reasons
8. Python sequence engine + timing engine run on timestamp data → results appended to Cosmos DB
9. Agent 2 writes keyframes to Blob Storage
10. Dashboard reads from Cosmos DB + Blob and renders compliance report

### Q&A flow (on-demand post-pipeline)
1. User types question in dashboard chat
2. Request routed to Agent 3
3. Agent 3 calls GPT-4o to interpret intent
4. Agent 3 calls MCP tools → queries Cosmos DB and/or fetches Blob clips
5. Agent 3 synthesises response → rendered in dashboard chat

---

## Content Understanding analyzer schema

Base: `prebuilt-video`
API version: `2025-11-01` (GA — never use preview)
Upload method: Blob Storage URL reference (not binary upload)

```json
{
  "baseAnalyzerId": "prebuilt-video",
  "models": {
    "completion": "gpt-4.1"
  },
  "fieldSchema": {
    "fields": {
      "ppe_status": {
        "type": "string",
        "method": "classify",
        "enum": ["compliant", "non-compliant", "not-visible"],
        "description": "PPE compliance status of the worker in this segment"
      },
      "tool_in_use": {
        "type": "string",
        "method": "generate",
        "description": "Identify the tool currently being used by the worker"
      },
      "component_contact": {
        "type": "string",
        "method": "generate",
        "description": "Describe which component the worker is contacting or assembling"
      },
      "visible_safety_concern": {
        "type": "boolean",
        "method": "classify",
        "description": "Whether a visible safety concern is present in this segment"
      },
      "action_observed": {
        "type": "string",
        "method": "generate",
        "description": "Natural language description of the primary action performed"
      }
    }
  }
}
```

---

## Eraser.io diagram code

Paste into a new Eraser file → Cloud Architecture Diagram.

```
// ProcedureGuard - 5-Layer Architecture

layer1 [label: "Layer 1 · Input", color: teal] {
  sop_pdf [label: "SOP PDF", icon: azure-blob-storage, color: teal]
  mfg_video [label: "Manufacturing Video", icon: azure-blob-storage, color: teal]
  user_uploads [label: "User Uploads", icon: azure-portal, color: teal]
  blob_archive [label: "Blob Storage Archive", icon: azure-blob-storage, color: teal]
}

layer2 [label: "Layer 2 · Data Extraction", color: grey] {
  doc_intelligence [label: "Document Intelligence\nLayout Model v4.0", icon: azure-cognitive-services, color: grey]
  ai_search [label: "AI Search\nMultimodal RAG — Visual SOP Index", icon: azure-search, color: grey]
  content_understanding [label: "Content Understanding\nAPI 2025-11-01", icon: azure-cognitive-services, color: grey]
  structured_output [label: "Structured Output\nSOP JSON + Video JSON\n+ Visual SOP Index", icon: azure-storage-accounts, color: grey]
}

layer3 [label: "Layer 3 · AI Agents (Foundry Agent Service)", color: purple] {
  agent1 [label: "Agent 1\nSOP Ingestion Agent", icon: azure-cognitive-services, color: purple]
  agent2 [label: "Agent 2\nCompliance Reasoning Agent", icon: azure-cognitive-services, color: purple]
  agent3 [label: "Agent 3\nQ&A Chat Agent", icon: azure-cognitive-services, color: purple]
  mcp_server [label: "MCP Tools\nmcp.ai.azure.com", icon: azure-api-management, color: orange]
  gpt4o [label: "GPT-4o\nAzure OpenAI", icon: azure-cognitive-services, color: purple]
  sequence_engine [label: "Sequence + Timing Engine\nPython", icon: azure-function-apps, color: purple]
}

layer4 [label: "Layer 4 · Data Management", color: blue] {
  cosmos_db [label: "Azure Cosmos DB\nChecklists · Verdicts · run_id", icon: azure-cosmos-db, color: blue]
  blob_storage [label: "Azure Blob Storage\nPDFs · Videos · Keyframes", icon: azure-blob-storage, color: blue]
}

layer5 [label: "Layer 5 · Presentation", color: green] {
  streamlit [label: "Streamlit Dashboard", icon: azure-app-service, color: green]
  compliance_summary [label: "Compliance Summary", icon: azure-monitor, color: green]
  adherence_score [label: "Adherence Score\n0-100%", icon: azure-monitor, color: green]
  deviation_timeline [label: "Deviation Timeline\nTimestamps + Keyframes", icon: azure-monitor, color: green]
  evidence_viewer [label: "Evidence Viewer\nVideo clips + SOP ref", icon: azure-monitor, color: green]
  chat_ui [label: "Chat Interface\n→ Agent 3 via MCP", icon: azure-bot-services, color: green]
}

sop_pdf > doc_intelligence: SOP pages
mfg_video > content_understanding: Production footage
user_uploads > blob_archive: Archive
blob_archive > content_understanding
blob_archive > doc_intelligence
blob_archive > ai_search
doc_intelligence > structured_output: Steps JSON
content_understanding > structured_output: Observations JSON
ai_search > structured_output: Visual SOP Index
structured_output > agent1
structured_output > agent2
agent1 > gpt4o: Generate checklist
agent2 > gpt4o: Per-step reasoning
agent2 > sequence_engine: Timing + order checks
agent3 > mcp_server: Tool calls
agent1 > cosmos_db: Write checklist
agent2 > cosmos_db: Write verdicts
agent2 > blob_storage: Write keyframes
mcp_server > cosmos_db: Query via MCP
mcp_server > blob_storage: Fetch clips via MCP
cosmos_db > streamlit
blob_storage > streamlit
streamlit > compliance_summary
streamlit > adherence_score
streamlit > deviation_timeline
streamlit > evidence_viewer
streamlit > chat_ui
chat_ui > agent3: User Q&A
```

---

## Service limits to keep in mind

| Service | Constraint |
|---|---|
| Content Understanding video | 1 fps frame sampling |
| Content Understanding video | All frames scaled to 512×512 px |
| Content Understanding video (binary upload) | Max 200 MB, 30 minutes |
| Content Understanding video (Blob URL) | Max 4 GB, 2 hours ← use this |
| Content Understanding throughput | Max 4 hours of video per minute (S0) |
| Cosmos DB | Keyed by `run_id` — all records must include this |
