# YouTube Content Automation — Claude Code Guide

This is a local AI-powered YouTube content management system. Claude Code acts as the AI brain; the MCP server handles all data operations (Google Sheets, Docs, Drive, web research).

## Architecture

```
You (conversation) → Claude Code (AI reasoning) → MCP Tools (data layer) → Google APIs
```

Claude **reads, synthesizes, and writes content**. The MCP tools **fetch data, save documents, and update the sheet**.

## MCP Server

The MCP server is at `mcp/server.py`. It must be running and connected to Claude Code.

The MCP server is configured in `.mcp.json` (project root). Claude Code auto-discovers it when you open this directory. The config uses the project's `.venv` Python interpreter.

If you need to register it manually:
```bash
claude mcp add youtube-content /Users/abdul/youtube-mcp/.venv/bin/python -- -m mcpserver.server
```

## Multi-Channel Support

Each channel has its own Google Spreadsheet and Drive folder. A `config/channels.json` file tracks all channels and which one is active. All content tools accept an optional `channel` param — if omitted, the active channel is used.

### Adding a second channel
1. Call `add_channel(name="real_estate", display_name="Real Estate Channel", sheet_id="...", drive_folder_id="...")`
2. Call `ensure_setup(channel="real_estate")` to create the tab + Drive folders
3. Call `set_active_channel("real_estate")` to switch, or pass `channel="real_estate"` per tool call

### Listing channels
- Call `list_channels()` — shows all channels and which is active

### Cross-channel example
- `get_stats()` → stats for active channel
- `get_stats(channel="finance")` → stats for a specific channel

## Workflow Patterns

### "Research 5 new ideas about US Taxes"
1. Call `get_stats()` and `list_videos()` to understand what already exists
2. Call `find_duplicates(topic)` for each candidate before adding
3. Call `build_research_brief(topic)` to gather web/news/Reddit data
4. Synthesize the research using the `research_prompt` field in the brief
5. Call `save_research_doc(topic, content, row)` to save and update sheet

### "Write a script for row 14"
1. Call `build_script_context(row=14)` — loads research doc + script prompt
2. Write the script using the research content and the script prompt instructions
3. Call `save_script_doc(topic, content, row=14)` to save and update sheet

### "Generate visuals for row 14"
1. Call `build_visual_context(row=14)` — loads script + visuals prompt
2. Generate scene-by-scene descriptions following the visuals prompt
3. Call `save_visuals_doc(topic, content, row=14)` to save

### "What are we publishing next week?"
1. Call `get_schedule(weeks=2)` — reads directly from Google Sheets

### "What needs a script?"
1. Call `list_pending_scripts()` — returns Research Complete videos

### "Add this topic: Property Tax Appeals"
1. Call `find_duplicates("Property Tax Appeals")` first
2. If no duplicates, call `add_video(topic, category, priority)`

## Available MCP Tools

### Channel Management
| Tool | Purpose |
|------|---------|
| `list_channels` | List all channels + which is active |
| `add_channel` | Register a new channel (sheet_id + drive_folder_id) |
| `set_active_channel` | Switch the default channel |
| `update_channel` | Edit a channel's config fields |
| `remove_channel` | Delete a channel from the registry |

### Content Tools (all accept optional `channel` param)
| Tool | Purpose |
|------|---------|
| `list_videos` | List sheet rows with optional status/category filter |
| `get_video` | Get a single video by row or ID |
| `add_video` | Add new topic (after duplicate check) |
| `update_video` | Update any field in a row |
| `find_duplicates` | Fuzzy-match check for existing topics |
| `get_schedule` | Publishing schedule for next N weeks |
| `list_pending_scripts` | Research Complete videos needing scripts |
| `get_workflow_summary` | Full pipeline snapshot |
| `get_stats` | Counts by status |
| `web_search` | Search the web (Brave API or DDG fallback) |
| `fetch_url` | Extract text from a webpage |
| `search_reddit` | Reddit post search |
| `search_news` | Google News RSS search |
| `build_research_brief` | Gather all raw research data for a topic |
| `save_research_doc` | Save research doc to Drive, update sheet |
| `build_script_context` | Load research + script prompt for a video |
| `save_script_doc` | Save script to Drive, update sheet |
| `build_visual_context` | Load script + visuals prompt for a video |
| `save_visuals_doc` | Save visuals doc to Drive |
| `create_google_doc` | Create any Google Doc in Drive |
| `get_prompt` | Load a prompt template by name |
| `list_prompts` | List all available prompts |
| `list_drive_files` | List files in a Drive folder |
| `ensure_setup` | Initialize sheet tab + Drive folders for a channel |
| `get_category_performance` | Analytics by category |
| `get_series_candidates` | Find topics that could be a series |

## Prompt Templates

All prompts are in `prompts/` as Markdown files. Edit them without changing any code.

- `research.md` — Research document structure and guidelines
- `script.md` — Script framework and writing style
- `visuals.md` — Scene-by-scene visual direction format
- `thumbnail.md` — Thumbnail concept generation
- `title.md` — Title generation with SEO guidance
- `description.md` — YouTube description writing

## Google Sheet Structure

Each channel has its own Google Spreadsheet. The tab name is configured per channel (default: `Videos`).
Columns: ID, Topic, Category, Status, Priority, Research Score, Research Doc, Script Doc, Thumbnail, Publish Date, Created At, Updated At, Video URL, Notes

Status flow: Idea → Researching → Research Complete → Script Writing → Script Complete → Thumbnail Ready → Scheduled → Published → Archived

## Setup (First Time)

```bash
cd /Users/abdul/youtube-mcp
pip install -r requirements.txt
cp .env.example .env
# Fill in .env with your Google credentials and Sheet ID
python -m commands.cli auth client_secrets.json   # one-time OAuth
python -m commands.cli setup                       # creates sheet headers + Drive folders
```

## CLI Commands

```bash
content setup              # initialize sheet and Drive
content list               # list all videos
content list --status "Research Complete"
content schedule           # show publishing calendar
content pending            # show pipeline summary
content stats              # counts by status
content research --topic "Property Tax"
content script --row 14
content visuals --row 14
```
