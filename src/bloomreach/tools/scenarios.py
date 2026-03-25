"""MCP tools: list and retrieve Bloomreach Engagement scenarios (campaigns)."""

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
        status: str | None = None,
        audience_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """List scenarios (campaigns) from Bloomreach Engagement.

        Each scenario includes its targeting segments, status, and audience size
        as returned by the Bloomreach API.

        Args:
            status: Optional filter by scenario status, e.g. "active", "paused",
                "draft". Case-insensitive exact match.
            audience_type: Optional filter applied as a case-insensitive substring
                match against audience or name fields (e.g. "paid").
        """
        scenarios = await get_client().list_scenarios()

        if status:
            needle = status.lower()
            scenarios = [s for s in scenarios if str(s.get("status", "")).lower() == needle]

        if audience_type:
            needle = audience_type.lower()
            scenarios = [
                s
                for s in scenarios
                if needle in str(s.get("audience", "")).lower()
                or needle in str(s.get("name", "")).lower()
            ]

        return scenarios

    @mcp.tool()
    async def get_scenario(campaign_id: str) -> dict[str, Any]:
        """Get full detail for a single Bloomreach scenario (campaign).

        Returns the scenario's name, status, audience configuration, targeting
        segments, audience size, and all other metadata provided by the API.

        Args:
            campaign_id: The Bloomreach scenario/campaign ID to retrieve.
        """
        return await get_client().get_scenario(campaign_id)
