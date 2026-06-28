import re
from datetime import date
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from services.google_auth import get_credentials
from services.logger import get_logger

logger = get_logger("youtube_service")

_VIDEO_ID_RE = re.compile(
    r'(?:youtube\.com/(?:watch\?[^#]*v=|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})'
)


def extract_video_id(url: str) -> str | None:
    m = _VIDEO_ID_RE.search(url)
    return m.group(1) if m else None


def get_video_stats(video_id: str) -> dict:
    """Fetch views, likes, comments via YouTube Data API v3."""
    service = build("youtube", "v3", credentials=get_credentials())
    try:
        resp = service.videos().list(part="statistics", id=video_id).execute()
        items = resp.get("items", [])
        if not items:
            return {}
        stats = items[0].get("statistics", {})
        return {
            "views": int(stats.get("viewCount", 0) or 0),
            "likes": int(stats.get("likeCount", 0) or 0),
            "comments": int(stats.get("commentCount", 0) or 0),
        }
    except HttpError as e:
        logger.warning(f"YouTube Data API error for {video_id}: {e}")
        return {}


def get_video_analytics(video_id: str, published_date: str = None) -> dict:
    """Fetch watch time, CTR, impressions, avg view duration via YouTube Analytics API."""
    service = build("youtubeAnalytics", "v2", credentials=get_credentials())
    start_date = published_date or "2020-01-01"
    end_date = date.today().isoformat()

    try:
        resp = service.reports().query(
            ids="channel==MINE",
            startDate=start_date,
            endDate=end_date,
            metrics="estimatedMinutesWatched,impressions,impressionClickThroughRate,averageViewDuration",
            dimensions="video",
            filters=f"video=={video_id}",
        ).execute()

        rows = resp.get("rows", [])
        if not rows:
            return {}

        # row columns: video, estimatedMinutesWatched, impressions, impressionClickThroughRate, averageViewDuration
        row = rows[0]
        return {
            "watch_time_mins": round(float(row[1]), 1),
            "impressions": int(row[2]),
            "ctr": round(float(row[3]) * 100, 2),
            "avg_view_duration_secs": int(row[4]),
        }
    except HttpError as e:
        logger.warning(f"YouTube Analytics API error for {video_id}: {e}")
        return {}


def get_full_metrics(video_url: str, published_date: str = None) -> dict:
    """Return combined Data API + Analytics API metrics for a video URL."""
    video_id = extract_video_id(video_url)
    if not video_id:
        return {"error": f"Could not extract video ID from: {video_url}"}

    stats = get_video_stats(video_id)
    analytics = get_video_analytics(video_id, published_date=published_date)

    return {"video_id": video_id, **stats, **analytics}
