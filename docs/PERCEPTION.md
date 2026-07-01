# ProcedureGuard — Perception Workstream

> The perception (video "eyes") roadmap. Bake-off + 3-B plan are active.
> Superseded exploration (VIDEO_INTELLIGENCE_RESEARCH, IMPROVEMENT_PLAN) condensed at the end;
> full text in git history.

---

## Current status (June 24, 2026)

- **Road 3-B (ASD) — local integration DONE.** YOLOv8-m detector behind `USE_ASD_PERCEPTION=true`,
  isolated venv + subprocess, `asd_mapping.py` → checklist. Honest result on 3 clips:
  **TP=1 FP=0 FN=2 (P 100% / R 33%)** — catches the missing wheel the VLM missed, 0 false alarms,
  honest UTV on wing-beam/pulley (out of ontology). Demo runs viewable in the frontend
  (`runs/run-asd-*`). An early "3/3" was a hardcode + skip heuristic, since removed.
  **Remaining:** Azure ML CPU endpoint (3B.5) — gated on the bake-off comparison.
- **Road 3-A (VLM salvage) — teammate's court.** Not yet measured; targets exactly 3-B's blind
  spots (pulley, wing-beam), so the two may end up complementary rather than either-or.
- The plan sections below (Parts 1–2) are the original handoff/plan, kept for the contract,
  scoreboard, and 3-B gating steps — still the source of truth for *how* the bake-off is run.

---

# Part 1 — Phase 3 Bake-off (ACTIVE — teammate handoff)

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


---

# Part 2 — Road 3-B Plan (ACTIVE)

# Plan: Road 3-B — Deploy IndustReal ASD as ProcedureGuard's perception

Priya's half of the Phase 3 bake-off (see Part 1 above). Gated, spike-first:
each phase has a go/no-go before committing to the expensive next one. The biggest risk is
**"does the model produce sane output on our footage,"** not the Azure deployment — so that's
front-loaded.

**In our favor:** our clips *are* IndustReal clips (`industreal_selected/videos/`, same STEMFIE
kit), so the model was trained on this exact kit.

