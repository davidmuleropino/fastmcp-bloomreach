"""FastMCP Bloomreach server — stdio and HTTP transports."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from dotenv import load_dotenv
from fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

load_dotenv()

from bloomreach.client import BloomreachClient  # noqa: E402
from bloomreach.resources.analyses import register_analyses_resources  # noqa: E402
from bloomreach.tools.analyses_config import register_analyses_config_tools  # noqa: E402
from bloomreach.tools.analytics import register_analytics_tools  # noqa: E402
from bloomreach.tools.catalogs import register_catalogs_tools  # noqa: E402
from bloomreach.tools.consent import register_consent_tools  # noqa: E402
from bloomreach.tools.customer import register_customer_tools  # noqa: E402

logger = logging.getLogger(__name__)

_client: BloomreachClient | None = None

_REQUIRED_ENV_VARS = [
    "BLOOMREACH_PROJECT_TOKEN",
    "BLOOMREACH_API_KEY_ID",
    "BLOOMREACH_API_SECRET",
]


def get_client() -> BloomreachClient:
    if _client is None:
        raise RuntimeError("Bloomreach client not initialised")
    return _client


@asynccontextmanager
async def lifespan(app: FastMCP) -> AsyncIterator[None]:
    global _client

    missing = [v for v in _REQUIRED_ENV_VARS if not os.environ.get(v)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    _client = BloomreachClient()
    await _client.start()
    logger.info("Bloomreach client started")
    try:
        yield
    finally:
        await _client.stop()
        _client = None
        logger.info("Bloomreach client stopped")


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Validates Bearer token for all requests except /health."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)
        api_key = os.environ.get("BLOOMREACH_MCP_API_KEY")
        if api_key:
            auth = request.headers.get("Authorization", "")
            if auth != f"Bearer {api_key}":
                return JSONResponse({"error": "Unauthorized"}, status_code=401)
        return await call_next(request)


mcp = FastMCP(name="Bloomreach", lifespan=lifespan)

register_analytics_tools(mcp, get_client)
register_catalogs_tools(mcp, get_client)
register_customer_tools(mcp, get_client)
register_consent_tools(mcp, get_client)
register_analyses_resources(mcp)
register_analyses_config_tools(mcp)


@mcp.custom_route("/health", methods=["GET"])
async def health(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


# Starlette app used in HTTP transport mode
app = mcp.http_app(path="/mcp", stateless_http=True)
app.add_middleware(APIKeyMiddleware)


def main() -> None:
    transport = os.environ.get("TRANSPORT", "stdio").lower()
    if transport == "http":
        import uvicorn

        port = int(os.environ.get("PORT", "8080"))
        uvicorn.run("bloomreach.server:app", host="0.0.0.0", port=port, log_level="info")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
