# ProcedureGuard

AI-powered manufacturing procedure verification on Azure AI Foundry. Reads an SOP PDF, analyses a production video, and produces a structured compliance report — per-step verdicts with confidence scores and video timestamp evidence.

> Built as a 4-week internship MVP at Microsoft. Research prototype — not a production system.

---

## What it does

1. Ingests an SOP document (Document Intelligence) → extracts a structured compliance checklist
2. Analyses a manufacturing video → GPT-4o Vision describes per-window observations
3. Reasons step-by-step → produces Compliant / Deviation / Requires Inspection / Unable to Verify verdicts
4. Surfaces results in a Next.js review dashboard with deviation timeline, keyframe evidence, and Q&A chat

---

## Architecture (as-built)

```
Input        SOP PDF + Manufacturing Video (local path or Blob SAS URL)
Extraction   SOP PDF → Document Intelligence → checklist (GPT-4o)
             Video   → OpenCV frames → GPT-4o Vision (Phase 2, per ~25s window)
Reasoning    Per-step GPT-4o verdict + deterministic guards (unique-evidence,
             absence-inference) + Python sequence/timing
Storage      Local JSON run store (runs/<run_id>.json + .review.json sidecar) · Blob (keyframes)
Presentation Next.js review dashboard (frontend/)
```

> The original 5-layer Azure design (AI Search, Content Understanding, Foundry agents, Cosmos DB)
> is recorded in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Those layers were not built — see the
> as-built banner there and [docs/DECISIONS_AND_RATIONALE.md](docs/DECISIONS_AND_RATIONALE.md).

---

## Datasets

| Dataset | Use | Format |
|---|---|---|
| IndustReal (WACV 2024) | Primary benchmark — procedural assembly videos with compliance annotations, Apache 2.0 | MP4 + annotations |
| Prusa MK3S+ + OPENMARCIE | Demo SOP-video pair — real SOP matched to real assembly footage | PDF + MP4 |
| SafetyCulture / Princeton SOP Templates | Additional demo SOP inputs | PDF |

See [docs/PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md) for download links and usage details.

---

## Repo structure

```
procedureguard/
├── docs/
│   ├── ARCHITECTURE.md          # As-built + original 5-layer design, data flows
│   ├── PROJECT_CONTEXT.md       # Internship constraints, persona, datasets, success criteria
│   ├── TECHNICAL_GUIDE.md       # Stack rules, code style, Azure doc URLs
│   ├── DECISIONS_AND_RATIONALE.md  # Architectural decision log
│   ├── WEEKLY_PROGRESS.md       # Week-by-week progress tracking
│   ├── KNOWN_ISSUES.md          # Azure gotchas and workarounds
│   ├── MODEL_CARD.md            # Model details, performance targets, limitations
│   └── BASELINE_DIFF_PLAN.md    # Next perception fix — deterministic baseline-diff
├── src/
│   ├── ingestion/               # Document Intelligence (SOP) + GPT-4o Vision (video)
│   ├── reasoning/               # GPT-4o prompts + Python sequence/timing + guards
│   └── storage/                 # Blob Storage client + local run store
├── frontend/                    # Next.js review dashboard (Next 16 / React 19)
├── schemas/                     # JSON contracts between pipeline stages
├── tests/
├── .env.example
└── requirements.txt
```

---

## Quick start

```bash
git clone <repo-url>
cd procedureguard
pip install -r requirements.txt

cp .env.example .env
# Fill in your Azure endpoints and keys — see .env.example for required variables

# Run a verification pipeline → writes a results JSON
python scripts/run_pipeline_demo.py

# Launch the review dashboard (Next.js)
cd frontend
npm install
npm run dev          # http://localhost:3000
```

Prerequisites: Azure OpenAI GPT-4o deployment, Azure Document Intelligence resource, and (optional) a Blob Storage account for keyframes — without it, keyframes fall back to the local runs store. Auth via `az login` (DefaultAzureCredential) or API key.

---

## Success criteria

| Metric | Target |
|---|---|
| SOP step extraction coverage | >90% of verifiable steps correctly identified |
| Compliance verdict accuracy | >80% agreement vs manual benchmark on IndustReal |
| End-to-end pipeline latency | <5 minutes per video |
| Dashboard demo-ready | End of Week 4 |

---

## Limitations

- Video is analysed in fixed ~25s windows (768 px longest edge) — fine-detail QC (torque, seating, pin orientation) is routed to *Requires Inspection* for a human rather than guessed
- Demo/eval video must be raw footage: some IndustReal clips ship as annotated renders with ground-truth labels burned into the frames (see [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md))
- Research prototype — verification reports require human review before informing any quality decision
- Production deployment requires QMS integration and regulatory validation

See [docs/MODEL_CARD.md](docs/MODEL_CARD.md) for the full limitations and intended use statement.

---

## Docs index

| File | Purpose |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | As-built pipeline + original 5-layer design, data flows, service limits |
| [docs/PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md) | Internship constraints, pilot persona, tech stack, datasets, success criteria |
| [docs/TECHNICAL_GUIDE.md](docs/TECHNICAL_GUIDE.md) | Stack constraints, code style rules, Azure documentation URLs |
| [docs/DECISIONS_AND_RATIONALE.md](docs/DECISIONS_AND_RATIONALE.md) | Architectural decision log — what was decided and why |
| [docs/WEEKLY_PROGRESS.md](docs/WEEKLY_PROGRESS.md) | Week-by-week progress, blockers, and deliverable tracking |
| [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md) | Azure gotchas and workarounds discovered during development |
| [docs/MODEL_CARD.md](docs/MODEL_CARD.md) | Model details, performance targets, known limitations, intended use |
| [docs/BASELINE_DIFF_PLAN.md](docs/BASELINE_DIFF_PLAN.md) | Plan for the deterministic baseline-diff perception fix |
| [docs/IMPROVEMENT_PLAN.md](docs/IMPROVEMENT_PLAN.md) | As-built vs as-designed gap analysis + prioritized roadmap |
| [docs/UI_BUILD_PLAN.md](docs/UI_BUILD_PLAN.md) · [docs/DESIGN-ProcedureGuard.md](docs/DESIGN-ProcedureGuard.md) | UI/UX spec + design-token source of truth (frontend) |
| [docs/VIDEO_INTELLIGENCE_RESEARCH.md](docs/VIDEO_INTELLIGENCE_RESEARCH.md) | Perception-model research (June 18) — provenance for current approach |
