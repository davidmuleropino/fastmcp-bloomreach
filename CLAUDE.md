# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Install dependencies
uv sync

# Interactive MCP Inspector (opens http://127.0.0.1:6274)
fastmcp dev src/bloomreach/server.py

# Run in stdio mode directly
uv run bloomreach-mcp

# Run in HTTP mode (port 8080)
TRANSPORT=http uv run bloomreach-mcp

# Run tests
uv run pytest -v

# Lint / format
uv run ruff check .
uv run ruff format .
```

## Transport Modes

Controlled by the `TRANSPORT` env var:

| Value | Mechanism | Use case |
|-------|-----------|----------|
| `stdio` (default) | `mcp.run()` | Claude Desktop, Claude Code, Cursor |
| `http` | uvicorn on `PORT` (default 8080) | Cloud Run, any HTTP host |

In HTTP mode, `APIKeyMiddleware` in `server.py` enforces `Authorization: Bearer <BLOOMREACH_MCP_API_KEY>` on all routes except `/health`.

## Project Structure

```
src/bloomreach/
├── server.py          FastMCP app, lifespan, middleware, transport switch, main()
├── client.py          Async httpx wrapper for the Bloomreach Engagement API
└── tools/
    ├── scenarios.py       list_scenarios tool
    └── email_metrics.py   get_email_campaign_metrics tool + EmailMetricsResult model
tests/
.env                   Gitignored — copy from .env.example
.env.example
.claude/docs/          Gitignored internal docs (API reference, architecture)
```

## Adding New Tools

1. Create `src/bloomreach/tools/<domain>.py` with a `register_<domain>_tools(mcp, get_client)` function
2. Add the corresponding client method(s) to `client.py`
3. Import and call `register_<domain>_tools(mcp, get_client)` in `server.py`

## Bloomreach API

- **Base URL**: `BLOOMREACH_BASE_URL` (default `https://api.exponea.com`)
- **Auth**: HTTP Basic Auth — `API_KEY_ID:API_SECRET` (no token refresh needed)
- **URL pattern**: `/track/v2/projects/{PROJECT_TOKEN}/{resource}`
- Analysis API endpoints return CSV; use `_request_csv()` + `_parse_csv_metrics()`
- See `.claude/docs/bloomreach-engagement-api.md` for endpoint details

## Conventional Commits

This repo uses [release-please](https://github.com/googleapis/release-please). Commit messages must follow Conventional Commits:
- `feat:` new tool or capability → minor bump
- `fix:` bug fix → patch bump
- `chore:` / `docs:` → no version bump
