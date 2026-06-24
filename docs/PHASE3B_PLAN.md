# Plan: Road 3-B — Deploy IndustReal ASD as ProcedureGuard's perception

Priya's half of the Phase 3 bake-off (see `docs/PHASE3_BAKEOFF.md`). Gated, spike-first:
each phase has a go/no-go before committing to the expensive next one. The biggest risk is
**"does the model produce sane output on our footage,"** not the Azure deployment — so that's
front-loaded.

**In our favor:** our clips *are* IndustReal clips (`industreal_selected/videos/`, same STEMFIE
kit), so the model was trained on this exact kit. The real unknown is whether our clips match the
*camera view* the ASD model expects.

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
- Register the ASD model in Azure ML; deploy as a **managed online endpoint** (GPU SKU if 3B.1 needed
  one), authenticated via the **same managed identity** (no keys).
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
