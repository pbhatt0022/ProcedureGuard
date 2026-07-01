# ProcedureGuard — Known Issues and Gotchas

> Log every bug, Azure quirk, and unexpected constraint here with its fix or workaround.
> This saves the whole team time — if you hit it once, log it.

---

## Template

```
## [Short title]
**Symptom:** What you observed
**Root cause:** Why it happened (if known)
**Fix / workaround:** What resolved it
**Affected component:** Which layer / service / file
**Date found:** Week X
**Source:** Doc URL or Stack Overflow link if applicable
```

---

## Pre-populated known constraints (from documentation research)

---

## Phase 2 vocabulary can't distinguish the rear pulley from other pink connectors
**Symptom:** Absence inference for check-025 ("install pulley on rear axle first") with `key_objects=["pulley"]` correctly flags the missing-pulley clip (22_assy_2_3) but ALSO false-positives on the clean baseline (23_assy_0_1). Both clips end at identical adherence scores.
**Root cause:** GPT-4o Vision Phase 2 describes the STEMFIE pulley as "pink connector" / "pink axle connector" in BOTH correct and incorrect clips — at overhead resolution the flat pink pulley is visually indistinguishable from the other pink connectors in the kit. So the token "pulley" appears in no window for either clip, and `apply_absence_inference` cannot tell "pulley genuinely absent" from "pulley present but described generically."
**Fix / workaround:** `key_objects` cleared to `[]` on check-025 for now (disables the detection rather than emit a false alarm on good work — see DECISIONS_AND_RATIONALE.md). Real fix (Week 3): checklist-aware Phase 2 that asks a targeted question per discriminating part ("is a flat pink disk/pulley seated on the rear axle before the wheel?") instead of a generic description, gated by `scripts/eval_harness.py` showing recall up without precision down.
**Affected component:** Layer 2 — Phase 2 GPT-4o Vision (`video_analyzer.py`); Layer 3 — `apply_absence_inference` (`compliance_engine.py`)
**Date found:** Week 4 (June 18)

---

## Front vs rear axle are indistinguishable from overhead → wheel-step false negatives
**Symptom:** Eval harness shows 3 false negatives, all on check-024 (front wheel) / check-025 (rear wheel): clips with a missing wheel (23_assy_1_2, 16_main_3_3) get "Compliant" because a wheel IS seen elsewhere in the clip.
**Root cause:** Overhead video can't reliably tell which axle (front vs rear) a wheel is being mounted on; `reason_step` sees *a* wheel-mount window and matches it to the step. The positional discriminator ("front"/"rear") is not visually resolvable.
**Fix / workaround:** Honest current behaviour — `enforce_unique_evidence` prevents one window backing both steps, so at most one wheel step goes green. Full resolution needs positional reasoning (which end of the frame / order relative to other parts) — Week 3 sequence-aware matching. Tracked quantitatively in `scripts/eval_harness.py` (Recall 25%, Precision 100% as of June 18).
**Affected component:** Layer 3 — `reason_step` (`compliance_engine.py`)
**Date found:** Week 4 (June 18)

---

## Content Understanding removed from the codebase (June 18) — CU entries below are historical
**Symptom:** N/A — informational. The CU-related entries that follow describe a component no longer in the pipeline.
**Root cause:** CU contributed no usable output for single-take assembly footage (0-segment custom fields; one segment from prebuilt-video; inaccessible keyframe URLs). See DECISIONS_AND_RATIONALE.md "Remove Azure AI Content Understanding entirely".
**Fix / workaround:** Duration via OpenCV `probe_video_duration()`; segments via `build_time_windowed_segments()`; fields via GPT-4o Vision. The CU entries below are retained for history and for anyone evaluating CU on different footage.
**Affected component:** Layer 2 — video pipeline
**Date found:** Week 4 (June 18)

---

## Content Understanding: fields return null on very short clips
**Symptom:** Custom `fieldSchema` fields all return null or empty when video clip is very short
**Root cause:** Generative field extraction requires enough visual context per segment — very short clips (under ~15 seconds) may not provide enough frames
**Fix / workaround:** Ensure test clips are at least 30 seconds; for production, minimum segment length ~15 seconds
**Affected component:** Layer 2 — Content Understanding video analyzer
**Date found:** Pre-build (anticipated from docs)
**Source:** https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/service-limits

