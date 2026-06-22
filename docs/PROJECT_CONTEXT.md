# ProcedureGuard — Project Context

> Paste this file at the start of every new conversation to give full project context.

---

## ⚠️ AS-BUILT (June 22, 2026) — read before the design sections below

The "Tech stack" and "Three agents" sections below describe the **original** Azure design. As-built
reality: **no Streamlit** (Next.js dashboard in `frontend/`), **no Cosmos DB** (local JSON run store
`runs/<run_id>.json` + `.review.json`), **no Foundry agents** (pipeline calls modules directly),
**no AI Search**, **no Content Understanding** (removed June 18 — OpenCV + GPT-4o Vision only). The
demo SOP is now **GT-grounded** from IndustReal labels, not the STEMFIE quality manual (which
produced mostly boilerplate). See `ARCHITECTURE.md` as-built banner and `DECISIONS_AND_RATIONALE.md`.

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
| OpenCV + GPT-4o Vision | Video frame extraction (direct Blob SAS URL) + per-window compliance field description — replaces Content Understanding (dropped June 18; same 1fps/512px, no gain) |
| Azure Document Intelligence (Layout Model v4.0) | SOP PDF ingestion — text, tables, numbered steps |
| Azure OpenAI GPT-4o | Checklist generation + per-step compliance reasoning + Q&A chat |
| Azure Foundry Agent Service | Agent orchestration stubs (deferred — direct module calls used for demo) |
| Azure Cosmos DB | Compliance checklists, verdicts, keyed by `run_id` (deferred to Week 3) |
| Azure Blob Storage | SOP PDFs, videos (`manufacturing-videos` container) |
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

- **STEMFIE vehicle kit SOP** (demo SOP, Week 2) — teammate-generated 14-page assembly manual at `tests/fixtures/STEMFIE_vehicle_kit_assembly_manual.pdf`. Procedure A = pages 4–11 → 29 extracted steps. Includes documented error modes for deviation-detection demos. **This is the SOP IndustReal participants are filmed performing** — every IndustReal demo run (correct, chassis_error, wrong_pin, and the June 16 23_assy clips) reuses this same checklist; there is no separate "IndustReal SOP" to extract.
- **IndustReal (WACV 2024)** — demo video source + verdict-accuracy benchmark, paired with the STEMFIE SOP above. 6 hours of egocentric assembly video, 27 participants, Apache 2.0. Clips are 4–5 min (good for iteration); videos ship as JPG frames (ffmpeg reassembly) or YouTube demo clips. `https://data.4tu.nl/datasets/b008dd74-020d-4ea4-a8ba-7bb60769d224`
- **Prusa MK3S+ assembly + OpenMarcie Scenario B** — Week 3 benchmark SOP-video pair. Access confirmed via DFKI portal; manual at `tests/fixtures/prusa_mk3s_plus_assembly.pdf`.

---

## Key technical constraints to remember

- Video frame sampling: ~1 fps via OpenCV (matches what Content Understanding offered; fine motor detail unreliable — fine-detail steps route to "Requires Inspection" by design)
- Frame resolution: 768px longest edge, `detail:high` sent to GPT-4o Vision (~4–5 frames per 25s window)
- Video URL: must be Blob SAS URL (public or private); OpenCV opens it directly via `cv2.VideoCapture`
- Azure Content Understanding: **removed from pipeline (June 18)** — same fps/resolution as OpenCV path, custom GENERATE fields require Foundry Hub with no accuracy gain. Do not re-add.
- A2A protocol: **not used** — pipeline is linear and Azure-native
- MCP: used only for Agent 3 Q&A — Cosmos DB + Blob as MCP tools
- Python path on this machine: `/c/Python314/python` (not `python` or `python3` in PATH)

---

## Current status

> **Update this every week.**

Week: 4 (as of June 18, 2026)
Status: **Dashboard live, IndustReal demo clips wired, architecture pivot decided.** Four-verdict pipeline (Compliant / Deviation Detected / Requires Inspection / Unable to Verify) with time-windowed segmentation, verifiability tiering, Phase 2 GPT-4o Vision enrichment, and unique-evidence guard. Three one-click demo buttons in Streamlit: correct assembly, IndustReal baseline (23_assy_0_1), IndustReal honest mix (22_assy_2_3). Azure Content Understanding **removed from pipeline** — replaced by direct OpenCV duration probe; decision documented in WEEKLY_PROGRESS.md Addendum 5. Next: implement `apply_absence_inference()` post-processor to detect omitted steps from full-clip coverage, then re-run demo clips to validate.
Current blocker: None. `apply_absence_inference()` implemented and validated — `22_assy_2_3` now shows check-011 as Deviation Detected (not_observed, 75% adherence). Dashboard ready for demo.
