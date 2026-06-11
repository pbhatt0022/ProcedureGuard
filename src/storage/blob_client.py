"""
Layer 4 — Blob Storage Client

Handles all binary asset storage: SOP PDFs, manufacturing videos, keyframes.

Container layout:
  sop-documents/        {run_id}/{filename}.pdf
  manufacturing-videos/ {run_id}/{filename}.mp4
  keyframes/            {run_id}/{step_id}.jpg

Azure: Azure Blob Storage
Owner: Person C (storage + orchestration)

NOTE: Always generate a SAS URL with read permission when passing a Blob
URL to Content Understanding or Document Intelligence — they need a
pre-authenticated URL, not just the path.
"""
import logging
from datetime import datetime, timedelta, timezone

from azure.identity import DefaultAzureCredential
from azure.storage.blob import (
    BlobServiceClient,
    BlobSasPermissions,
    generate_blob_sas,
)
from tenacity import retry, stop_after_attempt, wait_exponential

from config import cfg

logger = logging.getLogger(__name__)


def get_blob_service_client() -> BlobServiceClient:
    """Initialise Blob Storage client using DefaultAzureCredential."""
    credential = DefaultAzureCredential()
    return BlobServiceClient(
        account_url=cfg.storage_account_url,
        credential=credential,
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def upload_sop(local_path: str, run_id: str, filename: str) -> str:
    """
    Upload an SOP PDF to Blob Storage.

    Returns:
        SAS URL valid for 2 hours — pass directly to Document Intelligence.
    """
    # TODO Week 3: implement upload + SAS URL generation
    raise NotImplementedError("upload_sop not yet implemented")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def upload_video(local_path: str, run_id: str, filename: str) -> str:
    """
    Upload a manufacturing video to Blob Storage.

    Returns:
        SAS URL valid for 4 hours — pass directly to Content Understanding.
        NOTE: Use URL reference method (not binary upload) for Content Understanding.
    """
    # TODO Week 3: implement upload + SAS URL generation
    raise NotImplementedError("upload_video not yet implemented")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def write_keyframe(image_bytes: bytes, run_id: str, step_id: str) -> str:
    """
    Write a keyframe image to Blob Storage.
    Called by Agent 2 for each deviation or compliant step.

    Returns:
        Blob path string: keyframes/{run_id}/{step_id}.jpg
        Stored in the verification record for the evidence viewer.
    """
    blob_path = f"{run_id}/{step_id}.jpg"
    # TODO Week 3: implement upload
    raise NotImplementedError("write_keyframe not yet implemented")


def read_observations(run_id: str) -> dict:
    """
    Read the Observations JSON for a run from Blob Storage.
    Stored as a JSON blob alongside the video during extraction.
    """
    # TODO Week 3: implement download + parse
    raise NotImplementedError("read_observations not yet implemented")