---

## Content Understanding: fine motor actions may not be detected
**Symptom:** `component_contact` or `tool_in_use` fields return vague or incorrect values for close-up assembly actions
**Root cause:** Service analyzes ~1 frame per second and scales all frames to 512×512 px — small parts, precise tool contact, and sub-second actions are genuinely hard to observe at this resolution
**Fix / workaround:** (1) Broaden field descriptions to ask for general action category not precise contact point; (2) Classify steps that require fine motor precision as "Unable to Verify" by default; (3) Consider supplementing with audio transcript cues where worker narrates actions
**Affected component:** Layer 2 — Content Understanding; Layer 3 — Agent 2 confidence threshold
**Date found:** Pre-build (from documentation and service limits)
**Source:** https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/service-limits

---

## Content Understanding: binary upload fails for IndustReal clips
**Symptom:** `analyzeBinary` API returns 413 or timeout for full IndustReal session videos
**Root cause:** Binary upload limited to 200 MB and 30 minutes. IndustReal sessions exceed this.
**Fix / workaround:** Upload video to Azure Blob Storage first, then pass the Blob SAS URL to the `analyze` API (URL reference method). Limit: 4 GB / 2 hours via URL.
**Affected component:** Layer 2 — Content Understanding pipeline code
**Date found:** Pre-build (from service limits docs)
**Source:** https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/service-limits

---

## Foundry Agent Service: portal instability
**Symptom:** Agent project opens fine, then on re-login the schema or analyzer connection is missing
**Root cause:** Known portal instability reported in Microsoft Q&A (Dec 2025)
**Fix / workaround:** (1) Keep all analyzer definitions as JSON files in source control; (2) Re-connect resource if connection disappears; (3) Keep a fallback Python orchestration script that replicates Agent 2 logic without Foundry Agent Service in case portal is unstable during demo week
**Affected component:** Layer 3 — Foundry Agent Service
**Date found:** Pre-build (from Microsoft Q&A reports)
**Source:** https://learn.microsoft.com/en-us/answers/questions/5653494/azure-content-understanding-is-generally-available

---

## Cosmos DB: missing run_id partition key causes query failures
**Symptom:** Agent 3 MCP queries return no results or cross-partition scan errors
**Root cause:** All Cosmos DB documents must include `run_id` as the partition key — documents inserted without it land in the wrong partition
**Fix / workaround:** Enforce `run_id` as a required field in all write functions; add assertion before every Cosmos DB write
**Affected component:** Layer 4 — Cosmos DB; Layer 3 — Agents 1 and 2 write paths
**Date found:** Pre-build (anticipated)

---

## Content Understanding: analyzer ID cannot contain hyphens
**Symptom:** `create_or_update_analyzer()` returns HTTP 400 `InvalidAnalyzerId: The 'analyzerId' cannot contain '-'`
**Root cause:** The Content Understanding API (2025-11-01 GA) does not allow hyphens in custom analyzer IDs. Only alphanumeric characters and underscores are accepted.
**Fix / workaround:** Use underscores: `procedureguard_compliance_v1` not `procedureguard-compliance-v1`. Updated in `.env` and `config.py` default.
**Affected component:** Layer 2 — `video_analyzer.py`, `.env`, `config.py`
**Date found:** Week 1 (smoke test run)

---

## Content Understanding: `models` parameter not supported on standalone AIServices resources
**Symptom:** `create_or_update_analyzer()` returns HTTP 400 when `ContentAnalyzer` is constructed with `models={"completion": "gpt-4.1"}`
**Root cause:** The `models` parameter requires a full Azure AI Foundry project with explicit model deployments. Standalone `AIServices` resources (kind=AIServices, no custom subdomain) use service-managed models and reject explicit model references.
**Fix / workaround:** Remove the `models` parameter from `ContentAnalyzer`. The service uses its own managed GPT deployment automatically for GENERATE fields.
**Affected component:** Layer 2 — `video_analyzer.py`
**Date found:** Week 1 (smoke test run)

