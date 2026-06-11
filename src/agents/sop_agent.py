"""
Layer 3 — Agent 1: SOP Ingestion Agent (Foundry Agent Service)

Wraps the checklist_generator reasoning module in a Foundry Agent.
Receives Steps JSON from Layer 2, calls GPT-4o to generate a structured
compliance checklist, and writes the result to Cosmos DB.

Input:  Steps JSON (schemas/sop_steps.json) + run_id
Output: Compliance checklist written to Cosmos DB (schemas/compliance_checklist.json)
Azure:  Azure Foundry Agent Service + Azure OpenAI GPT-4o
Owner:  Person A (SOP pipeline)

Note: Direct SDK calls used here (no MCP). MCP is only for Agent 3.
See docs/DECISIONS_AND_RATIONALE.md — "MCP used only for Agent 3".
"""
import logging

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from tenacity import retry, stop_after_attempt, wait_exponential

from config import cfg
from src.reasoning.checklist_generator import generate_checklist
from src.storage.cosmos_client import write_checklist

logger = logging.getLogger(__name__)


def get_project_client() -> AIProjectClient:
    """Initialise Foundry Agent Service client."""
    credential = DefaultAzureCredential()
    return AIProjectClient(
        endpoint=cfg.foundry_project_endpoint,
        credential=credential,
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def run_sop_agent(sop_steps: dict, run_id: str) -> dict:
    """
    Execute Agent 1: convert Steps JSON into a compliance checklist.

    Args:
        sop_steps: Output of sop_extractor.extract_sop_steps()
        run_id:    Pipeline run identifier — used as Cosmos DB partition key.

    Returns:
        checklist dict matching schemas/compliance_checklist.json
    """
    # TODO Week 3: wrap generate_checklist() + write_checklist() in a Foundry Agent invocation
    logger.info(f"Agent 1 started | run_id={run_id}")
    raise NotImplementedError("run_sop_agent not yet implemented")
