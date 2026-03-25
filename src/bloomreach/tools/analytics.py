"""MCP tools: Bloomreach Engagement email campaign metrics and analysis API."""

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
    start_date: str
    end_date: str
    delivered: int
    opened: int
    clicked: int
    bounced: int
    unsubscribed: int
    open_rate: float
    """Opened / Delivered"""
    click_rate_from_delivered: float
    """Clicked / Delivered"""
    click_rate_from_opened: float
    """Clicked / Opened"""
    bounce_rate: float
    """Bounced / Delivered"""
    unsubscribe_rate: float
    """Unsubscribed / Delivered"""


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


def _parse_csv(csv_text: str) -> list[dict[str, str]]:
    """Parse a Bloomreach Analysis API CSV response into a list of row dicts."""
    reader = csv.DictReader(io.StringIO(csv_text))
    return [dict(row) for row in reader]


def _extract_int(data: dict[str, Any], *keys: str) -> int:
    """Return the integer value of the first matching key found in data."""
    for key in keys:
        val = data.get(key)
        if val is not None:
            try:
                return int(float(val))
            except (ValueError, TypeError):
                pass
    return 0


def register_analytics_tools(
    mcp: "FastMCP",
    get_client: Callable[[], "BloomreachClient"],
) -> None:
    @mcp.tool()
    async def get_email_campaign_metrics(
        campaign_id: str,
        start_date: str,
        end_date: str,
    ) -> EmailMetricsResult:
        """Get aggregate email engagement metrics for a Bloomreach campaign.

        Returns delivered, opened, clicked, bounced, and unsubscribed counts
        plus derived rates for the specified campaign over a date range.

        Args:
            campaign_id: The Bloomreach scenario/campaign ID.
            start_date: Start of the reporting period in YYYY-MM-DD format (inclusive).
            end_date: End of the reporting period in YYYY-MM-DD format (inclusive).
        """
        data = await get_client().get_email_campaign_metrics(
            campaign_id, start_date=start_date, end_date=end_date
        )

        delivered = _extract_int(
            data, "delivered", "emails_delivered", "emailsDelivered", "total_delivered"
        )
        opened = _extract_int(
            data, "opened", "emails_opened", "emailsOpened", "unique_opens", "total_opens"
        )
        clicked = _extract_int(
            data, "clicked", "emails_clicked", "emailsClicked", "unique_clicks", "total_clicks"
        )
        bounced = _extract_int(
            data, "bounced", "bounces", "hard_bounces", "hardBounces", "total_bounces"
        )
        unsubscribed = _extract_int(
            data,
            "unsubscribed",
            "unsubscribes",
            "opt_outs",
            "optOuts",
            "total_unsubscribes",
        )

        return EmailMetricsResult(
            campaign_id=campaign_id,
            start_date=start_date,
            end_date=end_date,
            delivered=delivered,
            opened=opened,
            clicked=clicked,
            bounced=bounced,
            unsubscribed=unsubscribed,
            open_rate=_safe_rate(opened, delivered),
            click_rate_from_delivered=_safe_rate(clicked, delivered),
            click_rate_from_opened=_safe_rate(clicked, opened),
            bounce_rate=_safe_rate(bounced, delivered),
            unsubscribe_rate=_safe_rate(unsubscribed, delivered),
        )

    @mcp.tool()
    async def get_funnel(analysis_id: str) -> list[dict[str, str]]:
        """Run a saved funnel analysis and return results as a list of row dicts.

        Fetches the analysis identified by analysis_id from the Bloomreach
        Analysis API and parses the CSV response into structured records.

        Args:
            analysis_id: The ID of the saved funnel analysis in Bloomreach.
        """
        csv_text = await get_client().get_analysis("funnel", analysis_id)
        return _parse_csv(csv_text)

    @mcp.tool()
    async def get_report(analysis_id: str) -> list[dict[str, str]]:
        """Run a saved report analysis and return results as a list of row dicts.

        Fetches the analysis identified by analysis_id from the Bloomreach
        Analysis API and parses the CSV response into structured records.

        Args:
            analysis_id: The ID of the saved report analysis in Bloomreach.
        """
        csv_text = await get_client().get_analysis("report", analysis_id)
        return _parse_csv(csv_text)

    @mcp.tool()
    async def get_retention(analysis_id: str) -> list[dict[str, str]]:
        """Run a saved retention analysis and return results as a list of row dicts.

        Fetches the analysis identified by analysis_id from the Bloomreach
        Analysis API and parses the CSV response into structured records.

        Args:
            analysis_id: The ID of the saved retention analysis in Bloomreach.
        """
        csv_text = await get_client().get_analysis("retention", analysis_id)
        return _parse_csv(csv_text)

    @mcp.tool()
    async def get_segmentation(analysis_id: str) -> list[dict[str, str]]:
        """Run a saved segmentation analysis and return results as a list of row dicts.

        Fetches the analysis identified by analysis_id from the Bloomreach
        Analysis API and parses the CSV response into structured records.

        Args:
            analysis_id: The ID of the saved segmentation analysis in Bloomreach.
        """
        csv_text = await get_client().get_analysis("segmentation", analysis_id)
        return _parse_csv(csv_text)
