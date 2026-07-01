# ProcedureGuard — UI & Design Reference

> Merged from DESIGN-ProcedureGuard.md + UI_BUILD_PLAN.md (June 24). The built `frontend/`
> app (Next.js 16 / React 19) is the source of truth; this is the design spec/provenance behind it.
>
> **As-built note:** these docs were written during the Streamlit→React migration, so any
> "the current implementation is Streamlit" phrasing below is **historical** — Streamlit was
> removed; the live dashboard is the Next.js app in `frontend/` (the React build these docs argued
> for, which shipped).

---

# Part 1 — Design Direction (Fluent/Azure)

---
version: alpha
name: ProcedureGuard-fluent-azure-design
description: "A Microsoft Fluent/Azure-tuned enterprise product interface for ProcedureGuard: clean blue system, white and neutral surfaces, Segoe UI typography, compact information density, accessible semantic states, DetailsList-style enterprise tables, evidence-backed audit trails, timestamp-linked video verification, and human-review-first compliance workflows. This adapts the rigorous IBM Carbon enterprise baseline into a Microsoft/Azure product console suitable for a regulated manufacturing QA demo."

colors:
  # Brand / Azure
  primary: "#0078D4"              # Azure / Microsoft blue
  primary-hover: "#106EBE"
  primary-pressed: "#005A9E"
  primary-subtle: "#EFF6FC"
  primary-border-subtle: "#C7E0F4"
  on-primary: "#FFFFFF"

  # Neutral surfaces
  canvas: "#FFFFFF"
  app-background: "#FAF9F8"
  surface-1: "#FFFFFF"
  surface-2: "#F3F2F1"
  surface-3: "#EDEBE9"
  surface-selected: "#EFF6FC"
  surface-hover: "#F5F5F5"
  surface-disabled: "#F3F2F1"

  # Text
  ink: "#201F1E"
  ink-muted: "#605E5C"
  ink-subtle: "#8A8886"
  ink-disabled: "#A19F9D"
  inverse-canvas: "#1B1A19"
  inverse-ink: "#FFFFFF"
  inverse-ink-muted: "#C8C6C4"

  # Borders / focus
  hairline: "#E1DFDD"
  hairline-strong: "#C8C6C4"
  focus-ring: "#0078D4"

  # Accessible semantic status colors
  semantic-success: "#107C10"     # Compliant
  semantic-success-bg: "#DFF6DD"
  semantic-warning: "#797673"     # Unable to verify / caution text
  semantic-warning-bg: "#FFF4CE"
  semantic-error: "#D13438"       # Deviation detected
  semantic-error-bg: "#FDE7E9"
  semantic-info: "#0078D4"        # Informational / processing
  semantic-info-bg: "#EFF6FC"
  semantic-review: "#5C2E91"      # Human review required
  semantic-review-bg: "#F3EAFF"

  # Data visualization / scores
  score-high: "#107C10"
  score-medium: "#F7630C"
  score-low: "#D13438"
  score-neutral: "#605E5C"

typography:
  display-xl:
    fontFamily: Segoe UI
    fontSize: 42px
    fontWeight: 600
    lineHeight: 1.16
    letterSpacing: "-0.02em"
  display-lg:
    fontFamily: Segoe UI
    fontSize: 34px
    fontWeight: 600
    lineHeight: 1.18
    letterSpacing: "-0.01em"
  display-md:
    fontFamily: Segoe UI
    fontSize: 28px
    fontWeight: 600
    lineHeight: 1.20
    letterSpacing: 0
  headline:
    fontFamily: Segoe UI
    fontSize: 24px
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: 0
  card-title:
    fontFamily: Segoe UI
    fontSize: 18px
    fontWeight: 600
    lineHeight: 1.33
    letterSpacing: 0
  subhead:
    fontFamily: Segoe UI
    fontSize: 16px
    fontWeight: 600
    lineHeight: 1.40
    letterSpacing: 0
  body-lg:
    fontFamily: Segoe UI
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.50
    letterSpacing: 0
  body:
    fontFamily: Segoe UI
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.43
    letterSpacing: 0
  body-sm:
    fontFamily: Segoe UI
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.38
    letterSpacing: 0
  body-emphasis:
    fontFamily: Segoe UI
    fontSize: 14px
    fontWeight: 600
    lineHeight: 1.43
    letterSpacing: 0
  caption:
    fontFamily: Segoe UI
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.33
    letterSpacing: 0
  metadata:
    fontFamily: Segoe UI
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.33
    letterSpacing: 0
  button:
    fontFamily: Segoe UI
    fontSize: 14px
    fontWeight: 600
    lineHeight: 1.43
    letterSpacing: 0
  mono:
    fontFamily: Cascadia Mono
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.45
    letterSpacing: 0

