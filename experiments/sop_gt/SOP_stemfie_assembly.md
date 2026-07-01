# STEMFIE Vehicle Kit — Assembly Procedure (GT-grounded)

> **Final version reconciled with the 6-item operational checklist.**
> Authored from the IndustReal action-recognition ground truth for the clean
> baseline reference take **`23_assy_0_1`** (the canonical correct assembly).
> Every step below corresponds to actions actually observable in the footage,
> phrased as *what the camera sees*, not as QA-framework prose.
>
> Source: IndustReal (Schoonbeek et al., WACV 2024) — `AR_labels`, ~9.8 fps.
> This assembly SOP covers the **assembly** clips (`22_assy_*`, `23_assy_*`).

---

## Section 0 — Scope & method *(reference only — NOT a verifiable step)*

This procedure governs the hand assembly of the STEMFIE construction-set vehicle.
All fastening is performed by hand (push-fit pins, finger-tightened screws, acorn
nuts); no power tools are used. Parts are colour-coded (white PLA braces/beams,
metal pins/washers/nuts). *This section is contextual and must be excluded from
the compliance verdict set — there is no physical action to observe.*

---

## Verifiable assembly steps

Each step lists the **observable action**, the **key objects** that should appear,
and the **expected verdict mode** (how the engine should be able to score it).

| # | Step (observable action) | Key objects | Expected mode |
|---|---|---|---|
| 1 | Mount the short braces onto the base frame and secure them with a short push-fit pin, a tooth-lock washer, and a hex nut. | base frame, short braces | **presence** |
| 2 | Attach the long brace to the assembly, align it, and secure it with a short push-fit pin, a tooth-lock washer, and a hex nut. | long brace | **presence / sequence** |
| 3 | Install an additional short push-fit pin at the next fastening point with a tooth-lock washer and a hex nut. | short push-fit pin | **presence** |
| 4 | Attach the wing beam and secure it in place with screw pins, a round washer, and an acorn nut. | wing beam | **presence** |
| 5 | Mount both wings and their wheels onto long pins and secure them with round washers, tooth-lock washers, and hex nuts. | wing, wheel | **presence** |
| 6 | Install the middle pin, mount a wheel and fit the pulley onto it, then secure with a round washer, a tooth-lock washer, and a hex nut. | middle pin, pulley, wheel | **presence** |

> **Note on torque and detail:** none of these steps claim to verify *tightness* — that's the
> genuinely-unverifiable fine-detail part and stays implicit. The verifiable claim
> is **component placement + fastener-stack presence**, which is what overhead
> video can actually show. A step like "verify torque to spec" would still
> (correctly) route to *Requires Inspection* — but we no longer manufacture a dozen
> of those out of document boilerplate.

---

## Provenance (operation → GT actions)

Derived grouping from `23_assy_0_1` (boundary at each `tighten_*` / model set-down):

- **Step 1** ← OP01: `take_short_brace > fit_short_brace ×2 > plug_short_pin > fit_tooth_washer > fit_nut > tighten_nut`
- **Step 2** ← OP03: `take_long_brace > align_objects > plug_short_pin > fit_long_brace > fit_tooth_washer > fit_nut > tighten_nut`
- **Step 3** ← OP05: `plug_short_pin > fit_tooth_washer > fit_nut > tighten_nut`
- **Step 4** ← OP07: `fit_wing_beam > put/plug_screw_pin > fit_round_washer > put_acorn_nut > tighten_acorn_nut`
- **Step 5** ← OP09: `put_wing > fit_wheel > plug_pin_long > fit_round_washer ×… > fit_tooth_washer > fit_nut > tighten_nut`
- **Step 6** ← OP11: `plug_pin_middle > fit_wheel > fit_pulley > fit_round_washer > fit_tooth_washer > fit_nut > tighten_nut`
