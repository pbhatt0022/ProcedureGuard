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

## Decision: Remove Azure AI Content Understanding entirely — OpenCV duration probe + GPT-4o Vision only
**Date:** Week 4 (June 18)
**Decision:** Deleted all Content Understanding code (`analyze_video`, `parse_observations`, `get_client`, `create_or_update_analyzer`, `COMPLIANCE_FIELD_SCHEMA`, the analyzer-provisioning helper). Video duration now comes from `probe_video_duration()` (OpenCV); the observations dict is built directly in `pipeline.py`; segments come from `build_time_windowed_segments()`; per-window fields come from GPT-4o Vision (Phase 2). `config.py` CU fields commented out (kept for re-add), `.env.example` entries commented out, and the CU-only diagnostic `scripts/inspect_cu_result.py` deleted.
**Rationale:** CU no longer contributed usable output for this footage. Its custom GENERATE/CLASSIFY fields silently returned 0 segments (see the now-superseded two-phase decision below), and `prebuilt-video` collapsed continuous single-take assembly footage to one segment (superseded by time windows, June 16). Its keyframe URLs were inaccessible (404 — see KNOWN_ISSUES), so OpenCV already does frame extraction. That left CU doing nothing but returning a duration number OpenCV gives for free — at the cost of an Azure dependency, an analyzer-provisioning step, and dead code paths.
**Alternatives considered:** Keep CU for the architecture-diagram story (rejected — paying real complexity for a component that does no work contradicts the project's honesty principle); keep CU only for duration (rejected — `probe_video_duration` is one OpenCV call, no provisioning, no SDK).
**Trade-offs:** The architecture loses a named Azure AI service. Accepted: being honest about what actually does the work beats a richer-looking diagram. Re-adding CU later is straightforward — config fields are preserved as comments.
**Supersedes:** "Two-phase video compliance extraction (prebuilt-video + GPT-4o vision)", "Use `prebuilt-video` base, not `prebuilt-videoSearch`", "Target Content Understanding API version `2025-11-01`", and "Use Blob Storage URL reference, not binary upload, for Content Understanding video" (all below, retained for history).
**Source:** `src/ingestion/video_analyzer.py`, `src/pipeline.py`, `config.py`; KNOWN_ISSUES.md keyframe-inaccessibility + 0-segment entries

---

## Decision: Confirmed-absence detection via deterministic `apply_absence_inference`, gated by `key_objects`
**Date:** Week 4 (June 18)
**Decision:** A post-reasoning pass `apply_absence_inference()` upgrades Unable to Verify → Deviation Detected for a presence-tier step ONLY when all hold: (1) windows tile ≥90% of clip duration, (2) at least one Compliant verdict exists in the run, and (3) the step declares `key_objects` and none of those object tokens appear in ANY window description. Items without `key_objects` are never auto-upgraded. Flagged verdicts carry `not_observed=True` and a dashed "↯ Not observed across full clip" dashboard pill.
**Rationale:** "The worker never performed step X" is a real and valuable compliance finding, but inferring it from silence is dangerous. The three guards make it safe: full-clip coverage proves the camera saw the whole job; an existing Compliant verdict proves the camera + pipeline actually work (not a dead feed); and `key_objects` narrows the absence test to a discriminating named part instead of generic vocabulary. The `key_objects` gate is the crux — Phase 2 describes parts by generic appearance ("pink connector", "gray rod"), which never matches functional SOP names ("screw", "front chassis"), so testing the full `observable_action` fires on nearly every correctly-done step. Restricting to an explicit, vocabulary-verified `key_object` is what keeps precision at 100%.
**Alternatives considered:** The `coverage_note` prompt hint (tried and removed — see next decision); testing the full `observable_action` token set (≈5 false positives per clean clip); a fixed confidence threshold with no coverage/sanity guard (fires on partial clips and dead cameras).
**Trade-offs:** Deliberately conservative — most steps get no absence detection, so recall is low. Requires per-item `key_objects` curation and verification that Phase 2 actually emits the token. Accepted: for a compliance tool whose entire pitch is "no bullshitting," zero false alarms outranks recall.
**Source:** `src/reasoning/compliance_engine.py` (`apply_absence_inference`), `src/reasoning/checklist_generator.py` (`key_objects` field + coercion), `schemas/verification_record.json` (`not_observed`)

---

## Decision: Remove the `coverage_note` prompt hint from `reason_step`
**Date:** Week 4 (June 18)
**Decision:** Deleted the `coverage_note` parameter, its payload injection, and the entire "COVERAGE NOTE" section of the reasoning `SYSTEM_PROMPT`. `reason_step` is now strictly positive-evidence: Compliant / Deviation Detected require a specifically-cited window; everything else is Unable to Verify. Confirmed-absence is handled only by `apply_absence_inference`.
**Rationale:** `coverage_note` told GPT-4o "if no window shows this action over a fully-covered clip, return Deviation Detected." On the clean baseline clip (23_assy_0_1) it produced **5 false positives** — GPT escalated steps that were performed correctly but whose functional vocabulary Phase 2 never used (check-007 hands, check-012 chassis, check-016 braces, check-021 bracket, check-022 screw). A soft natural-language hint cannot enforce the coverage + camera-sanity + key-object guards that make absence inference safe; a deterministic function can, and is unit-testable. Splitting the responsibility eliminated the FPs.
**Alternatives considered:** Tighten the `coverage_note` wording (rejected — still unguarded and still vocabulary-dependent); keep both mechanisms (rejected — double-counts and re-introduces the FPs).
**Trade-offs:** GPT-4o no longer has any path to flag absence on its own; all absence detection now flows through the `key_objects` gate. That concentration is intentional — one guarded, testable path instead of a diffuse prompt behaviour.
**Source:** `src/reasoning/compliance_engine.py`

---

## Decision: check-025 (rear pulley) — `key_objects` validated then cleared; pulley not yet reliably detectable
**Date:** Week 4 (June 18)
**Decision:** Set `key_objects=["pulley"]` on check-025, validated it end-to-end, then cleared it back to `[]`. The mechanism stays in place; this specific detection is disabled pending a vocabulary-aligned Phase 2.
**Rationale:** With `key_objects=["pulley"]`, absence inference correctly flagged the missing-pulley candidate clip (22_assy_2_3) as a true positive. BUT Phase 2 calls the STEMFIE pulley a "pink connector" / "pink axle connector" in BOTH the correct and the incorrect clips — at overhead resolution it is visually indistinguishable from the other pink connectors. So the same rule also fires on the clean baseline (false positive), and both clips land at identical adherence scores — useless for a demo and, worse, a false alarm on good work. Clearing `key_objects` trades the single true positive for zero false positives.
**Alternatives considered:** Keep `key_objects=["pulley"]` (1 TP but 1 FP on clean footage and indistinguishable scores — rejected on the no-false-alarms principle); checklist-aware Phase 2 that explicitly asks "is a pulley present on the rear axle?" rather than describing generically (the real fix — deferred to Week 3, gated by the eval harness).
**Trade-offs:** We knowingly give up the only wheel-related deviation the pipeline could currently detect, in exchange for never crying wolf on a correct build. Logged as a KNOWN_ISSUE with the resolution path.
**Source:** `demo_results_correct_v3.json` check-025; `scripts/eval_harness.py`; KNOWN_ISSUES.md pulley entry

---

## Decision: Presence-tier eval harness as the accuracy instrument
**Date:** Week 4 (June 18)
**Decision:** `scripts/eval_harness.py` maps IndustReal action-label deltas (`fit_wheel:-1`, `fit_pulley:-1`) onto checklist `item_id`s and computes TP/FP/FN/TN + precision/recall on the presence tier. Only "Deviation Detected" counts as a positive prediction; uncertain GT mappings are marked UNRESOLVED and excluded from the metric.
**Rationale:** Before this, every tuning change was judged by eyeballing one clip — no way to tell whether a "fix" improved detection or just relocated errors. The harness turns "does it work?" into a reproducible number and forces honesty about mapping uncertainty (STEMFIE-vs-IndustReal nomenclature gaps are excluded rather than guessed). It is the gate for the Week 3 Phase 2 work: don't ship checklist-aware Phase 2 unless the harness shows recall rising without precision regressing.
**Current result:** across 4 clips / 15 evaluated items — **Precision 100%, Recall 25%** (TP=1, FP=0, FN=3, TN=11). All 3 false negatives are front-vs-rear-axle confusions that overhead video cannot resolve.
**Alternatives considered:** Manual per-clip inspection (not reproducible or comparable); full frame-level action-recognition eval (overkill, needs labels we don't have).
**Trade-offs:** Small eval set (4 clips) with hand-curated GT mappings — metrics are directional, not statistically robust. Clips 17_assy_1_5 and 18_assy_2_5 are wired into the harness but await Blob upload. Accepted as the best available instrument for an MVP.
**Source:** `scripts/eval_harness.py`

---

## Decision: Code-review cleanup after CU removal + verifiability tiering
**Date:** Week 4 (June 18)
**Decision:** Deleted `scripts/inspect_cu_result.py` (CU-only diagnostic referencing the removed SDK and commented-out config). Rewrote `tests/test_video_analyzer.py` to drop the Phase 1 tests (`parse_observations`, `COMPLIANCE_FIELD_SCHEMA`, CU fixtures) and cover the current Phase 2 API. Fixed stale fixtures in `test_compliance_engine.py` and `test_checklist_generator.py` that predated verifiability tiering (missing `observable_action`/`verifiability`, so items were silently dropped or short-circuited to Requires Inspection). Added `key_objects` coercion in `_validate_items`. Updated stale CU / `parse_observations` docstrings across `video_analyzer.py`, `compliance_engine.py`, `sequence_timing.py`, `blob_client.py`.
**Rationale:** After removing CU and adding verifiability tiering, the suite had 15 failing/broken tests and several modules cited deleted functions in docstrings. Dead and stale references mislead the next human and the next agent, and a red test suite is worthless as a regression guard. Result: **69/69 tests pass**, and `src/` has zero references to `coverage_note` / `parse_observations` / `analyze_video` / `COMPLIANCE_FIELD_SCHEMA`.
**Alternatives considered:** Leave the broken tests (rejected — defeats the purpose of having tests); delete the whole test file (rejected — the Phase 2 tests remain valuable).
**Trade-offs:** The `inspect_cu_result.py` deletion is permanent (this repo isn't under git). Its one finding — CU keyframe URLs are inaccessible — is already preserved in VIDEO_INTELLIGENCE_RESEARCH.md / KNOWN_ISSUES.md.
**Source:** this session; `pytest` 69 passed

---

## Decision: Time-windowed video segmentation (replaces reliance on prebuilt-video scene cuts)
**Date:** Week 4 (June 16)
**Decision:** The pipeline imposes fixed ~25s time windows over each video (`build_time_windowed_segments()`), then runs GPT-4o Vision Phase 2 per window — instead of using whatever segments `prebuilt-video` returns.
**Rationale:** `prebuilt-video` segments by shot cut, and continuous single-take assembly footage has none, so it returned ONE segment per clip. That collapsed all evidence to a single blob: ~27–29 steps abstained, the rest cited the whole video as "evidence," and one run fabricated 2 deviations from absence. Time windows give every verdict a tight, real timestamp and let the model localize actions.
**Alternatives considered:** Trusting prebuilt-video segmentation (broken for this footage); semantic/action-boundary segmentation (fragile, overkill for a demo); pure OpenCV with no Content Understanding (loses CU from the architecture story — kept CU for duration + bounds, with `probe_video_duration()` as OpenCV fallback).
**Trade-offs:** ~10–14 Phase 2 vision calls per clip instead of 1 (more tokens, more rate-limit pressure); 25s window size is a tuned constant, not adaptive to action speed.
**Source:** `src/ingestion/video_analyzer.py`, `src/pipeline.py`; `docs/KNOWN_ISSUES.md` single-segment entry

---

## Decision: Verifiability tiering + "Requires Inspection" as a first-class verdict
**Date:** Week 4 (June 16)
**Decision:** `generate_checklist()` now tags each step `verifiability = presence | sequence | fine_detail` and extracts an `observable_action` (the gross physical action a camera can see). `reason_step()` short-circuits `fine_detail` steps to a new verdict **"Requires Inspection"** (no GPT call) and reasons only on `observable_action` for the rest. Verdicts are now Compliant / Deviation Detected / Requires Inspection / Unable to Verify.
**Rationale:** Most SOP criteria bundle an observable action ("assemble the wheel stack") with an unobservable QC clause ("verify it rotates freely / pin fully seated"). Judging the whole criterion forced honest abstention on nearly everything. Splitting them lets the system verify what video shows and openly route torque/seating/orientation checks to a human — a legitimate compliance behaviour, not a failure to hide.
**Alternatives considered:** Keep a single criterion and abstain (yields "29 Unable to Verify" — honest but useless); loosen the reasoning prompt to pass fine detail (re-introduces fabrication — rejected).
**Trade-offs:** Adds a verdict category the dashboard/score must handle; "Requires Inspection" is excluded from the adherence denominator (score is "X of Y video-verifiable steps"); tiering quality depends on GPT-4o classifying sensibly (defaults to `fine_detail` when unsure — conservative).
**Source:** `src/reasoning/checklist_generator.py`, `src/reasoning/compliance_engine.py`

---

## Decision: Phase 2 Vision enrichment + unique-evidence guard
**Date:** Week 4 (June 16)
**Decision:** Phase 2 vision uses `detail:"high"`, 768px frames, ~4–5 frames/window, and a prompt asking for concrete part-level descriptions (colour, shape, how parts are joined). A post-reasoning `enforce_unique_evidence()` guard ensures one video window can back at most one "Compliant" verdict.
**Rationale:** With generic descriptions ("assembling components by hand") observable steps still didn't match; richer descriptions ("a gray pin inserted through aligned holes in two white beams") unlocked real matches. But richer matching surfaced over-attribution: several position-variant steps (forward vs rearmost bore) all matched the same generic window and each claimed Compliant. The guard demotes the duplicates to Unable to Verify, since the video lacks distinct evidence for each.
**Alternatives considered:** Lower `detail`/resolution (cheaper, but no matches); allow shared evidence (over-counts greens — dishonest).
**Trade-offs:** detail:high + 768px costs more tokens per call; the guard can demote a legitimately-distinct step if the model cited the same window.
**Source:** `src/ingestion/video_analyzer.py`, `src/reasoning/compliance_engine.py` (`enforce_unique_evidence`)

---

## Decision: Demo on the clean clip only — no fabricated deviations
**Date:** Week 4 (June 16)
**Decision:** The demo runs on the clean `correct` clip (3 genuinely-earned Compliant, 18 Requires Inspection, 8 Unable to Verify, 0 fabricated). The `wrong_pin` and `chassis_error` clips were dropped from the dashboard.
**Rationale:** Those two clips are IndustReal annotated renders with ground-truth labels burned into the frames (see KNOWN_ISSUES) — GPT-4o can read the answer key and viewers see the labels. Their planted faults (wrong-length pin) are also invisible at our resolution, so an honest run on clean footage would look nearly identical to the correct clip (no real deviation). A manufactured red would betray the project's core "no bullshitting" principle.
**Alternatives considered:** Keep the annotated clips (answer-key contamination); hand-edit a deviation into the JSON (fabrication — rejected); run wrong_pin and present "routes-to-inspection" honestly (needs clean footage we don't have yet).
**Trade-offs:** No "caught a bad build" red moment until we source a clip with a grossly visible error. Accepted for integrity.
**Source:** `docs/KNOWN_ISSUES.md` burned-in-label entry; session June 16

---

## Decision: One cached Azure OpenAI client + hardened retries on all GPT-4o calls
**Date:** Week 4 (June 16)
**Decision:** Replaced four duplicated `get_openai_client()` factories with one `@lru_cache`'d factory in `src/openai_client.py`. Brought `reason_step`, `generate_checklist`, and `answer_question` up to the hardened retry profile already used by Phase 2 (`stop_after_attempt(6)`, `wait_exponential(multiplier=2, min=5, max=90)`).
**Rationale:** Each module rebuilt the client on every call, re-walking the full DefaultAzureCredential chain (incl. an IMDS metadata probe) ~40 times per run — which once hung a run for ~2 days on a wedged metadata call. Caching walks the chain once. The tight 3-attempt retries also risked crashing mid-run during sustained GPT-4o 429 windows; the hardened profile rides them out.
**Alternatives considered:** Leave duplication (slower, fragile); client-side throttling or request batching to cut call volume (better root-cause fix — deferred as the "make fewer calls" follow-up).
**Trade-offs:** Caching assumes one endpoint/credential per process (true here). Hardened retries make a genuinely-failing call take up to ~5 min before surfacing.
**Source:** `src/openai_client.py`; `compliance_engine.py`, `checklist_generator.py`, `qa_agent.py`

---

## Decision: Microsoft Entra ID (DefaultAzureCredential) for all service auth — no API keys
**Date:** Week 2 (June 12)
**Decision:** All Azure service calls authenticate via `DefaultAzureCredential` (az login locally). All `*_KEY` fields in `.env` stay blank. The `procedureguard-ai` hub got a custom subdomain (`pg-ai-priya.services.ai.azure.com`) to enable token auth; RBAC roles assigned: "Cognitive Services User" (procedureguard-ai), "Cognitive Services OpenAI User" (procedureguard-openai).
**Rationale:** The portal keys for the Foundry hub are 84-char Foundry API keys that 401 against the Document Intelligence SDK and the OpenAI resource — there is no usable Cognitive Services key to copy. Entra ID auth works uniformly across Document Intelligence, Content Understanding, Azure OpenAI, and Blob Storage, eliminates secrets from `.env`, and matches the production-recommended pattern. Verified by the first successful end-to-end pipeline run (June 12).
**Alternatives considered:** Hunting for/regenerating resource-level keys (the Foundry hub doesn't expose standard ones); per-service key juggling (fragile, already burned a session on 401s).
**Trade-offs:** Local dev requires an active `az login` session; RBAC propagation adds ~1–2 min after role assignment; OpenAI client code needed a `get_bearer_token_provider` fallback in three modules. Personal-account quirk: role assignment must use `--assignee-object-id`, not email.
**Source:** `docs/KNOWN_ISSUES.md` "Foundry hub keys" entry; June 12 E2E run `run-20260612-034fe502`

---

## Decision: STEMFIE vehicle kit SOP + IndustReal clips as the demo pair (supersedes Prusa/OpenMarcie for the June 15 demo)
**Date:** Week 2 (June 12)
**Decision:** The June 15 demo uses the teammate-generated `STEMFIE_vehicle_kit_assembly_manual.pdf` (14 pages, Procedure A = pages 4–11, 29 extracted steps) as the SOP, paired with a short IndustReal assembly clip. OpenMarcie/Prusa remains the Week 3 benchmark dataset.
**Rationale:** The Prusa manual is 200+ pages and OpenMarcie sessions are ~60 min — too heavy for iterative demo testing. The STEMFIE manual was authored with documented error modes (wrong pin type, acorn nut instead of bracket screw, missing washer), which makes deviation detection demonstrable on purpose rather than by luck. IndustReal clips are 4–5 min, matching the <5 min latency target.
**Alternatives considered:** Prusa manual + OpenMarcie clip (heavyweight, kept for benchmarking); fake/synthetic demo JSON (rejected in favour of a real pipeline run).
**Trade-offs:** IndustReal videos ship as JPG frame archives (need ffmpeg reassembly) or YouTube demo clips; no formal SOP ships with IndustReal so the STEMFIE manual stands in as the procedural ground truth. The Week 1 dataset decision below still governs quantitative evaluation.
**Source:** `tests/fixtures/STEMFIE_vehicle_kit_assembly_manual.pdf`; https://github.com/TimSchoonbeek/IndustReal

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
**⚠️ SUPERSEDED June 18** — Content Understanding removed entirely (see top of file). The URL-reference principle still applies to OpenCV/GPT-4o Vision, which open the Blob SAS URL directly.
**Decision:** All videos passed to Content Understanding via Blob Storage URL reference using the `analyze` API.
**Rationale:** Binary upload via `analyzeBinary` is limited to 200 MB and 30 minutes. IndustReal clips exceed this. The URL reference method supports up to 4 GB and 2 hours.
**Alternatives considered:** Binary upload, pre-chunking videos
**Trade-offs:** Requires Blob upload step before analysis; adds minor latency but is unavoidable for dataset videos
**Source:** https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/service-limits

---

## Decision: Use `prebuilt-video` base, not `prebuilt-videoSearch`
**Date:** Week 1 (pre-build)
**⚠️ SUPERSEDED June 18** — Content Understanding removed entirely; no analyzer base is used anymore. Retained for history.
**Decision:** Custom compliance analyzer extends `prebuilt-video`, not `prebuilt-videoSearch`.
**Rationale:** `prebuilt-videoSearch` is optimised for RAG and search — it returns natural language summaries and topic segments. ProcedureGuard needs structured field answers (PPE status, tool in use, component contact) that map to specific SOP steps. This requires a custom `fieldSchema`, which requires `prebuilt-video` as base.
**Alternatives considered:** `prebuilt-videoSearch`, `prebuilt-videoAnalysis`
**Trade-offs:** More setup required for custom schema; significantly better output for compliance use case
**Source:** https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/concepts/prebuilt-analyzers

---

## Decision: Target Content Understanding API version `2025-11-01` (GA)
**Date:** Week 1 (pre-build)
**⚠️ SUPERSEDED June 18** — Content Understanding removed entirely. Retained for history.
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
**⚠️ SUPERSEDED June 18** — Phase 1 (Content Understanding) removed entirely. Only the Phase 2 GPT-4o Vision pass remains, now fed by OpenCV time-windowed frames. This entry documents the 0-segment finding that justified dropping CU. Retained for history.
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

### Consider: Checklist-aware Phase 2 to fix recall (PENDING — deferred for UI/UX work, June 18)
**Raised:** Week 4 (June 18) — parked while we build the visual demo / UI-UX.
**What it is:** Today Phase 2 (`extract_compliance_fields`) asks GPT-4o Vision for a *generic, free-form* description of each window ("a black wheel is mounted onto a gray axle… a pink connector…"). That generic vocabulary is the single root cause of our low recall: it cannot distinguish the rear **pulley** from any other pink part, and it cannot tell the **front** axle from the **rear** axle. Checklist-aware Phase 2 flips the question: instead of "describe this window," pass GPT-4o the *specific discriminating things this clip's checklist cares about* and ask targeted, closed questions — e.g. *"Is a flat pink disk (pulley) seated on an axle BEFORE a wheel goes on? Which axle — the one nearer the front bracket or the rear? Answer present/absent/unclear with the window id."*

**Why it's the right next move (my recommendation):**
1. It attacks the actual bottleneck. Eval harness (June 18) = **Precision 100%, Recall 25%**; all 3 false negatives and the disabled pulley check are downstream of generic Phase 2 vocabulary. No amount of reasoning-layer tuning fixes a description that never contained the discriminating word.
2. It's the honest version of detection. We are not lowering a confidence threshold or guessing — we are asking the model to *look harder at the specific thing the SOP step hinges on*. If it still can't tell, the honest answer is "unclear" → Unable to Verify, which is exactly today's behaviour.
3. It re-enables the pulley deviation and the front/rear wheel distinction **without** re-introducing false alarms, because the eval harness gates it.

**What would change (concrete plan):**
- `checklist_generator.py` already emits `key_objects`. Extend it (or a small new step) to also emit, per presence-tier item, a short list of **discriminating questions** the camera could answer (the "pulley before wheel?" / "which axle?" style).
- `video_analyzer.py` Phase 2: in addition to (or instead of) the generic `action_observed`, run a second targeted prompt per window seeded with the discriminating questions for the steps whose time window overlaps. Capture structured answers (object → present/absent/unclear → window id).
- `compliance_engine.py`: let `reason_step` / `apply_absence_inference` consume those structured answers. With reliable per-object presence signals, `key_objects=["pulley"]` can be switched back on for check-025 and the front/rear axle steps can be disambiguated.
- Re-run `scripts/eval_harness.py`. **Gate:** ship only if recall rises *and* precision stays at 100% (no new false positives on the clean baseline 23_assy_0_1).

**Risk to weigh before committing:** the pulley may be genuinely unresolvable at overhead 1fps/512–768px even with a pointed question (it's a flat disk seen edge-on, often occluded by the wheel that follows). If a quick spike shows the model still answers "unclear," do NOT force it — keep the honest miss, and instead get the demo "red moment" from a clip with a grossly-visible deviation (whole subassembly missing). Time-box the spike to ~half a day.
**Blocker before deciding:** finish the UI/UX + visual demo first (current priority). Then a half-day spike on one targeted question (pulley) to see if the signal is even there before building the full path.
**Source:** `docs/KNOWN_ISSUES.md` (pulley + front/rear axle entries); `scripts/eval_harness.py`; June 18 decisions at top of this file.

---

### Consider: Front/rear axle positional disambiguation in reason_step
**Raised:** Week 4 (June 18)
**What it is:** Overhead video can't currently tell which axle a wheel is being mounted on, so `reason_step` matches *a* wheel-mount window to a wheel step and `enforce_unique_evidence` arbitrarily keeps one. This causes wheel-step false negatives (check-024/025). A positional/sequence-aware matcher would use frame position (which end of the chassis) and order relative to other identified parts to assign the right window to the right axle.
**Why consider it:** It's the other half of the recall gap (alongside the pulley). Likely subsumed by checklist-aware Phase 2 above (the "which axle?" question), so consider doing them together rather than separately.
**What would change:** `reason_step` matching logic and/or the Phase 2 targeted questions; possibly `sequence_timing.py` to supply ordering hints.
**Blocker before deciding:** Do the checklist-aware Phase 2 spike first — if targeted questions resolve "which axle," this is free.
**Source:** `docs/KNOWN_ISSUES.md` front/rear axle entry.

---

### Consider: Expand the eval set beyond 4 clips (cheap, do-anytime)
**Raised:** Week 4 (June 18)
**What it is:** `17_assy_1_5` and `18_assy_2_5` (both `fit_pulley:-1`) are already wired into `eval_harness.py` (`GT_ITEM_LEVEL` + `RESULT_FILES`) but their clips aren't in Blob Storage yet, so the harness skips them. Upload the two clips to `pgstorepriya2026/manufacturing-videos`, generate SAS URLs, run `scripts/run_industreal_demo.py candidate <url>` for each, and the harness picks them up automatically.
**Why consider it:** Takes the metric from 4 clips / 15 items to 6 clips, making whatever precision/recall we report in the final write-up materially more defensible. Pure upside, ~30–45 min, no code change. Worth doing regardless of which bigger direction we pick.
**Blocker before deciding:** None — just bandwidth. Watch GPT-4o 429 rate limits (run the two clips sequentially, not concurrently — concurrent 16-window runs exhausted the quota on June 18).
**Source:** `scripts/eval_harness.py`; June 18 session.

---

### Consider: Azure AI Search candidate pre-filter for reason_step (Week 3 upgrade path)
**Raised:** Week 2 (architecture), still pending.
**What it is:** `reason_step` currently passes all windows to GPT-4o (with a free local lexical prefilter, `_select_candidate_segments`, that no-ops under ~8 windows). The planned upgrade swaps in AI Search-retrieved candidate windows; the function signature is designed to stay identical.
**Why consider it:** Only matters for long videos (20+ windows) where token cost and disambiguation degrade. Our demo clips are 14–16 windows, so it's not urgent — but it's the documented scaling story for the write-up.
**Blocker before deciding:** `src/storage/sop_indexer.py` (indexer) must land first. Low priority unless we move to full-length sessions.
**Source:** "Compliance reasoning — GPT-4o receives all video segments (Option C)" decision above.

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
