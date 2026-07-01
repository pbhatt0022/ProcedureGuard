from __future__ import annotations

import asyncio
import json
import shlex
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_config


def _server_command() -> str:
    return get_config().mcp_server_command


async def _run() -> None:
    command_parts = shlex.split(_server_command())
    server_params = StdioServerParameters(command=command_parts[0], args=command_parts[1:])

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"- {tool.name}")
            print("-" * 80)

            test_calls = [
                ("retrieve_run_summary", {"run_id": "RUN-102"}),
                ("query_verdicts", {"run_id": "RUN-102", "step_id": "STEP-03"}),
                ("retrieve_checklist_step", {"run_id": "RUN-102", "step_id": "STEP-03"}),
                ("fetch_keyframes", {"run_id": "RUN-102", "step_id": "STEP-03"}),
                ("fetch_video_clips", {"run_id": "RUN-102", "step_id": "STEP-03"}),
                ("retrieve_ticket_status", {"ticket_id": "INC-2045"}),
                ("query_tickets", {"run_id": "RUN-102", "step_id": "STEP-03"}),
                ("query_incidents", {"run_id": "RUN-102", "severity": "Critical"}),
                ("retrieve_incidents", {"incident_id": "INC-2045"}),
                ("query_audit_logs", {"run_id": "RUN-102", "step_id": "STEP-03"}),
            ]

            for tool_name, arguments in test_calls:
                result = await session.call_tool(tool_name, arguments)
                structured = getattr(result, "structuredContent", None) or getattr(
                    result,
                    "structured_content",
                    None,
                )
                payload = structured if structured is not None else str(result)
                print(tool_name)
                print(json.dumps(payload, indent=2))
                print("-" * 80)


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
