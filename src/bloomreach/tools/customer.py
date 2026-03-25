"""MCP tools: Bloomreach Engagement customer attribute and export endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from fastmcp import FastMCP

    from bloomreach.client import BloomreachClient


def register_customer_tools(
    mcp: "FastMCP",
    get_client: Callable[[], "BloomreachClient"],
) -> None:
    @mcp.tool()
    async def get_customer_attributes(
        customer_id: str,
        attribute_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Fetch attributes for a Bloomreach customer by registered ID.

        When attribute_types is omitted all attribute types are requested.
        Valid types: "property", "expression", "prediction", "segmentation",
        "aggregate", "recommendation".

        Args:
            customer_id: The customer's registered (email or external) ID.
            attribute_types: Optional list of attribute type strings to fetch.
        """
        if attribute_types:
            attributes = [{"type": t} for t in attribute_types]
        else:
            attributes = [
                {"type": "property"},
                {"type": "expression"},
                {"type": "prediction"},
                {"type": "segmentation"},
                {"type": "aggregate"},
                {"type": "recommendation"},
            ]
        return await get_client().get_customer_attributes(customer_id, attributes)

    @mcp.tool()
    async def get_customer_properties(customer_id: str) -> list[dict[str, Any]]:
        """Fetch the property attributes for a Bloomreach customer.

        Returns the list of property attribute dicts as returned by the API.

        Args:
            customer_id: The customer's registered (email or external) ID.
        """
        data = await get_client().get_customer_attributes(customer_id, [{"type": "property"}])
        return data.get("attributes") or data.get("properties") or []

    @mcp.tool()
    async def get_customer_expressions(customer_id: str) -> list[dict[str, Any]]:
        """Fetch the expression attributes for a Bloomreach customer.

        Returns the list of expression attribute dicts as returned by the API.

        Args:
            customer_id: The customer's registered (email or external) ID.
        """
        data = await get_client().get_customer_attributes(customer_id, [{"type": "expression"}])
        return data.get("attributes") or data.get("expressions") or []

    @mcp.tool()
    async def get_customer_predictions(customer_id: str) -> list[dict[str, Any]]:
        """Fetch the prediction attributes for a Bloomreach customer.

        Returns the list of prediction attribute dicts as returned by the API.

        Args:
            customer_id: The customer's registered (email or external) ID.
        """
        data = await get_client().get_customer_attributes(customer_id, [{"type": "prediction"}])
        return data.get("attributes") or data.get("predictions") or []

    @mcp.tool()
    async def export_customer(customer_id: str) -> dict[str, Any]:
        """Export all data stored for a Bloomreach customer.

        Returns the full customer export dict containing all profile data,
        events, and attributes as provided by the Bloomreach export endpoint.

        Args:
            customer_id: The customer's registered (email or external) ID.
        """
        return await get_client().export_customer(customer_id)
