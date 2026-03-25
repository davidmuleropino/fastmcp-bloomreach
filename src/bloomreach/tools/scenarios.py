"""MCP tool: list Bloomreach scenarios (campaigns)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from fastmcp import FastMCP

    from bloomreach.client import BloomreachClient


def register_scenarios_tools(
    mcp: "FastMCP",
    get_client: Callable[[], "BloomreachClient"],
) -> None:
    @mcp.tool()
    async def list_scenarios(
        audience_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """List scenarios (campaigns) from Bloomreach Engagement.

        Args:
            audience_type: Optional filter applied as a case-insensitive
                substring match against the scenario's audience or name fields
                (e.g. "paid audience").  When omitted, all scenarios are returned.
        """
        scenarios = await get_client().list_scenarios()

        if audience_type:
            needle = audience_type.lower()
            scenarios = [
                s
                for s in scenarios
                if needle in str(s.get("audience", "")).lower()
                or needle in str(s.get("name", "")).lower()
            ]

        return scenarios