rounded:
  none: 0px
  xs: 2px
  sm: 4px
  md: 6px
  lg: 8px
  xl: 12px
  pill: 9999px
  full: 9999px

spacing:
  xxs: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 20px
  xl: 24px
  xxl: 32px
  section: 48px

elevation:
  none: "none"
  subtle: "0 1px 2px rgba(0,0,0,0.08)"
  card: "0 1px 3px rgba(0,0,0,0.12)"
  flyout: "0 8px 16px rgba(0,0,0,0.14)"
  dialog: "0 16px 32px rgba(0,0,0,0.18)"

components:
  app-shell:
    backgroundColor: "{colors.app-background}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    layout: "top header + left navigation + scrollable content canvas"
  top-command-bar:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    height: 48px
    borderBottom: "1px solid {colors.hairline}"
    shadow: "{elevation.subtle}"
  left-nav:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.ink-muted}"
    typography: "{typography.body-sm}"
    widthExpanded: 240px
    widthCollapsed: 56px
    borderRight: "1px solid {colors.hairline}"
  page-header:
    backgroundColor: "{colors.app-background}"
    textColor: "{colors.ink}"
    typography: "{typography.display-md}"
    padding: 24px 32px 16px
  command-bar-button:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.button}"
    rounded: "{rounded.sm}"
    padding: 6px 10px
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.button}"
    rounded: "{rounded.sm}"
    padding: 8px 12px
    minHeight: 32px
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
    textColor: "{colors.on-primary}"
    typography: "{typography.button}"
    rounded: "{rounded.sm}"
  button-secondary:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.ink}"
    typography: "{typography.button}"
    rounded: "{rounded.sm}"
    padding: 8px 12px
    border: "1px solid {colors.hairline-strong}"
    minHeight: 32px
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.primary}"
    typography: "{typography.button}"
    rounded: "{rounded.sm}"
    padding: 8px 10px
    minHeight: 32px
  button-danger:
    backgroundColor: "{colors.semantic-error}"
    textColor: "{colors.on-primary}"
    typography: "{typography.button}"
    rounded: "{rounded.sm}"
    padding: 8px 12px
    minHeight: 32px
  card:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: 16px
    border: "1px solid {colors.hairline}"
    shadow: "{elevation.subtle}"
  kpi-card:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: 16px
    border: "1px solid {colors.hairline}"
    shadow: "{elevation.subtle}"
  evidence-card:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.ink}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.md}"
    padding: 12px
    border: "1px solid {colors.hairline}"
  details-list:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.ink}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.md}"
    rowHeightCompact: 36px
    rowHeightDefault: 44px
    headerHeight: 40px
    border: "1px solid {colors.hairline}"
  text-input:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: 6px 10px
    border: "1px solid {colors.hairline-strong}"
    minHeight: 32px
  text-input-focused:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    border: "1px solid {colors.primary}"
    outline: "2px solid {colors.focus-ring}"
  dropdown:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: 6px 10px
    border: "1px solid {colors.hairline-strong}"
    minHeight: 32px
  search-box:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: 6px 10px
    border: "1px solid transparent"
    minHeight: 32px
  tab:
    backgroundColor: "transparent"
    textColor: "{colors.ink-muted}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: 8px 12px
  tab-selected:
    backgroundColor: "{colors.surface-selected}"
    textColor: "{colors.primary}"
    typography: "{typography.body-emphasis}"
    rounded: "{rounded.sm}"
    padding: 8px 12px
    borderBottom: "2px solid {colors.primary}"
  status-compliant:
    backgroundColor: "{colors.semantic-success-bg}"
    textColor: "{colors.semantic-success}"
    typography: "{typography.body-emphasis}"
    rounded: "{rounded.pill}"
    padding: 2px 8px
    icon: "CheckmarkCircle"
  status-deviation:
    backgroundColor: "{colors.semantic-error-bg}"
    textColor: "{colors.semantic-error}"
    typography: "{typography.body-emphasis}"
    rounded: "{rounded.pill}"
    padding: 2px 8px
    icon: "ErrorCircle"
  status-unable:
    backgroundColor: "{colors.semantic-warning-bg}"
    textColor: "{colors.ink}"
    typography: "{typography.body-emphasis}"
    rounded: "{rounded.pill}"
    padding: 2px 8px
    icon: "Warning"
  status-review:
    backgroundColor: "{colors.semantic-review-bg}"
    textColor: "{colors.semantic-review}"
    typography: "{typography.body-emphasis}"
    rounded: "{rounded.pill}"
    padding: 2px 8px
    icon: "PersonFeedback"
  status-processing:
    backgroundColor: "{colors.semantic-info-bg}"
    textColor: "{colors.semantic-info}"
    typography: "{typography.body-emphasis}"
    rounded: "{rounded.pill}"
    padding: 2px 8px
    icon: "Sync"
  timestamp-chip:
    backgroundColor: "{colors.primary-subtle}"
    textColor: "{colors.primary}"
    typography: "{typography.metadata}"
    rounded: "{rounded.sm}"
    padding: 2px 6px
    icon: "Clock"
  confidence-chip-high:
    backgroundColor: "{colors.semantic-success-bg}"
    textColor: "{colors.score-high}"
    typography: "{typography.metadata}"
    rounded: "{rounded.sm}"
    padding: 2px 6px
  confidence-chip-medium:
    backgroundColor: "{colors.semantic-warning-bg}"
    textColor: "{colors.score-medium}"
    typography: "{typography.metadata}"
    rounded: "{rounded.sm}"
    padding: 2px 6px
  confidence-chip-low:
    backgroundColor: "{colors.semantic-error-bg}"
    textColor: "{colors.score-low}"
    typography: "{typography.metadata}"
    rounded: "{rounded.sm}"
    padding: 2px 6px
  audit-timeline:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.ink}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.md}"
    padding: 12px
    borderLeft: "2px solid {colors.primary}"
  callout-info:
    backgroundColor: "{colors.semantic-info-bg}"
    textColor: "{colors.ink}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.md}"
    padding: 12px
    borderLeft: "4px solid {colors.semantic-info}"
  callout-warning:
    backgroundColor: "{colors.semantic-warning-bg}"
    textColor: "{colors.ink}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.md}"
    padding: 12px
    borderLeft: "4px solid #F7630C"
  callout-error:
    backgroundColor: "{colors.semantic-error-bg}"
    textColor: "{colors.ink}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.md}"
    padding: 12px
    borderLeft: "4px solid {colors.semantic-error}"
