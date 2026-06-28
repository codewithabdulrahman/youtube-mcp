import json
import time
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from config.settings import (
    BRAVE_SEARCH_API_KEY, REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET,
    REDDIT_USER_AGENT, CACHE_DIR, CACHE_TTL_HOURS
)
from services.logger import get_logger

logger = get_logger("research_service")

CACHE_DIR.mkdir(parents=True, exist_ok=True)
HEADERS = {"User-Agent": REDDIT_USER_AGENT}


def _cache_key(query: str) -> Path:
    h = hashlib.md5(query.encode()).hexdigest()
    return CACHE_DIR / f"{h}.json"


def _load_cache(key: Path) -> dict | None:
    if not key.exists():
        return None
    data = json.loads(key.read_text())
    cached_at = datetime.fromisoformat(data.get("cached_at", "2000-01-01"))
    if datetime.now() - cached_at > timedelta(hours=CACHE_TTL_HOURS):
        return None
    return data


def _save_cache(key: Path, data: dict):
    data["cached_at"] = datetime.now().isoformat()
    key.write_text(json.dumps(data, indent=2))


def web_search(query: str, num_results: int = 10) -> list[dict]:
    """Search the web using Brave Search API or a basic fallback."""
    cache_key = _cache_key(f"search:{query}:{num_results}")
    cached = _load_cache(cache_key)
    if cached:
        logger.debug(f"Cache hit for search: {query}")
        return cached["results"]

    results = []

    if BRAVE_SEARCH_API_KEY:
        results = _brave_search(query, num_results)
    else:
        logger.warning("No BRAVE_SEARCH_API_KEY set. Using DuckDuckGo scrape fallback.")
        results = _ddg_search(query, num_results)

    _save_cache(cache_key, {"results": results})
    return results


def _brave_search(query: str, num_results: int) -> list[dict]:
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": BRAVE_SEARCH_API_KEY,
    }
    params = {"q": query, "count": min(num_results, 20)}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for item in data.get("web", {}).get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("description", ""),
                "source": "brave",
            })
        return results
    except Exception as e:
        logger.error(f"Brave search failed: {e}")
        return []


def _ddg_search(query: str, num_results: int) -> list[dict]:
    """Scrape DuckDuckGo as a no-auth fallback."""
    url = "https://html.duckduckgo.com/html/"
    try:
        resp = requests.post(url, data={"q": query}, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for result in soup.select(".result")[:num_results]:
            title_el = result.select_one(".result__title")
            url_el = result.select_one(".result__url")
            snippet_el = result.select_one(".result__snippet")
            results.append({
                "title": title_el.get_text(strip=True) if title_el else "",
                "url": url_el.get_text(strip=True) if url_el else "",
                "description": snippet_el.get_text(strip=True) if snippet_el else "",
                "source": "duckduckgo",
            })
        return results
    except Exception as e:
        logger.error(f"DDG search failed: {e}")
        return []


def fetch_url(url: str, max_chars: int = 8000) -> dict:
    """Fetch and extract text content from a URL."""
    cache_key = _cache_key(f"url:{url}")
    cached = _load_cache(cache_key)
    if cached:
        return cached

    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove noise
        for tag in soup(["script", "style", "nav", "footer", "aside", "iframe"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        lines = [l for l in text.splitlines() if len(l.strip()) > 30]
        content = "\n".join(lines)[:max_chars]

        result = {
            "url": url,
            "title": soup.title.string if soup.title else "",
            "content": content,
            "fetched_at": datetime.now().isoformat(),
        }
        _save_cache(cache_key, result)
        return result
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return {"url": url, "title": "", "content": "", "error": str(e)}


def search_reddit(query: str, subreddit: str = None, limit: int = 10) -> list[dict]:
    """Search Reddit for discussions using the public JSON API."""
    cache_key = _cache_key(f"reddit:{subreddit}:{query}:{limit}")
    cached = _load_cache(cache_key)
    if cached:
        return cached["results"]

    try:
        if subreddit:
            url = f"https://www.reddit.com/r/{subreddit}/search.json"
            params = {"q": query, "restrict_sr": "1", "limit": limit, "sort": "relevance"}
        else:
            url = "https://www.reddit.com/search.json"
            params = {"q": query, "limit": limit, "sort": "relevance"}

        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for post in data.get("data", {}).get("children", []):
            p = post["data"]
            results.append({
                "title": p.get("title", ""),
                "url": f"https://reddit.com{p.get('permalink', '')}",
                "subreddit": p.get("subreddit", ""),
                "score": p.get("score", 0),
                "num_comments": p.get("num_comments", 0),
                "selftext": p.get("selftext", "")[:500],
                "created_utc": p.get("created_utc", 0),
            })

        _save_cache(cache_key, {"results": results})
        return results
    except Exception as e:
        logger.error(f"Reddit search failed: {e}")
        return []


def search_news(query: str, num_results: int = 5) -> list[dict]:
    """Search Google News RSS for recent articles."""
    cache_key = _cache_key(f"news:{query}")
    cached = _load_cache(cache_key)
    if cached:
        return cached["results"]

    try:
        from urllib.parse import quote
        url = f"https://news.google.com/rss/search?q={quote(query)}&hl=en-US&gl=US&ceid=US:en"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.content, "xml")

        results = []
        for item in soup.find_all("item")[:num_results]:
            results.append({
                "title": item.find("title").text if item.find("title") else "",
                "url": item.find("link").text if item.find("link") else "",
                "published": item.find("pubDate").text if item.find("pubDate") else "",
                "source": item.find("source").text if item.find("source") else "",
            })

        _save_cache(cache_key, {"results": results})
        return results
    except Exception as e:
        logger.error(f"News search failed: {e}")
        return []
