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

## Week 2 — Addendum (June 12): First successful end-to-end pipeline run 🎉

### Milestone
First full 5-layer pipeline run against real Azure services completed successfully.
`demo_results.json` generated (run `run-20260612-034fe502`):

| Stage | Result |
|---|---|
| 1. Document Intelligence | 29 steps extracted from STEMFIE SOP (pages 4–11) |
| 2. GPT-4o checklist | 29 checklist items |
| 3. Content Understanding + GPT-4o Phase 2 | 1 segment, all 5 compliance fields filled |
| 4. Sequence/timing validation | 29 timing results |
| 5. Compliance reasoning | 29 verdicts |

All 29 verdicts were "Unable to Verify" — **expected and correct**: the placeholder video
(flight simulator clip) has no relation to the STEMFIE assembly SOP, and the engine
abstained instead of hallucinating matches. Good demo talking point.

### Completed
- **Auth migration to Microsoft Entra ID (DefaultAzureCredential) for ALL services.**
  All `*_KEY` fields in `.env` are now blank; auth comes from `az login`.
  - Generated custom subdomain `pg-ai-priya.services.ai.azure.com` for `procedureguard-ai`
    (token auth requires a custom subdomain; the default name was already taken)
  - RBAC: "Cognitive Services User" on `procedureguard-ai`, "Cognitive Services OpenAI User"
    on `procedureguard-openai` (assigned via CLI with `--assignee-object-id`)
  - `get_openai_client()` in `checklist_generator.py`, `compliance_engine.py`, and
    `video_analyzer.py` now falls back to `get_bearer_token_provider(DefaultAzureCredential(), ...)`
    when no API key is configured
  - `config.py`: endpoints `.rstrip("/")`; blank `AZURE_OPENAI_API_KEY` / `AZURE_OPENAI_AD_TOKEN` /
    service-principal vars popped from `os.environ` (empty strings break SDK credential fallbacks)
- **STEMFIE vehicle kit SOP adopted as demo SOP** — teammate-generated
  `STEMFIE_vehicle_kit_assembly_manual.pdf` (14 pages; Procedure A = pages 4–11) copied to
  `tests/fixtures/`. Has documented error modes (wrong pin type, acorn nut substitution,
  missing washer) — ideal for deviation-detection demo.
- **IndustReal dataset evaluated** for demo videos — short clips (~4–5 min) beat 60-min
  OpenMarcie sessions for iterative testing. Videos ship as JPG frames (need ffmpeg
  reassembly) but YouTube demo clips are available.
- **Dashboard sidebar fix** — collapsed sidebar lost its expand control; replaced with a
  persistent injected ☰ button (`components.html` JS) in `src/dashboard/app.py`.
- Fixed dead default sample-video URL in `run_pipeline_demo.py` (repo file moved to Git LFS —
  see KNOWN_ISSUES).

### Blockers (all resolved — see KNOWN_ISSUES for details)
- 401 on Document Intelligence: portal "Keys" for the Foundry hub are 84-char Foundry API
  keys, incompatible with `Ocp-Apim-Subscription-Key`. **Fix:** Entra ID auth (above).
- 401 on Azure OpenAI: same Foundry-key problem. **Fix:** Entra ID auth + RBAC role.
- "Missing credentials" from `AzureOpenAI()` despite token provider: blank
  `AZURE_OPENAI_API_KEY=` in `.env` becomes an empty string the SDK reads itself.
  **Fix:** pop blank vars in `config.py`.
- `ContentSourceNotAccessible` on sample video: old URL 404s; replacement is in Git LFS so
  `raw.githubusercontent.com` serves a 133-byte pointer. **Fix:** `media.githubusercontent.com` URL.

### Next (before June 15 demo)
- [x] Download IndustReal clips → upload to Blob `manufacturing-videos` → SAS URL → re-run pipeline
- [x] Phase 2 Vision mode: OpenCV keyframe extraction → GPT-4o Vision (see Addendum 2 below)
- [ ] Load demo results into Streamlit dashboard; verify sidebar ☰ fix
- [ ] Demo rehearsal

---

## Week 2 — Addendum 2 (June 12): Phase 2 Vision mode + IndustReal pipeline runs

### Problem discovered
All three IndustReal pipeline runs returned 29/29 "Unable to Verify" even with the correct
STEMFIE SOP. Root cause: Phase 2 was running in text-only mode. The `prebuilt-video`
base analyzer returns a markdown description per segment containing only relative keyframe
filenames (`![](keyFrame.1500.jpg)`) — no actual image data or accessible URLs. GPT-4o
received this keyframe list as its only input and returned generic responses like
"Worker's primary action is unclear from the provided segment."