---

## Content Understanding: GitHub raw URLs blocked (ContentSourceNotAccessible)
**Symptom:** HTTP 400 `ContentSourceNotAccessible` when passing a `github.com/raw/...` or `raw.githubusercontent.com` URL to the analyze API
**Root cause:** GitHub CDN appears to block or restrict requests from Azure service IP ranges. The Content Understanding service cannot download the video from GitHub-hosted URLs.
**Fix / workaround:** Upload all test videos to Azure Blob Storage first and pass a SAS URL instead. Do not use GitHub URLs for Content Understanding inputs.
**Affected component:** Layer 2 — `video_analyzer.py`; `scripts/test_video_pipeline.py` default URL
**Date found:** Week 1 (smoke test run)
**Update (Week 2, June 12):** Not universally true — `media.githubusercontent.com` (the Git LFS media host) worked fine on the June 12 E2E run. The Week 1 failures may have been the LFS-pointer problem below rather than IP blocking. Blob SAS URLs remain the reliable path for real demo videos.

---

## ~~AIServices resource: no custom subdomain, token auth unavailable~~ — RESOLVED Week 2
**Symptom:** `DefaultAzureCredential` fails with HTTP 400 `BadRequest: Please provide a custom subdomain for token authentication`. DNS resolution fails for both `<name>.cognitiveservices.azure.com` and `<name>.services.ai.azure.com`.
**Root cause:** The `procedureguard-ai` resource was created without a custom subdomain (`customSubDomainName: null`). The only available endpoint was the regional one (`https://eastus.api.cognitive.microsoft.com/`), which only accepts API key auth.
**Fix / workaround:** **RESOLVED (Week 2, June 12):** Generated custom subdomain via the portal's "Generate Custom Domain Name" button. The default name `procedureguard-ai` was already taken globally (DNS-nonexistent but reserved by another tenant) — generated **`pg-ai-priya`** instead. Endpoint is now `https://pg-ai-priya.services.ai.azure.com` and `DefaultAzureCredential` token auth works for both Document Intelligence and Content Understanding. Requires "Cognitive Services User" RBAC role (see Foundry-keys entry below).
**Affected component:** Layer 2 — `video_analyzer.py`, `sop_extractor.py`, `.env`
**Date found:** Week 1 (smoke test run) · **Resolved:** Week 2 (June 12)
**Source:** `az cognitiveservices account show --query properties.customSubDomainName`

---

## OpenMarcie dataset: curl downloads fail mid-way with connection reset
**Symptom:** `curl.exe -u reviewer:1234 -O <url>` repeatedly fails with `curl: (56) Recv failure: Connection was reset` after downloading 30–60% of the file. Resuming with `-C -` also eventually resets. Downloading into OneDrive (`C:\Users\...\OneDrive\...`) makes this worse — OneDrive tries to sync the partial file while it is being written, which triggers additional connection resets.
**Root cause:** DFKI server (`projects.dfki.uni-kl.de`) is slow (~350–680 KB/s) and drops long-running single TCP connections. Single-connection curl cannot recover cleanly. Downloading to OneDrive adds file-locking contention on top of the network instability.
**Fix / workaround:** Use **aria2c** with 8 parallel connections and automatic retry. Download to a local non-OneDrive path (e.g. `C:\Users\priya\Downloads`). aria2c writes a `.aria2` control file alongside the zip — do not delete it mid-download or resume will restart from zero.
```powershell
cd C:\Users\priya\Downloads
aria2c.exe `
  --http-user=reviewer --http-passwd=1234 `
  --split=8 --max-connection-per-server=8 --min-split-size=50M `
  --max-tries=0 --retry-wait=10 --continue=true `
  "https://projects.dfki.uni-kl.de/open-marcie/3DPrinterExperiment/Vol2/Wearables/EgoZedVideo_Vol2.zip"
```
**Affected component:** Dataset acquisition — OpenMarcie Scenario B (applies to all Vol{N} zips)
**Date found:** Week 1

---

