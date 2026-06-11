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

---

## AIServices resource: no custom subdomain, token auth unavailable
**Symptom:** `DefaultAzureCredential` fails with HTTP 400 `BadRequest: Please provide a custom subdomain for token authentication`. DNS resolution fails for both `<name>.cognitiveservices.azure.com` and `<name>.services.ai.azure.com`.
**Root cause:** The `procedureguard-ai` resource was created without a custom subdomain (`customSubDomainName: null`). The only available endpoint is the regional one (`https://eastus.api.cognitive.microsoft.com/`), which only accepts API key auth.
**Fix / workaround:** Use `AzureKeyCredential` with the regional endpoint for local development. `get_client()` in `video_analyzer.py` automatically uses the key from `AZURE_CONTENT_UNDERSTANDING_KEY` when set. Long-term fix: recreate the resource with `--custom-domain` flag to enable token auth.
**Affected component:** Layer 2 — `video_analyzer.py`, `.env`
**Date found:** Week 1 (smoke test run)
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

## [Add new issues below this line as you find them]
