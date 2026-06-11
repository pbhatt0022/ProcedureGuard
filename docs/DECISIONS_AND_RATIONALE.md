# ProcedureGuard — Decisions and Rationale

> Log every significant architectural or technical decision here.
> Format: one entry per decision, newest at top.
> This file is for justifying choices to supervisors and avoiding re-litigating settled decisions.

---

## Template

```
## Decision: [short title]
**Date:** Week X
**Decision:** [What was decided — one sentence]
**Rationale:** [Why — 2-3 sentences]
**Alternatives considered:** [What else was evaluated]
**Trade-offs:** [What you give up with this choice]
**Source:** [Doc URL or conversation reference if applicable]
```

---

## Decision: Use OpenMarcie Scenario B (Prusa 3D printer) as primary test dataset
**Date:** Week 1 (pre-build)
**Decision:** OpenMarcie Scenario B is the primary video dataset for ProcedureGuard testing. IndustReal and OpenMarcie Scenario A are excluded.
**Rationale:** ProcedureGuard requires a procedural video dataset that has an accompanying SOP or instruction sequence for ground-truth compliance checking. OpenMarcie Scenario B (Prusa MK3S+ 3D printer assembly) meets this requirement — participants follow the official Prusa manufacturer instruction booklet, providing a natural SOP baseline. IndustReal was initially considered but uses a HoloLens 2 (not a ZED camera) and its clips are optimised for AR task guidance, not compliance verification. OpenMarcie Scenario A (bicycle assembly) is unscripted with no attached SOP, making it unsuitable for step-by-step compliance evaluation.
**Alternatives considered:** IndustReal (HoloLens 2, assembly/disassembly, no SOP); OpenMarcie Scenario A (bicycle assembly, unscripted, no SOP)
**Trade-offs:** OpenMarcie Scenario B sessions are ~60 minutes long — trimming is required (skip first ~10 min reading phase, use 5-min clips for Content Understanding smoke tests). Full dataset is 139 GB; use DFKI portal direct download (`projects.dfki.uni-kl.de/open-marcie`, `reviewer/1234`) to pull single-participant zips (~11.8 GB each) rather than the full archive. Ego video file per participant: `3DEgoZedChestVol{N}_RGB_anonymized.mp4` inside `EgoZedVideo_Vol{N}.zip`. Object mask files (`ObjectTracking_Vol{N}_Chest.zip`) are separate and not required for initial pipeline testing.
**Source:** OpenMarcie Kaggle page; DFKI portal dataset browser; Prusa MK3S+ assembly manual (https://help.prusa3d.com)

---

## Decision: Include Azure AI Search multimodal RAG in Layer 2
**Date:** Week 1 (pre-build)
**Decision:** Azure AI Search with multimodal embeddings is included in Layer 2 to index non-text SOP content — diagrams, figures, annotated tables, and safety symbols.
**Rationale:** SOP documents frequently contain visual instructions that carry compliance-relevant meaning. Plain text extraction from Document Intelligence misses embedded diagrams, flow charts, and safety pictograms. Multimodal RAG allows Agent 1 to retrieve and reason over visual SOP elements when generating the compliance checklist, producing a richer and more accurate representation of the SOP's full intent.
**Alternatives considered:** Text-only extraction via Document Intelligence alone; manual OCR of figures.
**Trade-offs:** Additional service to provision (Azure AI Search S1 tier, multimodal embedding model). Adds setup time in Week 1. Acceptable given the compliance accuracy benefit, especially for SOP documents with heavy visual content.
**Source:** ProcedureGuard Architecture DOCX; Azure AI Search multimodal embeddings docs

---

## Decision: Do not use A2A (Agent-to-Agent) protocol
**Date:** Week 1 (pre-build)
**Decision:** A2A protocol will not be used in ProcedureGuard.
**Rationale:** The pipeline is linear and entirely Azure-native. A2A is designed for cross-platform, cross-runtime agent collaboration. Adding it here would mean wrapping each agent in an A2A server, managing cross-agent authentication, and debugging protocol-level failures — all with no benefit since agents communicate through shared Cosmos DB state.
**Alternatives considered:** Full A2A integration between all three agents
**Trade-offs:** Cannot easily expose agents to external systems in future — acceptable for an internship MVP
**Source:** Azure A2A documentation; architectural review in project planning

---

## Decision: MCP used only for Agent 3 (Q&A Chat)
**Date:** Week 1 (pre-build)
**Decision:** MCP tool connections are scoped to Agent 3 only. Agents 1 and 2 use direct SDK calls.
**Rationale:** Agent 3 is the only agent that needs to dynamically query storage at user request. Agents 1 and 2 have deterministic, sequential data flows that are better served by direct SDK calls with explicit error handling. MCP for all agents adds setup overhead with no benefit.
**Alternatives considered:** MCP for all three agents
**Trade-offs:** Agent 3 Q&A is slightly more powerful (flexible queries) but Agents 1 and 2 are simpler to build and debug
**Source:** Azure Foundry MCP docs; architectural review

---

## Decision: Use Blob Storage URL reference, not binary upload, for Content Understanding video
**Date:** Week 1 (pre-build)
**Decision:** All videos passed to Content Understanding via Blob Storage URL reference using the `analyze` API.
**Rationale:** Binary upload via `analyzeBinary` is limited to 200 MB and 30 minutes. IndustReal clips exceed this. The URL reference method supports up to 4 GB and 2 hours.
**Alternatives considered:** Binary upload, pre-chunking videos
**Trade-offs:** Requires Blob upload step before analysis; adds minor latency but is unavoidable for dataset videos
**Source:** https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/service-limits

---

## Decision: Use `prebuilt-video` base, not `prebuilt-videoSearch`
**Date:** Week 1 (pre-build)
**Decision:** Custom compliance analyzer extends `prebuilt-video`, not `prebuilt-videoSearch`.
**Rationale:** `prebuilt-videoSearch` is optimised for RAG and search — it returns natural language summaries and topic segments. ProcedureGuard needs structured field answers (PPE status, tool in use, component contact) that map to specific SOP steps. This requires a custom `fieldSchema`, which requires `prebuilt-video` as base.
**Alternatives considered:** `prebuilt-videoSearch`, `prebuilt-videoAnalysis`
**Trade-offs:** More setup required for custom schema; significantly better output for compliance use case
**Source:** https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/concepts/prebuilt-analyzers

---

## Decision: Target Content Understanding API version `2025-11-01` (GA)
**Date:** Week 1 (pre-build)
**Decision:** All Content Understanding calls target API version `2025-11-01`.
**Rationale:** This is the current GA version. Preview versions (`2024-12-01-preview`, `2025-05-01-preview`) are retired by July 2026 and have no SLA. Building on GA from day one avoids migration work mid-project.
**Alternatives considered:** `2025-05-01-preview` (has Pro mode, but Pro mode only supports documents — not video)
**Trade-offs:** Pro mode (cross-file analysis) not available on GA for video — not needed for this project
**Source:** https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/whats-new

---

## Decision: Use Foundry Agent Service (not custom Python orchestration)
**Date:** Week 1 (pre-build)
**Decision:** All three agents built on Azure Foundry Agent Service, not custom Python loop orchestration.
**Rationale:** Foundry Agent Service provides built-in retry logic, tool calling, observability, and managed state. Building equivalent orchestration in Python would consume most of Week 2. The service is GA at `ai.azure.com`.
**Alternatives considered:** Raw Python with GPT-4o API calls and manual loop management; LangChain
**Trade-offs:** Slightly less control over exact execution; portal instability has been reported — keep fallback Python scripts ready
**Source:** https://learn.microsoft.com/en-us/azure/ai-foundry/

---

## Decision: Scope Cosmos DB as primary structured store, Blob for binaries
**Date:** Week 1 (pre-build)
**Decision:** Cosmos DB stores all structured compliance data (checklists, verdicts). Blob Storage stores all binary assets (PDFs, videos, keyframes).
**Rationale:** Clean separation by data type. Cosmos DB is queryable by `run_id`; Blob is addressable by path convention `{run_id}/{step_id}.jpg`. Agent 3 can query both independently via MCP.
**Alternatives considered:** Azure Table Storage (simpler, cheaper), single Blob store for everything
**Trade-offs:** Cosmos DB setup takes longer than Table Storage; provides better query flexibility for the dashboard and Q&A agent
**Source:** Architectural review

---

## Decision: Two-phase video compliance extraction (prebuilt-video + GPT-4o vision)
**Date:** Week 1 (post smoke-test diagnostic)
**Decision:** Video compliance field extraction uses a two-phase approach: (1) `prebuilt-video` for segment detection and keyframe extraction; (2) GPT-4o vision on keyframes for compliance field values. Custom Content Understanding GENERATE/CLASSIFY fields are not used.
**Rationale:** Custom GENERATE/CLASSIFY fields silently return 0 segments on our standalone AIServices resource (no linked Azure OpenAI deployment). Diagnostics confirmed `prebuilt-video` base works correctly (returns 1 segment, keyframes at ~2s intervals). Phase 2 GPT-4o vision pass will produce better compliance reasoning anyway — it can be given a prompt tailored to the specific SOP step rather than generic compliance instructions.
**Alternatives considered:** (1) Provision a full Foundry project hub with GPT-4o deployment and link via `models` param — feasible but takes additional setup time mid-Week 1. (2) Keep custom analyzer and accept 0-segment output — not viable for any real compliance checking.
**Trade-offs:** Adds one GPT-4o API call per video segment (latency + cost); gains full GPT-4o reasoning quality over service-managed model. Phase 1 (segment detection) is already implemented and working. Phase 2 (GPT-4o vision) awaits Azure OpenAI endpoint configuration in Week 2.
**Source:** `scripts/diagnose_video.py` diagnostic; `docs/KNOWN_ISSUES.md` entry "GENERATE/CLASSIFY fields return 0 segments"

---

## Decision: Heuristic SOP step parsing with paragraph/section granularity; Agent 1 refines
**Date:** Week 1 (SOP extractor build)
**Decision:** `sop_extractor.py` parses Layout output heuristically (no LLM): section headings track `section`, page furniture and TOC/index content are skipped, wait/cure text with a time quantity becomes a `duration` check, same-page figures become `visual_references`. A `granularity` parameter controls step size: `"paragraph"` (default, one step per paragraph — matches the schema example) or `"section"` (one step per section heading, paragraphs merged — right for the Prusa manual, whose procedural unit is the "STEP N <title>" heading).
**Rationale:** Deterministic parsing keeps Layer 2 cheap, fast, and unit-testable, and the architecture already routes raw steps through Agent 1 (GPT-4o checklist generator) which is the right place for semantic refinement. Paragraph mode on the Prusa manual produced ~6 micro-steps per real step (bullets, part labels); section mode produced 36 steps for 30 pages — matching the manual's actual structure (verified live, run-sop-smoke-003, 65s).
**Alternatives considered:** GPT-4o parsing of raw Layout markdown in the extractor (duplicates Agent 1, adds cost/latency per page); Document Intelligence custom extraction model (needs labeled training data we don't have).
**Trade-offs:** Heuristics admit noise (web furniture, part labels in section mode) and the duration regex only catches explicit time quantities — Agent 1 must tolerate noisy input. Acceptable: over-extraction is recoverable downstream, missed steps are not.
**Source:** `scripts/test_sop_pipeline.py` runs on `tests/fixtures/prusa_mk3s_plus_assembly.pdf` pages 1–30

---

## Decision: Official Prusa MK3S+ assembly manual PDF as SOP test fixture (gitignored)
**Date:** Week 1 (SOP extractor build)
**Decision:** The real SOP test document is the official web-generated kit assembly manual, downloaded to `tests/fixtures/prusa_mk3s_plus_assembly.pdf` (28.9 MB, 200+ pages, gitignored via `tests/fixtures/*.pdf`).
**Rationale:** Matches the video dataset — OpenMarcie Scenario B participants follow this exact manual, so SOP steps and video observations describe the same procedure. Local file analysis works (Document Intelligence accepts the 29 MB binary as base64; ~40 MB request body, well under the 500 MB S0 limit), so no Blob upload is required for testing. Always pass `--pages` (e.g. `1-30`) during testing — full-document analysis of 200+ pages is slow and costs per page.
**Alternatives considered:** Synthetic 2–3 page SOP only (no ground-truth link to the videos); uploading to Blob `sop-documents` and using SAS URLs (works too, but SAS expiry makes local testing brittle).
**Trade-offs:** 29 MB file lives outside git — each teammate re-downloads it (URL in `tests/fixtures/README.md`).
**Source:** https://help.prusa3d.com/wp-content/uploads/generated/original-prusa-i3-mk3s-kit-assembly_1128_en_2025-04-18.pdf

---

## Decision: Compliance reasoning — GPT-4o receives all video segments (Option C)
**Date:** Week 2
**Decision:** `reason_step()` passes the full observations dict (all segments) to GPT-4o in one call. GPT-4o identifies the best-matching segment and renders the verdict internally.
**Rationale:** For Week 2 clips (1–5 segments), the token cost of including all segments is negligible. Eliminates a separate pre-filtering step and lets GPT-4o do matching + verdict in one call — simpler and more robust for short clips where context boundaries are unclear.
**Alternatives considered:** (A) Positional sequence heuristic — fragile for non-linear assembly steps. (B) Sentence embedding similarity pre-filter — adds an embedding API call with no meaningful accuracy gain at 1–5 segments. (C) GPT-4o all-segments — chosen. Note: `find_matching_segments()` in `sequence_timing.py` uses keyword matching for the separate deterministic sequence/timing check only; it does not affect how `reason_step()` selects its evidence segment.
**Trade-offs:** Context window and token cost scale with segment count. Full-session videos with 60+ segments will hit token limits. Planned upgrade: Week 3, replace full observations dict with Azure AI Search pre-filtered candidates — `reason_step()` function signature stays the same.
**Source:** See `src/reasoning/compliance_engine.py`

---

## ⏳ Under Consideration (not yet decided)

These are architectural directions flagged for discussion — not committed to yet.

---

### Consider: Switch agent SDK to Microsoft Agent Framework
**Raised:** Week 1 (supervisor feedback)
**What it is:** Microsoft Agent Framework (v1.0, GA April 2026) is the official successor to both AutoGen and Semantic Kernel, which are now in maintenance mode. It provides a graph-based workflow model and first-class integration with Azure AI Foundry Agent Service. The pattern would be: Agent Framework SDK as the coding layer, Foundry Agent Service as the hosting/runtime layer.
**Why consider it:** Supervisor suggested using a specific Microsoft agent framework. Agent Framework is the current Microsoft recommendation for new 2026 projects. The workflow/graph model maps well to step-by-step compliance validation.
**What would change:** Agent code (sop_agent.py, reasoning_agent.py, qa_agent.py) would use the Agent Framework SDK instead of raw GPT-4o API calls or vanilla Foundry Agent Service calls.
**Blocker before deciding:** Assess implementation effort vs. timeline — Week 2 is agent build week. If Agent Framework adds significant learning curve, raw Foundry calls may be safer for MVP.
**Source:** https://learn.microsoft.com/en-us/agent-framework/overview/

---

### Consider: Add TimeGEN-1 for synthetic procedure timing data
**Raised:** Week 1 (supervisor feedback)
**What it is:** Nixtla's TimeGEN-1 is a 500M parameter zero-shot time series foundation model available in the Azure AI Foundry model catalog. No fine-tuning required — feed it seed data and it forecasts forward. Also has built-in anomaly detection.
**Why consider it:** Two potential uses: (1) generate synthetic procedure execution timing data (step durations, sequences) to create a richer test set without needing more real videos; (2) in production, model "expected" step durations and flag timing deviations as a compliance signal. Supervisor noted interest in time-series + gen AI for manufacturing.
**What would change:** Would add a new component to `sequence_timing.py` (currently a stub). May also add a synthetic data generation script under `scripts/`.
**Blocker before deciding:** Requires a hub-based Foundry project deployment (not standard project). Needs endpoint + `nixtlats` Python SDK. Assess if the timing deviation signal adds meaningful value on top of video-based compliance checking.
**Source:** https://ai.azure.com/explore/models/TimeGEN-1/version/1/registry/azureml-nixtla

---

## [Add new decisions below this line]
