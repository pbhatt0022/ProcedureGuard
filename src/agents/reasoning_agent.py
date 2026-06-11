"""
Layer 3 — Agent 2: Compliance Reasoning Agent (Foundry Agent Service)

The core reasoning agent. Retrieves the compliance checklist from Cosmos DB,
fetches the video Observations JSON, and for each SOP step:
  1. Calls GPT-4o (via compliance_engine) to produce a verdict
  2. Retries with adjacent segments if confidence < threshold
  3. Runs the Python sequence + timing engine
  4. Writes verdicts and keyframes to Cosmos DB / Blob Storage

Input:  run_id (used to fetch checklist + observations from Cosmos DB / Blob)
Output: Per-step verdicts written to Cosmos DB (schemas/verification_record.json)
Azure:  Azure Foundry Agent Service + Azure OpenAI GPT-4o
Owner:  Person B (video pipeline)

Note: Direct SDK calls only. No MCP. See docs/DECISIONS_AND_RATIONALE.md.
"""
import logging

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from tenacity import retry, stop_after_attempt, wait_exponential

from config import cfg
from src.reasoning.compliance_engine import reason_step
from src.reasoning.sequence_timing import validate_sequence_and_timing
from src.storage.cosmos_client import read_checklist, write_verdict
from src.storage.blob_client import write_keyframe, read_observations

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def run_reasoning_agent(run_id: str) -> list[dict]:
    """
    Execute Agent 2: produce per-step compliance verdicts for a pipeline run.

    Args:
        run_id: Identifies the run — used to fetch checklist + observations
                from Cosmos DB and Blob Storage.

    Returns:
        List of verdict dicts, each matching schemas/verification_record.json.
        Also written to Cosmos DB as a side effect.
    """
    # TODO Week 3: wrap pipeline reasoning loop (reason_step + sequence_timing) in a Foundry Agent
    logger.info(f"Agent 2 started | run_id={run_id}")
    raise NotImplementedError("run_reasoning_agent not yet implemented")
