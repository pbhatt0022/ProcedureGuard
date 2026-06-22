# ProcedureGuard — Architecture

> Update this file when any layer, agent, or service decision changes.

---

## ⚠️ AS-BUILT (June 22, 2026) — authoritative; the 5-layer design below is the original plan

Where the layered design below conflicts with this section, **this section wins.** The 5-layer
Azure design was the aspiration; much of it was deliberately not built (see
`DECISIONS_AND_RATIONALE.md`). What actually runs:

| Designed | As-built |
|---|---|
| Input uploaded via **Streamlit** | Local path or Blob SAS URL passed to `run_pipeline()`; **Streamlit removed** |
| **AI Search** multimodal visual index | Not built — never wired |
| **Content Understanding** for video | Removed June 18 — OpenCV duration probe + GPT-4o Vision Phase 2 only |
| **3 Foundry agents** (Layer 3) | Removed — `pipeline.py` calls modules directly (`generate_checklist`, `run_video_phase2`, `reason_step`); no agent runtime |
| **Cosmos DB** (Layer 4) | Removed — local JSON run store (`runs/<run_id>.json` + `.review.json` sidecar) |
| Q&A **Agent 3** via MCP | Q&A ported to a Next.js route handler (`frontend/.../chat/route.ts`) |
| **Streamlit** dashboard (Layer 5) | Next.js review dashboard (`frontend/`) |

Still accurate as-built: Document Intelligence (SOP extraction), GPT-4o checklist + reasoning,
GPT-4o Vision Phase 2 (OpenCV frames, **768 px**, `detail:high`, ~6 frames/25s window), the
four-verdict model and guards (below), Entra ID auth via `DefaultAzureCredential`, Blob keyframes
(local fallback).

---

## 5-Layer Architecture Overview *(original design — see as-built banner above)*

```
Layer 1 · Input
  SOP PDF + Manufacturing Video → uploaded via Streamlit → archived to Blob Storage

Layer 2 · Data Extraction
  SOP PDF    → Document Intelligence (Layout v4.0) → Steps JSON
             → AI Search (multimodal embeddings) → Visual SOP Index (diagrams, figures, symbols)
  Video MP4  → Content Understanding (prebuilt-video) → fixed ~25s time windows → GPT-4o Vision (Phase 2) → Observations JSON

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

## Compliance verdict model (updated June 16)

Each SOP step is first tagged by **verifiability** (in `checklist_generator`):
- `presence` / `sequence` — a gross physical action overhead video can confirm; carries an
  `observable_action` (the action stripped of any torque/seating/orientation clause).
- `fine_detail` — torque, seating, orientation, rotation, small-part counts, or inspection-only
  acts that 1 fps / 768 px video cannot resolve.

`reason_step` then renders one of **four verdicts**:
- **Compliant** — a video window clearly shows the `observable_action`.
- **Deviation Detected** — a window *positively* shows the action done wrong (never inferred from absence of evidence).
- **Requires Inspection** — a `fine_detail` step, short-circuited without a GPT-4o call and routed to a human.
- **Unable to Verify** — no window shows anything relevant.

`enforce_unique_evidence()` guarantees one window backs at most one Compliant verdict. Adherence
score = Compliant ÷ (Compliant + Deviation) — i.e. "of the video-verifiable steps"; Requires
Inspection and Unable to Verify are excluded from the denominator.

---

## Content Understanding analyzer schema

Base: `prebuilt-video`
API version: `2025-11-01` (GA — never use preview)
Upload method: Blob Storage URL reference (not binary upload)

> **Note (June 16):** the custom field schema below is **not used** in the running pipeline.
> `prebuilt-video` collapses continuous footage to one segment, so the pipeline imposes fixed ~25s
> time windows (`build_time_windowed_segments`) and fills compliance fields with a GPT-4o Vision
> Phase 2 pass per window. The schema is retained as the Week 3 target once a Foundry project with a
> linked OpenAI deployment is available. See `docs/KNOWN_ISSUES.md`.

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

## Phase 2 Vision mode (implemented June 12, 2026)

`prebuilt-video` returns only relative keyframe filenames in its markdown output — no accessible
image URLs. GPT-4o Phase 2 therefore uses **OpenCV** to extract frames directly from the video:

```
video URL (Blob SAS)
  → cv2.VideoCapture(url)        # opens ~4s, stays open across all segments
  → seek to N evenly-spaced timestamps per segment
  → cv2.resize to 512px longest edge
  → base64 JPEG data URI
  → GPT-4o Vision (detail: "low", ~85 tokens/frame)
  → ppe_status, tool_in_use, component_contact, visible_safety_concern, action_observed
```

- Up to 6 frames per segment; falls back to text-only if OpenCV can't open the URL
- Run pipelines **sequentially** — concurrent runs exhaust the GPT-4o rate limit
- Retry config on `extract_compliance_fields`: 6 attempts, exponential backoff up to 90s

---

## Authentication (confirmed working June 12, 2026)

All services authenticate via **Microsoft Entra ID** (`DefaultAzureCredential`) — no API keys.
Locally this resolves to the `az login` session (AzureCliCredential).

| Resource | Endpoint | Required RBAC role |
|---|---|---|
| `procedureguard-ai` (Foundry hub, Kind: AIServices) — serves Document Intelligence + Content Understanding | `https://pg-ai-priya.services.ai.azure.com` (custom subdomain — required for token auth) | Cognitive Services User |
| `procedureguard-openai` — GPT-4o deployment `gpt-4o` | `https://procedureguard-openai.openai.azure.com/` | Cognitive Services OpenAI User |
| `pgstorepriya2026` (Blob Storage) | account URL | Storage Blob Data Contributor |

Implementation notes:
- Azure SDK clients (`DocumentIntelligenceClient`, `ContentUnderstandingClient`) take `DefaultAzureCredential()` directly when the `.env` key is blank.
- The OpenAI SDK needs a token provider: `get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")` → `azure_ad_token_provider=`. Implemented in `checklist_generator.py`, `compliance_engine.py`, `video_analyzer.py`.
- `config.py` pops blank `AZURE_OPENAI_API_KEY` / `AZURE_OPENAI_AD_TOKEN` / service-principal vars from `os.environ` — empty strings break SDK credential fallback chains (see KNOWN_ISSUES).
- Do **not** use the 84-char keys from the Foundry hub's portal "Keys and Endpoint" page — they are Foundry API keys and 401 against everything in this pipeline (see KNOWN_ISSUES).

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
