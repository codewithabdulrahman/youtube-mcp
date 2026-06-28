"""
Publishing agent — answers workflow questions by reading Google Sheets.
All responses are derived from sheet data; no AI generation happens here.
"""
from services import sheets_service
from services.logger import get_logger

logger = get_logger("publishing_agent")


def get_schedule(weeks: int = 4, channel: str = None) -> dict:
    """Return the publishing schedule for the next N weeks."""
    scheduled = sheets_service.get_schedule(weeks=weeks, channel=channel)
    return {
        "weeks": weeks,
        "channel": channel,
        "scheduled_count": len(scheduled),
        "videos": scheduled,
    }


def get_pending_scripts(channel: str = None) -> dict:
    """Return videos that have research complete but no script yet."""
    research_complete = sheets_service.list_by_status("Research Complete", channel=channel)
    return {
        "channel": channel,
        "count": len(research_complete),
        "videos": research_complete,
    }


def get_pending_thumbnails(channel: str = None) -> dict:
    """Return videos with scripts complete but no thumbnail."""
    script_complete = sheets_service.list_by_status("Script Complete", channel=channel)
    no_thumbnail = [v for v in script_complete if not v.get("thumbnail")]
    return {
        "channel": channel,
        "count": len(no_thumbnail),
        "videos": no_thumbnail,
    }


def get_overdue_videos(channel: str = None) -> dict:
    """Return videos that are past their publish date but not published."""
    from datetime import datetime
    all_videos = sheets_service.list_videos(limit=500, channel=channel)
    now = datetime.now()
    overdue = []
    for v in all_videos:
        if v["status"] in ("Published", "Archived"):
            continue
        if v.get("publish_date"):
            try:
                pub = datetime.strptime(v["publish_date"], "%Y-%m-%d")
                if pub < now:
                    overdue.append(v)
            except ValueError:
                pass
    return {"channel": channel, "count": len(overdue), "videos": overdue}


def get_workflow_summary(channel: str = None) -> dict:
    """Return a full snapshot of the channel pipeline."""
    stats = sheets_service.get_stats(channel=channel)
    return {
        "channel": channel,
        "stats": stats,
        "pending_research": sheets_service.list_by_status("Idea", channel=channel),
        "in_research": sheets_service.list_by_status("Researching", channel=channel),
        "pending_scripts": sheets_service.list_by_status("Research Complete", channel=channel),
        "in_scripting": sheets_service.list_by_status("Script Writing", channel=channel),
        "pending_thumbnails": [
            v for v in sheets_service.list_by_status("Script Complete", channel=channel)
            if not v.get("thumbnail")
        ],
        "scheduled": sheets_service.list_by_status("Scheduled", channel=channel),
    }
