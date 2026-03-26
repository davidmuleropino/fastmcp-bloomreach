# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Scope:** This MCP server covers the Bloomreach **Engagement** API (formerly Exponea) only — `https://api.exponea.com`. The Bloomreach Discovery API (product search, recommendations) is out of scope.

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

In HTTP mode (Cloud Run), authentication uses a static Bearer token via `APIKeyMiddleware` (`BLOOMREACH_MCP_API_KEY`). `/health` is exempt. GCP IAM (`--no-allow-unauthenticated`) is also set at the Cloud Run level for defence-in-depth.

## Project Structure

```
src/bloomreach/
├── server.py              FastMCP app, lifespan, transport switch, main()
├── client.py              Async httpx wrapper for the Bloomreach Engagement API
├── analyses_config.py     Load/save analyses registry (env var or file)
├── resources/
│   └── analyses.py        MCP resources: bloomreach://analyses/{type}
└── tools/
    ├── analytics.py       Email metrics + analysis tools (funnel, report, retention, segmentation)
    ├── catalogs.py        list_catalogs
    ├── customer.py        Customer data tools
    ├── consent.py         Consent + anonymize tools
    ├── analyses_config.py list/upsert/delete analyses registry
    └── scenarios.py       (placeholder)
tests/
  test_server.py           Startup validation + HTTP endpoint tests
  test_tools.py            Client method tests (respx mocks)
cloudbuild.yaml            Cloud Build → Artifact Registry → Cloud Run pipeline
Dockerfile                 Python 3.13-slim, uv, TRANSPORT=http
.env                       Gitignored — copy from .env.example
.env.example
.claude/docs/              Gitignored internal docs
  troubleshooting.md       Known Cloud Run issues and fixes
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

## Google Cloud Deployment

- **Pipeline:** `cloudbuild.yaml` — build → push to Artifact Registry → deploy to Cloud Run
- **Service:** `bloomreach-engagement-mcp` in `us-central1`
- **Secrets (GCP Secret Manager):** `bloomreach-project-token`, `bloomreach-api-key-id`, `bloomreach-api-secret`, `bloomreach-mcp-api-key`
- **Plain env var:** `BLOOMREACH_BASE_URL=https://uk1-api.eng.bloomreach.com` (set via `--set-env-vars`)
- **Auth:** GCP IAM (`--no-allow-unauthenticated`) — set manually via Cloud Run console (org policy blocks CLI)
- See `README.md` for first-deploy commands and `.claude/docs/troubleshooting.md` for known issues

## Conventional Commits

This repo uses [release-please](https://github.com/googleapis/release-please). Commit messages must follow Conventional Commits:
- `feat:` new tool or capability → minor bump
- `fix:` bug fix → patch bump
- `chore:` / `docs:` → no version bump
