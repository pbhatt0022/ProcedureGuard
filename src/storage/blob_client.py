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
URL to Document Intelligence (SOP PDFs) or OpenCV/GPT-4o Vision (videos) —
they need a pre-authenticated URL, not just the path.
"""
import logging
import os
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
def write_keyframe(image_bytes: bytes, run_id: str, step_id: str) -> str:
    """
    Write a keyframe image to Blob Storage or local folder fallback.

    Returns:
        Blob path string: keyframes/{run_id}/{step_id}.jpg
        Stored in the verification record for the evidence viewer.
    """
    blob_path = f"keyframes/{run_id}/{step_id}.jpg"
    
    if cfg.storage_account_url:
        try:
            client = get_blob_service_client()
            blob_client = client.get_blob_client(
                container=cfg.storage_container_keyframes,
                blob=f"{run_id}/{step_id}.jpg"
            )
            blob_client.upload_blob(image_bytes, overwrite=True)
            logger.info(f"Uploaded keyframe to Azure Blob Storage: {blob_path}")
            return blob_path
        except Exception as exc:
            logger.warning(f"Failed to upload keyframe to Azure Blob Storage, falling back to local: {exc}")
            
    # Local fallback
    local_dir = os.path.join(cfg.runs_dir, run_id, "keyframes")
    os.makedirs(local_dir, exist_ok=True)
    local_file = os.path.join(local_dir, f"{step_id}.jpg")
    with open(local_file, "wb") as f:
        f.write(image_bytes)
    logger.info(f"Saved keyframe locally: {local_file}")
    
    return blob_path


