# ProcedureGuard — Technical Guide for Claude

> This file tells Claude how to behave when giving technical advice on this project.
> Paste alongside PROJECT_CONTEXT.md when asking coding or architecture questions.

---

## Documentation-first rule

**Before giving any technical advice about any Azure service, search the current official Microsoft documentation.**

Always check the live docs before answering — do not rely on training data for Azure service specifics, API versions, method names, SDK parameters, or service limits. These change frequently and outdated advice wastes the team's time.

### Documentation URLs to check first

| Service | Documentation URL |
|---|---|
| Azure Content Understanding | https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/ |
| Azure Content Understanding — Video | https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/video/overview |
| Azure Content Understanding — Service Limits | https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/service-limits |
| Azure Content Understanding — Custom Analyzer | https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/tutorial/create-custom-analyzer |
| Azure Document Intelligence | https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/ |
| Azure OpenAI | https://learn.microsoft.com/en-us/azure/ai-services/openai/ |
| Azure Foundry Agent Service | https://learn.microsoft.com/en-us/azure/ai-foundry/ |
| Azure Cosmos DB | https://learn.microsoft.com/en-us/azure/cosmos-db/ |
| Azure Blob Storage | https://learn.microsoft.com/en-us/azure/storage/blobs/ |
| MCP on Azure Foundry | https://learn.microsoft.com/en-us/azure/ai-foundry/agents/tools/mcp |

**If advice contradicts the live documentation, the documentation wins. Say so explicitly.**

---

## Stack constraints — hard rules

- **Azure-native only.** Never suggest a non-Azure service, even if it would be easier or cheaper.
- **Python for all pipeline code.** No other backend languages.
- **Streamlit for the dashboard.** No React, no Flask, no other frontend frameworks.
- **Content Understanding API version: `2025-11-01` (GA).** Never suggest or use preview API versions (`2024-12-01-preview`, `2025-05-01-preview`).
- **GPT-4o or GPT-4.1 only** for reasoning. No other models unless explicitly asked.
- **`prebuilt-video` as the base analyzer** for Content Understanding. Never suggest `prebuilt-videoSearch` for compliance use cases.
- **Blob Storage URL reference** for all video >200 MB or >30 minutes. Never binary upload for production use.
- **No A2A (Agent-to-Agent) protocol.** Pipeline is linear and Azure-native — A2A adds no value here.
- **MCP only for Agent 3** (Q&A Chat). Not for Agent 1 or Agent 2.

---

## Code style requirements

When writing Python code for this project:

```python
# Always include imports
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

# Use DefaultAzureCredential — never hardcoded keys or connection strings
credential = DefaultAzureCredential()

# Use environment variables via python-dotenv for all config
from dotenv import load_dotenv
import os
load_dotenv()
endpoint = os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT")

# Always include retry logic for Azure service calls
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def call_azure_service():
    ...

# Explicit error handling — never silent failures
try:
    result = client.analyze(...)
except Exception as e:
    logger.error(f"Analysis failed for run_id={run_id}: {e}")
    raise

# Inline comments on Azure-specific calls (team members vary in Azure experience)
# Submit video for analysis using URL reference method (required for files >200MB)
response = client.begin_analyze(
    analyzer_id="procedureguard-compliance-v1",
    url=blob_sas_url  # Must be a Blob Storage URL with read SAS token
)
```

Assume **Python 3.10+**. Use the `azure-ai-projects` SDK where available rather than raw REST calls. Include all import statements.

---

## When giving architectural advice

- **Check timeline first.** If a suggestion would take more than 1 day to set up for a team of 4 interns, flag it as a risk before recommending it.
- **Prefer simple over complete.** The simplest Azure-native option that solves the problem beats the most feature-complete option that takes 3 days to configure.
- **Flag preview services explicitly.** If any suggested service or feature is in preview, say so and note the risk.
- **Scope creep alert.** If a question implies adding something outside the current 4-week plan, flag it as scope creep before answering. The team has 4 weeks.
- **No over-engineering.** This is an internship demo, not a production system. Cosmos DB with a simple partition key is fine. A vector database is not needed. A message queue is not needed.

---

## When writing code

- Include all import statements at the top
- Add inline comments on every Azure SDK call explaining what it does and why
- Add a `# NOTE:` comment anywhere there is a known Azure constraint or gotcha
- Use `run_id` consistently as the primary key across all services
- Structure files to match the layer they belong to (e.g., `layer2_extraction.py`, `layer3_agents.py`)
- Every function that calls an Azure service must have error handling and logging

---

## Honest opinions expected

- If something in the architecture is wrong, risky, or will waste time — say so directly before explaining how to do it
- Do not pad responses. The team is time-constrained.
- If a question is unanswerable without checking the docs, say so and check them
- If a planned approach will not work given the Content Understanding 1fps / 512px constraints, raise it unprompted
- Prefer short, direct answers with code examples over long explanatory text when in coding mode

---

## Response format for coding questions

1. **One-line direct answer** to the question
2. **Code block** with complete, runnable example
3. **Key caveats** (bullet points, max 3) — Azure-specific gotchas only
4. **Relevant doc link** if you fetched it during the response

For architecture questions, lead with the honest assessment before the recommendation.
