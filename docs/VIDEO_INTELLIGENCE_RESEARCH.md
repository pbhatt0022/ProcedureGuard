# Video Intelligence Architecture Options — ProcedureGuard

*Research date: 2026-06-18*

---

## Executive Summary

**Top recommendation:** Implement Option A (full-coverage temporal inference) immediately — it is a ~50-line post-processor in `pipeline.py`, requires no new Azure services, and directly fixes the absence-inference gap that currently causes omitted steps to return "Unable to Verify" instead of "Deviation Detected." The implementation closes the gap by scanning all window verdicts after the per-step reasoning pass and upgrading any `verifiability == "presence"` step with zero lexical signal across all windows. Three safeguards (coverage check, at least one Compliant step in the run, and GPT-4o having found zero signal rather than ambiguous signal) keep false positives low.

**Runner-up:** Qwen2.5-VL-7B as a drop-in replacement for the GPT-4o Vision per-window description step, enabling single-call whole-clip absence queries. This requires a Foundry Hub project and H100 GPU quota — non-trivial during a short internship — but can be prototyped against the Alibaba/Together API without Azure infrastructure. Defer to Week 4 if Option A leaves gaps.

**Skip:** Azure Content Understanding (same 1fps/512px limit as the current pipeline, no accuracy gain), Azure AI Video Indexer (label taxonomy too coarse for assembly actions), and the IndustReal PSR model within the internship scope (requires per-product retraining with 3D CAD models).

---

## 1. The Core Problem

ProcedureGuard's current pipeline reasons per-window: GPT-4o evaluates whether a checklist item was observed within each 25-second segment and returns one of four verdicts. The critical gap is **absence inference across the full video**. When a step is never performed — the worker simply skips installing the rear wheel, for example — every window returns "Unable to Verify" because no single window positively contradicts that step. The SYSTEM_PROMPT in `compliance_engine.py` even explicitly states: *"Absence of evidence is 'Unable to Verify', never a deviation."* This is the correct, conservative stance for a single window, but it becomes incorrect when applied to the full clip: if the video tiles the entire procedure without a gap and the action is never present in any window, absence of evidence *is* evidence of absence.

The second structural issue is verifiability tiering. The checklist generator already distinguishes `verifiability = "presence"` (gross physical action visible from overhead video) from `"fine_detail"` (routes to inspection). This distinction is exactly the hook needed for full-coverage inference: only `"presence"` steps with zero lexical signal across all windows should ever be upgraded to "Deviation Detected (Not Observed)". Fine-detail steps, sequence steps, and any step where at least one window shows partial signal should be left alone.

---

## 2. Option A: Full-Coverage Temporal Inference (code-only fix)

### How it works

The insight is simple: ProcedureGuard's time-windowed segmentation is designed to tile the whole clip without gaps. If a `verifiability == "presence"` step has zero windows with any lexical signal matching its `observable_action`, the video did not contain that action. This is the same inference a human reviewer would make after watching the full video.

This is not a new idea in procedural video literature. The PREGO system (CVPR 2024, Flaborea et al.) detects procedural mistakes — including omissions — by comparing the current recognised action against an LLM-anticipated next step. When a step is skipped, the symbolic sequence becomes misaligned and the divergence flags an error. PREGO achieves F1=42.1 on Assembly101-O with zero-shot LLM anticipation. The same principle — using global sequence state to infer what is missing — is what ProcedureGuard needs, but in a simpler form: no sequence prediction model is required, just a post-hoc scan of the verdict list.

Research on differentiable task graph learning (arXiv 2406.01486) also addresses procedural absence: representing expected steps as a graph and flagging nodes never activated. The approach is structurally identical to what is proposed here, applied offline rather than online.

### Known failure modes and safeguards

The three main false-positive risks are:

1. **Action happened off-camera or in an unanalysed portion of the clip.** Safeguard: only upgrade if the video truly covers the full procedure timeline (check that total windowed duration ≈ video duration, with ≤10% gap tolerance). Do not upgrade if the last window ends significantly before the clip ends.

