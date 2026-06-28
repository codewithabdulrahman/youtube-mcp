"""
YouTube MCP Server — exposes all tools to Claude Code via the MCP protocol.

Run this server and add it to Claude Code's MCP configuration.
Claude Code uses these tools to read/write Google Workspace and fetch research data.
The AI reasoning (synthesis, writing, analysis) is always performed by Claude itself.
"""
import sys
import json
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from agents import research_agent, script_agent, visual_agent, publishing_agent, analytics_agent
from services import sheets_service, docs_service, drive_service, research_service, prompt_loader
from services import channel_service
from services.logger import get_logger

logger = get_logger("mcp_server")

app = Server("youtube-content-manager")

# ─── Shared channel param schema fragment ──────────────────────────────────────

_CHANNEL_PARAM = {
    "channel": {
        "type": "string",
        "description": "Channel name to use (defaults to active channel). Run list_channels to see available channels.",
    }
}


# ─── Helper ────────────────────────────────────────────────────────────────────

def _ok(data) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=json.dumps(data, indent=2, default=str))]


def _err(msg: str) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=json.dumps({"error": msg}, indent=2))]


# ─── Tool Definitions ──────────────────────────────────────────────────────────

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        # ── Channel management ──────────────────────────────────────────────
        types.Tool(
            name="list_channels",
            description="List all registered channels. Shows which one is currently active.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="add_channel",
            description=(
                "Register a new YouTube channel. Each channel needs its own Google Spreadsheet ID "
                "and Drive folder ID. The sheet_tab defaults to 'Videos'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Short slug, e.g. 'finance' or 'real_estate'"},
                    "display_name": {"type": "string", "description": "Human-readable name, e.g. 'Finance Channel'"},
                    "sheet_id": {"type": "string", "description": "Google Spreadsheet ID for this channel"},
                    "drive_folder_id": {"type": "string", "description": "Google Drive root folder ID for this channel"},
                    "sheet_tab": {"type": "string", "description": "Tab name in the spreadsheet (default: 'Videos')", "default": "Videos"},
                    "youtube_channel_id": {"type": "string", "description": "YouTube channel ID (UCxxxxxxxx) — required for Analytics API on brand accounts"},
                },
                "required": ["name", "display_name", "sheet_id", "drive_folder_id"],
            },
        ),
        types.Tool(
            name="set_active_channel",
            description="Switch the active channel. Future tool calls that omit the 'channel' param will use this channel.",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "description": "Channel name to make active"},
                },
                "required": ["channel"],
            },
        ),
        types.Tool(
            name="update_channel",
            description="Update config fields (display_name, sheet_id, sheet_tab, drive_folder_id, youtube_channel_id) for an existing channel.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Channel slug to update"},
                    "display_name": {"type": "string"},
                    "sheet_id": {"type": "string"},
                    "sheet_tab": {"type": "string"},
                    "drive_folder_id": {"type": "string"},
                    "youtube_channel_id": {"type": "string", "description": "YouTube channel ID (UCxxxxxxxx) — required for Analytics API on brand accounts"},
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="remove_channel",
            description="Remove a channel from the registry. Cannot remove the currently active channel.",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "description": "Channel name to remove"},
                },
                "required": ["channel"],
            },
        ),

        # ── Sheet tools ─────────────────────────────────────────────────────
        types.Tool(
            name="list_videos",
            description="List videos from the Google Sheet, optionally filtered by status or category.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter by status (e.g. 'Idea', 'Research Complete', 'Published')"},
                    "category": {"type": "string", "description": "Filter by category"},
                    "limit": {"type": "integer", "description": "Max rows to return (default 100)", "default": 100},
                    **_CHANNEL_PARAM,
                },
            },
        ),
        types.Tool(
            name="get_video",
            description="Get a single video by row number or ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "row": {"type": "integer", "description": "Sheet row number"},
                    "video_id": {"type": "string", "description": "Video ID (e.g. V0001)"},
                    **_CHANNEL_PARAM,
                },
            },
        ),
        types.Tool(
            name="add_video",
            description="Add a new video topic to the Google Sheet after checking for duplicates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Video topic or title idea"},
                    "category": {"type": "string", "description": "Content category (e.g. 'US Taxes', 'Real Estate')"},
                    "priority": {"type": "string", "description": "Priority: High, Medium, Low", "default": "Medium"},
                    "notes": {"type": "string", "description": "Optional notes"},
                    **_CHANNEL_PARAM,
                },
                "required": ["topic"],
            },
        ),
        types.Tool(
            name="update_video",
            description="Update fields of a video row in the Google Sheet.",
            inputSchema={
                "type": "object",
                "properties": {
                    "row": {"type": "integer", "description": "Sheet row number"},
                    "status": {"type": "string"},
                    "category": {"type": "string"},
                    "priority": {"type": "string"},
                    "research_score": {"type": "string"},
                    "research_doc": {"type": "string"},
                    "script_doc": {"type": "string"},
                    "thumbnail": {"type": "string"},
                    "publish_date": {"type": "string"},
                    "video_id": {"type": "string", "description": "YouTube video ID (11-char, e.g. dQw4w9WgXcQ)"},
                    "notes": {"type": "string"},
                    "views": {"type": "string"},
                    "reach": {"type": "string", "description": "Unique viewers (estimated)"},
                    "retention_rate": {"type": "string", "description": "Average view percentage (0-100)"},
                    "performance_state": {"type": "string", "description": "Video health: Growing, Stable, Declining, or Dead"},
                    "comment_sentiment": {"type": "string", "description": "Overall comment tone: Mostly Positive, Mixed, or Mostly Negative"},
                    **_CHANNEL_PARAM,
                },
                "required": ["row"],
            },
        ),
        types.Tool(
            name="find_duplicates",
            description="Check if a topic already exists in the sheet using fuzzy matching.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Topic to check for duplicates"},
                    "threshold": {"type": "integer", "description": "Similarity threshold 0-100 (default 75)", "default": 75},
                    **_CHANNEL_PARAM,
                },
                "required": ["topic"],
            },
        ),
        types.Tool(
            name="get_schedule",
            description="Get the publishing schedule for the next N weeks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "weeks": {"type": "integer", "description": "Number of weeks ahead to look (default 4)", "default": 4},
                    **_CHANNEL_PARAM,
                },
            },
        ),
        types.Tool(
            name="list_pending_scripts",
            description="List videos that have research complete but no script yet.",
            inputSchema={
                "type": "object",
                "properties": {**_CHANNEL_PARAM},
            },
        ),
        types.Tool(
            name="get_workflow_summary",
            description="Get a full snapshot of the content pipeline: counts and lists by status.",
            inputSchema={
                "type": "object",
                "properties": {**_CHANNEL_PARAM},
            },
        ),
        types.Tool(
            name="get_stats",
            description="Get video counts by status.",
            inputSchema={
                "type": "object",
                "properties": {**_CHANNEL_PARAM},
            },
        ),
        types.Tool(
            name="apply_status_colors",
            description="Apply background colors to all status cells in the sheet. Run this once to color-code existing rows; new rows are colored automatically going forward.",
            inputSchema={
                "type": "object",
                "properties": {**_CHANNEL_PARAM},
            },
        ),

        # ── Research tools ──────────────────────────────────────────────────
        types.Tool(
            name="web_search",
            description="Search the web for information on a topic. Returns titles, URLs, and descriptions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "num_results": {"type": "integer", "description": "Number of results (default 10)", "default": 10},
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="fetch_url",
            description="Fetch and extract text content from a webpage URL.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"},
                    "max_chars": {"type": "integer", "description": "Max characters to return (default 8000)", "default": 8000},
                },
                "required": ["url"],
            },
        ),
        types.Tool(
            name="search_reddit",
            description="Search Reddit for discussions on a topic.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "subreddit": {"type": "string", "description": "Specific subreddit to search (optional)"},
                    "limit": {"type": "integer", "description": "Number of results (default 10)", "default": 10},
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="search_news",
            description="Search for recent news articles on a topic.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "num_results": {"type": "integer", "description": "Number of results (default 5)", "default": 5},
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="build_research_brief",
            description="Gather all raw research data for a topic (web, news, Reddit). Returns structured data for Claude to synthesize into a research document.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Topic to research"},
                    "num_web": {"type": "integer", "description": "Web results to fetch", "default": 8},
                    "num_news": {"type": "integer", "description": "News articles to fetch", "default": 5},
                    "num_reddit": {"type": "integer", "description": "Reddit posts to fetch", "default": 5},
                    **_CHANNEL_PARAM,
                },
                "required": ["topic"],
            },
        ),
        types.Tool(
            name="save_research_doc",
            description="Save a completed research document to Google Drive and update the sheet.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Video topic"},
                    "content": {"type": "string", "description": "Full research document text"},
                    "row": {"type": "integer", "description": "Sheet row to update (optional)"},
                    **_CHANNEL_PARAM,
                },
                "required": ["topic", "content"],
            },
        ),
        types.Tool(
            name="build_script_context",
            description="Load research document and script prompt for a video. Returns everything Claude needs to write the script.",
            inputSchema={
                "type": "object",
                "properties": {
                    "row": {"type": "integer", "description": "Sheet row number"},
                    "video_id": {"type": "string", "description": "Video ID"},
                    **_CHANNEL_PARAM,
                },
            },
        ),
        types.Tool(
            name="save_script_doc",
            description="Save a completed script to Google Drive and update the sheet status to 'Script Complete'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Video topic"},
                    "content": {"type": "string", "description": "Full script text"},
                    "row": {"type": "integer", "description": "Sheet row to update"},
                    **_CHANNEL_PARAM,
                },
                "required": ["topic", "content", "row"],
            },
        ),
        types.Tool(
            name="build_visual_context",
            description="Load script content and visuals prompt for a video. Returns everything Claude needs to generate scene descriptions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "row": {"type": "integer", "description": "Sheet row number"},
                    "video_id": {"type": "string", "description": "Video ID"},
                    **_CHANNEL_PARAM,
                },
            },
        ),
        types.Tool(
            name="save_visuals_doc",
            description="Save visual scene descriptions as a Google Doc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Video topic"},
                    "content": {"type": "string", "description": "Visual scene descriptions text"},
                    "row": {"type": "integer", "description": "Sheet row number"},
                    **_CHANNEL_PARAM,
                },
                "required": ["topic", "content", "row"],
            },
        ),
        types.Tool(
            name="consolidate_visuals_into_scripts",
            description="For buildship & shorts: find all separate 'Visuals: ...' docs, merge them into their script docs with a clear heading, and delete the orphaned visuals docs.",
            inputSchema={
                "type": "object",
                "properties": {
                    **_CHANNEL_PARAM,
                    "status": {"type": "string", "description": "Filter by video status (e.g. 'Script Complete'). If omitted, all videos are checked."},
                },
            },
        ),
        types.Tool(
            name="cleanup_orphaned_visuals_docs",
            description="For buildship & shorts: delete orphaned 'Visuals: ...' docs from Drive (visuals now live in script docs). For other channels, does nothing.",
            inputSchema={
                "type": "object",
                "properties": {
                    **_CHANNEL_PARAM,
                },
            },
        ),

        types.Tool(
            name="fetch_video_comments",
            description=(
                "Fetch top comments for a published video so Claude can assess overall sentiment. "
                "Returns up to 50 comments sorted by relevance. "
                "After reading them, call update_video with comment_sentiment set to: "
                "'Mostly Positive', 'Mixed', or 'Mostly Negative'. "
                "Accepts a full YouTube URL or a bare 11-character video ID."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "video_url": {"type": "string", "description": "YouTube video URL or bare video ID (e.g. dQw4w9WgXcQ)"},
                    "max_results": {"type": "integer", "description": "Max comments to fetch (default 50)", "default": 50},
                },
                "required": ["video_url"],
            },
        ),

        # ── Document / Drive tools ──────────────────────────────────────────
        types.Tool(
            name="create_google_doc",
            description="Create a Google Doc with given title and content, saved to a Drive folder.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Document title"},
                    "content": {"type": "string", "description": "Document text content"},
                    "folder_type": {"type": "string", "description": "Drive folder: research, scripts, thumbnails, assets, published"},
                    **_CHANNEL_PARAM,
                },
                "required": ["title", "content"],
            },
        ),
        types.Tool(
            name="get_prompt",
            description="Load a prompt template by name. Checks for a channel-specific override in prompts/<channel>/ first, then falls back to the global default.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Prompt name (without .md extension): research, script, visuals, thumbnail, title, description"},
                    **_CHANNEL_PARAM,
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="list_prompts",
            description="List all available prompt templates, including any channel-specific overrides.",
            inputSchema={
                "type": "object",
                "properties": {**_CHANNEL_PARAM},
            },
        ),
        types.Tool(
            name="list_drive_files",
            description="List files in a Google Drive folder.",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_type": {"type": "string", "description": "Folder type: research, scripts, thumbnails, assets, published"},
                    "limit": {"type": "integer", "default": 20},
                    **_CHANNEL_PARAM,
                },
            },
        ),
        types.Tool(
            name="ensure_setup",
            description="Verify Google Sheet headers and Drive folder structure exist for the given channel. Run once on first use per channel.",
            inputSchema={
                "type": "object",
                "properties": {**_CHANNEL_PARAM},
            },
        ),
        types.Tool(
            name="sync_column_order",
            description=(
                "Reorder the Google Sheet columns to match the current SHEET_HEADERS definition in settings.py. "
                "Run this after changing the column order in code to keep the live sheet in sync. "
                "Preserves all existing data — no rows are lost."
            ),
            inputSchema={
                "type": "object",
                "properties": {**_CHANNEL_PARAM},
            },
        ),

        # ── Analytics tools ─────────────────────────────────────────────────
        types.Tool(
            name="get_category_performance",
            description="Analyze video distribution by category and status.",
            inputSchema={
                "type": "object",
                "properties": {**_CHANNEL_PARAM},
            },
        ),
        types.Tool(
            name="get_series_candidates",
            description="Identify groups of similar topics that could form a video series.",
            inputSchema={
                "type": "object",
                "properties": {**_CHANNEL_PARAM},
            },
        ),
        types.Tool(
            name="sync_youtube_stats",
            description=(
                "Fetch live YouTube metrics (views, likes, comments, watch time, CTR, impressions, "
                "avg view duration) for all Published videos and write them to the sheet. "
                "Reads the video ID from each row's Notes field (store the bare 11-char ID there, e.g. dQw4w9WgXcQ). "
                "Requires YouTube OAuth scopes — re-run auth if this fails."
            ),
            inputSchema={
                "type": "object",
                "properties": {**_CHANNEL_PARAM},
            },
        ),
        types.Tool(
            name="get_performance_insights",
            description=(
                "Analyze synced YouTube metrics to surface per-category performance, top/bottom "
                "performers by CTR, and weak content categories. Run sync_youtube_stats first to "
                "ensure data is fresh."
            ),
            inputSchema={
                "type": "object",
                "properties": {**_CHANNEL_PARAM},
            },
        ),
    ]


