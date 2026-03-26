# FastMCP — Bloomreach Engagement

A [FastMCP](https://gofastmcp.com) server that connects Claude (and any MCP-compatible AI) to the [Bloomreach Engagement API](https://documentation.bloomreach.com/engagement/reference/about) (formerly Exponea).

> **Scope:** Bloomreach **Engagement** only (`/track/v2`, `/data/v2`, `/email/v2`). Bloomreach Discovery (product search) is out of scope.

---

## Use Cases

### Email Campaign Analytics
Ask Claude natural language questions over your campaign data:
- *"Give me last 30 days open rate, click-to-delivered, and click-to-opened for all email campaigns"*
- *"Which campaigns had the highest click rate last month?"*
- *"How many paid-audience campaigns ran this week?"*

Powered by the Analysis API — run any saved report, funnel, retention, or segmentation directly from the conversation.

> **Note:** Bloomreach does not expose a REST API to list scenarios directly. Campaign data is retrieved via saved analyses. See [Known Limitations](#known-limitations).

### Campaign Analysis Registry
Manage which Bloomreach analyses are accessible to Claude:
- *"List all configured reports"*
- *"Add report ID 69725f8ce027af6777814609 — call it Email Campaign Performance"*
- *"Remove the old Q1 funnel from the config"*

### Customer Data & GDPR
- *"Export all data stored for customer john@example.com"*
- *"What properties does this customer have?"*
- *"What consents has this customer given?"*
- *"Anonymise customer jane@example.com"* ⚠️ irreversible — removes all PII

### Catalog & Consent Management
- *"List all product catalogs in the project"*
- *"List all consent categories defined in the project"*

---

## Requirements

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/)
- A Bloomreach Engagement project with API credentials

---

## Installation

```bash
git clone https://github.com/davidmuleropino/fastmcp-bloomreach.git
cd fastmcp-bloomreach
uv sync
cp .env.example .env
# Edit .env with your credentials
```

---

## Configuration

### 1. Environment variables

```env
# Bloomreach Engagement API
BLOOMREACH_BASE_URL=https://uk1-api.eng.bloomreach.com   # your regional API URL
BLOOMREACH_PROJECT_TOKEN=your_project_token
BLOOMREACH_API_KEY_ID=your_api_key_id
BLOOMREACH_API_SECRET=your_api_secret

# MCP server Bearer token (HTTP/Cloud Run mode only)
# Any secret string — users include this in their connector config
BLOOMREACH_MCP_API_KEY=your_mcp_api_key

# Transport: "stdio" (Claude Desktop / Claude Code) or "http" (Cloud Run)
TRANSPORT=stdio
```

Find credentials in Bloomreach under **Project Settings → Access Management → API**.

**Regional base URLs:**
| Region | URL |
|---|---|
| EU / UK1 | `https://uk1-api.eng.bloomreach.com` |
| Global | `https://api.exponea.com` |
| Custom instance | Check your browser URL when logged in |

### 2. Bloomreach API permissions

In your API group (**Project Settings → Access Management → API → [group]**), enable:

| Feature | Tab | Permission |
|---|---|---|
| Run analyses (reports, funnels, etc.) | GDPR | Export analyses |
| Customer properties | Customer | Get properties |
| Customer exports | GDPR | Export customers |
| Customer consents | Customer | Get consents |
| Anonymise customer | GDPR | Anonymize |
| List catalogs | Catalogs | Get catalog list |

### 3. Analysis ID registry

Bloomreach has no API endpoint to list saved analyses — you maintain a local registry that maps analysis IDs to human-readable names. Claude uses this registry to know which analyses to run.

#### Step 1 — Find the analysis ID in Bloomreach

Open any saved analysis (report, funnel, retention, or segmentation) in the Bloomreach UI and copy the hex ID from the URL:

```
https://<instance>/p/<project>/analytics/reports/<analysis_id>
                                                  ^^^^^^^^^^^^^^^^^^^^^^^^
```

Example: `https://app.bloomreach.com/p/abc/analytics/reports/69725f8ce027af6777814609`
→ ID is `69725f8ce027af6777814609`

#### Step 2 — Register it (choose one method)

**Option A: via Claude (recommended — works locally and in Cloud Run)**

Just ask Claude to add it:
```
Add report ID 69725f8ce027af6777814609 — call it "Email Campaign Performance"
```

Claude calls `upsert_analysis` internally. You can also do it explicitly:
```
Use upsert_analysis to add a report with id=69725f8ce027af6777814609 and name="Email Campaign Performance"
```

To register a funnel, retention, or segmentation, specify the type:
```
Add funnel ID abc123def456 — call it "Checkout Funnel"
Add retention ID xyz789 — call it "30-day Retention"
```

**Option B: edit `analyses.json` directly (local only)**

```bash
cp analyses.example.json analyses.json
```

```json
{
  "reports": {
    "69725f8ce027af6777814609": "Email Campaign Performance",
    "b3c1f7a2e8d540f9a6127834": "Weekly Newsletter Stats"
  },
  "funnels": {
    "abc123def456abc123def456": "Checkout Funnel"
  },
  "retentions": {},
  "segmentations": {}
}
```

#### Step 3 — Verify the registry via MCP resources

The registry is exposed as MCP resources. Ask Claude to read them:
```
Read the bloomreach://analyses/reports resource
```

Or list everything registered:
```
List all configured analyses
```

Claude calls `list_analyses` and returns all registered IDs and names grouped by type.

#### Step 4 — Run an analysis

Once registered, Claude can run any analysis by name:
```
Run the "Email Campaign Performance" report
Get me the "Checkout Funnel" results
Show me the "30-day Retention" analysis
```

#### Managing the registry

| Ask Claude to... | Tool used |
|---|---|
| `List all configured reports` | `list_analyses` |
| `Add report ID abc123 — call it "Q1 Stats"` | `upsert_analysis` |
| `Rename the "Old Report" to "New Name"` | `upsert_analysis` |
| `Remove the "Q1 Stats" report` | `delete_analysis` |

#### Cloud Run persistence

In Cloud Run, the filesystem is read-only — registry changes made via `upsert_analysis` / `delete_analysis` are in-memory only and lost on redeploy. Each tool response includes the **full updated JSON** — use it to set `BLOOMREACH_ANALYSES_JSON` on your next deploy:

```bash
# Redeploy with updated registry
gcloud run services update bloomreach-engagement-mcp \
  --region us-central1 \
  --set-env-vars 'BLOOMREACH_ANALYSES_JSON={"reports":{"69725f8ce027af6777814609":"Email Campaign Performance"},"funnels":{},"retentions":{},"segmentations":{}}' \
  --project growth-mcp-servers
```

---

## Adding as a Custom Connector in Claude

### Claude Desktop

Edit `claude_desktop_config.json`:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "bloomreach": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/fastmcp-bloomreach",
        "run",
        "bloomreach-mcp"
      ],
      "env": {
        "BLOOMREACH_BASE_URL": "https://uk1-api.eng.bloomreach.com",
        "BLOOMREACH_PROJECT_TOKEN": "your_project_token",
        "BLOOMREACH_API_KEY_ID": "your_api_key_id",
        "BLOOMREACH_API_SECRET": "your_api_secret"
      }
    }
  }
}
```

### Claude Code (CLI)

```bash
claude mcp add bloomreach \
  --command "uv" \
  --args "--directory /absolute/path/to/fastmcp-bloomreach run bloomreach-mcp" \
  --env BLOOMREACH_BASE_URL=https://uk1-api.eng.bloomreach.com \
  --env BLOOMREACH_PROJECT_TOKEN=your_project_token \
  --env BLOOMREACH_API_KEY_ID=your_api_key_id \
  --env BLOOMREACH_API_SECRET=your_api_secret