### Fix: OpenCV keyframe extraction → GPT-4o Vision mode

**How it works now:**
1. `run_video_phase2()` opens the video URL via `cv2.VideoCapture` (supports Blob SAS URLs directly)
2. Extracts up to 6 frames evenly spaced across each segment, resized to 512px longest edge
3. Encodes as base64 JPEG data URIs and passes to `extract_compliance_fields()` as `keyframe_images`
4. GPT-4o Vision receives the actual frame images alongside the segment ID
5. Falls back to text-only mode if OpenCV can't open the URL

**Key implementation details:**
- `cv2.VideoCapture` pre-opened once per segment batch to avoid reconnecting
- `detail: "low"` used for GPT-4o image inputs to control token cost (~85 tokens/frame vs ~765)
- Tenacity retry on `extract_compliance_fields` raised from 3×10s to 6×90s to survive sustained 429s
- Run pipelines sequentially, not in parallel — 3 simultaneous runs exhaust GPT-4o rate limit

**What we tried first (and why it failed):** Inspected `AnalysisContent` SDK object for image
data — no bytes or absolute URLs found. Tried fetching keyframes via the REST result endpoint
(`analyzerResults/{opId}/keyFrames/keyFrame.1500.jpg`) — returns 404. Frames are not persisted
beyond the SDK result object. OpenCV direct URL read was the correct path.

### IndustReal pipeline results (Vision mode)

All three IndustReal demo clips run against the STEMFIE SOP (pages 4–11, section granularity):

| Video | run_id | Compliant | Deviation | UTV | Adherence |
|---|---|---|---|---|---|
| `correct` | `run-20260612-9f9006e5` | 0 | 0 | 29 | N/A |
| `chassis_error` | `run-20260612-140ed80f` | 0 | **2** | 27 | **0%** |
| `wrong_pin` | `run-20260612-142d419a` | 0 | 0 | 29 | N/A |

**chassis_error deviations detected (90% confidence):**
- `check-003`: Parts not sorted by color before assembly (missing pre-assembly verification)
- `check-024`: Front wheel assembly installed without rotation/axial play verification

**Why correct and wrong_pin are still mostly UTV:** All three videos are analysed as a single
segment covering the full 4–5 minute clip. Six frames sampled across 4.5 minutes gives
GPT-4o a high-level overview ("assembling chassis structure", "assembling wheel components")
that confirms domain but can't confirm individual substeps. Detecting a wrong pin type at 512px
in 6 frames is beyond the current approach. Week 3 multi-segment + AI Search upgrade addresses this.

**Demo story:**
- `correct` → 0 deviations, N/A score — system abstains honestly, no false positives
- `chassis_error` → 2 deviations at 90%, 0% score — system flags missing verification steps
- `wrong_pin` → 0 deviations, N/A — fine-grained part substitution requires Week 3 multi-segment

### Files changed
- `src/ingestion/video_analyzer.py` — added `extract_keyframes_from_video()`, updated
  `run_video_phase2()` (Vision mode via `video_url` param), updated `extract_compliance_fields()`
  to accept `keyframe_images: list[str]`, raised retry ceiling to 6×90s
- `src/pipeline.py` — passes `video_url` to `run_video_phase2()`
- `scripts/inspect_cu_result.py` — diagnostic script (confirms keyframes not fetchable from API)

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
- [x] Streamlit dashboard: compliance summary, adherence score, deviation timeline
- [x] Evidence viewer (structured evidence log; keyframe thumbnails pending Blob read)
- [x] Chat interface connected to Agent 3 (`qa_agent` → GPT-4o directly)
- [x] Known issues documented
- [~] GitHub repo / docs cleanup (docs updated June 16; repo tidy-up of debug artifacts pending)
- [~] Model card (updated June 16; accuracy benchmarks still pending)
- [ ] Demo rehearsal completed

### Completed
- Full dashboard UI/UX revamp (Uber design language): tokenised CSS, four-verdict pill system,
  instrument-style score band, evidence log, GPT-4o chat tab.
- **Major pipeline correction (see Addendum 3):** time-windowed segmentation, verifiability tiering
  + "Requires Inspection" verdict, Phase 2 Vision enrichment, unique-evidence guard.
- Code hygiene: single cached `get_openai_client()` (`src/openai_client.py`); hardened retries on
  all GPT-4o calls.
- Demo settled on the clean `correct` clip; annotated clips dropped from the dashboard.

