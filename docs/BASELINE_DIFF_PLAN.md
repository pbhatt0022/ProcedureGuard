# Implementation Plan — Deterministic Baseline-Diff Compliance Pass

**Status:** Proposed (supersedes the GPT-driven baseline-diff draft)
**Author basis:** VLM stability probe (June 22, 2026) + 3-clip re-measurement (`experiments/sop_gt/remeasure_*.json`)

---

## 1. Why this design (and why NOT the GPT-diff)

The earlier draft put baseline segments into the prompt and asked GPT-4o to compare
candidate-vs-baseline and decide. That **moves the non-determinism, it doesn't remove it** —
the pulley is still named randomly, so a GPT comparison still coin-flips. It also can't
catch *count* errors (one wheel instead of two) because it compares **presence**, not **quantity**.

The probe gives us a better lever:

| Part class | Naming stability (3 runs) | Implication |
|---|---|---|
| Core parts (wheels, wings, braces) | **100% stable** | Can be **counted deterministically** — no GPT needed for the comparison |
| Lookalike/unique (pulley, wing beam) | Unstable / generic | Baseline-diff **cannot** rescue these; defer to reference-image grounding |

**Design principle:** Do the comparison in **plain Python over a counted action signature.**
Keep GPT-4o only for perception (Phase 2 description), where it's already in use. The diff
itself becomes deterministic, debuggable, and reproducible.

**Explicit scope:**
- ✅ Fixes: count errors (`fit_wheel:-1`), omissions of stably-named parts.
- ❌ Out of scope (deferred to reference-image grounding): pulley/wing-beam lookalike confusion.
  These remain honest `Unable to Verify` — we do **not** pretend baseline-diff solves them.

---

## 2. Components

### 2.1 [NEW] `src/reasoning/action_signature.py`
Pure, deterministic, fully unit-testable. No GPT, no Azure.

- **`CANONICAL_ACTIONS`** — controlled vocabulary seeded from the IndustReal GT action set
  (`fit_short_brace`, `fit_long_brace`, `fit_wheel`, `fit_wing`, `fit_wing_beam`,
  `fit_pulley`, `plug_pin`, `fit_washer`, `fit_nut`, …). This is the shared "language"
  both runs are reduced to.

- **`canonicalize_window(segment: dict) -> list[str]`**
  Maps one Phase 2 window's `action_observed` + `description` + `component_contact` to
  zero or more canonical action tokens via a keyword table (e.g. `"wheel"`→`fit_wheel`,
  `"long beam"/"wing beam"`→`fit_wing_beam`). Deterministic; same input → same output.

- **`extract_signature(observations: dict) -> list[ActionEvent]`**
  Produces an **ordered, de-duplicated, counted** event list for a run.
  - **De-duplication is the key subtlety:** windows overlap by 6 s, so the same physical
    action appears in adjacent windows. Collapse repeats of the same canonical token whose
    time spans are within `OVERLAP_MERGE_SECONDS` into a single event. Distinct occurrences
    separated by other actions (e.g. wheel … wing … wheel) are kept as separate counts.
  - `ActionEvent = {action: str, count: int, first_seen_s: float, windows: list[str]}`

### 2.2 [NEW] Baseline signature artifact
- **`experiments/sop_gt/baseline_signature_23_assy_0_1.json`** — the **reference** signature.
- Built **once** from the **3 probe runs** by majority/intersection (an action counts only if
  it appears in ≥2 of 3 runs), so the reference is stable, not a single noisy pass.
- A small builder script `scripts/build_baseline_signature.py` generates it from the probe
  result JSONs. Re-runnable when the baseline clip or vocab changes.

### 2.3 [NEW] `compare_signatures(baseline, candidate) -> list[SignatureDelta]`
(lives in `action_signature.py`)
- Sequence-aligns the two signatures (LCS/Needleman-Wunsch over canonical tokens) so it's
  robust to pace, pauses, and minor reordering — **not** naive time-window matching.
- Emits per-action deltas: `expected_count` vs `observed_count`.
  - `observed < expected` → **missing/reduced** (candidate deviation)
  - `observed > expected` → **extra/rework** (flag, lower severity)
  - equal → match.

### 2.4 [MODIFY] `src/reasoning/compliance_engine.py`
- **New deterministic post-pass** `apply_baseline_diff(verdicts, observations, baseline_signature, checklist_items)`,
  run alongside the existing `enforce_unique_evidence` / `apply_absence_inference` guards.
- For each checklist item, map it to its canonical action(s). If `compare_signatures` shows a
  negative delta for that action **and** the part is in the *stable* class, set
  `Deviation Detected` with `reasoning` citing the count delta and the baseline windows.
- **Guardrail:** never override a positive A1 vision flag for the SAME item (reuse
  `_vision_flagged_map`); and only act on stable-class actions (a curated allowlist) so the
  unstable pulley/beam are left as `Unable to Verify`.
- `reason_step` signature is **unchanged** — this is a separate deterministic pass, keeping the
  existing 69 tests' contracts intact.

### 2.5 [MODIFY] `scripts/validate_error_clip.py`
- Add `--baseline-signature <path>` (default: the 23_assy_0_1 reference artifact).
- Load the reference signature and call `apply_baseline_diff` after the existing guards.
- Report unchanged (it already prints TP/FP/FN + precision/recall).

### 2.6 [DEFER] `src/pipeline.py`
- Wiring the baseline-diff into the live pipeline happens **after** the harness proves the
  numbers. Not in this change — avoids touching production flow before validation.

---

## 3. Verification Plan

**Gate (must beat Phase 0 baseline of 0/4 recall, 1 FP):**

1. **Unit tests (deterministic, no GPT):**
   - `canonicalize_window` keyword mapping table.
   - `extract_signature` overlap de-duplication (the wheel-counted-once-not-twice case).
   - `compare_signatures` delta math (2 vs 1 wheel → one missing).
   - `apply_baseline_diff` respects the A1 flag guard and the stable-class allowlist.
   - `python -m pytest` — all existing 69 + new tests pass.

2. **Manual / harness (the real proof):**
   - `23_assy_1_2` (`fit_wheel:-1; fit_wing:-1`) → **check-005 Deviation Detected** (the count error we currently miss).
   - `22_assy_2_3` → wing-beam/pulley **remain UTV** (honest; not falsely "fixed").
   - `23_assy_0_1` clean **against the reference** → **0 deviations** (no false alarms — the non-negotiable).

**Success = recall up on the count error, zero new false positives on the clean clip.**

---

## 4. What this explicitly does NOT claim
- It does **not** fix the pulley or wing-beam (lookalike/generic naming). Those stay UTV and
  are the subject of the *separate* reference-image-grounding workstream.
- It does **not** touch the live pipeline or dashboard yet (Phase 4).

---

## 5. Task checklist

- [ ] `action_signature.py`: `CANONICAL_ACTIONS`, `canonicalize_window`, `extract_signature` (+ overlap de-dup), `compare_signatures` (+ alignment)
- [ ] `scripts/build_baseline_signature.py` + generate `baseline_signature_23_assy_0_1.json` from the 3 probe runs (majority rule)
- [ ] `compliance_engine.py`: `apply_baseline_diff` deterministic post-pass + A1-flag/stable-class guards
- [ ] `validate_error_clip.py`: `--baseline-signature` wiring
- [ ] Unit tests for all of the above; `pytest` green
- [ ] Harness re-measure on the 3 clips; compare to Phase 0; record in `experiments/sop_gt/`
