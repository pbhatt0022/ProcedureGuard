# ProcedureGuard — UI/UX Build Plan

> A complete brief for the engineer building the ProcedureGuard interface from scratch.
> Read this top to bottom before writing a line of code. The visual tokens live in
> [`DESIGN-ProcedureGuard.md`](DESIGN-ProcedureGuard.md) (colors, type, spacing, radius,
> elevation, component primitives) — that file is the source of truth for *what things look
> like*. This file is the source of truth for *what we are building, for whom, and why each
> screen is shaped the way it is*.

---

## 0. The 30-second version

You are building an **evidence console** for a Quality Assurance Manager who has to defend a
compliance record in an FDA / ISO 13485 audit. The product reads an SOP PDF and a production
video and returns per-step verdicts. The interface's only job: let that manager open a run,
understand what happened, confirm the deviations, and file a record — **in under two minutes,
with every verdict traceable to evidence.**

This is not a dashboard to admire. It is an instrument to act through. Build it like Linear or
Stripe's console built a regulated-manufacturing tool: calm, dense, fast, and quietly precise.
Then add the layer most enterprise tools skip — the *craft* (motion, focus, state transitions,
the evidence-reveal moment) that makes it feel trustworthy rather than merely functional.

---

## 1. Who we are building for

**Vikram Nair — Quality Assurance Manager, mid-size medical-device contract manufacturer.**

| Trait | Implication for the UI |
|---|---|
| Subject to FDA, CE Mark, ISO 13485 audits | Everything must be traceable. No verdict without evidence. The word "certify/guarantee" never appears. |
| Reviews results at a workstation, *after* a run — not on the shop floor in real time | Desktop-first, keyboard-driven, dense. No mobile-first compromises, no "live monitoring" theatrics. |
| Fluent in SAP, Jira, clinical QMS software | Standard patterns only. He should never have to learn an invented affordance. Familiar = trustworthy. |
| Under time pressure before the next run | The first screen must answer "what needs my attention?" in one glance. Speed is a feature. |
| Paper checklists cover only ~5% of volume; deviations go unrecorded | He is replacing a manual process. The tool must feel *more* rigorous than paper, not less. |

**The job-to-be-done, stated as Vikram would say it:**
> "Show me this run. Tell me what passed, what deviated, and what you couldn't see. For
> anything that deviated, show me the exact moment in the video and the exact SOP line, so I
> can confirm it and file the non-conformance. Don't make me trust you blindly — let me check
> your work."

**Design north star (one sentence):**
*"I can defend this record in an audit because every verdict has traceable evidence — and the
tool made that defense fast."*

---

## 2. Design philosophy

This synthesizes three inputs: the project's own `PRODUCT.md` principles, the Fluent/Azure
token system in `DESIGN-ProcedureGuard.md`, and the craft sensibility from Emil Kowalski's
design-engineering philosophy + the impeccable production bar. Where they tension, the order of
priority is: **trust → legibility → speed → delight.** Delight never competes with the first
three; it reinforces them.

### 2.1 The five principles (non-negotiable)

1. **Data is the hero.** Every layout decision serves legibility of verdicts, timestamps, and
   reasoning. No decoration competes with content. The SOP step verification table is the
   protagonist of the entire product — design everything else to feed it or follow from it.

2. **Confidence through precision.** Exact numbers, exact timestamps (`00:01:18–00:01:31`),
   exact step IDs (`step-014`, `check-011`). Round numbers and vague labels erode trust in a
   compliance tool. Show `74%`, never "low confidence." Show `2 of 24 verifiable steps`, never
   "most steps."

3. **Abstain clearly.** *Unable to Verify* and *Requires Inspection* are first-class outcomes,
   not failure states to hide. The visual language must make abstention as readable and as
   dignified as a pass. This is the product's integrity story — it is the reason a regulator
   trusts it.

4. **Earn familiarity.** Standard components, standard patterns. App shell + left nav + command
   bar + details table + evidence drawer. Someone fluent in Linear/Notion/Azure Portal is
   productive in 30 seconds. No invented navigation.

5. **Instrument, not app.** Density is correct. A 29-row table is expected and good. Do not pad,
   simplify, or "consumerize" the data. Compactness *is* the premium feel here.