**Camera view — VERIFIED egocentric, risk LOW (June 24).** Pulled a frame from
`baselines/23_assy_0_1.mp4` (90s): clear first-person view — both the worker's hands reach in from
the near edge (wristwatch visible), head-mounted GoPro-style, NOT a fixed overhead rig. So our clips
are the raw IndustReal **egocentric** recordings = the exact view ASD trained on. (The "overhead"
language in `KNOWN_ISSUES.md` is imprecise — it's a downward-angled egocentric view.) Clip specs:
1280×720, 10 fps, 260s. Residual 3B.0 check: IndustReal records multiple synced streams — confirm
the ASD weights expect the egocentric one and match its input res/fps.

## Goal
Replace the GPT-4o-Vision eyes with IndustReal's Assembly State Detection (ASD), which outputs a
per-component state vector (`1` assembled / `-1` wrong / `0` absent) instead of vague prose. Feed it
into the same reasoning + harness behind the same `observations`-dict contract, head-to-head with
3-A on the three clips. End state: deployed on Azure ML under the managed identity.

## Rules (same as the bake-off)
- Only the eyes change. Reasoning (`compliance_engine.py`) + harness (`validate_error_clip.py`)
  frozen. Output = `observations` dict (`schemas/video_observations.json`) with `segments` +
  `observed_items`.
- Metric: **zero false positives first, recall second.** ASD can be wrong too — same bar; honest UTV
  beats a false alarm.
- Keep `pytest` green (69).

---

## 3B.0 — Recon (read only, ~1–2 hrs) · GATE: "is it runnable?"
Read the ASD subdir README in `github.com/TimSchoonbeek/IndustReal` + the paper's ASD section.
Answer in a scratch note:
1. **Architecture & deps** — what model (likely a Detectron2/Faster-RCNN-style detector, given bboxes)? torch version, CUDA, other libs?
2. **Input format** — expected camera view (egocentric vs fixed overhead), resolution, fps, per-frame vs per-clip.
3. **Output format** — exactly how the state vector + 22 subgoal states + bboxes come back; which index = which component.
4. **Inference entry point** — ready `demo.py`/`inference.py`, or assemble the forward pass yourself?
5. **Does our clip's view match its expected input?** Cross-check a frame from `baselines/23_assy_0_1.mp4`.

**Go/no-go:** usable inference script + our clips plausibly match the input → proceed. View mismatch
→ flag now, reconsider (AR model? Phi-4? mentors) before sinking time.

## 3B.1 — Local load + run spike (the critical gate) · GATE: "sane output on our footage?"
Cheap and local. The most important phase.
1. **Isolated env** (separate venv/conda — ASD's torch/detector deps will likely conflict with the main project; don't pollute it yet).
2. Download ASD weights from 4TU (`data.4tu.nl/datasets/b008dd74-020d-4ea4-a8ba-7bb60769d224`, Apache-2.0).
3. **Run their own demo on their own sample first** — confirm it loads/runs at all before blaming our data.
4. **Then run on `baselines/23_assy_0_1.mp4`** (clean clip). Inspect raw output: does the state vector
   evolve plausibly (parts flipping `0→1` in order)? CPU or GPU needed?

**Go/no-go:** sane, plausible state vector → proceed. Garbage/constant → doesn't generalize to our
view; stop and reconsider. **Do not touch Azure ML until this passes** (same mistake we avoided in
Phase 2 — don't build on an unproven signal).

## 3B.2 — Map ASD components → checklist (deterministic, offline, unit-testable)
Pure Python, no model calls — the cheap part, build and verify fast.
- Lookup table: each ASD component / subgoal-state index → GT checklist item (`check-001`…`check-006`).
  E.g. wheel components → `check-005`; pulley → `check-006`.
- Decision rule per item: component `1` in the relevant window → item evidenced (`observed_items`
  entry); component still `0`/`-1` past its assembly point → deviation signal.
- `test_asd_mapping.py` pinning the mapping, using a real sample ASD output from 3B.1. No GPU cost.

## 3B.3 — The adapter (perception producer behind the contract)
A function mirroring `run_video_phase2`'s role but via ASD:
- In: video path + checklist. Out: `observations` dict, `segments[]` with `observed_items`, schema-conformant.
- Internally: ASD inference over the clip → per-frame state → bucket into the harness's ~25s windows →
  set `action_observed`/`component_contact` from dominant state, `observed_items` from the 3B.2 mapping.
- Keep ASD inference behind a thin seam (function pointable at local OR an Azure ML endpoint) so
  3B.5 is a one-line swap.

## 3B.4 — Run the shared harness, measure · GATE: "beats the baseline cleanly?"
- All three clips through the harness with your adapter as the perception source.
- Record in `proofrun_*.json` format. Check in priority order:
  1. `23_assy_0_1` clean → **0 deviations** (non-negotiable).
  2. `23_assy_1_2` (−1 wheel) → flags **check-005** (the recall win text couldn't get).
  3. `22_assy_2_3` → pulley/wing-beam caught or honest UTV.
- This is the number that goes against 3-A. Clears zero-FP + lifts recall → value proven → deploy now.

## 3B.5 — Azure ML deployment (only after 3B.4 passes)
- **Target a CPU SKU (e.g. `Standard_F4s_v2`), not GPU** — *if* ASD is YOLOv8-m (confirm in 3B.0).
  Rationale: this is OFFLINE batch clip analysis, no real-time need; YOLOv8-m (~25M params) on a
  compute-optimized CPU runs ~hundreds of ms/frame, and we sample frames per window, not all 2600.
  GPU buys throughput we don't need and a GPU online endpoint is expensive to leave running for a demo.
  **Let the 3B.1 spike pick the SKU:** time inference on one clip on a laptop CPU — acceptable there →
  `F4s_v2` is fine; painfully slow → you'll know you need GPU before provisioning anything.
- Register the ASD model in Azure ML; deploy as a **managed online endpoint** on that SKU,
  authenticated via the **same managed identity** (no keys).
- Point the adapter's inference seam at the endpoint.
- Re-run the harness against the endpoint → confirm parity with local (deployment must not change verdicts).
- Cost note: a GPU online endpoint bills while running — document the SKU; consider scale-to-zero /
  on-demand for a demo rather than always-on.

## 3B.6 — Report for the bake-off
Before/after verdict tables on the 3 clips, clean-clip = 0 deviations confirmation, recall delta,
`observations` output for one clip (contract check), plus a one-paragraph ops note (deps, GPU, endpoint
cost) — 3-B carries more operational weight than 3-A, a fair factor in the final pick.

---

## Critical path
```
3B.0 read ─► 3B.1 LOCAL SPIKE ─►(gate)─► 3B.2 mapping ─► 3B.3 adapter ─► 3B.4 measure ─►(gate)─► 3B.5 Azure ML
              ▲ make-or-break gate                                       ▲ value proven, deploy only now
```
The whole plan hinges on **3B.1**. Sane state vector on our footage → the rest is plumbing. If not,
half a day found out instead of a week — the same trade that made Phase 1B recon and the Phase 2
negative result worth it.


---

# Part 3 — Superseded explorations (provenance, condensed)

Earlier perception planning, kept here as a one-paragraph pointer; full text in git history
(`VIDEO_INTELLIGENCE_RESEARCH.md`, `IMPROVEMENT_PLAN.md`, removed June 24).

- **Video-intelligence options study (June 18):** surveyed Option A full-coverage temporal
  inference (the `apply_absence_inference` post-pass — **shipped**), Qwen2.5-VL as a VLM swap,
  Azure Content Understanding / Video Indexer (**skipped** — no accuracy gain over OpenCV+GPT-4o),
  and the IndustReal model (then deemed out-of-scope). The bake-off later **reversed** that last
  call: deploying IndustReal ASD became Road 3-B once Phase-1B recon found published Apache-2.0
  weights.
- **Improvement plan (gap analysis):** flagged deviation **recall (~25%)** as the core gap over
  precision-first design, plus unwired durable storage (Cosmos/Blob) and Foundry-agent stubs. The
  recall gap is exactly what the perception bake-off (Parts 1–2) addresses; the storage/agent
  fidelity items are tracked in DECISIONS_AND_RATIONALE.md.