---

# ProcedureGuard Microsoft Fluent/Azure Design Direction

ProcedureGuard should feel like a credible Microsoft enterprise product console: calm, precise, secure, evidence-first, and built for decision-making under regulatory scrutiny. The visual language should borrow from Microsoft Fluent and Azure product experiences rather than IBM Carbon marketing.

The goal is not to make the interface look decorative. The goal is to make a Quality Assurance Manager trust the result quickly: what SOP was evaluated, what video was analyzed, which steps passed, which deviated, what evidence supports each verdict, which items require human review, and whether the generated verification report is audit-ready.

## Design Positioning

**Product category:** Azure-native manufacturing quality verification dashboard.

**Primary user:** Quality Assurance Manager in regulated manufacturing.

**Core emotional promise:** “I can defend this record in an audit because every verdict has traceable evidence.”

**Visual personality:**
- Microsoft enterprise product, not marketing landing page
- White and neutral surfaces with Azure blue as the primary action and selection color
- Compact, data-dense, scannable layouts
- Status-aware, evidence-backed, human-review-safe
- Familiar to users of Azure Portal, Microsoft 365, Power Platform, and Dynamics-style enterprise apps

## What Changed from the IBM Base

The uploaded IBM file is built around IBM Carbon: square geometry, IBM Plex Sans, IBM Blue, thin-bordered tiles, minimal elevation, and a marketing-page rhythm. For ProcedureGuard, keep the enterprise seriousness but shift to a Microsoft product surface.