2. **Poor visibility / unusual angle in all windows.** Safeguard: require that *at least one other* `presence` step in the same run produced a `Compliant` verdict backed by the same camera view. If the video is so degraded that no presence steps are verifiable, fall through to "Unable to Verify" for all.

3. **Lexical signal absent but action genuinely occurred.** The window descriptions use generic vocabulary ("black pin pushed through aligned holes") that may not share tokens with the observable_action ("insert chassis pin through bores"). Safeguard: use the same `_significant_tokens` overlap logic already in `_select_candidate_segments` — if the lexical match is zero *and* the existing GPT-4o verdict for the step is already "Unable to Verify" (not "Compliant" downgraded by `enforce_unique_evidence`), the upgrade is allowed. Never upgrade a step that GPT-4o already returned a verdict on.

### Implementation sketch

**New field on the verdict JSON:** add `"not_observed": true` when the upgrade fires. This disambiguates "never seen in any window" from the existing "Unable to Verify" that means "seen but unclear." The `reasoning` string should read: `"No video window contained any signal matching this action across [N] windows covering [T]s of footage. Upgraded from Unable to Verify."`.

**New function `apply_absence_inference(verdicts, observations, checklist_items)`** — call it from `pipeline.py` *after* `enforce_unique_evidence` and *before* writing to Cosmos DB. Signature:

```python
def apply_absence_inference(
    verdicts: list[dict],
    observations: dict,
    checklist_items: list[dict],
    coverage_tolerance: float = 0.10,
) -> list[dict]:
```

Logic:
1. Check total coverage: `last_window_end / video_duration_seconds >= (1.0 - coverage_tolerance)`. If not, return verdicts unchanged.
2. Check that at least one `Compliant` verdict exists in this run (proxy for "camera was working and steps are visible"). If not, return unchanged.
3. For each verdict where `verdict == "Unable to Verify"` and the matching checklist item has `verifiability == "presence"` and `observable_action` is not None:
   - Compute `query_tokens = _significant_tokens(observable_action)`
   - Check all segments: if `sum(len(query_tokens & seg_tokens) for seg in segments) == 0`, upgrade.
4. Set `verdict = "Deviation Detected"`, `not_observed = True`, update `reasoning`.

**Changes to `compliance_engine.py`:** none — the function is a post-processor, not a change to `reason_step`. It sits in `pipeline.py` as a pipeline step.

**Effort:** 1–2 hours of implementation, 1 hour of testing against the IndustReal demo clip. No new Azure resources, no new dependencies.

**Recommendation:** Ship this immediately. It closes the gap for unambiguous omissions (a wheel that was never touched) while the safeguards keep it conservative for ambiguous cases.

---

## 3. Option B: Qwen2.5-VL Integration

### Architecture and temporal reasoning capability

Qwen2.5-VL (Alibaba/Qwen team, technical report arXiv:2502.13923, released February 2025) is available in 7B, 32B, and 72B parameter sizes. Its key advance for ProcedureGuard is **Multimodal Rotary Position Embedding (M-RoPE)** extended into the temporal domain with absolute time encoding — meaning the model encodes *when* a frame occurred, not just its position in the input sequence. This is architecturally different from frame-by-frame VLMs: a single forward pass over multiple frames produces temporally grounded outputs.

Claimed capabilities relevant to ProcedureGuard:
- **Second-level event localisation:** can answer "at what time did X happen?" with timestamps.
- **Hour-scale video understanding:** processes videos up to several hours with dynamic FPS sampling.
- **Cross-frame reasoning:** asks "did X happen at any point?" over the full input rather than per-frame.

The 7B model is sufficient for coarse action recognition (was a wheel installed?); the 72B model is better for ambiguous, fine-grained spatial relations ("was the pin inserted from the correct side?"). For ProcedureGuard's absence-inference problem, the 7B model is the right trade-off: the question is "did this gross action happen in this N-second clip?" not "what exact torque was applied?".

