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
_BARE_ID_RE = re.compile(r'^[A-Za-z0-9_-]{11}$')


def extract_video_id(url: str) -> str | None:
    m = _VIDEO_ID_RE.search(url)
    if m:
        return m.group(1)
    s = url.strip()
    if _BARE_ID_RE.match(s):
        return s
    return None


def get_video_stats(video_id: str, credentials=None) -> dict:
    """Fetch views, likes, comments via YouTube Data API v3."""
    service = build("youtube", "v3", credentials=credentials or get_credentials())
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


def get_video_analytics(video_id: str, published_date: str = None, youtube_channel_id: str = None, credentials=None) -> dict:
    """Fetch watch time, avg view duration, retention, impressions, CTR, and reach via YouTube Analytics API."""
    service = build("youtubeAnalytics", "v2", credentials=credentials or get_credentials())
    start_date = published_date or "2020-01-01"
    end_date = date.today().isoformat()
    channel_ref = "channel==MINE"

    # Metrics that require content-owner-level access may not be available on all accounts.
    # Try the full set first; fall back to the baseline set if it fails.
    full_metrics = (
        "estimatedMinutesWatched,averageViewDuration,averageViewPercentage,"
        "impressions,impressionsClickThroughRate,uniqueViewers"
    )
    baseline_metrics = "estimatedMinutesWatched,averageViewDuration,averageViewPercentage"

    def _query(metrics: str):
        return service.reports().query(
            ids=channel_ref,
            startDate=start_date,
            endDate=end_date,
            metrics=metrics,
            dimensions="video",
            filters=f"video=={video_id}",
        ).execute()

    try:
        try:
            resp = _query(full_metrics)
            extended = True
        except HttpError:
            resp = _query(baseline_metrics)
            extended = False

        rows = resp.get("rows", [])
        if not rows:
            return {}

        row = rows[0]
        # row columns: video, estMinWatched, avgViewDuration, avgViewPct[, impressions, ctr, uniqueViewers]
        result = {
            "watch_time_mins": round(float(row[1]), 1),
            "avg_view_duration_secs": int(float(row[2])),
            "retention_rate": round(float(row[3]), 1),
        }
        if extended and len(row) >= 7:
            result["impressions"] = int(float(row[4]))
            result["ctr"] = round(float(row[5]), 2)
            result["reach"] = int(float(row[6]))
        return result
    except HttpError as e:
        logger.warning(f"YouTube Analytics API error for {video_id}: {e}")
        return {}


def get_video_comments(video_id: str, max_results: int = 50, credentials=None) -> list[dict]:
    """Fetch top comments for a video using YouTube Data API v3."""
    service = build("youtube", "v3", credentials=credentials or get_credentials())
    try:
        resp = service.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=max_results,
            order="relevance",
            textFormat="plainText",
        ).execute()
        comments = []
        for item in resp.get("items", []):
            s = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "text": s.get("textDisplay", ""),
                "likes": s.get("likeCount", 0),
                "author": s.get("authorDisplayName", ""),
                "published": s.get("publishedAt", ""),
            })
        return comments
    except HttpError as e:
        logger.warning(f"YouTube Comments API error for {video_id}: {e}")
        return []


def get_full_metrics(video_url: str, published_date: str = None, youtube_channel_id: str = None, credentials=None) -> dict:
    """Return combined Data API + Analytics API metrics for a video URL."""
    video_id = extract_video_id(video_url)
    if not video_id:
        return {"error": f"Could not extract video ID from: {video_url}"}

    stats = get_video_stats(video_id, credentials=credentials)
    analytics = get_video_analytics(video_id, published_date=published_date, youtube_channel_id=youtube_channel_id, credentials=credentials)

    return {"video_id": video_id, **stats, **analytics}
