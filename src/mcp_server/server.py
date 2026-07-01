from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from src.mcp_server.tools import create_mcp_server


def build_server() -> FastMCP:
    return create_mcp_server()
