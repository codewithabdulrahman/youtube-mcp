"""
Analytics agent — identifies trends and gaps from sheet data.
YouTube API integration is a future feature; interfaces are defined here.
"""
from collections import Counter
from services import sheets_service
from services.logger import get_logger

logger = get_logger("analytics_agent")


def get_category_performance(channel: str = None) -> dict:
    """Analyze the distribution of videos by category and status."""
    videos = sheets_service.list_videos(limit=1000, channel=channel)
    by_category: dict[str, dict] = {}

    for v in videos:
        cat = v.get("category") or "Uncategorized"
        if cat not in by_category:
            by_category[cat] = {"total": 0, "published": 0, "statuses": Counter()}
        by_category[cat]["total"] += 1
        by_category[cat]["statuses"][v["status"]] += 1
        if v["status"] == "Published":
            by_category[cat]["published"] += 1

    return {"channel": channel, "by_category": by_category, "total_videos": len(videos)}


def find_topic_gaps(category: str = None, channel: str = None) -> list[str]:
    """
    Identify topic areas that have few or no videos.
    Returns a list of suggested gap areas for Claude to research further.
    """
    videos = sheets_service.list_videos(limit=1000, channel=channel)
    if category:
        videos = [v for v in videos if v.get("category", "").lower() == category.lower()]

    existing_topics = [v["topic"].lower() for v in videos]
    return existing_topics


def get_series_candidates(channel: str = None) -> list[dict]:
    """Find topics that could become a series (similar topics with high scores)."""
    from thefuzz import fuzz
    videos = sheets_service.list_videos(limit=1000, channel=channel)

    groups: list[list[dict]] = []
    used = set()
    for i, v1 in enumerate(videos):
        if i in used:
            continue
        group = [v1]
        for j, v2 in enumerate(videos[i + 1:], start=i + 1):
            if j in used:
                continue
            if fuzz.token_set_ratio(v1["topic"], v2["topic"]) >= 60:
                group.append(v2)
                used.add(j)
        if len(group) >= 2:
            used.add(i)
            groups.append(group)

    return [
        {
            "potential_series": [v["topic"] for v in group],
            "count": len(group),
            "categories": list({v.get("category", "") for v in group}),
        }
        for group in groups
    ]


def get_youtube_analytics(video_url: str) -> dict:
    """YouTube Analytics API stub — not implemented in MVP."""
    return {
        "status": "not_implemented",
        "message": "YouTube Analytics API integration is planned for a future version.",
        "video_url": video_url,
    }
