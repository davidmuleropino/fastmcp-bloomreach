"""MCP tools: Bloomreach Engagement consent categories and customer consent."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from fastmcp import FastMCP

    from bloomreach.client import BloomreachClient


def register_consent_tools(
    mcp: "FastMCP",
    get_client: Callable[[], "BloomreachClient"],
) -> None:
    @mcp.tool()
    async def list_consent_categories() -> list[dict[str, Any]]:
        """List all consent categories configured in the Bloomreach project.

        Returns each category's ID, name, and configuration as provided by
        the Bloomreach consent categories endpoint.
        """
        return await get_client().list_consent_categories()

    @mcp.tool()
    async def get_customer_consents(customer_id: str) -> dict[str, Any]:
        """Fetch the consent status for a Bloomreach customer.

        Returns the customer's opt-in / opt-out state across all consent
        categories as provided by the Bloomreach API.

        Args:
            customer_id: The customer's registered (email or external) ID.
        """
        return await get_client().get_customer_consents(customer_id)

    @mcp.tool()
    async def anonymize_customer(customer_id: str) -> dict[str, Any]:
        """Anonymize a Bloomreach customer by removing all PII properties.

        WARNING: Removes all properties marked as Private (PII) in Bloomreach
        Data Manager. This action is irreversible.

        Args:
            customer_id: The customer's registered (email or external) ID.
        """
        return await get_client().anonymize_customer(customer_id)
