# fastmcp-bloomreach

A [FastMCP](https://gofastmcp.com) server that exposes the [Bloomreach Engagement API](https://documentation.bloomreach.com/engagement/reference/welcome) as MCP tools for use with Claude Desktop, Claude Code, and any MCP-compatible client.

## Tools

| Tool | Description |
|------|-------------|
| `list_scenarios` | List Bloomreach scenarios (campaigns), optionally filtered by audience type |
| `get_email_campaign_metrics` | Get open rate, click rate from delivered, and click rate from opened for an email campaign over the last N days |

## Installation

Requires [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/davidmuleropino/fastmcp-bloomreach.git
cd fastmcp-bloomreach
uv sync
cp .env.example .env
# Edit .env with your Bloomreach credentials
```

## Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
BLOOMREACH_BASE_URL=https://api.exponea.com
BLOOMREACH_PROJECT_TOKEN=your_project_token
BLOOMREACH_API_KEY_ID=your_api_key_id
BLOOMREACH_API_SECRET=your_api_secret
```

Credentials are found in **Project settings → Access management → API** in the Bloomreach dashboard.

## Usage

### stdio (Claude Desktop / Claude Code)

Add to your MCP client config:

```json
{
  "mcpServers": {
    "bloomreach": {
      "command": "uv",
      "args": ["--directory", "/path/to/fastmcp-bloomreach", "run", "bloomreach-mcp"],
      "env": {
        "BLOOMREACH_BASE_URL": "https://api.exponea.com",
        "BLOOMREACH_PROJECT_TOKEN": "...",
        "BLOOMREACH_API_KEY_ID": "...",
        "BLOOMREACH_API_SECRET": "..."
      }
    }
  }
}
```

### HTTP (Google Cloud Run or self-hosted)

Set `TRANSPORT=http` and optionally `BLOOMREACH_MCP_API_KEY` for Bearer token auth:

```bash
TRANSPORT=http PORT=8080 uv run bloomreach-mcp
```

MCP client config for HTTP:

```json
{
  "mcpServers": {
    "bloomreach": {
      "type": "http",
      "url": "https://your-service.run.app/mcp",
      "headers": {
        "Authorization": "Bearer your_mcp_api_key"
      }
    }
  }
}
```

### Docker

```bash
docker build -t fastmcp-bloomreach .
docker run -p 8080:8080 \
  -e BLOOMREACH_BASE_URL=https://api.exponea.com \
  -e BLOOMREACH_PROJECT_TOKEN=... \
  -e BLOOMREACH_API_KEY_ID=... \
  -e BLOOMREACH_API_SECRET=... \
  -e BLOOMREACH_MCP_API_KEY=... \
  fastmcp-bloomreach
```

## Development

```bash
# Install dev dependencies
uv sync

# Interactive MCP Inspector (http://127.0.0.1:6274)
fastmcp dev src/bloomreach/server.py

# Run tests
uv run pytest -v

# Lint
uv run ruff check .
uv run ruff format .
```

## Releases

This project uses [release-please](https://github.com/googleapis/release-please) for automated versioning. Use [Conventional Commits](https://www.conventionalcommits.org/) when merging to `main`:

- `feat:` → minor version bump
- `fix:` → patch version bump
- `chore:`, `docs:`, `refactor:` → no version bump