## Content Understanding: GENERATE/CLASSIFY fields return 0 segments on standalone AIServices resource
**Symptom:** Custom analyzer with `GENERATE` or `CLASSIFY` fields returns `result.contents = []` (0 segments, no errors, no warnings) even for a 5-minute video that `prebuilt-video` correctly returns 1 segment for. Reproducible with a single-field minimal schema too.
**Root cause:** `GENERATE`/`CLASSIFY` methods internally invoke Azure OpenAI to fill field values. On a standalone `AIServices` resource (`kind: AIServices`, no custom subdomain, regional endpoint `https://eastus.api.cognitive.microsoft.com/`), there is no Azure OpenAI deployment linked — the service silently drops all segments rather than returning them with null fields.
**Fix / workaround:** Two options:
  1. *(Long-term)* Provision a proper Azure AI Foundry project hub with GPT-4o or GPT-4.1 deployed and link it to the analyzer via the `models` parameter on `ContentAnalyzer`.
  2. *(Current MVP workaround)* Use `prebuilt-video` base directly (no custom field schema). This returns segments with keyframe timestamps. Run a separate GPT-4o vision pass on keyframes to extract compliance fields.
**Affected component:** Layer 2 — `video_analyzer.py` (`analyze_video`, `create_or_update_analyzer`); custom `procedureguard_compliance_v1` analyzer
**Date found:** Week 1 (smoke test diagnostic)
**Diagnosed via:** `scripts/diagnose_video.py` — Tests 3/4/5 (custom fields) return 0 segments; Test 2 (prebuilt-video) returns 1 segment for same video.

---

## Prusa manual PDF: TOC spans 10+ pages and pollutes extracted steps
**Symptom:** `extract_sop_steps` on pages 1–15 of the Prusa manual returned 373 "steps" that were actually table-of-contents entries ("Step 1 - All the required tools are included", etc.)
**Root cause:** The manual's TOC lists every step title across ~13 pages. Layout model correctly returns them as body paragraphs, so the paragraph-level parser turned each into a step.
**Fix / workaround:** `parse_sop_steps` now skips body content under any section heading matching `table of contents|contents|index` (`_NON_PROCEDURE_SECTION_RE` in `sop_extractor.py`). Verified: same page range now yields only real instruction content.
**Affected component:** Layer 2 — `sop_extractor.py`
**Date found:** Week 1 (SOP smoke test)

---

## Prusa manual PDF: web-generated, contains web-page furniture in extracted text
**Symptom:** Some extracted steps contain text like "Contact us English Currency : CZK ¥ Sign In" or cover-page text ("PRUSA RESEARCH by JOSEF PRUSA"). Icon glyphs also leak in as stray characters (") No soldering is required. i").
**Root cause:** The official PDF (`help.prusa3d.com/wp-content/uploads/generated/...`) is generated from the web guide, so promo pages and site chrome are real page content — Layout extracts them faithfully.
**Fix / workaround:** Accepted for v1 — Agent 1 (checklist generator, GPT-4o) filters non-procedural text when building the compliance checklist. If it becomes a problem, add noise patterns to the skip logic or restrict page ranges to assembly chapters.
**Affected component:** Layer 2 — `sop_extractor.py`; Layer 3 — Agent 1 prompt
**Date found:** Week 1 (SOP smoke test)

---

## Foundry hub "Keys and Endpoint" keys are NOT Cognitive Services keys (401 everywhere)
**Symptom:** HTTP 401 `PermissionDenied` from Document Intelligence, and 401 from Azure OpenAI, when using the keys shown on the `procedureguard-ai` portal "Keys and Endpoint" page. The keys are 84 characters long (standard Cognitive Services keys are 32).
**Root cause:** `procedureguard-ai` is an AI Foundry hub (Kind: AIServices). Its portal keys are **Foundry API keys** — they work with the Foundry/OpenAI-style `api-key` header on Foundry endpoints, but are rejected by the Document Intelligence SDK (`Ocp-Apim-Subscription-Key`) and by the separate `procedureguard-openai` resource.
**Fix / workaround:** Don't use the 84-char keys at all. Authenticate with Microsoft Entra ID (`DefaultAzureCredential` via `az login`):
  1. Custom subdomain required for token auth → `https://pg-ai-priya.services.ai.azure.com`
  2. RBAC roles: "Cognitive Services User" on `procedureguard-ai`; "Cognitive Services OpenAI User" on `procedureguard-openai`
  3. Personal Outlook accounts aren't resolvable by email in AAD graph — use `--assignee-object-id $(az ad signed-in-user show --query id -o tsv)` with `--assignee-principal-type User`
  4. Leave all `*_KEY` fields blank in `.env`; clients fall back to `DefaultAzureCredential` automatically
