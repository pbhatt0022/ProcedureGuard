# ProcedureGuard — Weekly Progress

> Update at the end of each week. One section per week.
> Use this for supervisor check-ins and for giving Claude current status context.

---

## Week 1 — Data Extraction + Schema Validation

### Planned deliverables
- [x] Azure Foundry resource created in supported region
- [x] GPT-4o deployed and connected to pipeline
- [x] Content Understanding custom video analyzer schema defined and validated
- [x] Document Intelligence SOP ingestion pipeline — first pass
- [x] Structured SOP extraction JSON confirmed
- [x] OpenMarcie / Prusa dataset access confirmed
- [x] Smoke test: Content Understanding returns segments + timestamps on test clip

### Completed
- Azure AIServices resource `procedureguard-ai` provisioned in East US
- Azure OpenAI resource `procedureguard-openai` with GPT-4o deployment
- Custom Content Understanding analyzer `procedureguard_compliance_v1` defined
- `sop_extractor.py` — Layout Model v4.0 pipeline with paragraph/section granularity
- Verified on Prusa MK3S+ manual: section mode → 36 steps for pages 1–30
- OpenMarcie Scenario B (Prusa 3D printer) dataset access confirmed via DFKI portal
- Prusa manual PDF (`prusa_mk3s_plus_assembly.pdf`) in test fixtures
- Smoke test: `prebuilt-video` returns segments + timestamps on a test clip

### Blockers (resolved)
- GENERATE/CLASSIFY custom fields silently return 0 segments on standalone AIServices resource — no linked Azure OpenAI deployment. **Fix:** two-phase workaround using `prebuilt-video` + separate GPT-4o call. See `docs/KNOWN_ISSUES.md`.
- Prusa manual TOC spans 13 pages and polluted step extraction with 373 fake steps. **Fix:** `_NON_PROCEDURE_SECTION_RE` filter in `sop_extractor.py`.
- GitHub raw URLs blocked by Content Understanding (`ContentSourceNotAccessible`). **Fix:** use Azure Blob Storage SAS URLs.
- OpenMarcie dataset `curl.exe` downloads reset mid-transfer. **Fix:** `aria2c` with 8 parallel connections. See `docs/KNOWN_ISSUES.md`.

### Changed from original plan
- GPT-4.1 not used for video analysis — not available on standalone AIServices. Two-phase approach with GPT-4o used instead.
- Azure AI Search provisioning pushed to Week 3 (not on the critical path for Week 1–2 pipeline).

### Notes / observations from smoke test
- `prebuilt-video` reliably returns segment boundaries and keyframe timestamps at 1fps/512px.
- GENERATE/CLASSIFY fields on `prebuilt-video` extension silently drop all segments without a linked Azure OpenAI deployment — the two-phase workaround is the correct approach for this resource configuration.
- Section-granularity mode for the Prusa manual produces the right step count (~36 for 30 pages).

---

## Week 2 — Agent Pipeline + Compliance Reasoning

### Planned deliverables
- [x] GPT-4o Phase 2 compliance field extraction (`video_analyzer.py`)
- [x] `generate_checklist()` with validation (`checklist_generator.py`)
- [x] Segment matching strategy decided and documented
- [x] `reason_step()` — per-step compliance verdict (`compliance_engine.py`)
- [x] Python sequence + timing engine (`sequence_timing.py`)
- [x] End-to-end pipeline orchestrator (`pipeline.py`) + demo script
- [x] 73 unit tests passing, 0 skipped
- [ ] Agent 1 / Agent 2 Foundry Agent Service wrappers — deferred to Week 3
- [ ] Cosmos DB persistence — deferred to Week 3
- [ ] Azure AI Search segment pre-filtering — deferred to Week 3

### Completed
- `video_analyzer.py` — `extract_compliance_fields()` and `run_video_phase2()`: GPT-4o extracts 5 compliance fields per segment from Content Understanding markdown descriptions; vision mode ready for keyframe images (Week 3)
- `checklist_generator.py` — `generate_checklist()`: GPT-4o converts Steps JSON into compliance checklist; `_validate_items()` coerces bad check_type / duration values
- `compliance_engine.py` — `reason_step()`: GPT-4o receives all video segments + criterion, identifies best-matching segment, renders verdict with confidence and evidence reference
- `sequence_timing.py` — `find_matching_segments()` (keyword overlap) and `validate_sequence_and_timing()` (deterministic sequence + duration checks)
- `pipeline.py` — full 5-step orchestrator with per-step error isolation and adherence score
- `scripts/run_pipeline_demo.py` — end-to-end smoke test + formatted compliance report
- Test coverage: 73 tests across 5 test files, all passing

### Blockers
- None

### Changed from original plan
- Agent Service wrappers (`sop_agent.py`, `reasoning_agent.py`) deferred to Week 3 — `pipeline.py` calls reasoning modules directly, which is sufficient for the demo. The agent wrapper stubs are in place.
- Segment matching: GPT-4o all-segments strategy for Week 2 (1–5 segments per clip, negligible token cost). Azure AI Search pre-filtering upgrade planned for Week 3. `reason_step()` signature stays the same.

### Notes
- Full test suite: 73 passed, 0 skipped
- Demo target: June 15
- Streamlit UI build starts June 12

---

## Week 3 — Integration, Storage, and Testing

### Planned deliverables
- [ ] Agent 1 / Agent 2 Foundry Agent Service wrappers implemented
- [ ] Cosmos DB persistence: `write_checklist()`, `write_verdict()` in storage clients
- [ ] Blob Storage upload/download: `upload_sop()`, `upload_video()`, `write_keyframe()`
- [ ] Azure AI Search provisioned + `sop_indexer.py` implemented
- [ ] End-to-end test on real Prusa clip with GPT-4o Phase 2 results
- [ ] Verification records retrievable by `run_id`

### Completed
- [ ] ...

### Blockers
- [ ] ...

### Changed from original plan
- [ ] ...

---

## Week 4 — Dashboard + Demo Prep

### Planned deliverables
- [ ] Streamlit dashboard: compliance summary, adherence score, deviation timeline
- [ ] Evidence viewer: keyframe thumbnails + video clip links per deviation
- [ ] Chat interface connected to Agent 3
- [ ] GitHub repository cleaned up with README and architecture documentation
- [ ] Model card written
- [ ] Demo rehearsal completed
- [ ] Known issues documented

### Completed
- [ ] ...

### Blockers
- [ ] ...

### Changed from original plan
- [ ] ...