### What it would replace in ProcedureGuard

Currently: `video_analyzer.py` runs OpenCV frame extraction → GPT-4o Vision describes each 25s window separately → `compliance_engine.py` reasons per-window. With Qwen2.5-VL, the pipeline becomes: pass all frames for a step's candidate time range (or the full clip for short procedures) into a single Qwen2.5-VL call and ask "Was [observable_action] performed in this video? If yes, at what timestamp?". This replaces both the per-window description step and the per-step reasoning step with a single call per checklist item.

### Azure deployment steps

Qwen2.5-VL-32B-Instruct is available in the Azure AI Foundry / Azure Machine Learning model catalog under the HuggingFace collection. Deployment requires:

1. **A Hub-based project on Microsoft Foundry** (not a standalone AIServices resource). This is the key prerequisite — your current `pg-ai-priya.services.ai.azure.com` standalone resource cannot host Managed Online Endpoints for open HuggingFace models.
2. Create a `ManagedOnlineEndpoint` + `ManagedOnlineDeployment` via `azure-ai-ml` SDK, using instance type `Standard_NC40ads_H100_v5` (1× H100 80 GB). Deployment takes 10–15 minutes.
3. Inference via OpenAI-compatible `/v1/chat/completions` with the `azureml-model-deployment` header.

The 7B variant requires a lower SKU (typically `Standard_NC24ads_A100_v4`), but availability in East US varies — quota increase requests are often needed.

### Cost

Managed Online Endpoints bill per hour the instance is running, not per token. An `NC40ads_H100_v5` instance costs approximately $3.67/hour in East US (as of mid-2025). For a batch demo run this is acceptable; for production at scale it is expensive unless the endpoint is auto-scaled to zero between runs. There is no serverless/per-token pricing option for open HuggingFace models on Foundry — only the pay-as-you-go managed endpoint model.

For comparison: GPT-4o on Azure OpenAI is ~$0.005/1K input tokens (~$0.10 per full video analysis), with no idle cost. Qwen2.5-VL at $3.67/hour requires at least 37 analyses per hour to break even on cost alone.

### Known limitations for fine-grained assembly

Qwen2.5-VL's training data skews toward natural scenes, web images, and general video. For industrial egocentric footage:
- **Hand/tool occlusion:** the model may miss actions when hands obscure the work area — a known gap for all current VLMs on fine-grained assembly (acknowledged in HA-VID and InstructionBench benchmarks, 2024–2025).
- **Part similarity:** STEMFIE toy components look nearly identical (black beams, pins of similar diameter). The model may confuse a front-axle installation with a rear-axle installation.
- **No assembly-specific fine-tuning:** without fine-tuning on IndustReal or similar data, Qwen2.5-VL is unlikely to outperform GPT-4o Vision on this specific domain.

**Recommendation:** Deferred. The absence-inference gap (Option A) is the bottleneck, not the per-window description quality. Qwen2.5-VL is worth revisiting in Week 4 if GPT-4o Vision continues to produce poor descriptions, but requires creating a Foundry Hub project and significant quota procurement, which is non-trivial during a short internship.

---

## 4. Option C: Azure Content Understanding + Foundry Hub

### What a Foundry Hub unlocks

Your current setup (standalone `AIServices` resource) gives access to GPT-4o, Document Intelligence, and Speech. A Foundry Hub-based project adds:
- Managed Online Endpoints for open models from the HuggingFace collection (required for Qwen2.5-VL).
- Azure Content Understanding (video), which is a Foundry Tools service.
- Azure AI Search integration and vector store management.
- Prompt flow and evaluation tooling.

Content Understanding does not require a Hub for API calls once configured, but the setup portal requires one.

### What Content Understanding video actually does