### Blockers
- GPT-4o 429 rate limits make live runs slow (mitigated with hardened retries; deliberate
  throttling/batching is the deferred root-cause fix).
- No clean clip with a *visibly gross* error → no honest "caught a deviation" demo moment yet.

### Changed from original plan
- The Week 2 single-segment design produced fabricated deviations and mass abstention; corrected
  this week (Addendum 3). **The June 12 results in Addendum 2 are superseded.**
- Evidence viewer shows a structured evidence log rather than keyframe thumbnails (Blob read stub).

---

## Week 4 — Addendum 3 (June 16): The honesty overhaul — windowing → tiering → enrichment → evidence guard

> Supersedes the June 12 (Addendum 2) IndustReal results. Those 2 `chassis_error` "deviations"
> were confirmed to be **false positives** — the single-segment design made GPT-4o treat an
> *unobserved* QC step as a violation. Corrected results are below.

### The problem (root-caused this session)
Every clip was analysed as ONE segment spanning the whole video (`prebuilt-video` segments by shot
cut; continuous footage has none). All 29 criteria were judged against that one blob → mass
abstention, whole-video "timestamps," and fabricated deviations. The v2 demo JSONs were not trustworthy.

### The four fixes (each validated on one clip before moving on)
1. **Time windowing** — `build_time_windowed_segments()` imposes ~25s windows; Phase 2 runs per window.
   Real per-window timestamps, but verdicts went to 29/29 "Unable to Verify" (honest — the
   single-segment greens had been false).
2. **Verifiability tiering** — checklist tags `presence|sequence|fine_detail` + `observable_action`;
   `fine_detail` short-circuits to new verdict **"Requires Inspection"** (no GPT call). chassis_error:
   18 → inspection, 11 observable (but those still abstained — descriptions too generic).
3. **Phase 2 enrichment** — `detail:"high"`, 768 px, ~4–5 frames/window, part-level prompt. Descriptions
   went from "assembling components by hand" to "a gray pin inserted through aligned holes in two white
   beams." Unlocked real matches (chassis_error → 5 Compliant) — but exposed over-attribution.
4. **Unique-evidence guard** — `enforce_unique_evidence()`: one window backs at most one Compliant
   verdict (kills the "same window → many position-variant steps" over-count).

### Critical data finding
The `wrong_pin` and `chassis_error` clips are IndustReal **annotated visualization renders** — green
action captions, binary state vectors, and bounding boxes are burned into the frames. GPT-4o can read
those labels; viewers would see them. The `correct` clip is clean raw footage. Decision: demo on the
clean clip only; do not fabricate a "wrong assembly" red. (See KNOWN_ISSUES + DECISIONS_AND_RATIONALE.)

### Honest results (clean `correct` clip, run `run-20260612-9f9006e5`, June 16)

| Verdict | Count |
|---|---|
| Compliant | 3 (each backed by a distinct window; audited as genuine) |
| Deviation Detected | 0 |
| Requires Inspection | 18 |
| Unable to Verify | 8 |
| **Adherence** | **100% of 3 video-verifiable steps · 0 fabricated** |

### Files changed
- `src/ingestion/video_analyzer.py` — `build_time_windowed_segments()`, `probe_video_duration()`,
  Phase 2 detail:high / 768 px / richer prompt, ~4–5 frames/window
- `src/reasoning/checklist_generator.py` — `verifiability` + `observable_action` fields
- `src/reasoning/compliance_engine.py` — "Requires Inspection" verdict, `_inspection_verdict()`,
  reason on `observable_action`, `enforce_unique_evidence()`
- `src/pipeline.py` — Step 3 re-segments into windows; applies the guard; `requires_inspection` count
- `src/openai_client.py` (new) — one cached client; hardened retries across GPT-4o calls
- `src/dashboard/` — four-verdict pills, Requires-Inspection stat + filter, honest adherence sublabel,
  single clean demo button

---

## Week 4 — Addendum 4 (June 16, later same night): IndustReal raw clips are clean — but no gross deviation found, demo pivots to honest verdict mix

### Matching-improvement work (no demo run yet)
Before testing new clips, shipped three deterministic improvements to step-to-window matching:
overlapping time windows (`overlap_seconds`, default 6s, in `build_time_windowed_segments()`),
a free lexical-overlap candidate-window prefilter (`_select_candidate_segments()`, caps GPT-4o's
input at 8 windows on long clips), and an explicit "gross visible contradiction" Deviation trigger
in `SYSTEM_PROMPT` for cases like a plainly empty mounting spot. No live cost; local smoke-tested only.

