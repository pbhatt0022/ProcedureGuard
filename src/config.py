from __future__ import annotations

from dataclasses import dataclass

from dotenv import load_dotenv
import os
from pathlib import Path


load_dotenv()


@dataclass(frozen=True)
class Config:
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment_name: str = "gpt-4.1-mini"
    azure_openai_api_version: str = ""
    provider_mode: str = "mcp"
    mcp_server_command: str = "python scripts/run_mcp_server.py"
    sqlite_db_path: str = str(Path("src/local_data/procedureguard.db"))
    redis_url: str = "redis://localhost:6379/0"
    session_ttl_seconds: int = 3600

    @classmethod
    def from_env(cls) -> "Config":
        session_ttl_seconds = os.environ.get("SESSION_TTL_SECONDS", "3600").strip() or "3600"
        return cls(
            azure_openai_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip(),
            azure_openai_api_key=os.environ.get("AZURE_OPENAI_API_KEY", "").strip(),
            azure_openai_deployment_name=(
                os.environ.get("QA_DEPLOYMENT_NAME", "").strip()
                or os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "").strip()
                or "gpt-4.1-mini"
            ),
            azure_openai_api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "").strip(),
            provider_mode=os.environ.get("PROVIDER_MODE", "mcp").strip().lower() or "mcp",
            mcp_server_command=os.environ.get(
                "MCP_SERVER_COMMAND",
                "python scripts/run_mcp_server.py",
            ).strip()
            or "python scripts/run_mcp_server.py",
            sqlite_db_path=os.environ.get(
                "SQLITE_DB_PATH",
                str(Path("src/local_data/procedureguard.db")),
            ).strip()
            or str(Path("src/local_data/procedureguard.db")),
            redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379/0").strip()
            or "redis://localhost:6379/0",
            session_ttl_seconds=int(session_ttl_seconds),
        )

    def validate_for_gpt(self) -> None:
        missing = []
        if not self.azure_openai_endpoint:
            missing.append("AZURE_OPENAI_ENDPOINT")
        if not self.azure_openai_api_key:
            missing.append("AZURE_OPENAI_API_KEY")
        if not self.azure_openai_deployment_name:
            missing.append("AZURE_OPENAI_DEPLOYMENT_NAME")
        if not self.azure_openai_api_version:
            missing.append("AZURE_OPENAI_API_VERSION")

        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"Missing Azure OpenAI configuration: {joined}")


def get_config() -> Config:
    return Config.from_env()
