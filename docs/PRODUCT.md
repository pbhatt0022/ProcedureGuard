# ProcedureGuard — Product Brief

> Audience, purpose, and design principles for the review dashboard. Companion to
> `UI_BUILD_PLAN.md` and `DESIGN-ProcedureGuard.md`.

## Users

Quality engineers and process engineers in regulated manufacturing environments (FDA, ISO 13485 contexts). They review compliance verification reports after a production run, investigate deviation findings, and decide whether to escalate to a non-conformance record. They are fluent with enterprise tooling (SAP, Jira, clinical QMS software) and expect the interface to get out of the way. They are not on the shop floor in real-time — they are reviewing results at a workstation, often under time pressure before the next run.

## Product Purpose

ProcedureGuard ingests an SOP PDF and a manufacturing video and produces a structured compliance verification report: per-step verdicts (Compliant / Deviation Detected / Unable to Verify) with confidence scores and video timestamps. It replaces paper checklist sampling (which covers ~5% of production volume) with automated, evidence-backed quality records. Success: a quality engineer can open a run, confirm the two deviation findings, and file a non-conformance report in under two minutes.

## Brand Personality

Clean · Modern · Professional. The tool should feel like a serious instrument used in a regulated environment — not a startup analytics product. Confidence is earned through precision and clarity, not decoration. Data is the hero; the interface should disappear into the task.

## Anti-references

- **AI product clichés**: gradient text, glassmorphism, purple-blue AI color palettes, animated orbs, "hero metric" big-number cards with gradient accents, cream/warm-neutral backgrounds.
- Avoid anything that reads as "a Claude demo" or "startup SaaS." The audience is engineering professionals, not investors.

## Design Principles

1. **Data is the hero.** Every layout decision serves legibility of verdicts, timestamps, and reasoning text. No decoration competes with content.
2. **Confidence through precision.** Exact numbers, exact timestamps, exact step IDs. Round numbers and vague labels erode trust in a compliance tool.
3. **Earn familiarity.** The tool should feel immediately navigable to someone fluent in Linear, Notion, or Stripe's admin. No invented affordances. Standard components, standard patterns.
4. **Abstain clearly.** Unable to Verify is a first-class outcome, not a failure state to hide. The visual language should make abstention as readable as a verdict.
5. **Instrument, not app.** Density is acceptable. Tables with 29 rows are expected. Don't pad or simplify data to make it feel "consumer."

## Accessibility & Inclusion

WCAG AA minimum. Body text and verdict labels must meet 4.5:1 contrast. Focus indicators must be visible (engineering tools are keyboard-navigated). No color-only verdict encoding — verdict pills must carry text labels, not just color. Reduced-motion support for any transitions added in future passes.