The `prebuilt-videoAnalysis` analyzer runs at **~1 FPS, 512×512 px** — identical to ProcedureGuard's current frame sampling. It produces:
- Natural-language segment descriptions (same as what GPT-4o Vision currently generates per window).
- Shot-boundary-based automatic segmentation or custom segmentation via natural-language prompt (`contentCategories`).
- Key-frame thumbnails per segment.
- Transcript (WEBVTT) — irrelevant for silent assembly video.

The custom GENERATE fields allow prompting the model to extract domain-specific metadata per segment (e.g., "which component is being installed in this segment?"). This is functionally equivalent to ProcedureGuard's current Phase 2 GPT-4o per-window enrichment step — it offers no architectural advantage, just a managed API wrapper around the same underlying capability.

### Custom segmentation for continuous assembly footage

The `enableSegment: true` + `contentCategories` option lets you write a natural-language prompt to segment the video: e.g., "Segment by assembly step: each segment should correspond to one distinct assembly action." For a news broadcast with clear scene changes, this works well. For **continuous, silent assembly footage** with no scene cuts and visually similar frames, the shot-detection backbone (which aligns segments to camera shot boundaries) will produce arbitrary or overlapping segments that do not correspond to procedure steps. There is no guarantee that the segmentation prompt produces step-aligned segments on egocentric assembly video.

### Verdict

The 1 FPS / 512 px hard limit is the fundamental problem. ProcedureGuard already samples at this rate with GPT-4o Vision. Content Understanding does not provide higher temporal resolution or better spatial resolution than the current pipeline. The custom segmentation feature is unreliable for silent assembly footage. The main operational cost is the Hub project setup (estimated 1–2 days including quota provisioning and configuration), with no meaningful accuracy gain for the absence-inference problem.

**Recommendation:** Skip for Week 3. If the project continues into Week 4–5 and needs a production-grade managed video indexing pipeline with RAG support, revisit. Do not spend time on it now.

---

## 5. Option D: IndustReal PSR Model

### Architecture

IndustReal (Schoonbeek et al., WACV 2024, arXiv:2310.17323) introduces the **Procedure Step Recognition (PSR)** task: given a video and a known procedure, predict which steps have been correctly completed and in what order, in real time. The follow-up STORM-PSR paper (arXiv:2510.12385, ScienceDirect 2025) improves on the baseline with a **spatial encoder pre-trained via weakly supervised learning + transformer-based temporal encoder**. The exact vision backbone is not published in the abstract, but the weakly-supervised spatial encoder is a key contribution — it learns part-appearance features from synthetic 3D renders of STEMFIE components, then transfers to real egocentric footage (sim2real).

STORM-PSR reduces the average delay between actual and predicted step completions by **26.1% compared to prior PSR methods** on the IndustReal test set. The dataset includes 38 execution errors across train/val/test splits, with 14 errors exclusive to val+test to test generalisation to unseen mistake types.

### Output format

PSR produces an estimate $\hat{y}_t$ at each time $t$: a set of (step_id, completion_timestamp) pairs representing all correctly completed steps up to that point. This is exactly "step X completed at time T" — not post-hoc classification. The system can be run offline (full video) to produce the complete step list, and steps absent from the output but present in the SOP represent missed/omitted steps directly.

### Generalisation to new SOPs

The IndustReal PSR model is trained on STEMFIE toy-vehicle assembly exclusively. The spatial encoder learns appearance features for the specific STEMFIE part set (14 unique components). **It does not generalise to new SOPs without retraining.** The sim2real training pipeline requires 3D CAD models of the new assembly's components — a non-trivial authoring requirement (each new product requires a CAD model and synthetic render pipeline).

The STORM-PSR paper acknowledges dataset scale as the primary limitation: "the number of procedures only ranges up to hundreds, which is a limitation for current deep learning techniques." With 190 procedures in Assembly101-O and IndustReal covering one assembly type, the model's generalisation to arbitrary manufacturing SOPs is unproven.

### When it makes sense

