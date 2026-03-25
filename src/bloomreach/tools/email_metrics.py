"""MCP tool: Bloomreach email campaign engagement metrics."""

from __future__ import annotations

import csv
import io
from typing import TYPE_CHECKING, Any, Callable

from pydantic import BaseModel

if TYPE_CHECKING:
    from fastmcp import FastMCP

    from bloomreach.client import BloomreachClient


class EmailMetricsResult(BaseModel):
    campaign_id: str
    period_days: int
    delivered: int
    opened: int
    clicked: int
    open_rate: float
    """Opened / Delivered"""
    click_rate_from_delivered: float
    """Clicked / Delivered"""
    click_rate_from_opened: float
    """Clicked / Opened"""


def _safe_rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator > 0 else 0.0


def _parse_csv_metrics(csv_text: str) -> dict[str, int]:
    """Parse a Bloomreach Analysis API CSV response into a flat metric dict."""
    reader = csv.DictReader(io.StringIO(csv_text))
    totals: dict[str, int] = {}
    for row in reader:
        for k, v in row.items():
            try:
                totals[k] = totals.get(k, 0) + int(float(v))
            except (ValueError, TypeError):
                pass
    return totals


def _extract_int(data: dict[str, Any], *keys: str) -> int:
    """Return the first non-None value from a list of candidate key names."""
    for key in keys:
        val = data.get(key)
        if val is not None:
            try:
                return int(float(val))
            except (ValueError, TypeError):
                pass
    return 0


def register_email_metrics_tools(
    mcp: "FastMCP",
    get_client: Callable[[], "BloomreachClient"],
) -> None:
    @mcp.tool()
    async def get_email_campaign_metrics(
        campaign_id: str,
        days: int = 30,
    ) -> EmailMetricsResult:
        """Get email engagement metrics for a Bloomreach campaign.

        Returns open rate, click rate from delivered, and click rate from
        opened for the specified campaign over the last N days.

        Args:
            campaign_id: The Bloomreach scenario/campaign ID.
            days: Number of past days to aggregate (default 30).
        """
        data = await get_client().get_email_campaign_metrics(campaign_id, days=days)

        delivered = _extract_int(
            data, "delivered", "emails_delivered", "emailsDelivered", "total_delivered"
        )
        opened = _extract_int(
            data, "opened", "emails_opened", "emailsOpened", "unique_opens", "total_opens"
        )
        clicked = _extract_int(
            data,
            "clicked",
            "emails_clicked",
            "emailsClicked",
            "unique_clicks",
            "total_clicks",
        )

        return EmailMetricsResult(
            campaign_id=campaign_id,
            period_days=days,
            delivered=delivered,
            opened=opened,
            clicked=clicked,
            open_rate=_safe_rate(opened, delivered),
            click_rate_from_delivered=_safe_rate(clicked, delivered),
            click_rate_from_opened=_safe_rate(clicked, opened),
        )
