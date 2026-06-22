import os
from dotenv import load_dotenv

load_dotenv()

# If service principal vars were left blank in .env, remove them from the environment
# so DefaultAzureCredential skips EnvironmentCredential and falls through to AzureCliCredential.
# Without this, an empty AZURE_CLIENT_ID causes a ValueError instead of a graceful fallback.
for _var in (
    "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "AZURE_TENANT_ID",
    # If these are blank in .env, remove them so SDK credential helpers
    # skip the empty-string path and fall through to DefaultAzureCredential.
    "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_AD_TOKEN",
):
    if not os.environ.get(_var):
        os.environ.pop(_var, None)

# On Windows, ensure the Azure CLI directory is on PATH so AzureCliCredential can find `az`.
# The CLI installer doesn't always update the PATH for the current session.
_AZ_CLI_WIN = r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin"
if os.name == "nt" and _AZ_CLI_WIN not in os.environ.get("PATH", ""):
    os.environ["PATH"] = os.environ["PATH"] + ";" + _AZ_CLI_WIN


class _Config:
    # Azure Identity
    tenant_id: str = os.getenv("AZURE_TENANT_ID", "")
    subscription_id: str = os.getenv("AZURE_SUBSCRIPTION_ID", "")

    # Azure OpenAI
    openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
    openai_deployment: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
    openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")

    # Azure AI Document Intelligence
    doc_intelligence_endpoint: str = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", "").rstrip("/")
    doc_intelligence_key: str = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY", "")

    # Azure Blob Storage
    storage_account_name: str = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "")
    storage_account_url: str = os.getenv("AZURE_STORAGE_ACCOUNT_URL", "")
    storage_container_sop: str = os.getenv("AZURE_STORAGE_CONTAINER_SOP", "sop-documents")
    storage_container_video: str = os.getenv("AZURE_STORAGE_CONTAINER_VIDEO", "manufacturing-videos")
    storage_container_keyframes: str = os.getenv("AZURE_STORAGE_CONTAINER_KEYFRAMES", "keyframes")

    # Application
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    runs_dir: str = os.path.abspath(os.getenv("PROCEDUREGUARD_RUNS_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs"))


cfg = _Config()