IndustReal PSR is the ideal architecture for a **production system locked to a single assembly procedure** where accuracy is critical and retraining investment is justified. It gives sub-step temporal precision and explicit missed-step output. For a demo/internship scope covering one IndustReal clip, it would produce the best possible step-tracking results — but only because the test clip is in-distribution for the model.

**Recommendation:** Not for Week 3. Running the IndustReal PSR model on IndustReal clips is a closed-loop evaluation (model trained on same distribution as test). For the broader ProcedureGuard goal of working with *any* SOP PDF and *any* assembly video, PSR requires retraining per-product. Worth noting in the architecture document as the production-grade path for a single-product deployment.

---

## 6. Option E: Other Options

### Azure AI Video Indexer

Video Indexer runs 30+ AI models producing labels, faces, OCR, transcripts, topics, and named entities. The **Labels Identification** feature identifies "visual objects, like sunglasses, or actions, like swimming." The label taxonomy is generic (web-scale visual concepts). For manufacturing assembly, expect labels like "hand", "tool", "table", "object" — not "installs rear wheel" or "inserts chassis pin". There is no custom label training capability; you cannot add assembly-specific action labels. Video Indexer improved label accuracy by ~30% in recent updates, but this applies to its built-in label set.

For ProcedureGuard, Video Indexer would only add value as a supplement (detecting faces, OCR on part labels, transcribing any verbal instructions) — not as a replacement for the GPT-4o Vision description step. It does not address absence inference.

### LLaVA-Video (2024)

LLaVA-Video (ByteDance, 2024) extends LLaVA-Next to native video input with a video token compression scheme. It performs competitively on Video-MME and MVBench. Like Qwen2.5-VL, it supports multi-frame input and can answer presence questions across a clip. It is available on HuggingFace but **not in the Azure AI Foundry model catalog** as of June 2026. Deployment would require a custom AKS or ACI container, adding operational complexity. No advantage over Qwen2.5-VL for this use case.

### VideoChat-Flash (OpenGVLab, ICLR 2026)

VideoChat-Flash achieves first place on AuroraCap Video Detail Caption Benchmark (2025). It uses a hierarchical compression approach for long-context video (hour-scale). Built on InternVideo + Qwen backbone. Not available on Azure. Architecturally interesting for long assembly sessions, but the same deployment complexity as LLaVA-Video applies. Not a practical option for the current internship scope.

### InternVL2 (2024–2025)

InternVL2 is a strong open-source VLM family that unifies image and video as multi-frame sequences. Competitive with GPT-4o Vision on image benchmarks. Available on HuggingFace, partially available in Azure AI Foundry catalog. The same concerns about assembly-specific fine-tuning and deployment complexity as Qwen2.5-VL apply. Not differentiated enough from Qwen2.5-VL to pursue separately.

---

## 7. Comparison Table

| Option | Solves absence inference? | Generalises to new SOPs? | Azure-native? | Effort (1–5) | Cost impact | Production-ready? |
|--------|--------------------------|--------------------------|---------------|--------------|-------------|-------------------|
| **A: Full-coverage temporal inference** | Yes — for clean omissions | Yes — language-based, SOP-agnostic | Yes (no new services) | 1 | Zero | Yes (this week) |
| **B: Qwen2.5-VL** | Yes — with a single full-clip call per step | Yes — zero-shot | Partial (requires Foundry Hub + H100 quota) | 4 | +$3.67/hr idle | Prototype only |
| **C: Azure Content Understanding** | No — same 1fps/512px limit, per-segment reasoning | Yes | Yes (requires Foundry Hub) | 3 | Low per-call | No (GA but wrong tool) |
| **D: IndustReal PSR** | Yes — explicit missed-step output | No — retrain per product | No | 5 | High (custom training) | Yes for single-product |
| **E: Video Indexer** | No — coarse generic labels only | N/A | Yes | 2 | Low per-minute | No (wrong granularity) |
| **E: Qwen/LLaVA/InternVL variants** | Partial | Yes | No (HuggingFace only) | 4–5 | High | No |

