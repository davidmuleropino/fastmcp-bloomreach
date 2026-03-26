"""MCP resources: analysis ID→name maps for reports, funnels, retentions, segmentations."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from bloomreach.analyses_config import load

if TYPE_CHECKING:
    from fastmcp import FastMCP


def register_analyses_resources(mcp: "FastMCP") -> None:
    @mcp.resource("bloomreach://analyses/reports")
    def list_reports() -> str:
        """Map of report analysis_id → name. Use an ID with the get_report tool."""
        data = load().get("reports", {})
        if not data:
            return "No reports configured. Use upsert_analysis to add entries."
        return json.dumps([{"id": k, "name": v} for k, v in data.items()], indent=2)

    @mcp.resource("bloomreach://analyses/funnels")
    def list_funnels() -> str:
        """Map of funnel analysis_id → name. Use an ID with the get_funnel tool."""
        data = load().get("funnels", {})
        if not data:
            return "No funnels configured. Use upsert_analysis to add entries."
        return json.dumps([{"id": k, "name": v} for k, v in data.items()], indent=2)

    @mcp.resource("bloomreach://analyses/retentions")
    def list_retentions() -> str:
        """Map of retention analysis_id → name. Use an ID with the get_retention tool."""
        data = load().get("retentions", {})
        if not data:
            return "No retentions configured. Use upsert_analysis to add entries."
        return json.dumps([{"id": k, "name": v} for k, v in data.items()], indent=2)

    @mcp.resource("bloomreach://analyses/segmentations")
    def list_segmentations() -> str:
        """Map of segmentation analysis_id → name. Use an ID with the get_segmentation tool."""
        data = load().get("segmentations", {})
        if not data:
            return "No segmentations configured. Use upsert_analysis to add entries."
        return json.dumps([{"id": k, "name": v} for k, v in data.items()], indent=2)
