# ProcedureGuard — Model Card

> This card covers the models used in ProcedureGuard: **Azure OpenAI GPT-4o/4.1** (reasoning + the
> default VLM perception) and **IndustReal ASD** (an optional, purpose-built perception detector,
> added June 24 — see PERCEPTION.md). Azure AI Content Understanding was **removed June 18** and is
> no longer part of the system. Update the Evaluation section as benchmark results come in.

---

## Model Details

### GPT-4o / GPT-4.1 (Azure OpenAI)

| Field | Value |
|---|---|
| Model family | OpenAI GPT-4o / GPT-4.1 |
| Deployment | Azure OpenAI — hosted in the project's Azure AI Foundry resource |
| API | Azure OpenAI Chat Completions API |
| Roles in pipeline | (1) Checklist generation + verifiability tiering (presence / sequence / fine_detail + observable_action). (2) Phase 2 Vision: per-window compliance field extraction from sampled frames. (3) Per-step reasoning: matches each observable_action to a time window → one of four verdicts. |
| Output format | Structured JSON — verdicts are Compliant / Deviation Detected / Requires Inspection / Unable to Verify |

### GPT-4o Vision — default perception (Phase 2)

| Field | Value |
|---|---|
| Role | Describes each ~25s video window in English (`action_observed`, `component_contact`, etc.) so reasoning can match it to a checklist item |
| Frame sampling | ~1 fps via OpenCV; 768 px longest edge, `detail:"high"`, ~6 frames per 25s window |
| Strength / weakness | General, flexible describer — but non-deterministic, vague on lookalike parts, and cannot count. This is the gap the ASD swap (below) targets. |

### IndustReal ASD — optional perception (Road 3-B, June 24)

| Field | Value |
|---|---|
| Model | YOLOv8-m object detector (~25M params), pretrained on IndustReal synthetic + real egocentric footage |
| Source / license | 4TU dataset `b008dd74-...`; **Apache-2.0**; PyTorch `.pt` |
| Output | Per-component assembly-state vector (11 components: base / chassis / pins / brackets / wheels) → mapped to checklist items via `src/ingestion/asd_mapping.py` |
| Deployment | Runs in an isolated venv via subprocess; ~2–3 FPS on CPU (no GPU needed); target Azure ML CPU SKU |
| Toggle | `USE_ASD_PERCEPTION=true` (default off — GPT-4o Vision remains the default path) |
| Ontology gap | No wing-beam or pulley class → those steps stay honest **Unable to Verify** |

---

## Intended Use

### Primary use case

Quality assurance documentation for manufacturing production runs. A Quality Assurance Manager uploads an SOP PDF and a production video; ProcedureGuard produces a structured compliance report aligned to that SOP.

### Intended users

- Quality Assurance Managers in regulated industries (medical device, pharmaceuticals, food, automotive)
- Compliance teams generating evidence records for FDA, ISO 13485, GMP, HACCP audits

### Out-of-scope uses

- Real-time production monitoring (system processes pre-recorded video, not live feeds)
- Worker surveillance or performance evaluation — the system analyses the product and process, not the individual
- Autonomous quality gating without human review — all reports require human review before informing a quality decision
- Production deployment without QMS integration and regulatory validation

---

## Performance Targets

| Metric | Target | Evaluation dataset |
|---|---|---|
| SOP step extraction coverage | >90% of verifiable steps correctly identified | Prusa MK3S+ SOP manual (manual annotation) |
| Compliance verdict accuracy | >80% agreement vs manual benchmark | IndustReal (WACV 2024) |
| End-to-end pipeline latency | <5 minutes per video | Internal timing benchmark |

> **Update this section as benchmark results come in during Week 3 testing.**

---

## Evaluation

### Datasets used for evaluation

**IndustReal (WACV 2024)**
- 6 hours of egocentric procedural assembly video, 27 participants
- Contains annotated correct and incorrect procedure execution — ground truth for compliance verdicts
- License: Apache 2.0
- Used for: compliance verdict accuracy benchmark

**Prusa MK3S+ Assembly Manual + OPENMARCIE videos**
- Real SOP document paired with real assembly footage
- Used for: SOP extraction coverage evaluation (Week 3 benchmark)

**STEMFIE Vehicle Kit Assembly Manual (demo SOP)**
- 14-page teammate-generated manual with documented error modes (wrong pin type, fastener substitution, missing washer)
- Used for: end-to-end pipeline runs and the June 15 deviation-detection demo

### Status (June 16, 2026 — supersedes June 12)

The June 12 single-segment results (`chassis_error` "2 deviations") were later found to be **false
positives**: with the whole clip as one segment, GPT-4o treated an *unobserved* QC step as a
violation. The pipeline was corrected — time windowing → verifiability tiering → Phase 2 enrichment →
unique-evidence guard (see the Milestones section in ARCHITECTURE.md).

Honest result on the clean `correct` clip (`run-20260612-9f9006e5`):