### Replace

| IBM / Carbon baseline | Fluent / Azure ProcedureGuard tuning |
|---|---|
| IBM Plex Sans | Segoe UI |
| IBM Blue `#0f62fe` | Azure/Microsoft Blue `#0078D4` |
| Mostly square 0px corners | 4–8px Fluent radius |
| Marketing hero/card rhythm | Product console layout |
| Flat cards only | Subtle Fluent elevation |
| Feature-card language | Dashboard cards, DetailsList tables, command bars |
| Footer/page sections | App shell, left nav, top command bar |
| Single accent philosophy | Brand blue + accessible semantic states |
| General enterprise tiles | QA evidence cards, verdict badges, audit trail timeline |

## Layout System

### App Shell

Use a classic Azure-style product shell:

1. **Top command bar**
   - Product name: ProcedureGuard
   - Workspace/run selector
   - Global search
   - Actions: Upload SOP, Upload Video, Run Verification, Export Report
   - User/help/settings icons on the right

2. **Left navigation**
   - Dashboard
   - Verification runs
   - SOP library
   - Video evidence
   - Deviations
   - Human review
   - Audit trail
   - Settings

3. **Main content canvas**
   - White/neutral background
   - Page header with title, run metadata, and primary action
   - KPI cards and summary panels
   - Compact DetailsList tables
   - Right-side evidence drawer or split pane

4. **Optional right panel**
   - Evidence viewer
   - SOP excerpt
   - Video timestamp preview
   - Reasoning summary
   - Human review controls

### Recommended Dashboard Structure

```text
Top command bar
└── Left navigation
    └── Page: Verification Report
        ├── Page header
        │   ├── Run name
        │   ├── SOP name
        │   ├── Video name
        │   ├── Generated timestamp
        │   └── Export / Review / Re-run actions
        ├── KPI summary cards
        │   ├── Overall adherence score
        │   ├── Compliant steps
        │   ├── Deviations detected
        │   ├── Unable to verify
        │   └── Human review required
        ├── Main table: SOP step verification
        │   ├── Step number
        │   ├── SOP criterion
        │   ├── Verdict
        │   ├── Confidence
        │   ├── Evidence timestamp
        │   ├── Reviewer status
        │   └── Actions
        └── Evidence split pane
            ├── Video key frame
            ├── Timestamp range
            ├── SOP excerpt
            ├── Model observation
            ├── GPT reasoning summary
            └── Audit log
```

## Colors

Use color sparingly, but do not make the system monochrome. ProcedureGuard depends on status interpretation, so color should help users scan risk quickly.

### Brand Color

Use Azure/Microsoft blue for:
- Primary buttons
- Selected navigation items
- Active tabs
- Focus rings
- Timestamp chips
- Links to evidence
- Selected table rows
- Informational callouts

Avoid using blue for:
- Every card header
- Large decorative backgrounds
- Status states that need semantic meaning

### Neutral Surfaces

Use:
- `canvas` for main cards and tables
- `app-background` for the shell background
- `surface-2` for command bars, search boxes, filters, and subtle grouped regions
- `hairline` borders to separate dense table rows and panels

### Semantic Color Rules

Every status must use **text + icon + color**, never color alone.

| ProcedureGuard state | Color treatment | Icon suggestion | UX meaning |
|---|---|---|---|
| Compliant | Green text on light green background | CheckmarkCircle | Step has sufficient evidence and passed |
| Deviation detected | Red text on light red background | ErrorCircle | Evidence suggests non-compliance |
| Unable to verify | Dark text on yellow background | Warning | Model could not safely determine outcome |
| Human review required | Purple text on light purple background | PersonFeedback | Needs QA reviewer decision |
| Processing | Blue text on light blue background | Sync | Pipeline still running |
| Exported / archived | Neutral gray | Archive | Record is stored and report generated |

## Typography

Use **Segoe UI** as the default. It will feel native to Microsoft enterprise products and works well in dense dashboards.

### Typography Rules

