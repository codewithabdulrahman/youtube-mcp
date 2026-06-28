"""
Script agent — assembles context for script generation and saves outputs.
Claude Code performs the actual script writing using the loaded research and prompt.
"""
from services import sheets_service, docs_service, drive_service, prompt_loader
from services.logger import OperationLogger, get_logger

logger = get_logger("script_agent")


def build_script_context(row: int = None, video_id: str = None, channel: str = None) -> dict:
    """
    Load everything Claude needs to write a script:
    - Research document content
    - Script prompt template
    - Video metadata
    """
    video = sheets_service.get_video(row=row, video_id=video_id, channel=channel)
    if not video:
        raise ValueError(f"Video not found: row={row}, id={video_id}")

    research_content = ""
    if video.get("research_doc"):
        doc_id = _extract_doc_id(video["research_doc"])
        if doc_id:
            from services.docs_service import get_doc_content
            research_content = get_doc_content(doc_id)

    script_prompt = prompt_loader.load_prompt("script", channel=channel)

    return {
        "video": video,
        "channel": channel,
        "research_content": research_content,
        "script_prompt": script_prompt,
        "has_research": bool(research_content),
    }


def save_script_doc(topic: str, content: str, row: int, channel: str = None) -> dict:
    """Save a completed script to Google Drive and update the sheet."""
    op = OperationLogger(f"save_script:{topic}", "script_agent")
    try:
        folder_id = drive_service.get_folder_id("scripts", channel=channel)
        doc = docs_service.create_doc(
            title=f"Script: {topic}",
            content=content,
            folder_id=folder_id,
        )
        op.add_document(doc["id"], doc["title"])

        sheets_service.update_video(
            row,
            channel=channel,
            status="Script Complete",
            script_doc=doc["url"],
        )
        op.add_row_update(row, "script_doc", doc["url"])
        op.add_row_update(row, "status", "Script Complete")

        return doc
    finally:
        op.finish()


def _extract_doc_id(url: str) -> str | None:
    """Extract Google Doc ID from a docs.google.com URL."""
    try:
        parts = url.split("/d/")
        if len(parts) > 1:
            return parts[1].split("/")[0]
    except Exception:
        pass
    return None
