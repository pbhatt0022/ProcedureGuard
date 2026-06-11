# ProcedureGuard

AI-powered manufacturing procedure verification on Azure AI Foundry. Reads an SOP PDF, analyses a production video, and produces a structured compliance report — per-step verdicts with confidence scores and video timestamp evidence.

> Built as a 4-week internship MVP at Microsoft. Research prototype — not a production system.

---

## What it does

1. Ingests an SOP document → extracts structured compliance checklist
2. Indexes SOP visual content (diagrams, figures, safety symbols) via multimodal RAG
3. Analyses a manufacturing video → extracts per-segment observations
4. Reasons step-by-step → produces Compliant / Deviation / Unable to Verify verdicts
5. Surfaces results in a Streamlit dashboard with deviation timeline, keyframe evidence, and Q&A chat

---

## Architecture

5-layer pipeline on Azure:

```
Layer 1 · Input          SOP PDF + Manufacturing Video → Blob Storage
Layer 2 · Extraction     Document Intelligence + AI Search (multimodal RAG) + Content Understanding
Layer 3 · Agents         Agent 1 (SOP Ingestion) · Agent 2 (Compliance Reasoning) · Agent 3 (Q&A)
Layer 4 · Storage        Cosmos DB (checklists, verdicts) · Blob Storage (PDFs, videos, keyframes)
Layer 5 · Presentation   Streamlit Dashboard
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full breakdown including data flows, the Content Understanding field schema, and the Eraser diagram source.

---

## Datasets

| Dataset | Use | Format |
|---|---|---|
| IndustReal (WACV 2024) | Primary benchmark — procedural assembly videos with compliance annotations, Apache 2.0 | MP4 + annotations |
| Prusa MK3S+ + OPENMARCIE | Demo SOP-video pair — real SOP matched to real assembly footage | PDF + MP4 |
| SafetyCulture / Princeton SOP Templates | Additional demo SOP inputs | PDF |

See [docs/DATASETS.md](docs/DATASETS.md) for download links and usage details.

---

## Repo structure

```
procedureguard/
├── docs/
│   ├── ARCHITECTURE.md          # 5-layer breakdown, data flows, service limits
│   ├── PROJECT_CONTEXT.md       # Internship constraints, persona, success criteria
│   ├── TECHNICAL_GUIDE.md       # Stack rules, code style, Azure doc URLs
│   ├── DECISIONS_AND_RATIONALE.md  # Architectural decision log
│   ├── WEEKLY_PROGRESS.md       # Week-by-week progress tracking
│   ├── KNOWN_ISSUES.md          # Azure gotchas and workarounds
│   └── MODEL_CARD.md            # Model details, performance targets, limitations
├── src/
│   ├── ingestion/               # Layer 2: Document Intelligence + Content Understanding
│   ├── agents/                  # Layer 3: Foundry Agent Service agents (1, 2, 3)
│   ├── reasoning/               # GPT-4o prompts + Python sequence/timing engine
│   ├── storage/                 # Cosmos DB + Blob Storage clients
│   └── dashboard/               # Streamlit app + components
├── schemas/                     # JSON contracts between pipeline layers
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

streamlit run src/dashboard/app.py
```

Prerequisites: Azure AI Foundry resource, Cosmos DB account, Blob Storage account, Azure OpenAI GPT-4o or GPT-4.1 deployment, Azure AI Search (S1 tier).

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

- Content Understanding operates at 1 fps / 512×512 px — fine motor precision and sub-second actions are classified *Unable to Verify* and flagged for human review
- Research prototype — verification reports require human review before informing any quality decision
- Production deployment requires QMS integration and regulatory validation

See [docs/MODEL_CARD.md](docs/MODEL_CARD.md) for the full limitations and intended use statement.

---

## Docs index

| File | Purpose |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 5-layer architecture, data flows, Content Understanding schema, service limits |
| [docs/PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md) | Internship constraints, pilot persona, tech stack, success criteria |
| [docs/TECHNICAL_GUIDE.md](docs/TECHNICAL_GUIDE.md) | Stack constraints, code style rules, Azure documentation URLs |
| [docs/DECISIONS_AND_RATIONALE.md](docs/DECISIONS_AND_RATIONALE.md) | Architectural decision log — what was decided and why |
| [docs/WEEKLY_PROGRESS.md](docs/WEEKLY_PROGRESS.md) | Week-by-week progress, blockers, and deliverable tracking |
| [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md) | Azure gotchas and workarounds discovered during development |
| [docs/MODEL_CARD.md](docs/MODEL_CARD.md) | Model details, performance targets, known limitations, intended use |