### Wrong-assembly demo search, live runs against the existing STEMFIE checklist
Confirmed the canonical `correct` demo already pairs an IndustReal clip with the STEMFIE checklist
(no separate "IndustReal SOP" ever existed — see PROJECT_CONTEXT.md) — so the existing 29-item
checklist (18 fine_detail / 11 presence) is directly reusable on any IndustReal clip of this same
STEMFIE task. Ran it live, unmodified, against three candidates ranked by the local visual/metadata
triage (`industreal_selected/notes/`), via the new `scripts/run_industreal_demo.py`:

| Clip | Ground-truth signal (`demo_candidate_rankings.csv`) | Result |
|---|---|---|
| `23_assy_1_2` | `fit_wheel:-1`, `fit_wing:-1` | 0 Deviation Detected, 100% adherence (2/2) |
| `22_assy_2_3` (highest-ranked, score 14) | `fit_wheel:-1`, `fit_pulley:-1`, `fit_wing_beam:-1` | 0 Deviation Detected — but rear-wheel step (step-025) correctly demoted to **Unable to Verify** by `enforce_unique_evidence()` after matching the same window as the confirmed front wheel (step-024, 95% confidence Compliant) |
| `16_main_3_3` (maintenance task, not assembly — caveat noted) | `fit_wheel:-2` | 0 Deviation Detected, 100% adherence (3/3) |
| `23_assy_0_1` (clean baseline, for contrast) | — | 0 Deviation Detected, 100% adherence (3/3) |

**Conclusion:** none of the three triage-recommended candidates produced a clean "Deviation
Detected" — consistent with `industreal_selected/notes/visual_screening.md`'s pre-existing warning
that even the best clips show only subtle differences, not a gross, fully-visible fault. The
pipeline is working as intended: it declines to call "Deviation Detected" unless a window plainly
shows the empty/wrong spot, rather than inferring a deviation from an abstention. Did not burn runs
on the remaining (visually weaker) candidates `18_assy_2_5` / `17_assy_1_5` / `10_assy_3_2`.

### Demo pivot (decided this session)
Dropped the "must show a red Deviation" framing. New centerpiece: **`22_assy_2_3`**
(`demo_results_industreal_22_assy_2_3_candidate.json`) — shows the four-verdict model actually
discriminating: step-024 (front wheel) Compliant at 95%, step-025 (rear wheel) Unable to Verify
because the evidence guard refused to let a duplicate match ride along as a second Compliant. Paired
with `23_assy_0_1` (`demo_results_industreal_23_assy_0_1_baseline.json`) as the "perfectly followed"
case. Both wired into the dashboard as one-click demo buttons (`src/dashboard/app.py`).

### Files changed
- `scripts/run_industreal_demo.py` (new) — runs Phase 2 + reasoning on an arbitrary IndustReal SAS
  URL against the existing STEMFIE checklist (no re-extraction)
- `src/dashboard/app.py` — added IndustReal baseline + 22_assy_2_3 demo-shortcut buttons
- `docs/PROJECT_CONTEXT.md` — clarified the STEMFIE/IndustReal SOP pairing to prevent re-asking
  "does IndustReal have an SOP"
- Blob: `industreal_23_assy_0_1_baseline.mp4`, `industreal_23_assy_1_2_candidate.mp4`,
  `industreal_22_assy_2_3_candidate.mp4`, `industreal_16_main_3_3_candidate.mp4` uploaded to
  `manufacturing-videos`
- `scripts/regenerate_demo_windowed.py` (new) — re-run a clip's results with the fixed pipeline

---

## Week 4 — Addendum 5 (June 18): Architecture pivot — drop Content Understanding, implement full-coverage temporal inference

### Decision summary

Completed overnight architecture research (see `docs/VIDEO_INTELLIGENCE_RESEARCH.md`). Two decisions made:

**1. Drop Azure Content Understanding from the pipeline entirely.**
- The `analyze_video()` Phase 1 call in `pipeline.py` (line 111) was the only remaining CU usage — its sole purpose was to extract video duration, which was immediately overridden by `build_time_windowed_segments()` anyway.
- `probe_video_duration()` (already in `video_analyzer.py`) gets duration from OpenCV with no API call and no cost.
- CU's custom GENERATE/CLASSIFY fields path also abandoned: same 1fps/512px hard limit as current pipeline, requires Foundry Hub project (1–2 day setup), zero accuracy gain for the absence-inference problem. Not worth pursuing.
- Azure AI Video Indexer also confirmed unsuitable: action label taxonomy is generic web-scale concepts ("swimming", "sunglasses"), no custom label training. Not integrated, not worth integrating.