- Use 14px as the default body size.
- Use 13px for compact table metadata.
- Use 12px for timestamps, IDs, run metadata, and confidence labels.
- Use 18px or 20px for card titles.
- Use 24–28px for page titles.
- Avoid oversized hero typography. This is a working product, not a marketing page.
- Use `Cascadia Mono` only for IDs, JSON fragments, run IDs, or logs.

## Components

## 1. Top Command Bar

Purpose: Provide product identity and the most common actions.

Recommended actions:
- Upload SOP
- Upload video
- Run verification
- Export report
- Create review task
- Search verification history

Visual rules:
- Height: 48px
- Background: white
- Bottom border: 1px `hairline`
- Primary action: `Run verification`
- Secondary actions: upload/export/review
- Avoid crowding; use overflow menu for less common actions

## 2. Left Navigation

Use a persistent vertical nav like Azure product consoles.

Navigation items:
- Dashboard
- Runs
- SOP library
- Video evidence
- Deviations
- Human review
- Audit trail
- Settings

Selected item:
- Blue left rail or soft blue background
- Semibold label
- Icon + text
- Do not rely only on color

## 3. KPI Cards

Use cards to answer the QA manager’s first five questions:

| KPI | Suggested display |
|---|---|
| Overall adherence | Large percentage + status |
| Compliant steps | Count + green badge |
| Deviations detected | Count + red badge |
| Unable to verify | Count + yellow badge |
| Human review required | Count + purple badge |

Rules:
- Keep cards compact.
- Use one main number per card.
- Add a small explanatory caption.
- Do not add decorative charts unless they clarify status.

Example:
```text
Overall adherence
87%
24 of 28 verifiable SOP steps compliant
```

## 4. SOP Step Verification Table

This is the central UI component.

Use a Fluent DetailsList-style compact enterprise table.

Columns:
1. Step
2. SOP criterion
3. Check type
4. Verdict
5. Confidence
6. Evidence timestamp
7. Reviewer status
8. Action

Recommended table behavior:
- Sticky header
- Sort by verdict, confidence, step number, review status
- Filter by Compliant / Deviation / Unable / Review required
- Row click opens evidence drawer
- Red/yellow/purple rows should show a subtle left status bar
- Support compact density by default

### Table Row Pattern

```text
Step 04 | Verify operator wears gloves before component contact
Presence check | Deviation detected | 74% | 00:01:18–00:01:31 | Needs review | View evidence
```

## 5. Evidence Drawer / Split Pane

When a user clicks a table row, open a right-side evidence panel.

Panel sections:
- Verdict summary
- Video timestamp and key frame
- SOP excerpt
- Structured model observation
- Reasoning summary
- Confidence explanation
- Reviewer decision
- Audit log

This panel is more important than a chatbot. It is where trust is built.

### Evidence Panel Layout

```text
Evidence for Step 04

Verdict
Deviation detected · Confidence 74%

Video evidence
00:01:18–00:01:31
[Key frame thumbnail]
Open video at timestamp

SOP requirement
"Operator must wear gloves before touching sterile component."

Observed action
"Component contact visible. PPE field indicates gloves not visible."

Reasoning summary
The required PPE condition was not observed before component contact in the relevant segment.

Review decision
[Confirm deviation] [Mark compliant] [Unable to verify] [Add note]
```

## 6. Audit Trail

ProcedureGuard must look audit-ready. Add an audit timeline for every verification run.

Audit events:
- SOP uploaded
- SOP parsed
- Checklist generated
- Video uploaded
- Analyzer completed
- Compliance reasoning completed
- Human reviewer opened item
- Reviewer changed verdict
- Report exported

Each event should include:
- Timestamp
- Actor: system / reviewer name
- Action
- Object: SOP, video, step, report
- Notes / reason
- Version or run ID

### Audit Trail Pattern

```text
10:42:18 · System
Generated checklist from SOP v1.3
28 verifiable steps extracted. 3 duration checks, 5 sequence checks.

10:47:56 · System
Detected deviation in Step 04
Evidence: video segment 00:01:18–00:01:31.

10:51:22 · Vikram Nair
Confirmed deviation
Reviewer note: gloves not visible before component handling.
```