```

Or add to `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "bloomreach": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/fastmcp-bloomreach",
        "run",
        "bloomreach-mcp"
      ],
      "env": {
        "BLOOMREACH_BASE_URL": "https://uk1-api.eng.bloomreach.com",
        "BLOOMREACH_PROJECT_TOKEN": "your_project_token",
        "BLOOMREACH_API_KEY_ID": "your_api_key_id",
        "BLOOMREACH_API_SECRET": "your_api_secret"
      }
    }
  }
}
```

### Cloud Run (Claude.ai custom connector)

The server is hosted on Google Cloud Run. Add it as a custom connector in Claude.ai using `mcp-remote`:

1. Go to **Claude.ai → Settings → Integrations → Add custom connector**
2. Use this config:

```json
{
  "mcpServers": {
    "bloomreach-engagement": {
      "command": "npx",
      "args": [
        "mcp-remote@latest",
        "https://bloomreach-engagement-mcp-457192737792.us-central1.run.app/mcp",
        "--header",
        "Authorization: Bearer YOUR_API_KEY"
      ]
    }
  }
}
```

Replace `YOUR_API_KEY` with the `BLOOMREACH_MCP_API_KEY` value stored in Keeper. This is a static token — set it once and it never expires.

For cloud persistence of the analyses registry, set the env var on deploy:
```env
BLOOMREACH_ANALYSES_JSON={"reports":{"69725f8ce027af6777814609":"Email Campaign Performance"},"funnels":{},"retentions":{},"segmentations":{}}
```

> In HTTP/cloud mode, analyses registry changes made via `upsert_analysis` / `delete_analysis` are written to file if available, or in-memory only. Each tool returns the full updated JSON — paste it into `BLOOMREACH_ANALYSES_JSON` on your next deploy to persist changes.

---

## Deploying to Google Cloud Run

### GCP one-time setup

```bash
# Set your GCP project
export PROJECT_ID=growth-mcp-servers
gcloud config set project $PROJECT_ID

