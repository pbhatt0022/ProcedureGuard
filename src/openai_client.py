"""
Shared Azure OpenAI client factory.

One process-wide cached AzureOpenAI client. Previously video_analyzer,
checklist_generator, compliance_engine, and qa_agent each defined their own
get_openai_client() and rebuilt the client on *every* call — which re-walked the
full DefaultAzureCredential chain (EnvironmentCredential → ManagedIdentity/IMDS →
AzureCliCredential) and added an IMDS metadata-probe round-trip to each of the
~40 GPT-4o calls in a pipeline run. Caching the client removes that per-call cost.

Auth: API key when cfg.openai_api_key is set, otherwise DefaultAzureCredential
(the az login session locally). The bearer-token provider refreshes tokens
internally on each request, so caching the client across the process is safe.
"""
import functools

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

from config import cfg


@functools.lru_cache(maxsize=1)
def get_openai_client() -> AzureOpenAI:
    """Return a process-wide cached AzureOpenAI client (key auth or Entra ID)."""
    if cfg.openai_api_key:
        return AzureOpenAI(
            azure_endpoint=cfg.openai_endpoint,
            api_version=cfg.openai_api_version,
            api_key=cfg.openai_api_key,
        )
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default",
    )
    return AzureOpenAI(
        azure_endpoint=cfg.openai_endpoint,
        api_version=cfg.openai_api_version,
        azure_ad_token_provider=token_provider,
    )
