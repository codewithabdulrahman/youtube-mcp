# YouTube Content Automation

A local AI-powered YouTube content management system. Claude Code acts as the AI brain; an MCP server handles all data operations against Google Sheets, Docs, Drive, and web research APIs.

```
You (conversation) → Claude Code (AI reasoning) → MCP Tools (data layer) → Google APIs
```

## Prerequisites

- Python 3.10+
- [Claude Code](https://claude.ai/code) CLI installed
- A Google Cloud project with the Sheets, Docs, and Drive APIs enabled
- A Google Sheet to use as your content database

## Installation

```bash
git clone <repo-url>
cd youtube-mcp

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
pip install -e .                   # installs the `content` CLI command
```

## Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/) and create or select a project.
2. Enable these APIs: **Google Sheets API**, **Google Docs API**, **Google Drive API**.
3. Under **APIs & Services → Credentials**, create an **OAuth 2.0 Client ID** (Desktop app type).
4. Download the JSON file and save it as `client_secret.json` in the project root.

## Environment Configuration

```bash
cp .env.example .env
```

Open `.env` and fill in:

| Variable | Where to find it |
|---|---|
| `GOOGLE_CLIENT_ID` | OAuth client ID from Cloud Console |
| `GOOGLE_CLIENT_SECRET` | OAuth client secret from Cloud Console |
| `GOOGLE_REFRESH_TOKEN` | Generated during the auth step below |
| `GOOGLE_SHEET_ID` | The ID in your Sheet URL: `spreadsheets/d/<ID>/edit` |
| `GOOGLE_DRIVE_FOLDER` | The ID in your Drive folder URL: `drive/folders/<ID>` |
| `BRAVE_SEARCH_API_KEY` | Optional — [Brave Search API](https://brave.com/search/api/) for web research |
| `REDDIT_CLIENT_ID` | Optional — Reddit API app credentials for Reddit research |
| `REDDIT_CLIENT_SECRET` | Optional — Reddit API app credentials |

## One-Time Google Auth

Run the OAuth flow once to generate a refresh token:

```bash
python -m commands.cli auth client_secret.json
```

A browser window will open asking you to sign in. After approval, the terminal prints your `GOOGLE_REFRESH_TOKEN` — copy it into `.env`. The token is also cached locally in `config/token.json` and auto-refreshed on subsequent runs.

## Initial Sheet & Drive Setup

```bash
python -m commands.cli setup
```

This creates the column headers in your Google Sheet and the Drive subfolder structure (Research, Scripts, Thumbnails, Assets, Published) under your `GOOGLE_DRIVE_FOLDER`.

## Registering the MCP Server with Claude Code

Open `.mcp.json` (project root) and update the paths to match your environment:

```json
{
  "mcpServers": {
    "youtube-content": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["-m", "mcpserver.server"],
      "cwd": "/absolute/path/to/youtube-mcp",
      "env": {
        "PYTHONPATH": "/absolute/path/to/youtube-mcp"
      }
    }
  }
}
```

Claude Code auto-discovers `.mcp.json` when you open the project directory. Alternatively register it manually:

```bash
claude mcp add youtube-content /path/to/.venv/bin/python -- -m mcpserver.server
```

Restart Claude Code and confirm the server appears under `/mcp`.

## Using the System

Once the MCP server is connected, talk to Claude Code naturally:

| What you say | What happens |
|---|---|
| "Research 5 new ideas about US Taxes" | Claude checks for duplicates, gathers web/news/Reddit data, synthesizes a research doc, and saves it to Drive |
| "Write a script for row 14" | Claude loads the research doc and script prompt, writes the script, saves it to Drive, and updates the sheet |
| "Generate visuals for row 14" | Claude loads the script, writes scene-by-scene visual directions, saves to Drive |
| "What needs a script?" | Returns all videos at Research Complete status |
| "What are we publishing next week?" | Reads the sheet and shows the publishing calendar |
| "Add this topic: Property Tax Appeals" | Checks for duplicates, then adds the row |

## CLI Commands

You can also drive the system from the terminal without Claude Code:

```bash
content setup                              # initialize sheet and Drive
content list                               # list all videos
content list --status "Research Complete"  # filter by status
content schedule                           # show publishing calendar
content pending                            # pipeline snapshot
content stats                              # counts by status
content research --topic "Property Tax"    # build a research brief
content script --row 14                    # load script context
content visuals --row 14                   # load visual context
```

## Customizing Prompts

All AI prompt templates are plain Markdown files in `prompts/`. Edit them to change tone, structure, or guidelines without touching any code:

| File | Purpose |
|---|---|
| `research.md` | Research document structure |
| `script.md` | Script framework and writing style |
| `visuals.md` | Scene-by-scene visual direction format |
| `thumbnail.md` | Thumbnail concept generation |
| `title.md` | Title generation with SEO guidance |
| `description.md` | YouTube description writing |

## Google Sheet Schema

Sheet name: `Videos`

| Column | Description |
|---|---|
| ID | Auto-assigned row ID |
| Topic | Video title / topic |
| Category | Content category |
| Status | Workflow state (see below) |
| Priority | High / Medium / Low |
| Research Score | 0–100 quality score |
| Research Doc | Drive link to research document |
| Script Doc | Drive link to script document |
| Thumbnail | Thumbnail concept notes |
| Publish Date | Scheduled publish date |
| Created At / Updated At | Timestamps |
| Video URL | Live YouTube URL after publishing |
| Notes | Freeform notes |

**Status flow:**
`Idea → Researching → Research Complete → Script Writing → Script Complete → Thumbnail Ready → Scheduled → Published → Archived`

## Project Structure

```
youtube-mcp/
├── mcpserver/        # MCP server (tools Claude Code calls)
├── services/         # Google API clients (Sheets, Docs, Drive, Auth)
├── agents/           # Agent logic (research, script, visual, analytics)
├── commands/         # CLI entry points
├── config/           # Settings and cached OAuth token
├── prompts/          # Editable AI prompt templates
├── logs/             # Rotating daily log files
├── cache/            # Research cache (TTL configurable in .env)
├── .mcp.json         # MCP server config for Claude Code
├── .env.example      # Environment variable template
└── requirements.txt  # Python dependencies
```

## Troubleshooting

**MCP server not connecting** — check that the `command` path in `.mcp.json` points to the Python binary inside your `.venv`, and that `cwd` is the absolute project path.

**Google auth errors** — delete `config/token.json` and re-run `python -m commands.cli auth client_secret.json`.

**"No valid Google credentials"** — make sure `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REFRESH_TOKEN` are all set in `.env`.

**Web search returning no results** — the system falls back to DuckDuckGo when `BRAVE_SEARCH_API_KEY` is unset, but Brave gives better results.
