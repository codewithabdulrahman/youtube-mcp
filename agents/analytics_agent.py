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


def _compute_performance_state(ctr: float, retention_rate: float, views: int) -> str:
    # CTR not available from YouTube Analytics API per-video — fall back to views
    if ctr == 0:
        if views >= 50000:
            return "Growing"
        if views >= 5000:
            return "Stable"
        if views >= 500:
            return "Declining"
        return "Dead"
    if views < 100 and ctr < 0.5:
        return "Dead"
    if ctr >= 4.0 or retention_rate >= 50:
        return "Growing"
    if ctr >= 2.0 or retention_rate >= 35:
        return "Stable"
    if ctr >= 0.5:
        return "Declining"
    return "Dead"


def get_youtube_analytics(video_url: str, published_date: str = None) -> dict:
    """Fetch real-time metrics for a single video URL from YouTube APIs."""
    from services.youtube_service import get_full_metrics
    return get_full_metrics(video_url, published_date=published_date)


def sync_all_published(channel: str = None) -> dict:
    """
    Fetch latest YouTube metrics for all Published videos and write them to the sheet.
    Returns a summary of how many rows were synced and which failed.
    """
    from services.youtube_service import get_full_metrics
    from services.channel_service import get_channel_config
    from services.google_auth import get_credentials
    from config.settings import BASE_DIR
    videos = sheets_service.list_videos(status="Published", limit=500, channel=channel)
    cfg = get_channel_config(channel)
    youtube_channel_id = cfg.get("youtube_channel_id") or None
    token_file = cfg.get("token_file")
    credentials = get_credentials(token_path=BASE_DIR / token_file if token_file else None)

    synced = 0
    failed = []

    for v in videos:
        url = v.get("video_id", "").strip() or v.get("notes", "").strip()
        if not url:
            continue

        metrics = get_full_metrics(url, published_date=v.get("publish_date") or None, youtube_channel_id=youtube_channel_id, credentials=credentials)

        if "error" in metrics:
            failed.append({"row": v["row"], "topic": v["topic"], "reason": metrics["error"]})
            continue

        update_fields = {k: metrics[k] for k in
                         ("views", "likes", "comments", "watch_time_mins", "ctr",
                          "avg_view_duration_secs", "impressions", "reach", "retention_rate")
                         if k in metrics}

        if update_fields:
            try:
                update_fields["performance_state"] = _compute_performance_state(
                    ctr=float(update_fields.get("ctr", 0)),
                    retention_rate=float(update_fields.get("retention_rate", 0)),
                    views=int(update_fields.get("views", 0)),
                )
            except (ValueError, TypeError):
                pass
            sheets_service.update_video(v["row"], channel=channel, **update_fields)
            synced += 1
        else:
            failed.append({"row": v["row"], "topic": v["topic"], "reason": "no metrics returned"})

    logger.info(f"sync_all_published: synced={synced}, failed={len(failed)} (channel={channel or 'active'})")
    return {"synced": synced, "failed": failed, "total_published": len(videos)}


def get_performance_insights(channel: str = None) -> dict:
    """
    Analyze synced YouTube metrics to surface per-category performance and weak spots.
    Reads from the sheet — run sync_all_published first to get fresh data.
    """
    videos = sheets_service.list_videos(status="Published", limit=500, channel=channel)

    by_category: dict[str, dict] = {}
    top_performers = []
    bottom_performers = []

    metric_keys = ("views", "likes", "ctr", "watch_time_mins", "avg_view_duration_secs", "impressions")

    for v in videos:
        cat = v.get("category") or "Uncategorized"
        if cat not in by_category:
            by_category[cat] = {k: [] for k in metric_keys}
            by_category[cat]["topics"] = []

        by_category[cat]["topics"].append(v["topic"])
        for k in metric_keys:
            raw = v.get(k, "")
            try:
                by_category[cat][k].append(float(raw))
            except (ValueError, TypeError):
                pass

        # Collect (ctr, topic) for ranking — skip videos without CTR data
        try:
            top_performers.append({"topic": v["topic"], "category": cat, "ctr": float(v.get("ctr") or 0),
                                    "views": int(float(v.get("views") or 0))})
        except (ValueError, TypeError):
            pass

    # Compute per-category averages
    category_summary = {}
    for cat, data in by_category.items():
        summary = {"video_count": len(data["topics"]), "topics": data["topics"]}
        for k in metric_keys:
            vals = data[k]
            summary[f"avg_{k}"] = round(sum(vals) / len(vals), 2) if vals else None
        category_summary[cat] = summary

    # Top / bottom 3 by CTR (only videos with CTR data)
    ranked = sorted([p for p in top_performers if p["ctr"] > 0], key=lambda x: x["ctr"], reverse=True)
    top3 = ranked[:3]
    bottom3 = ranked[-3:] if len(ranked) >= 3 else ranked[::-1]

    # Weak areas: categories with avg CTR below overall average
    all_ctrs = [v for cat in category_summary.values() for v in ([cat["avg_ctr"]] if cat["avg_ctr"] else [])]
    overall_avg_ctr = round(sum(all_ctrs) / len(all_ctrs), 2) if all_ctrs else None
    weak_categories = [
        cat for cat, s in category_summary.items()
        if s["avg_ctr"] is not None and overall_avg_ctr and s["avg_ctr"] < overall_avg_ctr
    ]

    return {
        "channel": channel,
        "published_videos_analyzed": len(videos),
        "overall_avg_ctr": overall_avg_ctr,
        "weak_categories": weak_categories,
        "top_performers_by_ctr": top3,
        "bottom_performers_by_ctr": bottom3,
        "by_category": category_summary,
    }


def fetch_comments_for_sentiment(video_url: str, max_results: int = 50) -> dict:
    """
    Fetch top comments for a video so Claude can assess overall sentiment.
    After reviewing, call update_video(row, comment_sentiment=...) with:
    'Mostly Positive', 'Mixed', or 'Mostly Negative'.
    """
    from services.youtube_service import extract_video_id, get_video_comments
    video_id = extract_video_id(video_url)
    if not video_id:
        return {"error": f"Could not extract video ID from: {video_url}"}
    comments = get_video_comments(video_id, max_results=max_results)
    return {
        "video_id": video_id,
        "comment_count": len(comments),
        "comments": comments,
        "instruction": (
            "Read these comments and call update_video with comment_sentiment set to one of: "
            "'Mostly Positive', 'Mixed', or 'Mostly Negative'."
        ),
    }
