"""
Layer 4 — Cosmos DB Client

Reads and writes all structured compliance data to Azure Cosmos DB (NoSQL API).
All documents must include run_id as the partition key.

Collections:
  - compliance-checklists: Agent 1 output (schemas/compliance_checklist.json)
  - verification-records:  Agent 2 output (schemas/verification_record.json)

Azure: Azure Cosmos DB (NoSQL API)
Owner: Person C (storage + orchestration)

IMPORTANT: Every write must include run_id. Missing run_id causes
cross-partition scan errors. See docs/KNOWN_ISSUES.md.
"""
import logging

from azure.cosmos import CosmosClient, PartitionKey
from azure.identity import DefaultAzureCredential
from tenacity import retry, stop_after_attempt, wait_exponential

from config import cfg

logger = logging.getLogger(__name__)


def get_cosmos_client() -> CosmosClient:
    """Initialise Cosmos DB client using DefaultAzureCredential."""
    credential = DefaultAzureCredential()
    # NOTE: Use endpoint + credential, never a connection string, for production.
    return CosmosClient(url=cfg.cosmos_endpoint, credential=credential)


def _get_container(container_name: str):
    """Return a Cosmos DB container client."""
    client = get_cosmos_client()
    database = client.get_database_client(cfg.cosmos_database)
    return database.get_container_client(container_name)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def write_checklist(checklist: dict) -> None:
    """
    Write a compliance checklist to Cosmos DB.
    Called by Agent 1 after generate_checklist().

    Args:
        checklist: dict matching schemas/compliance_checklist.json.
                   Must include run_id — used as partition key.
    """
    assert "run_id" in checklist, "run_id is required for all Cosmos DB writes"
    container = _get_container(cfg.cosmos_checklist_container)
    # TODO Week 3: implement upsert
    logger.info(f"Writing checklist | run_id={checklist['run_id']}")
    raise NotImplementedError("write_checklist not yet implemented")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def read_checklist(run_id: str) -> dict:
    """Fetch the compliance checklist for a given run_id."""
    # TODO Week 3: implement point read by run_id
    raise NotImplementedError("read_checklist not yet implemented")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def write_verdict(verdict: dict) -> None:
    """
    Write a single per-step verdict to Cosmos DB.
    Called by Agent 2 for each SOP step.

    Args:
        verdict: dict matching schemas/verification_record.json.
                 Must include run_id — used as partition key.
    """
    assert "run_id" in verdict, "run_id is required for all Cosmos DB writes"
    container = _get_container(cfg.cosmos_verdicts_container)
    logger.info(f"Writing verdict | run_id={verdict['run_id']} | step={verdict.get('step_id')}")
    raise NotImplementedError("write_verdict not yet implemented")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def read_verdicts(run_id: str) -> list[dict]:
    """Fetch all per-step verdicts for a given run_id. Used by the dashboard."""
    # TODO Week 3: implement query by partition key
    raise NotImplementedError("read_verdicts not yet implemented")
