"""
Research agent — coordinates finding new topics and building research documents.
All AI reasoning is performed by Claude Code; this module handles orchestration
and data assembly.
"""
from services import sheets_service, docs_service, drive_service, research_service, prompt_loader
from services.logger import OperationLogger, get_logger

logger = get_logger("research_agent")


def _format_existing_catalog(channel: str = None) -> tuple[list[dict], str]:
    """
    Pull every topic already in the channel's sheet and render a compact
    text block. Returns (raw_list, formatted_block) so the brief can both
    expose the data and embed it in the prompt as a do-not-repeat guardrail.
    """
    videos = sheets_service.list_videos(limit=1000, channel=channel)
    catalog = [
        {
            "topic": v.get("topic", ""),
            "category": v.get("category", ""),
            "status": v.get("status", ""),
        }
        for v in videos
        if v.get("topic")
    ]

    if not catalog:
        return [], "(no existing videos in the sheet yet)"

    lines = [f"- {c['topic']}  [{c['category']} | {c['status']}]" for c in catalog]
    return catalog, "\n".join(lines)


def _append_dedup_guardrail(research_prompt: str, catalog_block: str) -> str:
    """Append the existing-catalog and a final cross-check rule to the prompt."""
    return f"""{research_prompt}

---

## EXISTING CHANNEL CONTENT — ALREADY PUBLISHED OR IN THE PIPELINE
These topics are ALREADY done or planned for this channel. Treat every one of
them — and any close variation — as SATURATED for this channel. Do NOT propose
them again.

{catalog_block}

## FINAL STEP (MANDATORY) — DEDUPLICATION CHECK
Before you output your final answer, review EVERY niche and example title you
are about to suggest against the EXISTING CHANNEL CONTENT list above.
- If an idea matches, or is a close variation of, anything we have already
  done, REMOVE it and replace it with a genuinely new one.
- End your response with a short "✅ Dedup check" section confirming that none
  of your final suggestions overlap with content we have already produced, and
  briefly note any ideas you dropped because they were too close to existing ones.
"""


def build_research_brief(topic: str, num_web: int = 8, num_news: int = 5, num_reddit: int = 5, channel: str = None) -> dict:
    """
    Gather raw research data for a topic.

    Returns a structured dict with all source material ready for Claude to
    synthesize into a research document.
    """
    op = OperationLogger(f"research:{topic}", "research_agent")

    try:
        duplicates = sheets_service.find_duplicates(topic, channel=channel)
        web_results = research_service.web_search(topic, num_results=num_web)
        news_results = research_service.search_news(topic, num_results=num_news)
        reddit_results = research_service.search_reddit(topic, limit=num_reddit)

        fetched_pages = []
        for r in web_results[:3]:
            if r.get("url"):
                page = research_service.fetch_url(r["url"])
                fetched_pages.append(page)

        research_prompt = prompt_loader.load_prompt("research", channel=channel)
        existing_catalog, catalog_block = _format_existing_catalog(channel=channel)
        research_prompt = _append_dedup_guardrail(research_prompt, catalog_block)

        op.set_metadata("web_results", len(web_results))
        op.set_metadata("news_results", len(news_results))
        op.set_metadata("reddit_results", len(reddit_results))
        op.set_metadata("existing_catalog", len(existing_catalog))

        return {
            "topic": topic,
            "channel": channel,
            "duplicate_check": duplicates,
            "existing_catalog": existing_catalog,
            "web_results": web_results,
            "news_results": news_results,
            "reddit_results": reddit_results,
            "fetched_pages": fetched_pages,
            "research_prompt": research_prompt,
            "has_duplicates": len(duplicates) > 0,
        }
    finally:
        op.finish()


def save_research_doc(topic: str, content: str, row: int = None, channel: str = None) -> dict:
    """
    Save a completed research document to Google Drive and update the sheet.
    Returns the created doc metadata.
    """
    op = OperationLogger(f"save_research:{topic}", "research_agent")
    try:
        folder_id = drive_service.get_folder_id("research", channel=channel)
        doc = docs_service.create_doc(
            title=f"Research: {topic}",
            content=content,
            folder_id=folder_id,
        )
        op.add_document(doc["id"], doc["title"])

        if row:
            sheets_service.update_video(
                row,
                channel=channel,
                status="Research Complete",
                research_doc=doc["url"],
            )
            op.add_row_update(row, "research_doc", doc["url"])
            op.add_row_update(row, "status", "Research Complete")

        return doc
    finally:
        op.finish()


def add_topic_to_sheet(topic: str, category: str = "", priority: str = "Medium", notes: str = "", channel: str = None) -> dict:
    """Add a new topic to the sheet after duplicate-checking."""
    duplicates = sheets_service.find_duplicates(topic, channel=channel)
    if duplicates:
        top = duplicates[0]
        return {
            "added": False,
            "reason": "duplicate",
            "existing": top,
            "similarity": top["similarity_score"],
        }

    video = sheets_service.add_video(topic, category=category, priority=priority, notes=notes, channel=channel)
    return {"added": True, "video": video}