## 7. Human Review Workflow

Human review should be explicit and visible.

Use review states:
- Not reviewed
- Review required
- In review
- Confirmed compliant
- Confirmed deviation
- Marked unable to verify
- Escalated

Do not auto-finalize low-confidence or ambiguous findings. The UI should make this safety principle visible.

Recommended controls:
- Confirm model verdict
- Override verdict
- Add reviewer note
- Assign reviewer
- Export draft only
- Export final reviewed report

## 8. Report Export Screen

The report export experience should feel formal and defensible.

Include:
- SOP name and version
- Video file name
- Production run ID
- Generated timestamp
- Analyzer version
- Model version / deployment name
- Overall adherence score
- Step-level verdict table
- Deviations
- Unable-to-verify steps
- Reviewer decisions
- Audit timeline
- Limitations and required human review statement

Buttons:
- Export PDF
- Export CSV
- Save to archive
- Copy summary
- Send for review

## Data Visualization

Use simple, non-decorative visuals.

Recommended:
- Donut or progress ring for adherence score
- Stacked bar for verdict distribution
- Timeline strip showing when deviations occurred in the video
- Small sparkline only if showing trend across production runs

Avoid:
- Flashy gradients
- 3D charts
- Overly colorful dashboards
- “AI magic” visuals that reduce trust

## Accessibility

ProcedureGuard should meet enterprise accessibility expectations.

Rules:
- Standard body text must meet WCAG AA contrast.
- Do not encode verdict by color alone.
- Every status badge needs icon + label.
- Focus rings must be visible.
- Keyboard users must be able to move from table row to evidence panel to reviewer controls.
- Video evidence needs text equivalents: timestamp, observed action, SOP excerpt, and generated reasoning.
- Avoid tiny table text below 12px.
- Use descriptive button labels: “View evidence,” not “View.”

## Iconography

Use Fluent-style outline icons.

Recommended icons:
- ShieldCheckmark: audit-ready / verified
- DocumentText: SOP
- Video: production video
- CheckmarkCircle: compliant
- ErrorCircle: deviation
- Warning: unable to verify
- PersonFeedback: human review
- Clock: timestamp
- Database: stored record
- History: audit trail
- Search: global search
- ArrowDownload: export report

Keep icons 16px or 20px. Avoid illustrative icons inside dense tables unless needed for status recognition.

## Microcopy

Tone should be precise, not promotional.

### Good

- “Deviation detected”
- “Unable to verify from available video evidence”
- “Human review required before final report”
- “Open video at 00:01:18”
- “SOP Step 04: PPE must be visible before component contact”
- “Confidence reflects available visual evidence, not final quality disposition”

### Avoid

- “AI found a mistake!”
- “Fully automated quality decision”
- “Guaranteed compliance”
- “Worker violation”
- “Surveillance result”

The system evaluates procedure execution evidence, not worker performance.

## Page Templates

## Dashboard

Purpose: Give an operational overview across runs.

Sections:
- Recent verification runs
- Open deviations
- Human review queue
- SOPs used most recently
- Verification trend
- Exported reports

## Verification Run Detail

Purpose: Show the full evidence-backed result for one production run.

Sections:
- Run metadata
- Adherence score
- Verdict distribution
- Step table
- Evidence drawer
- Audit trail

## SOP Library

Purpose: Manage SOP sources and extracted checklists.

Sections:
- SOP file list
- SOP version
- Extraction coverage
- Number of verifiable steps
- Last used run
- Checklist preview

## Video Evidence

Purpose: Manage videos and analyzer outputs.

Sections:
- Video file
- Duration
- Segment count
- Analyzer status
- Extracted observations
- Linked SOP/run

## Human Review Queue

Purpose: Help QA managers process ambiguous or high-risk items.

Sections:
- Items requiring review
- Priority
- Verdict
- Confidence
- Evidence timestamp
- Assigned reviewer
- Due date / SLA

## Implementation Notes for Streamlit

Streamlit can still follow this design direction.

