"""MCP tools: list, upsert, and delete entries in the analyses ID→name config."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Literal

from bloomreach.analyses_config import ANALYSIS_TYPES, load, save

if TYPE_CHECKING:
    from fastmcp import FastMCP

AnalysisType = Literal["reports", "funnels", "retentions", "segmentations"]


def register_analyses_config_tools(mcp: "FastMCP") -> None:
    @mcp.tool()
    def list_analyses(
        type: AnalysisType | Literal["all"] = "all",
    ) -> dict:
        """List all configured analyses by type with their IDs and names.

        Use this to discover which analysis IDs are available before calling
        get_report, get_funnel, get_retention, or get_segmentation.

        Args:
            type: Filter by analysis type, or "all" to return every type.
        """
        config = load()
        if type == "all":
            return {
                t: [{"id": k, "name": v} for k, v in config.get(t, {}).items()]
                for t in ANALYSIS_TYPES
            }
        return [{"id": k, "name": v} for k, v in config.get(type, {}).items()]

    @mcp.tool()
    def upsert_analysis(
        type: AnalysisType,
        analysis_id: str,
        name: str,
    ) -> dict:
        """Add or update an analysis entry in the config.

        Creates the entry if the analysis_id is new; updates the name if it
        already exists.  Works in both stdio (writes analyses.json) and HTTP /
        cloud mode (writes to file if the path is writable, otherwise in-memory
        only for this session).

        For cloud deployments with an ephemeral filesystem, copy the
        "updated_config" value from the response into the
        BLOOMREACH_ANALYSES_JSON environment variable so changes survive
        restarts.

        Args:
            type: Analysis type — "reports", "funnels", "retentions", or "segmentations".
            analysis_id: The Bloomreach analysis ID (from the URL when editing the analysis).
            name: A human-readable label for this analysis.
        """
        config = load()
        section = config.setdefault(type, {})
        action = "updated" if analysis_id in section else "added"
        section[analysis_id] = name

        persisted = save(config)
        return {
            "action": action,
            "type": type,
            "analysis_id": analysis_id,
            "name": name,
            "persisted_to_file": persisted,
            "cloud_note": (
                None
                if persisted
                else (
                    "Filesystem is read-only. Copy updated_config into"
                    " BLOOMREACH_ANALYSES_JSON env var to persist."
                )
            ),
            "updated_config": json.dumps(config),
        }

    @mcp.tool()
    def delete_analysis(
        type: AnalysisType,
        analysis_id: str,
    ) -> dict:
        """Remove an analysis entry from the config.

        For cloud deployments with an ephemeral filesystem, copy the
        "updated_config" value from the response into the
        BLOOMREACH_ANALYSES_JSON environment variable so the deletion
        survives restarts.

        Args:
            type: Analysis type — "reports", "funnels", "retentions", or "segmentations".
            analysis_id: The Bloomreach analysis ID to remove.
        """
        config = load()
        section = config.get(type, {})

        if analysis_id not in section:
            return {
                "action": "not_found",
                "type": type,
                "analysis_id": analysis_id,
            }

        del section[analysis_id]
        persisted = save(config)
        return {
            "action": "deleted",
            "type": type,
            "analysis_id": analysis_id,
            "persisted_to_file": persisted,
            "cloud_note": (
                None
                if persisted
                else (
                    "Filesystem is read-only. Copy updated_config into"
                    " BLOOMREACH_ANALYSES_JSON env var to persist."
                )
            ),
            "updated_config": json.dumps(config),
        }