**Affected component:** All Azure auth — `config.py`, `sop_extractor.py`, `video_analyzer.py`, `checklist_generator.py`, `compliance_engine.py`
**Date found:** Week 2 (June 12) — cost roughly a full session of debugging; do not re-litigate

---

## AzureOpenAI SDK: empty-string AZURE_OPENAI_API_KEY breaks token auth ("Missing credentials")
**Symptom:** `AzureOpenAI(azure_ad_token_provider=...)` raises `OpenAIError: Missing credentials. Please pass an api_key...` even though a valid token provider is passed. Works in an isolated shell, fails in the pipeline.
**Root cause:** `.env` contained `AZURE_OPENAI_API_KEY=` (blank). `load_dotenv()` puts the **empty string** into `os.environ`. `AzureOpenAI.__init__` reads that env var itself when `api_key` isn't passed — the empty string is "present but falsy", so it bypasses the token-provider sentinel path and the parent `OpenAI.__init__` rejects the falsy key. (Verified against openai 2.41.0 source.)
**Fix / workaround:** `config.py` pops blank `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_AD_TOKEN` from `os.environ` after `load_dotenv()` (same treatment as the blank service-principal vars for `EnvironmentCredential`). Rule of thumb: **a blank env var is not the same as an absent one** — SDKs that read `os.environ` directly will trip on empty strings.
**Affected component:** `config.py`; all three `get_openai_client()` call sites
**Date found:** Week 2 (June 12)

---

## Azure-Samples sample video moved to Git LFS — raw URL serves a text pointer
**Symptom:** Pipeline default video URL fails: first 404 (file renamed), then after fixing the name, Content Understanding returns `ContentSourceNotAccessible`.
**Root cause:** The repo replaced `data/sample_video.mp4` with `data/FlightSimulator.mp4` stored in **Git LFS**. `raw.githubusercontent.com` serves the 133-byte LFS pointer file (`text/plain`), not the video. Content Understanding downloads the pointer text and rejects it.
**Fix / workaround:** Use the LFS media host: `https://media.githubusercontent.com/media/Azure-Samples/azure-ai-content-understanding-python/main/data/FlightSimulator.mp4` (serves the real 38.6 MB binary). Updated as the default in `scripts/run_pipeline_demo.py`. Diagnostic tip: `curl -sI <url>` — `Content-Length: 133` + `text/plain` = LFS pointer.
**Affected component:** `scripts/run_pipeline_demo.py` default `SAMPLE_VIDEO_URL`
**Date found:** Week 2 (June 12)

---

## Streamlit: collapsed sidebar loses its expand control
**Symptom:** With custom CSS theming active, collapsing the dashboard sidebar leaves no visible way to expand it again — the `collapsedControl` element is hidden/unstyled.
**Root cause:** Streamlit's built-in expand chevron is fragile under custom CSS and its test-ids change between versions.
**Fix / workaround:** Inject a persistent ☰ button into the parent page DOM via `components.html` JS (`id="pg-menu-btn"`, fixed top-left). Click handler tries `collapsedControl`, then `stSidebarCollapseButton`, then the first sidebar button. A `MutationObserver` re-creates the button if Streamlit re-renders the DOM.
**Affected component:** Layer 5 — `src/dashboard/app.py`
**Date found:** Week 2 (June 12)

---

