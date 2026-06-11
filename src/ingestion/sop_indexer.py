"""
Layer 2 — SOP Indexer (Multimodal RAG)

Indexes non-text SOP content — diagrams, figures, annotated tables, and
safety symbols — into Azure AI Search using multimodal embeddings.
Enables Agent 1 to retrieve visual SOP context when generating the
compliance checklist.

Input:  Blob Storage URL pointing to an SOP PDF
Output: Confirmation that the index has been populated for this run_id
Azure:  Azure AI Search (S1 tier, multimodal embeddings)
Owner:  Person A (SOP pipeline)
"""
import logging

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from tenacity import retry, stop_after_attempt, wait_exponential

from config import cfg

logger = logging.getLogger(__name__)


def get_search_index_client() -> SearchIndexClient:
    """Initialise AI Search index management client."""
    credential = DefaultAzureCredential()
    return SearchIndexClient(endpoint=cfg.search_endpoint, credential=credential)


def get_search_client() -> SearchClient:
    """Initialise AI Search document client for the SOP visual index."""
    credential = DefaultAzureCredential()
    return SearchClient(
        endpoint=cfg.search_endpoint,
        index_name=cfg.search_index_name,
        credential=credential,
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def index_sop_visuals(sop_blob_url: str, run_id: str) -> None:
    """
    Index visual content from an SOP PDF into Azure AI Search.

    Args:
        sop_blob_url: SAS URL to the SOP PDF in Blob Storage.
        run_id:       Pipeline run identifier — used to scope index entries.
    """
    # TODO Week 3: implement multimodal indexing once AI Search S1 is provisioned
    logger.info(f"Indexing SOP visuals | run_id={run_id}")
    raise NotImplementedError("index_sop_visuals not yet implemented")


def query_visual_context(query: str, run_id: str, top: int = 3) -> list[dict]:
    """
    Retrieve relevant visual SOP context for a given compliance criterion.
    Called by Agent 1 during checklist generation.

    Args:
        query:  Natural language description of the SOP step.
        run_id: Scopes the search to this run's indexed SOP.
        top:    Number of results to return.

    Returns:
        List of relevant visual context chunks with captions and page refs.
    """
    # TODO Week 3: implement semantic retrieval once AI Search index is built
    raise NotImplementedError("query_visual_context not yet implemented")