### 2.2 Hard anti-references (do not ship these)

These come straight from `PRODUCT.md` and are absolute:

- ❌ Gradient text, glassmorphism, purple-blue "AI" palettes, animated orbs, glowing borders.
- ❌ Hero big-number cards with gradient accents. (Plain KPI cards, yes. Gradient KPI cards, no.)
- ❌ Cream / warm-neutral "startup SaaS" backgrounds. The canvas is white and cool-neutral.
- ❌ Anything that reads as "a Claude/AI demo" or "investor landing page." The audience is
  engineers, not investors.
- ❌ Marketing rhythm: oversized heroes, decorative illustrations, alternating dark promo bands.
- ❌ "AI magic" visuals. Confidence is shown as a sober number, not a sparkle.
- ❌ Color-only status encoding. Every verdict carries an icon + a text label, always.

### 2.3 Where we "go beyond the basics" (the craft layer)

The Fluent token file gives a competent enterprise baseline. A competent baseline is not the
goal — the user explicitly asked for *amazing*. The differentiation is **invisible correctness
that compounds** (Emil's thesis). Concretely, the moves that lift this above a stock Fluent
dashboard:

- **The evidence-reveal moment.** Clicking a step row opens the evidence drawer with a fast,
  origin-aware transition and a 1-frame keyframe that settles into place. This is the emotional
  core of the product — the instant the verdict becomes *defensible*. It deserves real motion
  craft (see §8).
- **A deviation timeline scrubber** synced to the video — a horizontal filmstrip of the run
  where deviations sit as red ticks. Click a tick → drawer + video seek. This is the one piece
  of "data viz" that earns its place because it maps directly to "when did it happen."
- **Confidence as a quiet, honest visual** — a thin determinate meter inside the pill area, not
  a number floating alone. Tier it (high/medium/low) with the score colors, never with alarm.
- **Keyboard-first review flow.** `j`/`k` to move through steps, `Enter` to open evidence,
  `c`/`d`/`u` to set reviewer disposition, `e` to export. A power QA reviewer should be able to
  clear a queue without touching the mouse. (This is the single biggest "feels pro" lever.)
- **Stable, fast, interruptible transitions.** Tabs, drawer, row selection — all use CSS
  transitions under 250ms with strong custom easing, all respecting `prefers-reduced-motion`.
- **Optical precision.** Tabular numbers for all metrics, monospace for IDs/timestamps,
  sticky table header, consistent 4px-grid spacing, no accidental misalignment. The thousand
  barely-audible voices singing in tune.

---

## 3. Recommended tech stack

The current implementation is a Streamlit dashboard (`src/dashboard/`). Streamlit is excellent
for the pipeline-engineer's internal tool, but it caps the craft ceiling: you cannot get
origin-aware drawers, keyboard navigation, real focus management, or interruptible motion out of
it. Since the brief is "build an app from scratch" that "looks amazing, beyond the basics,"
build a real frontend and feed it the pipeline's JSON.

**Recommended:**

| Layer | Choice | Why |
|---|---|---|
| Framework | **Next.js (App Router) + React + TypeScript** | App-surface interactivity, routing per run, server components for fast first paint of dense tables. The persona's mental model is "an app," not "a notebook." |
| Styling | **Tailwind CSS** with the design tokens wired into `tailwind.config` (or CSS custom properties from §6) | Token-driven, dense utility control, zero runtime cost. Map every token in `DESIGN-ProcedureGuard.md` to a CSS variable + Tailwind alias. |
| Components | **Radix UI primitives** (Dialog/Drawer, Tabs, Tooltip, Dropdown, Popover) styled to Fluent | Accessible, focus-trapped, origin-aware popovers for free. Do not pull in a heavy themed kit (MUI/AntD) — it will fight the token system. |
| Tables | Headless: **TanStack Table** | Sort/filter/virtualize a 29+ row step table without inventing it. Virtualization matters once runs have 100+ steps. |
| Icons | **Fluent UI System Icons** (outline, 16/20px) | Native Microsoft feel; matches the iconography list in the token file. One set only. |
| Motion | **CSS transitions + `@starting-style`** for enter/exit; **Motion (Framer Motion)** only for the drawer + timeline scrubber where interruptible springs help | Per Emil: CSS for predetermined motion (off main thread, smooth under load), JS only for dynamic/interruptible. |
| Fonts | **Segoe UI** stack with system fallbacks; **Cascadia Mono** for IDs/timestamps/logs | Exactly as specified in the token file. Self-host Cascadia Mono; Segoe is system on Windows, fall back to `system-ui`. |
| Data | Read the pipeline's `verification_record` JSON (see §9). Static import for the demo runs; a thin `/api/runs/[id]` route for live runs. | The contract already exists — do not redesign the data model. |
| Charts | Hand-rolled SVG for the adherence ring + verdict stack-bar + deviation timeline. No charting lib. | Three bespoke, restrained visuals. A charting library would import a whole aesthetic we explicitly reject. |

**If the team must stay in Streamlit** (timeline/scope constraint): keep the current
`src/dashboard/` structure, but treat §5–§8 here as the target and push as far as custom CSS +
`st.components.v1.html` islands allow. The React build is the recommendation; Streamlit is the
fallback, not the goal.

---

## 4. Information architecture

```
App shell
├── Top command bar  (identity · run selector · global search · primary actions · user/help)
├── Left nav         (persistent, collapsible 240 → 56px)
│   ├── Dashboard            ← cross-run operational overview
│   ├── Verification runs    ← list of runs; click → Run Detail (the core surface)
│   ├── SOP library          ← SOP sources + extracted checklists
│   ├── Video evidence       ← videos + analyzer outputs
│   ├── Deviations           ← cross-run deviation queue
│   ├── Human review         ← the reviewer's work queue
│   ├── Audit trail          ← run-scoped event log (also embedded per run)
│   └── Settings
└── Content canvas   (white; page header + body; optional right evidence drawer/split pane)
```

**Primary surface = Verification Run Detail.** 80% of Vikram's time is here. Everything else
exists to get him into a run or to aggregate across runs. Build Run Detail first and best.

**Navigation depth = 2.** Shell → list → detail. Never make the reviewer dig a third level for
evidence; evidence is a drawer over the detail, not a new page.

---

## 5. Screen-by-screen specification

For each screen: purpose, layout, components, states, and the one thing that must be right.

### 5.1 Verification Run Detail — the hero screen

**Purpose:** the complete, evidence-backed result for one production run. Answer in order:
*What happened? What needs review? Can I defend each verdict?*

**Layout (top to bottom):**

1. **Page header** — run ID (mono), SOP name, video name, generated timestamp, analyzer/model
   version, segment count + duration. A workspace status badge (`Deviation review required` /
   `Manual inspection required` / `Ready for export`) that color-keys the whole run. Primary
   actions right-aligned: **Export report**, **Send for review**, **Re-run**.

2. **KPI summary row** — five compact cards, one number each, no charts inside:
   - **Overall adherence** — large %, with the caption `2 of 2 verifiable steps compliant`.
     Adherence = Compliant ÷ (Compliant + Deviation). *Requires Inspection* and *Unable to
     Verify* are excluded from the denominator — state this in the caption so the number is
     never misread. Pair with a small SVG progress ring (the one sanctioned ring).
   - **Compliant** (count, green) · **Deviations** (count, red) · **Unable to verify**
     (count, amber) · **Requires inspection** (count, purple/review).
   - Each card is a filter: clicking it filters the step table below to that verdict.

3. **Verdict distribution stack-bar** — a single horizontal bar segmented by the four verdicts,
   labeled with counts. This replaces a pie chart. It doubles as a legend.

4. **Deviation timeline** (signature component, §7) — horizontal filmstrip of the run duration
   with deviation/inspection ticks positioned by timestamp. The product's "when did it happen."

5. **SOP step verification table** (the protagonist, §6.5) — sticky-header DetailsList. Default
   sorted by sequence; one-click sort by verdict/confidence/review status; filter chips for the
   four verdicts + "needs review." Row click opens the evidence drawer.

6. **Audit trail** (collapsible, or its own tab) — the run's event timeline (§5.5).

**Tabs vs. single scroll:** the current Streamlit build uses tabs (Overview / Step verification
/ Evidence / Human review / Audit / Ask). Keep that tab spine in the React build — it matches
the persona's mental chunks and keeps each surface dense. *Overview* = KPIs + distribution +
timeline + the deviation/attention shortlist. *Step verification* = the full table + drawer.

**The one thing that must be right:** the path from "I see a red deviation count" → "I'm looking
at the exact video frame and SOP line that justify it" must be **two clicks and under one
second.** Time it. If it's slower, the screen has failed its only job.

**States:** loading (skeleton rows, not a spinner over blank), empty (no run selected → the
demo-library launcher), error (pipeline failed → clear message + retry), large (100+ steps →
virtualized table, sticky header holds).

### 5.2 Dashboard (cross-run overview)

**Purpose:** operational overview before drilling into a run.

Sections: recent verification runs (compact list with run ID, SOP, adherence, status, age) ·
open deviations across runs · human-review queue depth · SOPs used recently · a small verdict
trend across recent runs (sparkline — the *only* place a trend line is allowed, and only if real
data exists). No hero. No welcome copy. This is a desk, not a lobby.

### 5.3 Human Review Queue

**Purpose:** help Vikram process ambiguous / high-risk items efficiently.

A focused worklist of items requiring a human: every Deviation Detected, Requires Inspection,
and Unable to Verify across the active run (or all runs). Columns: priority, step, verdict,
confidence, evidence timestamp, assigned reviewer, SLA/due. Row → evidence drawer with the
reviewer disposition controls front and center.

**Review states** (explicit, never auto-finalized): Not reviewed → Review required → In review →
Confirmed compliant / Confirmed deviation / Marked unable to verify / Escalated. The system must
**never auto-finalize a low-confidence or abstained finding** — and the UI must make that safety
visible (e.g., "Draft — pending reviewer sign-off" watermark on unreviewed reports).

Disposition controls in the drawer: **Confirm model verdict** · **Override verdict** · **Add
reviewer note** · **Assign reviewer** · **Escalate**. Keyboard: `c` confirm, `d` deviation,
`u` unable, `n` note.

### 5.4 SOP Library & Video Evidence

**SOP Library:** file list, version, extraction coverage (`29 of 31 steps extracted`), count of
verifiable steps, last-used run, checklist preview. The checklist preview shows the
verifiability tier of each step (presence / sequence / fine_detail) so the reviewer understands
*before* a run why some steps will route to inspection.

**Video Evidence:** video file, duration, segment count, analyzer status, extracted observation
count, linked SOP/run. A reviewer lands here to confirm the footage is raw (some IndustReal
clips ship as annotated renders — flag those loudly, they invalidate a run).

### 5.5 Audit Trail

Per-run event timeline, audit-ready. Each event = timestamp · actor (System / analyzer /
reviewer name) · action · object (SOP / video / step / report) · note · run/version ID.
Events: SOP uploaded → parsed → checklist generated (`28 verifiable steps, 3 duration checks`) →
video uploaded → analyzer completed → reasoning completed → deviation detected (with evidence
window) → reviewer opened item → reviewer changed verdict → report exported. Left-rail timeline
treatment (2px primary border-left), monospace timestamps, color-keyed actor tone.

### 5.6 Report Export

Formal and defensible. A preview of the exact record that leaves the building: SOP name +
version, video file, production run ID, generated timestamp, analyzer + model/deployment
version, overall adherence, step-level verdict table, deviations, unable-to-verify steps,
reviewer decisions, audit timeline, and a **required "Limitations & human-review" statement**
(this is a research prototype; verdicts require human review before any quality decision).
Buttons: Export PDF · Export CSV · Save to archive · Copy summary · Send for review. Unreviewed
runs export as **Draft** only.

### 5.7 Ask (Q&A chat) — secondary, not central

Agent 3 lives here. Keep it as a tab, not a floating bubble. It answers questions over the run
("which steps had no evidence?") and cites back to steps/timestamps. Per `PRODUCT.md`, the
evidence drawer — not the chatbot — is where trust is built; the chat is a convenience, sized
accordingly. Every chat answer that references a verdict must link to the step row.

---

## 6. The component system

Pull all values from [`DESIGN-ProcedureGuard.md`](DESIGN-ProcedureGuard.md). Below is how to
*use* them, plus the few components that file leaves to interpretation.

### 6.1 Tokens → CSS variables (wire these once)

Mirror the token file into `:root` custom properties (the existing Streamlit `app.py` already
does a version of this — reuse those variable names for continuity): `--pg-primary #0078D4`,
`--pg-canvas`, `--pg-surface`, `--pg-ink #201F1E`, `--pg-muted #605E5C`, the four semantic
families (success/error/warning/review each with text + bg), score colors, hairlines, focus
ring, the elevation ramp, and radius scale (4–8px Fluent radius — never 0px square, never pill
except on status chips and toggles).

> **One contrast fix to carry over:** the token file lists `semantic-warning #797673` (a gray)
> for "Unable to verify" text, which is too low-contrast as a label color. The shipped Streamlit
> build already corrected this to `#8A6A00` on `#FFF4CE`. Use `#8A6A00` for warning text to
> meet WCAG AA. Keep the amber background.

### 6.2 Status & verdict badges (icon + label + color, always)

| Verdict | Text | BG | Icon (Fluent) |
|---|---|---|---|
| Compliant | `#107C10` | `#DFF6DD` | CheckmarkCircle |
| Deviation Detected | `#D13438` | `#FDE7E9` | ErrorCircle |
| Requires Inspection | `#5C2E91` | `#F3EAFF` | PersonFeedback |
| Unable to Verify | `#8A6A00` | `#FFF4CE` | Warning |
| Processing | `#0078D4` | `#EFF6FC` | Sync (animated, the one sanctioned spinner) |

Pill shape (`rounded.pill`), `2px 8px` padding, `body-emphasis` weight. **Never** render a
verdict as color alone — the icon and label travel together everywhere (table, drawer, timeline,
KPI cards). This is both an accessibility requirement and the trust story.

### 6.3 Confidence chip

A compact chip showing the exact percent + a 3px determinate meter beneath it, tinted by tier:
high ≥85 `score-high`, medium 60–84 `score-medium`, low <60 `score-low`. Caption nearby (or in
the drawer): *"Confidence reflects available visual evidence, not final quality disposition."*
Never alarm-style; this is information, not a warning.

### 6.4 KPI card

Surface-1, hairline border, 6px radius, subtle elevation. One big number (`display-md`, tabular
figures), a label above (`caption`, uppercase, subtle), a one-line explanatory caption below.
Optional small ring only on the adherence card. Hover: border → primary, 1px lift
(`translateY(-1px)`), 160ms. Clickable cards get `:active { scale(0.98) }` and a real focus ring.

### 6.5 SOP step verification table (DetailsList) — the protagonist

Columns: **Step** (mono `step-014`) · **SOP criterion** (truncated to ~2 lines, full on hover/
drawer) · **Check type** (presence / sequence / fine_detail) · **Verdict** (badge) ·
**Confidence** (chip) · **Evidence** (timestamp chip `00:01:18–00:01:31`, or "No evidence
window") · **Reviewer status** (pill) · **Action** ("View evidence").

Behavior:
- Sticky header (40px), compact rows (36px default; 44px comfortable toggle).
- Sortable: verdict, confidence, step, review status. Default = sequence ascending.
- Filter chips: Compliant / Deviation / Unable / Inspection / Needs review. KPI cards drive the
  same filter.
- **Status left-rail:** deviation rows get a 2px red left border, inspection purple, unable
  amber — a quiet scan cue *in addition to* the badge, never instead of it.
- Row states: hover (`surface-hover`), selected (`surface-selected` + primary left rail),
  focus-visible (2px primary ring). Selected row stays highlighted while its drawer is open.
- Row click / `Enter` → evidence drawer. The whole row is the target; "View evidence" is a
  secondary affordance, not the only one.
- Empty filter result → inline empty state ("No steps match this filter"), not a blank table.

### 6.6 Evidence drawer / split pane (where trust is built)

Right-side drawer (Radix Dialog, ~480px, focus-trapped) over the run detail. Origin-aware:
slides + scales subtly from the right, `--ease-drawer cubic-bezier(0.32,0.72,0,1)`, ~280ms in /
200ms out. Sections, in order:

1. **Verdict summary** — `Deviation detected · Confidence 74%` with badge + confidence meter.
2. **Video evidence** — keyframe thumbnail + timestamp window + **"Open video at 00:01:18"** (a
   real seek into an embedded `<video>` or the source clip). The keyframe is the hero image of
   the drawer; load it with a 1px blur-up so it settles rather than pops.
3. **SOP requirement** — the verbatim SOP excerpt the step maps to. Quoted, serif-free, exact.
4. **Observed action** — the structured model observation for the matched segment.
5. **Reasoning summary** — the GPT reasoning, plainly worded. For *Requires Inspection*, this is
   the honest "fine-detail QC not assessable from overhead 1fps/512px video — routed to manual
   inspection" line. Render abstention reasoning with the same dignity as a pass.
6. **Reviewer decision** — `Confirm deviation` · `Mark compliant` · `Unable to verify` · `Add
   note` · `Assign`. Keyboard-bound. State persists to the review queue.
7. **Audit log** — the per-step slice of the audit trail.

Keyboard inside drawer: `Esc` closes (smoothly reverses), `j`/`k` moves to next/prev step
*without closing* (the drawer retargets its content — this is the power-reviewer superpower).

### 6.7 Command bar & left nav

Command bar: 48px, white, 1px bottom hairline, subtle shadow. Identity left, run selector +
global search center-left, primary actions right (`Run verification` primary; Upload SOP / Upload
video / Export secondary; overflow menu for the rest). Left nav: 240px expanded / 56px collapsed,
icon + label, selected item = soft blue background **+** primary left rail **+** semibold label
(never color alone). Active route is obvious without reading.

### 6.8 Inputs, tabs, callouts

Inputs: 32px min height, 4px radius, hairline-strong border, primary border + 2px focus ring on
focus. Tabs: underline-style, selected = primary text + 2px primary underline +
`surface-selected`. Callouts (info/warning/error): tinted bg + 4px semantic left border, used
for the limitations notice and coverage warnings. All per token file.

---

## 7. Signature component: the deviation timeline

This is the one bespoke data-visualization that earns its place, because it answers Vikram's
literal question "when did it happen?" and ties evidence to the video.

- A horizontal track representing the full run duration (`0:00 → 5:06`), `surface-2`, 8px radius.
- Tick marks positioned by `evidence_timestamp_start`. Deviations = red ticks (tallest),
  inspection = purple, unable = amber (shortest), compliant = faint green hairlines.
- Hover a tick → tooltip (instant after the first, per Emil's tooltip rule) with step ID +
  verdict + window.
- Click a tick → opens the evidence drawer for that step **and** seeks the embedded video.
- A playhead line tracks the embedded video's `currentTime` so scrubbing the video moves the
  timeline and vice versa — they are two views of one truth.
- Respect reduced motion: the playhead still moves (it's information), but no decorative easing.

Build it as inline SVG. No library. Keep it to ~64px tall — it's a scanner, not a chart.

---

## 8. Motion system (the craft layer)

From Emil Kowalski's framework. Motion here is **crisp and fast** — this is a professional
instrument, so match the motion to that mood (no bounce, no playfulness).

**Tokens (define once):**
```css
--ease-out: cubic-bezier(0.23, 1, 0.32, 1);      /* enter/exit, the default */
--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);  /* on-screen movement */
--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);   /* the evidence drawer */
```

**Rules:**
- **Never animate keyboard-initiated actions.** `j`/`k` row movement, tab switches via keyboard,
  command-palette toggles → instant. These happen hundreds of times in a review session;
  animating them makes the tool feel slow. (This is the single most important motion decision in
  the whole product.)
- Durations: button press 100–160ms · tooltips 125–200ms · dropdowns 150–250ms · drawer
  200–280ms. Nothing over 300ms.
- Easing: `ease-out` for enter/exit; never `ease-in` on UI. Custom curves only — the built-in
  CSS easings are too weak.
- Buttons/rows/cards: `transform: scale(0.97-0.98)` on `:active` for "the UI heard you."
- Never animate from `scale(0)` — start at `scale(0.95)` + `opacity:0`. Use `@starting-style`
  for enter.
- Popovers/menus: `transform-origin` = trigger (Radix gives you the CSS var). The drawer scales
  from the right edge; modals (rare here) stay centered.
- Only animate `transform` and `opacity` (GPU). Never animate height/width/padding for motion.
- Use CSS transitions (interruptible) for anything rapidly retriggered (row selection, filter
  changes, drawer retarget on `j`/`k`). Reserve Motion/JS springs for the drawer + timeline
  scrubber only.
- Keyframe-reveal on first table paint: subtle stagger (40–60ms between rows, cap the total) —
  decorative, never blocking. Skip entirely under reduced motion.
- `prefers-reduced-motion`: keep opacity/color transitions that aid comprehension; remove
  position/scale motion. The deviation playhead remains (it's data).

**Loading:** skeleton rows for the table (shape-preserving), the `Sync` spinner only for live
pipeline runs. A faster spinner reads as a faster app — keep it brisk.

---

## 9. Data contract (build against this, don't redesign it)

The pipeline already emits the record the UI renders. Source of truth:
[`schemas/verification_record.json`](../schemas/verification_record.json) and the demo files at
the repo root (`demo_results_industreal_*.json`). The normalizer in
[`src/dashboard/components/common.py`](../src/dashboard/components/common.py) is the reference
for how raw records become UI rows — port its logic to TypeScript.

**Top-level run object:**
```jsonc
{
  "run_id": "run-20260618-1e0ebcb5",
  "sop_steps":   { "sop_document", "extracted_at", "total_steps", "steps": [...] },
  "checklist":   { "items": [ { "item_id", "step_id", "criterion", "check_type", ... } ] },
  "observations":{ "video_file"|"video_url", "video_duration_seconds",
                   "analyzer_id", "total_segments", "segments": [...] },
  "verdicts": [ /* one per checklist item — see below */ ],
  "adherence_score": 1.0,
  "summary": { "total", "compliant", "deviation", "unable_to_verify",
               "requires_inspection", "adherence_score" }
}
```

**Per-verdict row (the table's atom):**
```jsonc
{
  "item_id": "check-011", "step_id": "step-014", "sequence": 14,
  "criterion": "Worker attaches Y-axis motor to frame using screws",
  "verdict": "Compliant" | "Deviation Detected" | "Requires Inspection" | "Unable to Verify",
  "confidence": 0.74,                      // 0–1 → render as exact %
  "evidence_segment_id": "seg-001",
  "evidence_timestamp_start": 73.0,        // seconds → format mm:ss
  "evidence_timestamp_end": 91.0,
  "keyframe_blob_path": "keyframes/<run>/<step>.jpg" | null,
  "reasoning": "…",                        // drawer reasoning summary
  "sequence_ok": true|false|null,          // → "Out of order" flag
  "duration_ok": true|false|null,          // → "Duration exception" flag
  "not_observed": false,                   // absence-inferred deviation
  "created_at": "2026-06-08T10:06:00Z"
}
```

**Derived fields the UI must compute** (mirror `common.py`):
- **Adherence** = `compliant / (compliant + deviation)`; caption must say "of verifiable steps"
  and exclude inspection + unable from the denominator. Don't recompute differently.
- **Review queue count** = deviation + unable + inspection.
- **Workspace status/tone** = deviation→critical, else inspection/unable→review, else
  score≥0.95→clear, else below-threshold→critical. Drives the run's header badge.
- **Segment match** for the drawer = match `evidence_segment_id`, else overlap by timestamp
  window (see `find_matching_segment`).
- **Audit events** are *synthesized* from the record today (no stored `audit_trail` key) — port
  `build_audit_events`. When the pipeline later persists real events, swap the source; keep the
  component.
- **Keyframes** may be `null` for inspection/unable rows (no frame to show) — the drawer must
  render gracefully without an image (show the timestamp + reasoning, omit the thumbnail).

**Demo data to build against:** load `demo_results_industreal_22_assy_2_3_candidate.json`
(honest mix: 2 compliant, 0 deviation, 8 unable, 19 inspection — exercises every abstention
path), `..._23_assy_0_1_baseline.json`, and `..._16_main_3_3_candidate.json`. If you build the
abstention-heavy run beautifully, the easy all-green run is free.

---

## 10. Accessibility (WCAG AA, non-negotiable for a regulated tool)

- Body text and verdict labels meet **4.5:1** contrast (hence the `#8A6A00` warning fix in §6.1).
- **No color-only encoding** — every verdict = icon + label + color. Every status pill carries
  text.
- Visible focus rings everywhere (2px primary, 2px offset). This tool is keyboard-driven by
  design — focus must always be locatable.
- Full keyboard path: command bar → nav → table row → evidence drawer → reviewer controls →
  export, with no mouse-only affordance anywhere. Drawer is focus-trapped; `Esc` returns focus
  to the originating row.
- Video evidence has text equivalents: timestamp, observed action, SOP excerpt, reasoning — a
  screen-reader user gets the full case without the frame.
- No table text below 12px. Descriptive labels: "View evidence for step 14," not "View."
- `prefers-reduced-motion` honored throughout (§8).
- Tabular numbers for all metrics so columns don't jitter; `aria-sort` on sortable headers;
  `aria-live="polite"` on filter-result counts and toast confirmations.

---

## 11. Microcopy

Precise, never promotional. The system evaluates *procedure-execution evidence*, not worker
performance — copy reflects that throughout.

**Use:** "Deviation detected" · "Unable to verify from available video evidence" · "Requires
inspection — fine-detail check, routed to a human" · "Human review required before final report"
· "Open video at 00:01:18" · "SOP Step 04: PPE must be visible before component contact" ·
"Confidence reflects available visual evidence, not final quality disposition."

**Never:** "AI found a mistake!" · "Fully automated quality decision" · "Guaranteed compliance"
· "Certified" · "Worker violation" · "Surveillance result." Never imply automated regulatory
approval.

Empty states are instructive, not cute: "No deviations in this run." / "Load a saved report to
see the full review workflow." Errors are specific and recoverable: "Pipeline failed: video URL
unreachable. Check the SAS token expiry and retry."

---

## 12. Build sequence (suggested phases)

1. **Foundation.** Token → CSS-variable layer, Tailwind config, font loading, app shell
   (command bar + collapsible nav + canvas), routing, the TS port of `common.py` normalizer +
   demo-JSON loading. *Exit:* a styled empty shell that loads a demo run into memory.
2. **The protagonist.** Run Detail page header + KPI row + verdict stack-bar + the step
   verification table (sort/filter/sticky/states). No drawer yet. *Exit:* you can scan a run.
3. **The trust moment.** Evidence drawer with all seven sections, keyframe blur-up, video seek,
   origin-aware motion, `j`/`k` retarget. *Exit:* two clicks from deviation count to evidence.
4. **The scanner.** Deviation timeline synced to the embedded video.
5. **The workflow.** Human review queue + reviewer disposition + review states + draft/final
   gating + audit trail.
6. **The perimeter.** Dashboard, SOP library, Video evidence, Report export, Ask tab.
7. **Polish pass (Emil's "review the next day").** Slow-motion every transition, fix easing/
   timing, verify focus order, run an AA contrast audit, test the full keyboard flow, check the
   100-step virtualized case, confirm reduced-motion. *Exit:* defensible in a high-end studio
   review.

Build phases 1–3 to a high bar before widening. A flawless Run Detail + evidence drawer is the
entire product; the rest is scaffolding around it.

---

## 13. Acceptance checklist

Ship only when all are true:

- [ ] Looks like a credible Microsoft/Azure enterprise console — not a marketing page, not an
      "AI demo." None of the §2.2 anti-references are present.
- [ ] The first screen answers "what happened in this run, and what needs review?" in one glance.
- [ ] Every verdict traces to evidence: SOP excerpt + video timestamp + confidence, reachable in
      ≤2 clicks and <1s.
- [ ] Deviation, Unable to Verify, and Requires Inspection are visible and dignified — not hidden,
      not alarmist.
- [ ] Human-review status is explicit; nothing low-confidence auto-finalizes; unreviewed exports
      are watermarked Draft.
- [ ] The audit trail is reachable from every run.
- [ ] The table stays usable and fast at 100+ steps.
- [ ] Full keyboard operation, visible focus, AA contrast, reduced-motion all verified.
- [ ] Motion is crisp (<300ms, custom easing, no animated keyboard actions) and respects reduced
      motion.
- [ ] Nothing implies fully automated regulatory approval; copy follows §11.
```
