"""MCP tools: Bloomreach Engagement catalog management."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from fastmcp import FastMCP

    from bloomreach.client import BloomreachClient


def register_catalogs_tools(
    mcp: "FastMCP",
    get_client: Callable[[], "BloomreachClient"],
) -> None:
    @mcp.tool()
    async def list_catalogs() -> list[dict[str, Any]]:
        """List all product catalogs in the Bloomreach project.

        Returns each catalog's id and name.
        Requires: Catalogs > Get catalog list permission in your API group.
        """
        return await get_client().list_catalogs()