Use:
- A top-level page title and command buttons
- Sidebar navigation
- `st.metric` for KPI cards, styled through CSS if needed
- `st.dataframe` or `st.data_editor` for compact step verification table
- `st.tabs` for Summary / Steps / Evidence / Audit trail
- `st.expander` for each evidence record if split pane is difficult
- Status badges rendered with safe HTML/CSS
- Video timestamp links using `st.video` plus timestamp metadata shown next to it

Recommended Streamlit pages:
```text
pages/
  1_Dashboard.py
  2_Verification_Run.py
  3_SOP_Library.py
  4_Human_Review.py
  5_Audit_Trail.py
```

## Do's and Don'ts

### Do

- Use Azure blue only for primary actions, links, selections, timestamps, and focus states.
- Use white and neutral surfaces as the dominant visual system.
- Make the SOP step verification table the hero of the product.
- Add clear status badges for every verdict.
- Always show evidence references next to model conclusions.
- Make “Unable to verify” a first-class safe outcome, not an error.
- Include an audit trail in every run.
- Use reviewer actions to distinguish AI output from final quality decision.
- Keep layouts compact and enterprise-ready.
- Use Microsoft-style command bars, side nav, tabs, panels, and details lists.

### Don't

- Do not make the UI look like a marketing landing page.
- Do not use IBM Plex Sans or IBM Blue if the goal is Microsoft/Azure fit.
- Do not use large hero graphics, gradients, or decorative AI visuals.
- Do not show a deviation without timestamped evidence.
- Do not say the system “certifies” or “guarantees” compliance.
- Do not make worker identity the center of the UI.
- Do not hide uncertainty; show confidence and review status.
- Do not rely only on color for status.
- Do not overuse cards where a compact table is clearer.

## Cursor / Copilot Build Instruction

Use this when asking an AI coding assistant to generate the UI:

```text
Build the ProcedureGuard UI as a Microsoft Fluent/Azure-style enterprise dashboard. Use Segoe UI, Azure blue (#0078D4), white and neutral surfaces, compact data density, subtle 4–8px radius, visible focus states, and accessible status badges with icon + label. The core page is a verification report for a manufacturing production run. It must show run metadata, adherence score, compliant/deviation/unable-to-verify counts, a compact SOP step verification table, and an evidence panel with SOP excerpt, video timestamp, model observation, reasoning summary, confidence, and reviewer decision controls. Do not create a marketing landing page. Make it feel like an Azure product console for regulated QA users.
```

## Acceptance Checklist

A ProcedureGuard UI is on-brand for this direction if:

- It looks like a Microsoft/Azure enterprise product console.
- The first screen answers: “What happened in this run, and what needs review?”
- Every verdict has evidence: SOP section + video timestamp + confidence.
- Deviation and unable-to-verify items are visible without being alarmist.
- Human review status is clear.
- The audit trail is accessible from the run detail page.
- The interface remains usable with many SOP steps.
- The product does not imply fully automated regulatory approval.


---

# Part 2 — UI/UX Build Plan

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


---

# Part 3 — Product principles (from PRODUCT.md)

**Users:** Quality/process engineers in regulated manufacturing (FDA, ISO 13485). They review
compliance reports after a run, investigate deviations, and decide whether to file a
non-conformance. Fluent with enterprise tooling; reviewing at a workstation under time pressure.

**Purpose:** SOP PDF + manufacturing video → per-step verdicts (Compliant / Deviation Detected /
Unable to Verify) with confidence + timestamps. Replaces ~5%-coverage paper sampling. Success: an
engineer confirms findings and files a non-conformance in under two minutes.

**Design principles:** (1) Data is the hero — no decoration competes with verdicts/timestamps.
(2) Confidence through precision — exact numbers, timestamps, step IDs. (3) Earn familiarity —
feels navigable to a Linear/Notion/Stripe user; standard patterns. (4) Abstain clearly — Unable to
Verify is first-class, as readable as a verdict. (5) Instrument, not app — density is fine, 29-row
tables expected.

**Anti-references:** no gradient text, glassmorphism, purple-blue AI palettes, animated orbs,
gradient hero-metric cards, warm-neutral backgrounds. Not "a Claude demo" or "startup SaaS."

**Accessibility:** WCAG AA min; 4.5:1 contrast on body + verdict labels; visible focus indicators
(keyboard-navigated); verdict pills carry text not color-only; reduced-motion support.