| Verdict | Count |
|---|---|
| Compliant | 3 (each backed by a distinct ~25s window, audited as genuine) |
| Deviation Detected | 0 |
| Requires Inspection | 18 (fine-detail QC routed to a human) |
| Unable to Verify | 8 |
| **Adherence** | **100% of 3 video-verifiable steps; 0 fabricated** |

**Evaluation caveat:** the `wrong_pin` and `chassis_error` clips are IndustReal *annotated
visualization renders* with ground-truth labels (action captions, state vectors) burned into the
frames — unusable for honest evaluation, since the model can read them. Quantitative accuracy on
clean IndustReal ground truth (target >80%) remains pending.

### Status (June 24, 2026 — perception bake-off, honest numbers)

Measured on the GT-grounded 6-item checklist over 3 clean IndustReal clips
(`scripts/validate_error_clip.py`; results in `runs/run-asd-*.json`). See PERCEPTION.md.

| Perception | Missing-wheel clip (23_assy_1_2) | Clean clip (23_assy_0_1) | Missing beam+pulley (22_assy_2_3) | Net |
|---|---|---|---|---|
| GPT-4o Vision (default) | false **Compliant** (missed) | 0 FP | coin-flip pulley | recall 0 |
| **IndustReal ASD (3-B)** | **Deviation (caught)** | 0 FP | honest UTV (out of ontology) | **TP=1 FP=0 FN=2 → P 100% / R 33%** |

ASD cleanly catches the count/presence error the VLM is structurally incapable of, with zero false
alarms; it is honest (UTV) about wing-beam and pulley, which are outside its ontology. A prior
"3/3 recall" was found to be a filename hardcode + skip heuristic and was removed (KNOWN_ISSUES.md).
The deterministic baseline-diff approach was tried and rejected (window-count ≠ part-count).

### Evaluation method

Compliance verdict accuracy is measured as agreement rate between ProcedureGuard verdicts and manually annotated ground truth labels from IndustReal. Steps labelled *Unable to Verify* are excluded from the accuracy calculation (they are not wrong verdicts — they are honest abstentions).

---

## Known Limitations

### Perception constraints

| Limitation | Impact | Mitigation |
|---|---|---|
| ~1 fps / 768 px sampling | Sub-second actions and fine motor detail (torque, seating, orientation) unresolvable | Such steps are tagged `fine_detail` → **Requires Inspection**, not guessed |
| GPT-4o Vision is non-deterministic + vague | Can't count; names lookalike parts (pulley ≈ "pink connector") inconsistently → missed deviations | The ASD swap (Road 3-B) targets exactly this for count/presence |
| ASD ontology is fixed (11 components) | No wing-beam or pulley class | Those steps stay honest **Unable to Verify** — never a fabricated verdict |
| Occlusion | Actions obscured from camera cannot be observed | Classify occluded steps as Unable to Verify |

### GPT-4o reasoning constraints

- Compliance verdicts are only as good as the perception observations. If a window returns vague observations, GPT-4o may produce a low-confidence verdict.
- The reasoning GPT-4o does not see the raw video — it reasons over the structured observations only. It cannot recover information the perception layer missed.
- Prompt drift: if the SOP step description is ambiguous, GPT-4o may interpret the compliance criterion inconsistently across runs.

### System-level limitations

- ProcedureGuard is a research prototype. Verification reports require human review before informing any real quality decision.
- Production deployment requires QMS integration and regulatory validation.
- The system does not verify the authenticity or version control of the SOP document. An outdated SOP produces an outdated checklist.
- Demo/eval video must be raw footage. Some IndustReal clips ship as annotated renders with ground-truth labels burned into the frames; the model would read those rather than observe the assembly (see KNOWN_ISSUES). Verify clips are clean before trusting results.

---

## Ethical Considerations

- **Worker privacy:** The system analyses process compliance, not worker behaviour or identity. No facial recognition, no individual tracking, no worker performance scoring.
- **False verdicts:** Steps where Content Understanding cannot make a reliable determination are classified *Unable to Verify*, not forced into a Compliant or Deviation verdict. The system is designed to abstain rather than fabricate confidence.
- **Audit use:** Reports are evidence records, not enforcement tools. The system surfaces what it observed; quality decisions remain with human reviewers.
- **Bias in training data:** Content Understanding and GPT-4o are general-purpose models trained on broad data. Their performance on specific manufacturing contexts (e.g., medical device assembly under cleanroom conditions) has not been independently validated beyond the IndustReal benchmark.

---

## Caveats and Recommendations

- Always review *Unable to Verify* steps manually before treating a run as fully compliant
- Do not use ProcedureGuard as the sole quality record for regulated production runs without additional human review
- Test the perception layer on your specific SOP-video pair before relying on results — VLM prompts (and the ASD ontology) may need adjustment for domain-specific actions
- Keep the SOP document version-controlled and tied to each `run_id` record in the run store
