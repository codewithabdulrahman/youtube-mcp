import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent

# Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN", "")

# Search APIs
BRAVE_SEARCH_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY", "")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "youtube-mcp/1.0")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = BASE_DIR / os.getenv("LOG_DIR", "logs")

# Cache
CACHE_DIR = BASE_DIR / os.getenv("CACHE_DIR", "cache")
CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))

# Google Drive folders
DRIVE_RESEARCH_FOLDER = os.getenv("DRIVE_RESEARCH_FOLDER", "Research")
DRIVE_SCRIPTS_FOLDER = os.getenv("DRIVE_SCRIPTS_FOLDER", "Scripts")
DRIVE_THUMBNAILS_FOLDER = os.getenv("DRIVE_THUMBNAILS_FOLDER", "Thumbnail Ideas")
DRIVE_ASSETS_FOLDER = os.getenv("DRIVE_ASSETS_FOLDER", "Assets")
DRIVE_PUBLISHED_FOLDER = os.getenv("DRIVE_PUBLISHED_FOLDER", "Published")

# Token storage
TOKEN_PATH = BASE_DIR / "config" / "token.json"

# Google Sheets column mapping (1-indexed)
SHEET_COLUMNS = {
    "id": 1,
    "topic": 2,
    "category": 3,
    "status": 4,
    "priority": 5,
    "research_score": 6,
    "research_doc": 7,
    "script_doc": 8,
    "thumbnail": 9,
    "publish_date": 10,
    "created_at": 11,
    "updated_at": 12,
    "video_url": 13,
    "notes": 14,
    "views": 15,
    # YouTube metrics — synced via sync_youtube_stats
    "likes": 16,
    "comments": 17,
    "watch_time_mins": 18,
    "ctr": 19,
    "avg_view_duration_secs": 20,
    "impressions": 21,
}

SHEET_HEADERS = [
    "ID", "Topic", "Category", "Status", "Priority",
    "Research Score", "Research Doc", "Script Doc", "Thumbnail",
    "Publish Date", "Created At", "Updated At", "Video URL", "Notes", "Views",
    "Likes", "Comments", "Watch Time (mins)", "CTR (%)", "Avg View Duration (secs)", "Impressions",
]

VALID_STATUSES = [
    "Idea", "Researching", "Research Complete", "Script Writing",
    "Script Complete", "Thumbnail Ready", "Scheduled", "Published", "Archived"
]

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
    # Temporarily disabled — requires re-auth to mint a refresh token with these scopes.
    # "https://www.googleapis.com/auth/youtube.readonly",
    # "https://www.googleapis.com/auth/yt-analytics.readonly",
]
