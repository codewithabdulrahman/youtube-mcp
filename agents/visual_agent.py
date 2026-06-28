"""
Visual scene agent — loads script content and the visuals prompt for Claude to process.
Claude Code generates the actual scene descriptions.
"""
from services import sheets_service, docs_service, drive_service, prompt_loader
from services.logger import OperationLogger, get_logger

logger = get_logger("visual_agent")


def build_visual_context(row: int = None, video_id: str = None, channel: str = None) -> dict:
    """
    Load script content and visuals prompt for Claude to generate scene descriptions.
    """
    video = sheets_service.get_video(row=row, video_id=video_id, channel=channel)
    if not video:
        raise ValueError(f"Video not found: row={row}, id={video_id}")

    script_content = ""
    if video.get("script_doc"):
        doc_id = _extract_doc_id(video["script_doc"])
        if doc_id:
            script_content = docs_service.get_doc_content(doc_id)

    visuals_prompt = prompt_loader.load_prompt("visuals", channel=channel)

    return {
        "video": video,
        "channel": channel,
        "script_content": script_content,
        "visuals_prompt": visuals_prompt,
        "has_script": bool(script_content),
    }


def save_visuals_to_script_doc(script_doc_id: str, visuals_content: str) -> bool:
    """Append visual descriptions to the existing script document."""
    op = OperationLogger(f"save_visuals:{script_doc_id}", "visual_agent")
    try:
        existing = docs_service.get_doc_content(script_doc_id)
        combined = existing + "\n\n" + "=" * 60 + "\nVISUAL SCENE DESCRIPTIONS\n" + "=" * 60 + "\n\n" + visuals_content
        docs_service.update_doc(script_doc_id, combined)
        logger.info(f"Appended visuals to doc {script_doc_id}")
        return True
    finally:
        op.finish()


def save_visuals_doc(topic: str, content: str, row: int, channel: str = None) -> dict:
    """Save visuals as a separate Google Doc."""
    op = OperationLogger(f"save_visuals_doc:{topic}", "visual_agent")
    try:
        folder_id = drive_service.get_folder_id("scripts", channel=channel)
        doc = docs_service.create_doc(
            title=f"Visuals: {topic}",
            content=content,
            folder_id=folder_id,
        )
        op.add_document(doc["id"], doc["title"])
        logger.info(f"Saved visuals doc for {topic}")
        return doc
    finally:
        op.finish()


def _extract_doc_id(url: str) -> str | None:
    try:
        parts = url.split("/d/")
        if len(parts) > 1:
            return parts[1].split("/")[0]
    except Exception:
        pass
    return None