---

## 8. Recommended Path

### Tomorrow (Day 1 of Week 3)

Implement **Option A: `apply_absence_inference()`** in `pipeline.py`. This is a ~50-line pure-Python post-processor that requires no new Azure resources, no new dependencies, and closes the core absence-detection gap for the demo. The safeguards (coverage check + at least one Compliant step in the run) keep false positives low. Add a `not_observed: bool` field to the verdict JSON schema and update `schemas/verification_record.json`. Run against the `23_assy_1_2` IndustReal clip to validate — the rear-wheel omission error in that clip should flip from "Unable to Verify" to "Deviation Detected (Not Observed)".

### Week 3 (days 2–5)

1. Run the full IndustReal demo pipeline with `apply_absence_inference` enabled. Measure precision/recall on the 14 val/test-exclusive errors — specifically how many omissions are now caught vs. false positives triggered.
2. If false-positive rate is acceptable (< 1 per 10-step run), add a confidence floor: only upgrade when `confidence` of the existing "Unable to Verify" verdict is < 0.3 (i.e., GPT-4o found no signal at all, not low-confidence partial signal).
3. Tighten the lexical match: consider using `_select_candidate_segments` scoring as a proxy — if the max score across all segments for this checklist item is 0, the upgrade is safe; if the max score is ≥ 1, at least one window is semantically adjacent and the item should stay "Unable to Verify".

### Week 4 (if time permits)

Evaluate **Option B: Qwen2.5-VL 7B** on a single IndustReal clip as a proof-of-concept. Goal: can a single Qwen2.5-VL call over the full clip answer "was the rear wheel ever installed?" more reliably than the current per-window GPT-4o approach? To do this without H100 quota, use the Qwen2.5-VL-7B-Instruct API via Alibaba Cloud Model Studio (the same model, pay-per-call, no instance setup) or via Together AI. This validates the approach before requesting Azure quota.

### What to defer / skip

- **Azure Content Understanding:** skip entirely. Architecturally equivalent to what you already have, with higher operational overhead and a Foundry Hub prerequisite.
- **IndustReal PSR model:** mention in architecture docs as the long-term production path for single-product deployment, but do not attempt to run it within the internship. The sim2real training pipeline is a multi-week project on its own.
- **Video Indexer:** no value for this specific use case. Its label taxonomy is too coarse.

---

*Sources consulted:*
- PREGO (CVPR 2024): [arxiv.org/abs/2404.01933](https://arxiv.org/abs/2404.01933)
- STORM-PSR (2025): [arxiv.org/abs/2510.12385](https://arxiv.org/abs/2510.12385)
- IndustReal (WACV 2024): [arxiv.org/abs/2310.17323](https://arxiv.org/abs/2310.17323) · [timschoonbeek.github.io/industreal.html](https://timschoonbeek.github.io/industreal.html)
- Qwen2.5-VL Technical Report: [arxiv.org/abs/2502.13923](https://arxiv.org/abs/2502.13923)
- Qwen2.5-VL on Azure Foundry (HuggingFace docs): [huggingface.co/docs/microsoft-azure/foundry/examples/deploy-vision-language-models](https://huggingface.co/docs/microsoft-azure/foundry/examples/deploy-vision-language-models)
- Azure Content Understanding video overview: [learn.microsoft.com/azure/ai-services/content-understanding/video/overview](https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/video/overview)
- Azure AI Video Indexer insights: [learn.microsoft.com/azure/azure-video-indexer/insights-overview](https://learn.microsoft.com/en-us/azure/azure-video-indexer/insights-overview)
- VideoChat-Flash (ICLR 2026): [github.com/OpenGVLab/VideoChat-Flash](https://github.com/OpenGVLab/VideoChat-Flash)
- TI-PREGO (2024): [arxiv.org/abs/2411.02570](https://arxiv.org/abs/2411.02570)