## Phase 2 text-only mode: keyframes not accessible from Content Understanding result
**Symptom:** Phase 2 GPT-4o returns generic responses ("Worker's primary action is unclear",
`tool_in_use: null`, `component_contact: null`) even when the correct SOP-video pair is used.
All verdicts return "Unable to Verify".
**Root cause:** The `prebuilt-video` base analyzer returns a markdown description per segment
containing only relative keyframe filenames (`![](keyFrame.1500.jpg)`) — not absolute URLs.
These are internal references with no backing storage accessible after the result is returned:
- `GET analyzerResults/{opId}/keyFrames/keyFrame.1500.jpg` → 404
- `GET analyzerResults/{opId}/contents/0/keyFrames/...` → 404
- `AnalysisContent.key_frame_times_ms` → `None` (not populated by base analyzer)
GPT-4o received a list of keyframe filenames as text input and correctly abstained.
**Fix / workaround:** Use OpenCV (`cv2.VideoCapture`) to open the video URL directly (supports
Blob SAS URLs). Extract frames at evenly-spaced timestamps, resize to 512px, encode as base64
JPEG data URIs, pass to GPT-4o Vision. Implemented in `run_video_phase2(video_url=...)` and
`extract_compliance_fields(keyframe_images=[...])` in `video_analyzer.py`.
**Affected component:** Layer 2 — `video_analyzer.py`; Layer 3 — `pipeline.py`
**Date found:** Week 2 (June 12)

---

## GPT-4o 429 RateLimitError exhausts tenacity retries on concurrent pipeline runs
**Symptom:** `tenacity.RetryError` wrapping `openai.RateLimitError` when multiple pipeline runs
are executing in parallel. The `@retry(stop=stop_after_attempt(3), wait=wait_exponential(max=10))`
decorator on `extract_compliance_fields` runs out of attempts (3 × 10s = 30s total) before the
rate limit window clears. The OpenAI SDK's own internal retry also can't recover in this window.
**Root cause:** Three simultaneous pipeline runs each make 30 GPT-4o calls (1 Phase 2 + 29
reasoning steps) = 90 concurrent requests hitting the same deployment. Combined with high-detail
Vision images per call, token rate is exceeded.
**Fix / workaround:**
  1. Run pipeline instances sequentially, not in parallel
  2. Raised tenacity ceiling: `stop_after_attempt(6)`, `wait_exponential(multiplier=2, min=5, max=90)`
     — allows up to ~5 minutes of retries per call to survive sustained rate-limit windows
**Affected component:** `src/ingestion/video_analyzer.py` `extract_compliance_fields` retry decorator
**Date found:** Week 2 (June 12)

---

## Content Understanding: prebuilt-video returns ONE segment for continuous footage → mass abstention + fake timestamps
**Symptom:** Every demo clip was analysed as a single segment spanning the whole 4–5 min video. All 29 SOP criteria were then judged against that one undifferentiated blob, so ~27–29 steps came back "Unable to Verify" and the few verdicts that did render cited the entire clip (e.g. `0.0s–263.0s`) as their "evidence." The June 12 `chassis_error` run even produced 2 "Deviation Detected" verdicts later confirmed to be **false positives** — GPT-4o treating *absence* of an observed QC step as a violation.
**Root cause:** `prebuilt-video` segments by shot/scene cut. Continuous single-take assembly footage has no cuts, so it correctly returns one segment for the whole clip — which silently destroys the evidence-localization the pipeline depends on.
**Fix / workaround:** Stop relying on shot-cut segmentation. `build_time_windowed_segments()` (`video_analyzer.py`) imposes fixed ~25s time windows over the clip duration; `run_video_phase2()` runs the GPT-4o Vision pass per window. `pipeline.py` Step 3 re-segments into windows before Phase 2. Each verdict now localizes to a tight ~25s slice. `probe_video_duration()` (OpenCV) is the duration fallback when Content Understanding reports no usable bounds.
**Affected component:** Layer 2 — `video_analyzer.py`; Layer 3 — `pipeline.py`
**Date found:** Week 4 (June 16)

---

