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
