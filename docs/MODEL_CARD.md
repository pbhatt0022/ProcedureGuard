# ProcedureGuard — Model Card

> This card covers the two AI models used in ProcedureGuard: Azure OpenAI GPT-4o/4.1 and Azure AI Content Understanding. Update the Evaluation section as benchmark results come in.

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

### Azure AI Content Understanding (Custom Video Analyzer)

| Field | Value |
|---|---|
| Service | Azure AI Content Understanding |
| API version | `2025-11-01` (GA) |
| Base analyzer | `prebuilt-video` |
| Custom field schema | `ppe_status`, `tool_in_use`, `component_contact`, `visible_safety_concern`, `action_observed` |
| Frame sampling | ~1 fps |
| Frame resolution | Phase 1 ~512 px; Phase 2 GPT-4o Vision at 768 px, `detail:"high"` |
| Segmentation | Fixed ~25s time windows imposed by the pipeline (scene-boundary segmentation collapses continuous footage to one segment — see KNOWN_ISSUES) |
| Output | Structured JSON per segment — one value per field per segment, with timestamps |

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
unique-evidence guard (see WEEKLY_PROGRESS Addendum 3).

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

### Evaluation method

Compliance verdict accuracy is measured as agreement rate between ProcedureGuard verdicts and manually annotated ground truth labels from IndustReal. Steps labelled *Unable to Verify* are excluded from the accuracy calculation (they are not wrong verdicts — they are honest abstentions).

---

## Known Limitations

### Content Understanding constraints

| Limitation | Impact | Mitigation |
|---|---|---|
| ~1 fps frame sampling | Sub-second actions and fast transitions may not be captured | Flag fast-action steps as Unable to Verify by default |
| Low effective resolution (512 px Phase 1 / 768 px Phase 2) | Fine motor detail — torque, seating, pin orientation, "rotates freely" — is unresolvable | Steps needing such detail are tagged `fine_detail` and routed to **Requires Inspection**, not guessed |
| Minimum segment length | Fields return null on very short clips (<~15 seconds) | Ensure minimum clip length of 30 seconds for reliable extraction |
| Occlusion | Actions obscured from camera cannot be observed | Classify occluded steps as Unable to Verify |

### GPT-4o reasoning constraints

- Compliance verdicts are only as good as the Content Understanding observations. If a segment returns vague observations, GPT-4o may produce a low-confidence verdict.
- GPT-4o does not have access to the raw video — it reasons over structured observations only. It cannot recover information missed by Content Understanding.
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
- Test the custom Content Understanding schema on your specific SOP-video pair before relying on results — field descriptions may need adjustment for domain-specific actions
- Keep the SOP document version-controlled and tied to each `run_id` record in Cosmos DB