# ─── Tool Handlers ─────────────────────────────────────────────────────────────

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        ch = arguments.get("channel")  # None → active channel

        # Channel management
        if name == "list_channels":
            return _ok(channel_service.list_channels())

        if name == "add_channel":
            return _ok(channel_service.add_channel(
                name=arguments["name"],
                display_name=arguments["display_name"],
                sheet_id=arguments["sheet_id"],
                drive_folder_id=arguments["drive_folder_id"],
                sheet_tab=arguments.get("sheet_tab", "Videos"),
                youtube_channel_id=arguments.get("youtube_channel_id", ""),
            ))

        if name == "set_active_channel":
            return _ok(channel_service.set_active_channel(arguments["channel"]))

        if name == "update_channel":
            name_arg = arguments.pop("name")
            arguments.pop("channel", None)
            return _ok(channel_service.update_channel(name_arg, **arguments))

        if name == "remove_channel":
            return _ok(channel_service.remove_channel(arguments["channel"]))

        # Google Sheets tools
        if name == "list_videos":
            return _ok(sheets_service.list_videos(
                status=arguments.get("status"),
                category=arguments.get("category"),
                limit=arguments.get("limit", 100),
                channel=ch,
            ))

        if name == "get_video":
            return _ok(sheets_service.get_video(
                row=arguments.get("row"),
                video_id=arguments.get("video_id"),
                channel=ch,
            ))

        if name == "add_video":
            result = research_agent.add_topic_to_sheet(
                topic=arguments["topic"],
                category=arguments.get("category", ""),
                priority=arguments.get("priority", "Medium"),
                notes=arguments.get("notes", ""),
                channel=ch,
            )
            return _ok(result)

        if name == "update_video":
            row = arguments.pop("row")
            arguments.pop("channel", None)
            result = sheets_service.update_video(row, channel=ch, **arguments)
            return _ok({"updated": result, "row": row})

        if name == "find_duplicates":
            return _ok(sheets_service.find_duplicates(
                topic=arguments["topic"],
                threshold=arguments.get("threshold", 75),
                channel=ch,
            ))

        if name == "get_schedule":
            return _ok(publishing_agent.get_schedule(weeks=arguments.get("weeks", 4), channel=ch))

        if name == "list_pending_scripts":
            return _ok(publishing_agent.get_pending_scripts(channel=ch))

        if name == "get_workflow_summary":
            return _ok(publishing_agent.get_workflow_summary(channel=ch))

        if name == "get_stats":
            return _ok(sheets_service.get_stats(channel=ch))

        if name == "apply_status_colors":
            return _ok(sheets_service.apply_status_colors(channel=ch))

        # Research tools (no channel — research is channel-agnostic)
        if name == "web_search":
            return _ok(research_service.web_search(
                query=arguments["query"],
                num_results=arguments.get("num_results", 10),
            ))

        if name == "fetch_url":
            return _ok(research_service.fetch_url(
                url=arguments["url"],
                max_chars=arguments.get("max_chars", 8000),
            ))

        if name == "search_reddit":
            return _ok(research_service.search_reddit(
                query=arguments["query"],
                subreddit=arguments.get("subreddit"),
                limit=arguments.get("limit", 10),
            ))

        if name == "search_news":
            return _ok(research_service.search_news(
                query=arguments["query"],
                num_results=arguments.get("num_results", 5),
            ))

        if name == "build_research_brief":
            return _ok(research_agent.build_research_brief(
                topic=arguments["topic"],
                num_web=arguments.get("num_web", 8),
                num_news=arguments.get("num_news", 5),
                num_reddit=arguments.get("num_reddit", 5),
                channel=ch,
            ))

        if name == "save_research_doc":
            return _ok(research_agent.save_research_doc(
                topic=arguments["topic"],
                content=arguments["content"],
                row=arguments.get("row"),
                channel=ch,
            ))

        if name == "build_script_context":
            return _ok(script_agent.build_script_context(
                row=arguments.get("row"),
                video_id=arguments.get("video_id"),
                channel=ch,
            ))

        if name == "save_script_doc":
            return _ok(script_agent.save_script_doc(
                topic=arguments["topic"],
                content=arguments["content"],
                row=arguments["row"],
                channel=ch,
            ))

        if name == "build_visual_context":
            return _ok(visual_agent.build_visual_context(
                row=arguments.get("row"),
                video_id=arguments.get("video_id"),
                channel=ch,
            ))

        if name == "save_visuals_doc":
            return _ok(visual_agent.save_visuals_doc(
                topic=arguments["topic"],
                content=arguments["content"],
                row=arguments["row"],
                channel=ch,
            ))

        if name == "consolidate_visuals_into_scripts":
            return _ok(visual_agent.consolidate_visuals_into_scripts(
                channel=ch,
                status=arguments.get("status"),
            ))

        if name == "cleanup_orphaned_visuals_docs":
            return _ok(visual_agent.cleanup_orphaned_visuals_docs(
                channel=ch,
            ))

        # Document tools
        if name == "create_google_doc":
            folder_id = None
            folder_type = arguments.get("folder_type")
            if folder_type:
                folder_id = drive_service.get_folder_id(folder_type, channel=ch)
            return _ok(docs_service.create_doc(
                title=arguments["title"],
                content=arguments["content"],
                folder_id=folder_id,
            ))

        # Prompt tools
        if name == "get_prompt":
            content = prompt_loader.load_prompt(arguments["name"], channel=ch)
            return _ok({"name": arguments["name"], "channel": ch, "content": content})

        if name == "list_prompts":
            return _ok(prompt_loader.list_prompts(channel=ch))

        # Drive tools
        if name == "list_drive_files":
            folder_type = arguments.get("folder_type")
            folder_id = drive_service.get_folder_id(folder_type, channel=ch) if folder_type else None
            return _ok(drive_service.list_files(
                folder_id=folder_id,
                limit=arguments.get("limit", 20),
                channel=ch,
            ))

        if name == "ensure_setup":
            sheets_service.ensure_sheet_exists(channel=ch)
            drive_service.ensure_drive_structure(channel=ch)
            cfg = channel_service.get_channel_config(ch)
            return _ok({"status": "ok", "channel": cfg["name"], "message": "Sheet and Drive structure verified."})

        if name == "sync_column_order":
            return _ok(sheets_service.sync_column_order(channel=ch))

        # Analytics tools
        if name == "get_category_performance":
            return _ok(analytics_agent.get_category_performance(channel=ch))

        if name == "get_series_candidates":
            return _ok(analytics_agent.get_series_candidates(channel=ch))

        if name == "sync_youtube_stats":
            return _ok(analytics_agent.sync_all_published(channel=ch))

        if name == "get_performance_insights":
            return _ok(analytics_agent.get_performance_insights(channel=ch))

        if name == "fetch_video_comments":
            return _ok(analytics_agent.fetch_comments_for_sentiment(
                video_url=arguments["video_url"],
                max_results=arguments.get("max_results", 50),
            ))

        return _err(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Tool {name} failed: {e}", exc_info=True)
        return _err(str(e))


# ─── Entry Point ───────────────────────────────────────────────────────────────

async def main():
    logger.info("YouTube MCP Server starting (stdio transport)")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