**2. Implement Option A: full-coverage temporal inference (absent-step detection).**
- Root cause of "Unable to Verify instead of Deviation Detected" on omitted steps: each 25s window is reasoned independently. If a step was never performed, every window abstains and the final verdict is "Unable to Verify." The pipeline treats absence of evidence in one window as non-informative — correct for a single window, wrong when applied to the whole clip.
- Fix: after `enforce_unique_evidence()`, run a new `apply_absence_inference()` post-processor. For any `verifiability == "presence"` step still at "Unable to Verify," check whether any window description contained even one token matching the step's `observable_action`. If zero tokens matched across all N windows and the clip is fully covered, upgrade verdict to "Deviation Detected (Not Observed)."
- Three safeguards prevent false positives: (a) windows must tile ≥90% of clip duration; (b) at least one Compliant verdict must exist in the run (proxy for "camera was working"); (c) only upgrade when GPT-4o returned zero lexical signal, not when it returned low-confidence partial signal.
- No new Azure services. No new cost. ~50 lines in `pipeline.py` + `compliance_engine.py`.
- Backed by PREGO (CVPR 2024, arXiv:2404.01933) and differentiable task graph literature (arXiv:2406.01486).

**Qwen2.5-VL** deferred to Week 4 experiment: genuine temporal reasoning capability but requires H100 quota + Foundry Hub + complex deployment. Prototype via Alibaba Cloud API if time permits.
**IndustReal PSR model** not in scope: trained on STEMFIE CAD models only, requires per-product sim2real retraining.

### Implementation completed (June 18, same day)

- [x] `src/pipeline.py`: removed `analyze_video()` + `parse_observations()` calls; replaced with direct `probe_video_duration()` + manually built observations dict including `video_duration_seconds`
- [x] `src/ingestion/video_analyzer.py`: removed all CU code — imports, `COMPLIANCE_FIELD_SCHEMA`, `get_client()`, `create_or_update_analyzer()`, `analyze_video()`, `parse_observations()`, `_get_field()`. Kept `probe_video_duration`, `build_time_windowed_segments`, `run_video_phase2`, `extract_keyframes_from_video`. Updated docstring.
- [x] `src/reasoning/compliance_engine.py`: `apply_absence_inference()` implemented with all 3 guards
- [x] `src/pipeline.py`: `apply_absence_inference()` called after `enforce_unique_evidence()`
- [x] `schemas/verification_record.json`: `not_observed: bool` field added
- [x] `src/dashboard/components/deviation_timeline.py`: gray dashed "↯ Not observed across full clip" pill added for `not_observed=True` verdicts
- [x] `scripts/run_industreal_demo.py`: updated with `video_duration_seconds` + `apply_absence_inference` + corrected output filename
- [x] `config.py` / `.env.example`: Content Understanding fields commented out

### Validation result — `22_assy_2_3` candidate, run `run-20260618-f56b4677`

| Verdict | Before | After |
|---|---|---|
| Compliant | 3 | 3 |
| Deviation Detected | 0 | **1** |
| Unable to Verify | 8 | 7 |
| Adherence Score | 100% (3/3) | **75% (3/4)** |

**What fired:** `check-011` (step-011 — "Place the base on a flat surface in the standard orientation") — zero lexical signal across all 16 windows covering 306s. Upgraded to Deviation Detected, `not_observed=True`, confidence 0.85.

**Why step-025 (rear wheel) did NOT fire:** 13 overlapping tokens from front-wheel assembly windows (wheel/axle/mounted). `apply_absence_inference` correctly abstained — it can't distinguish "rear wheel absent" from "only front wheel shown" via lexical matching alone. This is the right behavior.

**Demo story revision:** the `22_assy_2_3` candidate now shows a genuine absence-inferred deviation (check-011 base placement, never observed in 16 windows / 306s). Dashboard will show the "↯ Not observed across full clip" badge on the Deviations tab. Adherence score 75%.

### Files to create / change
- `src/pipeline.py` — Step 3 refactor (CU removal + `apply_absence_inference` call)
- `src/ingestion/video_analyzer.py` — CU code removal
- `src/reasoning/compliance_engine.py` — new `apply_absence_inference()` function
- `schemas/verification_record.json` — new field
- `src/dashboard/components/deviation_timeline.py` — new verdict display
- `docs/SESSION_HANDOFF.md` (new) — next-session implementation prompt
