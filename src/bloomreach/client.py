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
        self._base_url: str = os.environ["BLOOMREACH_BASE_URL"].rstrip("/")
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

    # ---- Scenarios / Campaigns ----

    async def list_scenarios(self) -> list[dict[str, Any]]:
        """Fetch all scenarios (campaigns) from the Engagement API.

        Endpoint: GET /track/v2/projects/{project_token}/campaigns

        Each item includes campaign metadata such as name, status, targeting
        segments, and audience size as provided by the Bloomreach API.
        """
        path = f"/track/v2/projects/{self._project_token}/campaigns"
        data = await self._request("GET", path)
        # Bloomreach wraps results; key may vary across API versions
        return (
            data.get("data")
            or data.get("campaigns")
            or data.get("results")
            or (data if isinstance(data, list) else [])
        )

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
