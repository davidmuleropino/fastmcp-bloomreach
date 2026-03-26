"""Async HTTP client for the Bloomreach Engagement API."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_MAX_RETRIES = 5
_INITIAL_BACKOFF = 1.0
_MAX_BACKOFF = 30.0


class BloomreachClient:
    """Async Bloomreach Engagement API client.

    Uses HTTP Basic Auth (API_KEY_ID:API_SECRET). No token refresh needed —
    credentials are static API keys. The project token is embedded in every
    URL path as /track/v2/projects/{project_token}/...
    """

    def __init__(self) -> None:
        self._base_url: str = os.environ.get(
            "BLOOMREACH_BASE_URL", "https://api.exponea.com"
        ).rstrip("/")
        self._project_token: str = os.environ["BLOOMREACH_PROJECT_TOKEN"]
        self._api_key_id: str = os.environ["BLOOMREACH_API_KEY_ID"]
        self._api_secret: str = os.environ["BLOOMREACH_API_SECRET"]
        self._http: httpx.AsyncClient | None = None

    async def start(self) -> None:
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            auth=(self._api_key_id, self._api_secret),
            timeout=30.0,
        )

    async def stop(self) -> None:
        if self._http:
            await self._http.aclose()
            self._http = None

    def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            raise RuntimeError("BloomreachClient not started; call start() first")
        return self._http

    @property
    def project_token(self) -> str:
        return self._project_token

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """Make an authenticated request with 429 retry + exponential backoff."""
        backoff = _INITIAL_BACKOFF
        for attempt in range(_MAX_RETRIES):
            response = await self._client().request(method, path, params=params, json=json)

            if response.status_code == 429 and attempt < _MAX_RETRIES - 1:
                wait = min(backoff, _MAX_BACKOFF)
                logger.warning("Rate limited (429), retrying in %.1fs", wait)
                await asyncio.sleep(wait)
                backoff *= 2
                continue

            response.raise_for_status()
            return response.json()

        raise RuntimeError("Exceeded max retries")

    async def _request_csv(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> str:
        """Make a request that returns CSV text (Bloomreach Analysis API)."""
        response = await self._client().request(method, path, json=json)
        response.raise_for_status()
        return response.text

    # ---- Email Campaign Metrics ----

    async def get_email_campaign_metrics(
        self,
        campaign_id: str,
        start_date: str,
        end_date: str,
    ) -> dict[str, Any]:
        """Fetch aggregate email metrics for a campaign over a date range.

        Endpoint: GET /track/v2/projects/{project_token}/campaigns/{id}/metrics
        Query params: start_date=YYYY-MM-DD, end_date=YYYY-MM-DD

        Metrics include delivered, opened, clicked, bounced, and unsubscribed.
        """
        path = f"/track/v2/projects/{self._project_token}/campaigns/{campaign_id}/metrics"
        return await self._request(
            "GET", path, params={"start_date": start_date, "end_date": end_date}
        )

    # ---- Analysis API (CSV) ----

    async def get_analysis(self, analysis_type: str, analysis_id: str) -> str:
        """Run a saved analysis and return the raw CSV response text.

        Endpoint: POST /data/v2/projects/{project_token}/analyses/{analysis_type}

        Args:
            analysis_type: One of "funnel", "report", "retention", "segmentation".
            analysis_id: The ID of the saved analysis in Bloomreach.
        """
        path = f"/data/v2/projects/{self._project_token}/analyses/{analysis_type}"
        return await self._request_csv(
            "POST", path, json={"analysis_id": analysis_id, "format": "csv"}
        )

    # ---- Customer API ----

    async def get_customer_attributes(
        self,
        customer_id: str,
        attributes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Fetch customer attributes of the specified types.

        Endpoint: POST /data/v2/projects/{project_token}/customers/attributes
        """
        path = f"/data/v2/projects/{self._project_token}/customers/attributes"
        return await self._request(
            "POST",
            path,
            json={
                "customer_ids": {"registered": customer_id},
                "attributes": attributes,
            },
        )

    async def export_customer(self, customer_id: str) -> dict[str, Any]:
        """Export all data stored for a customer.

        Endpoint: POST /data/v2/projects/{project_token}/customers/export-one
        """
        path = f"/data/v2/projects/{self._project_token}/customers/export-one"
        return await self._request("POST", path, json={"customer_ids": {"registered": customer_id}})

    # ---- Catalogs API ----

    async def list_catalogs(self) -> list[dict[str, Any]]:
        """List all catalogs for the project.

        Endpoint: GET /data/v2/projects/{project_token}/catalogs
        """
        path = f"/data/v2/projects/{self._project_token}/catalogs"
        data = await self._request("GET", path)
        return data.get("data") or data.get("catalogs") or (data if isinstance(data, list) else [])

    # ---- Consent API ----

    async def list_consent_categories(self) -> list[dict[str, Any]]:
        """List all consent categories for the project.

        Endpoint: GET /data/v2/projects/{project_token}/consent/categories
        """
        path = f"/data/v2/projects/{self._project_token}/consent/categories"
        data = await self._request("GET", path)
        return (
            data.get("data") or data.get("categories") or (data if isinstance(data, list) else [])
        )

    async def get_customer_consents(self, customer_id: str) -> dict[str, Any]:
        """Fetch consent status for a customer.

        Endpoint: POST /data/v2/projects/{project_token}/customers/consents
        """
        path = f"/data/v2/projects/{self._project_token}/customers/consents"
        return await self._request("POST", path, json={"customer_ids": {"registered": customer_id}})

    async def anonymize_customer(self, customer_id: str) -> dict[str, Any]:
        """Anonymize a customer by removing all PII properties.

        Endpoint: POST /data/v2/projects/{project_token}/customers/anonymize

        WARNING: Removes all properties marked as Private (PII) in Bloomreach
        Data Manager. This action is irreversible.
        """
        path = f"/data/v2/projects/{self._project_token}/customers/anonymize"
        return await self._request("POST", path, json={"customer_ids": {"registered": customer_id}})