# Create secrets in Secret Manager (run each line separately to avoid name corruption)
echo -n "$BLOOMREACH_PROJECT_TOKEN" | gcloud secrets create bloomreach-project-token --data-file=-
echo -n "$BLOOMREACH_API_KEY_ID"    | gcloud secrets create bloomreach-api-key-id    --data-file=-
echo -n "$BLOOMREACH_API_SECRET"    | gcloud secrets create bloomreach-api-secret    --data-file=-
echo -n "$BLOOMREACH_MCP_API_KEY"   | gcloud secrets create bloomreach-mcp-api-key   --data-file=-

# Create Artifact Registry repository
gcloud artifacts repositories create bloomreach-engagement \
  --repository-format=docker \
  --location=us-central1

# First deploy — pass COMMIT_SHA explicitly ($COMMIT_SHA is only set automatically by CI triggers)
gcloud builds submit . --substitutions=COMMIT_SHA=$(git rev-parse HEAD)
```

After the first deploy, set authentication manually in the Cloud Run console:
**Cloud Run → bloomreach-engagement-mcp → Security → Authentication → set as required**

> The org policy (`constraints/iam.allowedPolicyMemberDomains`) prevents setting authentication via the CLI — it must be done in the console.

### Subsequent deploys

Push to `main` — Cloud Build triggers automatically via `cloudbuild.yaml`.

### Updating secrets

```bash
echo -n "$NEW_VALUE" | gcloud secrets versions add bloomreach-project-token --data-file=-
```

Then redeploy (or Cloud Run will pick up `:latest` on next cold start).

---

## Available Tools

| Tool | Description |
|---|---|
| `get_report` | Run a saved report analysis |
| `get_funnel` | Run a saved funnel analysis |
| `get_retention` | Run a saved retention analysis |
| `get_segmentation` | Run a saved segmentation analysis |
| `list_analyses` | List configured analysis IDs and names (by type or all) |
| `upsert_analysis` | Add or update an analysis in the registry |
| `delete_analysis` | Remove an analysis from the registry |
| `get_customer_properties` | Get all properties for a customer |
| `get_customer_attributes` | Get specific attributes for a customer |
| `get_customer_expressions` | Get expression results for a customer |
| `get_customer_predictions` | Get prediction scores for a customer |
| `get_customer_consents` | Get consent status for a customer |
| `export_customer` | Export all data stored for a customer |
| `anonymize_customer` | Remove all PII for a customer ⚠️ irreversible |
| `list_consent_categories` | List all consent categories in the project |
| `list_catalogs` | List all product catalogs in the project |

## Available Resources

| URI | Description |
|---|---|
| `bloomreach://analyses/reports` | Configured report IDs and names |
| `bloomreach://analyses/funnels` | Configured funnel IDs and names |
| `bloomreach://analyses/retentions` | Configured retention IDs and names |
| `bloomreach://analyses/segmentations` | Configured segmentation IDs and names |

---

## Development

```bash
# Interactive MCP Inspector (opens http://127.0.0.1:6274)
fastmcp dev src/bloomreach/server.py

# Run in stdio mode directly
uv run bloomreach-mcp

# Run in HTTP mode
TRANSPORT=http uv run bloomreach-mcp

# Run tests
uv run pytest -v

# Lint / format
uv run ruff check .
uv run ruff format .
```

---

## Known Limitations

- **No scenario/campaign listing:** Bloomreach Engagement does not expose a REST API to list or query scenarios. Campaign data is only accessible via saved analyses (reports). As a workaround, add a custom campaign event property (e.g. `audience_type = "paid"`) to each scenario in the Bloomreach UI — the property will appear in report results and can be used for filtering.
- **Analysis results cached:** Bloomreach may cache analysis results for up to 10 minutes.
- **No automatic analysis discovery:** Analysis IDs must be registered manually in `analyses.json` or via the `upsert_analysis` tool.
- **Custom instance URLs:** The API base URL varies by region — update `BLOOMREACH_BASE_URL` to match your instance.

---

## Releases

Uses [release-please](https://github.com/googleapis/release-please) for automated versioning. Follow [Conventional Commits](https://www.conventionalcommits.org/) when merging to `main`:

| Prefix | Effect |
|---|---|
| `feat:` | minor version bump |
| `fix:` | patch version bump |
| `chore:`, `docs:`, `refactor:` | no version bump |
