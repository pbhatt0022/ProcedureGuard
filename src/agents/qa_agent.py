"""
Layer 3 — Agent 3: Q&A Chat Agent (Foundry Agent Service + MCP)

Serves the interactive chat panel in the Streamlit dashboard.
Receives a natural language question from the operator, interprets intent
via GPT-4o, then uses MCP tool calls to query Cosmos DB verdicts and/or
fetch video clips from Blob Storage.

Input:  User question (str) + run_id to scope the query
Output: Evidence-backed natural language answer (str)
Azure:  Azure Foundry Agent Service + MCP tools (mcp.ai.azure.com)
Owner:  Person D (dashboard)

Note: MCP is used ONLY in this agent. See docs/DECISIONS_AND_RATIONALE.md.
"""
import logging

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from tenacity import retry, stop_after_attempt, wait_exponential

from config import cfg

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def answer_question(question: str, run_id: str) -> str:
    """
    Route a user question to Agent 3 and return an evidence-backed answer.

    Args:
        question: Natural language question from the dashboard chat panel.
        run_id:   Scopes MCP queries to this run's verdicts and clips.

    Returns:
        Natural language answer with evidence references (timestamps, step IDs).
    """
    # TODO Week 3: implement MCP tool connections + agent invocation
    logger.info(f"Agent 3 received question | run_id={run_id}")
    raise NotImplementedError("answer_question not yet implemented")
