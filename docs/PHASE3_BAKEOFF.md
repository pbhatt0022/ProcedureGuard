# Phase 3 — Perception Bake-off (parallel work)

**Decided June 23 2026.** The Phase 3 "which perception model" question is being settled
empirically instead of by a meeting: two roads built in parallel, judged by the same harness.

- **Road 3-A — VLM salvage** (teammate): keep GPT-4o Vision, make it precise.
- **Road 3-B — real detector** (priya): swap in IndustReal's Assembly State Detection (ASD) model.

Whichever scores better on the shared scoreboard wins and goes into the live pipeline (Phase 4).

---

## Why this fork exists (read first)

Perception (the "eyes" — describe the video) is the bottleneck, not reasoning. Today the eyes
are a general chatbot (GPT-4o Vision) describing frames in English: non-deterministic, vague
("white perforated beam" for both wing and beam; "pink connector" for the pulley), and **can't
count**.

We already proved (June 22, see `docs/KNOWN_ISSUES.md` → "Deterministic baseline-diff…") that you
**cannot fix this in software on top of the chatbot's text** — a missing-wheel clip produced *more*
wheel-mentions than the clean clip, because word-count tracks camera dwell, not part count. So the
fix has to be at the perception layer. Hence the two roads.

---

## THE SHARED CONTRACT (do not break this — it's what makes the bake-off valid)

Both roads change **only the eyes**. Everything below the eyes is shared and must stay untouched:
the reasoning (`reason_step` + guards), the GT checklist, and the harness.

**The boundary is the `observations` dict** (schema: `schemas/video_observations.json`):

- **Producer (the part each road replaces):** `run_video_phase2(observations, run_id, video_url=, checklist=)`
  in `src/ingestion/video_analyzer.py`. It fills `observations["segments"]`.
- **Consumer (shared, DO NOT EDIT for this work):** `reason_step()` +
  `enforce_unique_evidence` / `apply_absence_inference` in `src/reasoning/compliance_engine.py`.
- **Runner (shared):** `scripts/validate_error_clip.py`.

Each `segment` your perception produces MUST carry these fields (others may be null):

```jsonc
{
  "segment_id": "seg-001",
  "start_time_seconds": 0.0,
  "end_time_seconds": 25.0,
  "description": "...",            // free-text, optional
  "ppe_status": "not-visible",
  "tool_in_use": null,
  "component_contact": "...",      // what parts are in contact
  "visible_safety_concern": false,
  "action_observed": "...",        // the main thing reasoning reads
  "observed_items": [              // A1 signal: which checklist items this window evidences
    { "item_id": "check-005", "confidence": 0.9 }
  ]
}
```

`observed_items` is the important one: it's how perception tells reasoning "this window shows
checklist item X." The reasoning's `_vision_flagged_map` reads it. **As long as your road fills
`segments` (with `observed_items`) in this shape, it plugs in with zero reasoning changes** and the
comparison is apples-to-apples.

> Rule of thumb: if you find yourself editing `compliance_engine.py` or `validate_error_clip.py` to
> make your road work, stop — that means you're changing the judge, not the eyes, and the bake-off
> result becomes meaningless. The contract above is the only thing you both target.

---

## THE SHARED SCOREBOARD (how we decide a winner)

Same harness, same clips, same metric for both roads.

**Run:**
```powershell
python scripts/validate_error_clip.py industreal_selected/videos/candidates/23_assy_1_2.mp4
python scripts/validate_error_clip.py industreal_selected/videos/baselines/23_assy_0_1.mp4
python scripts/validate_error_clip.py industreal_selected/videos/candidates/22_assy_2_3.mp4
```
(~9 min each — sequential, rate-limited Vision calls. `az login` first.)

**Three clips, what each must show:**
| Clip | Truth | A winning perception should… |
|---|---|---|
| `23_assy_1_2` | one fewer wheel (`fit_wheel:-1`) | flag **check-005** Deviation (catch the count error) |
| `23_assy_0_1` | clean build | **0 deviations** — the non-negotiable |
| `22_assy_2_3` | missing pulley + wing-beam | catch them if it can; honest UTV is acceptable |

**Metric, in priority order (non-negotiable):**
1. **Zero new false positives.** A false alarm on good work is worse than a missed deviation.
   Nobody "wins" by guessing. If a road raises recall but also flags the clean clip → it loses.
2. **Then recall** on the real deviations.

**Agreed "before" baseline:** `experiments/sop_gt/proofrun_*.json` (today's runs — recall 0, the
count error currently sails through as Compliant). Beat that without breaking rule #1.

---

## Road 3-A brief — VLM salvage (teammate)

**Goal:** make GPT-4o Vision precise enough to catch the count/identity errors, staying on Azure OpenAI.

**Where you work:** `src/ingestion/video_analyzer.py` — the Phase 2 prompt + how `observed_items`
gets populated. (Plus a reference-image asset folder if you add grounding images.) Do **not** touch
the reasoning or harness.

**Things to try (in rough order of bang-for-buck):**
1. **Structured output** — instead of free prose, make the model answer a fixed schema per window
   ("wheels_visible": N, "pulley_present": true/false) so counts/identities are explicit.
2. **Reference-image grounding** — include a cropped photo of the actual STEMFIE pulley / wing in
   the prompt and ask "is *this specific* part present?" rather than hoping it volunteers the word.
3. **Voting** — call each window 3× (temperature low) and take majority, to kill run-to-run flips.

**Watch out for:** the pulley is described as "pink connector" in both good and bad clips
(`KNOWN_ISSUES.md`); generic naming ("white perforated beam") hides wing vs beam. Those are your
real targets. Honesty principle applies — if you can't tell, output UTV, don't guess.

---

## Road 3-B brief — IndustReal ASD model (priya)

**Goal:** replace the eyes with a purpose-built detector. ASD outputs a per-component state vector
(`1` assembled / `-1` wrong / `0` absent) + 22 subgoal labels + bboxes — i.e. the count/identity
signal the chatbot can't give. Weights are published, Apache-2.0, PyTorch (4TU link in
`MEMORY`/project notes). Deploy on **Azure ML** under the same managed identity.

**Spike FIRST (before any integration — buy info before effort):**
1. Do the ASD weights **load and run** locally? (PyTorch version, CPU vs GPU.)
2. On **one** of our clips, do they output a **sane state vector**, or were they trained on too
   different a camera angle/kit to generalize? If they don't generalize, you want to know day one.

**Then** the integration is: write an adapter that maps ASD per-component state → the shared
`segments`/`observed_items` shape above (e.g. component `1` in a window → `observed_items` entry for
the matching checklist item; `0`/`-1` where a part should be present → the deviation signal). Same
contract, so it drops into the same harness.

---

## Ground rules recap
- Only the eyes change. The contract (`observations` dict) + reasoning + harness are shared and frozen.
- Same harness, same 3 clips, zero-FP-then-recall.
- Don't guess to win. UTV is an honest answer.
- Keep `python -m pytest` green (69 tests) — neither road should break existing tests.
