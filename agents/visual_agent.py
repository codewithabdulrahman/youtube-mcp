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
    """Save visuals — behavior depends on channel.

    For buildship & shorts: append visuals content directly into the script doc
    with a clear separator and heading, keeping script and visuals as one unit.

    For other channels: create a separate visuals doc (legacy behavior).
    """
    from services.channel_service import get_active_channel_name

    active_ch = channel or get_active_channel_name()

    # For buildship & shorts, append to script doc.
    if active_ch in ("buildship", "shorts"):
        op = OperationLogger(f"save_visuals_doc:{topic}", "visual_agent")
        try:
            video = sheets_service.get_video(row=row, channel=channel)
            script_url = (video or {}).get("script_doc", "")
            script_doc_id = _extract_doc_id(script_url) if script_url else None

            if not script_doc_id:
                raise ValueError(f"Row {row} has no script_doc; cannot save visuals")

            existing = docs_service.get_doc_content(script_doc_id)
            combined = existing.rstrip() + "\n\n" + "=" * 70 + "\n# VISUAL SCENE DESCRIPTIONS\n" + "=" * 70 + "\n\n" + content
            docs_service.update_doc(script_doc_id, combined)

            logger.info(f"Appended visuals to script doc {script_doc_id} for {topic}")

            return {
                "id": script_doc_id,
                "title": f"Script: {topic}",
                "url": script_url,
            }
        finally:
            op.finish()

    # For other channels, create a separate visuals doc.
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


def consolidate_visuals_into_scripts(channel: str = None, status: str = None) -> dict:
    """Consolidate existing separate visuals docs into their script docs for buildship/shorts.

    For each video with a script doc (optionally filtered by status), finds matching
    "Visuals: {title}" doc, appends its content to the script, and deletes the orphaned doc.
    """
    from services.channel_service import get_active_channel_name
    from services.drive_service import delete_file

    active_ch = channel or get_active_channel_name()
    if active_ch not in ("buildship", "shorts"):
        return {"consolidated": 0, "reason": f"Channel {active_ch} keeps separate visuals docs"}

    op = OperationLogger(f"consolidate_visuals:{active_ch}", "visual_agent")
    try:
        videos = sheets_service.list_videos(channel=channel, status=status)
        consolidated = []
        errors = []

        for video in videos:
            title = video.get("title", "")
            script_url = video.get("script_doc", "")
            if not script_url or not title:
                continue

            script_doc_id = _extract_doc_id(script_url)
            if not script_doc_id:
                continue

            # Find matching "Visuals: {title}" doc
            folder_id = drive_service.get_folder_id("scripts", channel=channel)
            files = drive_service.list_files(folder_id)
            visuals_file = None
            for f in files:
                if f["name"] == f"Visuals: {title}":
                    visuals_file = f
                    break

            if not visuals_file:
                continue

            try:
                # Read script and visuals
                script_content = docs_service.get_doc_content(script_doc_id)
                visuals_content = docs_service.get_doc_content(visuals_file["id"])

                # Check if visuals already in script
                if "VISUAL SCENE DESCRIPTIONS" in script_content:
                    logger.info(f"Visuals already in script for {title}; just deleting orphaned doc")
                    delete_file(visuals_file["id"])
                    consolidated.append(f"{title} (deleted orphan)")
                else:
                    # Append visuals to script
                    combined = script_content.rstrip() + "\n\n" + "=" * 70 + "\n# VISUAL SCENE DESCRIPTIONS\n" + "=" * 70 + "\n\n" + visuals_content
                    docs_service.update_doc(script_doc_id, combined)
                    delete_file(visuals_file["id"])
                    consolidated.append(f"{title} (consolidated)")
                    logger.info(f"Consolidated visuals into script for {title}")
            except Exception as e:
                error_msg = f"{title}: {str(e)}"
                errors.append(error_msg)
                logger.warning(f"Could not consolidate {title}: {e}")

        op.add_row_update(0, "consolidation_count", len(consolidated))
        return {
            "consolidated": len(consolidated),
            "items": consolidated,
            "errors": errors,
        }
    finally:
        op.finish()


def cleanup_orphaned_visuals_docs(channel: str = None) -> dict:
    """Find and delete orphaned 'Visuals: ...' docs for buildship/shorts.

    For these channels, visuals live in the script doc, so standalone
    visuals docs are no longer needed. Returns count of deleted docs.
    """
    from services.channel_service import get_active_channel_name
    from services.drive_service import delete_file

    active_ch = channel or get_active_channel_name()
    if active_ch not in ("buildship", "shorts"):
        return {"deleted": 0, "reason": f"Channel {active_ch} keeps separate visuals docs"}

    op = OperationLogger(f"cleanup_visuals:{active_ch}", "visual_agent")
    try:
        folder_id = drive_service.get_folder_id("scripts", channel=channel)
        files = drive_service.list_files(folder_id)

        deleted = []
        for f in files:
            if f["name"].startswith("Visuals: "):
                try:
                    delete_file(f["id"])
                    deleted.append(f["name"])
                    logger.info(f"Deleted orphaned visuals doc: {f['name']}")
                except Exception as e:
                    logger.warning(f"Could not delete {f['id']}: {e}")

        op.add_row_update(0, "orphaned_visuals_deleted", len(deleted))
        return {"deleted": len(deleted), "files": deleted}
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