## IndustReal demo clips ship with ground-truth labels burned into the video
**Symptom:** Frames from the `wrong_pin` and `chassis_error` clips have a green action caption (e.g. "Install front chassis pin"), a binary assembly-state vector (e.g. `11110110000`), and a bounding box rendered directly into the picture. The `correct` clip is clean raw footage.
**Root cause:** Those two clips are IndustReal's **annotated visualization renders**, not the raw egocentric recordings — the labels are part of the Procedure-Step-Recognition demo output.
**Impact (demo integrity):** GPT-4o Vision sees those captions, so verdicts on those clips may be reading the answer key rather than observing the assembly — and any demo audience sees the labels on screen. Disqualifying for a "we don't fabricate" tool.
**Fix / workaround:** Demo on the **clean `correct` clip only**; the two annotated clips were dropped from the dashboard. A real "wrong assembly" demo needs clean (unlabeled) footage with a *grossly visible* error — the planted faults here (wrong-LENGTH pin) are not resolvable at 1 fps / 768 px anyway (even IndustReal's own model "does not see error in front chassis"). Inspect frames with OpenCV (no GPT cost) before trusting any error clip.
**Affected component:** Demo data — `demo_results_{wrong_pin,chassis_error}_*.json`; dashboard demo buttons
**Date found:** Week 4 (June 16)
**Source:** https://github.com/timschoonbeek/industreal

---

## Deterministic baseline-diff (window-count signature) cannot recover part counts — abandoned
**Symptom:** A "baseline-diff" pass (`action_signature.py` + `apply_baseline_diff`) reduced each run to a per-action count = number of Phase-2 windows mentioning that action, then flagged a checklist item when a *stable* action's count dropped to ≤50% of a known-good 3-run baseline. Proof run on 3 clips (June 22): it fired **zero** deltas and gave **zero** recall on the count error.
**Root cause:** Window-count is not a proxy for part-count. The baseline clip (23_assy_0_1) yielded 6 wheel-windows; the count-error clip 23_assy_1_2 (GT `fit_wheel:-1`, one *fewer* wheel) yielded **9** — *more*, not fewer. Window count tracks camera dwell time and VLM verbosity, not how many wheels were mounted. No threshold recovers a −1 error from a signal that moves the wrong direction.
**Fix / workaround:** Approach abandoned and code deleted (the deterministic text-signature path can't recover counts — the signal isn't in the VLM narration). The real fix is per-component perception: IndustReal's **Assembly State Detection** model emits a per-component `1/-1/0` state vector (correctly/incorrectly/not assembled) — that IS the count/state signal. Apache-2.0, PyTorch weights published; Phase 3-B deploy on Azure ML. Do NOT reintroduce a count proxy from VLM text, and do NOT lower the drop ratio to manufacture recall (honesty principle: zero false alarms > recall).
**Evidence retained:** `experiments/sop_gt/proofrun_*.json` + `proofrun.log` (the three measured runs).
**Affected component:** Layer 3 — was `src/reasoning/action_signature.py`, `apply_baseline_diff` in `compliance_engine.py`, `--baseline-signature` in `scripts/validate_error_clip.py` (all removed)
**Date found:** Week 4 (June 22)
**Source:** https://github.com/TimSchoonbeek/IndustReal · weights: https://data.4tu.nl/datasets/b008dd74-020d-4ea4-a8ba-7bb60769d224

---

## IndustReal ASD ontology has no wing-beam or pulley class
**Symptom:** With `USE_ASD_PERCEPTION=true`, check-004 (wing beam) and check-006 (pulley) always return Unable to Verify, even when those parts are genuinely present or genuinely missing.
**Root cause:** The ASD model detects 11 components (base / front+rear chassis / pins / front bracket + screw / front+rear wheel assemblies) — there is no wing-beam class, and the pulley is bundled inside the "rear wheel assembly" component so it can't be isolated. Mapping check-004→bracket or check-006→rear-wheel would falsely confirm the wrong part, so `asd_mapping.py` deliberately does not emit them.
**Fix / workaround:** Honest UTV by design — those two steps fall through to manual verification (or the 3-A grounded-VLM road, which targets exactly these lookalike parts). Do NOT re-add a heuristic to fake a verdict for them; an earlier filename hardcode + skip heuristic that did this was removed (see DECISIONS_AND_RATIONALE.md, June 24).
**Affected component:** `src/ingestion/asd_mapping.py`, `run_video_asd` in `video_analyzer.py`
**Date found:** Week 4 (June 24)
**Source:** PERCEPTION.md; the de-hardcoding review.

---

## [Add new issues below this line as you find them]
