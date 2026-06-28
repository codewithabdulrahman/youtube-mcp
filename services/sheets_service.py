from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from thefuzz import fuzz
from services.google_auth import get_credentials
from services.channel_service import get_channel_config
from config.settings import SHEET_COLUMNS, SHEET_HEADERS, VALID_STATUSES
from services.logger import get_logger

logger = get_logger("sheets_service")

DUPLICATE_THRESHOLD = 75

STATUS_COLORS = {
    "Idea":              {"red": 0.91, "green": 0.91, "blue": 0.91},  # light gray
    "Researching":       {"red": 0.80, "green": 0.90, "blue": 1.00},  # light blue
    "Research Complete": {"red": 0.70, "green": 0.88, "blue": 0.86},  # teal
    "Script Writing":    {"red": 1.00, "green": 0.88, "blue": 0.70},  # light orange
    "Script Complete":   {"red": 0.86, "green": 0.93, "blue": 0.78},  # light green
    "Thumbnail Ready":   {"red": 0.88, "green": 0.75, "blue": 0.91},  # light purple
    "Scheduled":         {"red": 1.00, "green": 0.98, "blue": 0.77},  # light yellow
    "Published":         {"red": 0.78, "green": 0.90, "blue": 0.79},  # green
    "Archived":          {"red": 0.81, "green": 0.85, "blue": 0.86},  # blue-gray
}


def _get_service():
    return build("sheets", "v4", credentials=get_credentials())


def _resolve(channel: str = None) -> tuple[str, str]:
    """Return (sheet_id, tab_name) for the given channel (or active channel)."""
    cfg = get_channel_config(channel)
    return cfg["sheet_id"], cfg["sheet_tab"]


def _col_letter(n: int) -> str:
    """Convert 1-indexed column number to letter (1→A, 26→Z, 27→AA)."""
    result = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        result = chr(65 + r) + result
    return result


def _get_tab_id(service, sheet_id: str, tab_name: str) -> int:
    meta = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    for s in meta["sheets"]:
        if s["properties"]["title"] == tab_name:
            return s["properties"]["sheetId"]
    raise ValueError(f"Tab '{tab_name}' not found in sheet {sheet_id}")


def _color_status_cell(service, sheet_id: str, tab_id: int, row: int, status: str):
    color = STATUS_COLORS.get(status)
    if not color:
        return
    col = SHEET_COLUMNS["status"] - 1  # 0-indexed
    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": [{
            "repeatCell": {
                "range": {
                    "sheetId": tab_id,
                    "startRowIndex": row - 1,
                    "endRowIndex": row,
                    "startColumnIndex": col,
                    "endColumnIndex": col + 1,
                },
                "cell": {"userEnteredFormat": {"backgroundColor": color}},
                "fields": "userEnteredFormat.backgroundColor",
            }
        }]},
    ).execute()


def _row_to_dict(row: list, row_number: int) -> dict:
    def safe_get(idx: int) -> str:
        return row[idx - 1] if len(row) >= idx else ""

    title_value = safe_get(SHEET_COLUMNS["title"])
    return {
        "row": row_number,
        "id": safe_get(SHEET_COLUMNS["id"]),
        "title": title_value,
        "topic": title_value,  # alias — both reference column 2
        "type": title_value,   # backward compatibility
        "category": safe_get(SHEET_COLUMNS["category"]),
        "status": safe_get(SHEET_COLUMNS["status"]),
        "priority": safe_get(SHEET_COLUMNS["priority"]),
        "research_score": safe_get(SHEET_COLUMNS["research_score"]),
        "research_doc": safe_get(SHEET_COLUMNS["research_doc"]),
        "script_doc": safe_get(SHEET_COLUMNS["script_doc"]),
        "thumbnail": safe_get(SHEET_COLUMNS["thumbnail"]),
        "publish_date": safe_get(SHEET_COLUMNS["publish_date"]),
        "created_at": safe_get(SHEET_COLUMNS["created_at"]),
        "updated_at": safe_get(SHEET_COLUMNS["updated_at"]),
        "video_id": safe_get(SHEET_COLUMNS["video_id"]),
        "notes": safe_get(SHEET_COLUMNS["notes"]),
        "views": safe_get(SHEET_COLUMNS["views"]),
        "likes": safe_get(SHEET_COLUMNS["likes"]),
        "comments": safe_get(SHEET_COLUMNS["comments"]),
        "watch_time_mins": safe_get(SHEET_COLUMNS["watch_time_mins"]),
        "ctr": safe_get(SHEET_COLUMNS["ctr"]),
        "avg_view_duration_secs": safe_get(SHEET_COLUMNS["avg_view_duration_secs"]),
        "impressions": safe_get(SHEET_COLUMNS["impressions"]),
        "reach": safe_get(SHEET_COLUMNS["reach"]),
        "retention_rate": safe_get(SHEET_COLUMNS["retention_rate"]),
        "performance_state": safe_get(SHEET_COLUMNS["performance_state"]),
        "comment_sentiment": safe_get(SHEET_COLUMNS["comment_sentiment"]),
    }


def ensure_sheet_exists(channel: str = None):
    """Create the channel's sheet tab with headers if it doesn't exist."""
    sheet_id, tab_name = _resolve(channel)
    service = _get_service()
    try:
        meta = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        sheet_titles = [s["properties"]["title"] for s in meta["sheets"]]

        if tab_name not in sheet_titles:
            service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id,
                body={"requests": [{"addSheet": {"properties": {"title": tab_name}}}]},
            ).execute()
            _write_headers(sheet_id, tab_name)
            logger.info(f"Created tab '{tab_name}' with headers in sheet {sheet_id}")
        else:
            last_col = _col_letter(len(SHEET_HEADERS))
            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=f"{tab_name}!A1:{last_col}1",
            ).execute()
            existing = result.get("values", [[]])[0] if result.get("values") else []
            if len(existing) < len(SHEET_HEADERS):
                _write_headers(sheet_id, tab_name)
    except HttpError as e:
        logger.error(f"Failed to ensure sheet exists: {e}")
        raise


def _write_headers(sheet_id: str, tab_name: str):
    service = _get_service()
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"{tab_name}!A1",
        valueInputOption="RAW",
        body={"values": [SHEET_HEADERS]},
    ).execute()


def list_videos(status: str = None, category: str = None, limit: int = 200, channel: str = None) -> list[dict]:
    """Return all videos from the channel's sheet tab, optionally filtered."""
    sheet_id, tab_name = _resolve(channel)
    service = _get_service()
    last_col = _col_letter(len(SHEET_HEADERS))
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"{tab_name}!A2:{last_col}{limit + 1}",
    ).execute()
    rows = result.get("values", [])

    videos = []
    for i, row in enumerate(rows, start=2):
        if not row or not row[0]:
            continue
        video = _row_to_dict(row, i)
        if status and video["status"].lower() != status.lower():
            continue
        if category and video["category"].lower() != category.lower():
            continue
        videos.append(video)

    return videos


def get_video(row: int = None, video_id: str = None, channel: str = None) -> dict | None:
    """Get a single video by row number or ID."""
    sheet_id, tab_name = _resolve(channel)
    if row:
        service = _get_service()
        last_col = _col_letter(len(SHEET_HEADERS))
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"{tab_name}!A{row}:{last_col}{row}",
        ).execute()
        rows = result.get("values", [])
        if rows:
            return _row_to_dict(rows[0], row)
        return None

    if video_id:
        videos = list_videos(limit=500, channel=channel)
        for v in videos:
            if v["id"] == video_id:
                return v
    return None


def add_video(topic: str, category: str = "", priority: str = "Medium", notes: str = "", channel: str = None) -> dict:
    """Add a new video row and return it."""
    sheet_id, tab_name = _resolve(channel)
    service = _get_service()
    all_videos = list_videos(limit=1000, channel=channel)
    next_id = f"V{len(all_videos) + 1:04d}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    row_data = [""] * len(SHEET_HEADERS)
    row_data[SHEET_COLUMNS["id"] - 1] = next_id
    row_data[SHEET_COLUMNS["topic"] - 1] = topic
    row_data[SHEET_COLUMNS["category"] - 1] = category
    row_data[SHEET_COLUMNS["status"] - 1] = "Idea"
    row_data[SHEET_COLUMNS["priority"] - 1] = priority
    row_data[SHEET_COLUMNS["created_at"] - 1] = now
    row_data[SHEET_COLUMNS["updated_at"] - 1] = now
    row_data[SHEET_COLUMNS["notes"] - 1] = notes

    result = service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=f"{tab_name}!A:{_col_letter(len(SHEET_HEADERS))}",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [row_data]},
    ).execute()

    updated_range = result.get("updates", {}).get("updatedRange", "")
    try:
        row_num = int(updated_range.split("!")[1].split(":")[0][1:])
    except Exception:
        row_num = len(all_videos) + 2

    try:
        tab_id = _get_tab_id(service, sheet_id, tab_name)
        _color_status_cell(service, sheet_id, tab_id, row_num, "Idea")
    except Exception as e:
        logger.warning(f"Could not apply status color: {e}")

    logger.info(f"Added video '{topic}' as {next_id} at row {row_num} (channel={channel or 'active'})")
    return {"row": row_num, "id": next_id, "topic": topic, "status": "Idea"}


def update_video(row: int, channel: str = None, **fields) -> bool:
    """Update specific fields of a video row."""
    sheet_id, tab_name = _resolve(channel)
    service = _get_service()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    fields["updated_at"] = now

    updates = []
    for field, value in fields.items():
        if field not in SHEET_COLUMNS:
            logger.warning(f"Unknown field: {field}")
            continue
        col = SHEET_COLUMNS[field]
        col_letter = _col_letter(col)
        updates.append({
            "range": f"{tab_name}!{col_letter}{row}",
            "values": [[str(value)]],
        })

    if not updates:
        return False

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=sheet_id,
        body={"valueInputOption": "RAW", "data": updates},
    ).execute()

    if "status" in fields:
        try:
            tab_id = _get_tab_id(service, sheet_id, tab_name)
            _color_status_cell(service, sheet_id, tab_id, row, fields["status"])
        except Exception as e:
            logger.warning(f"Could not apply status color: {e}")

    logger.info(f"Updated row {row}: {list(fields.keys())} (channel={channel or 'active'})")
    return True


def find_duplicates(topic: str, threshold: int = DUPLICATE_THRESHOLD, channel: str = None) -> list[dict]:
    """Return existing videos with similar topics using fuzzy matching."""
    videos = list_videos(limit=1000, channel=channel)
    matches = []
    for v in videos:
        score = fuzz.token_set_ratio(topic.lower(), v["topic"].lower())
        if score >= threshold:
            matches.append({**v, "similarity_score": score})
    matches.sort(key=lambda x: x["similarity_score"], reverse=True)
    return matches


def get_schedule(weeks: int = 4, channel: str = None) -> list[dict]:
    """Return videos with publish dates in the next N weeks."""
    from datetime import timedelta
    cutoff = datetime.now() + timedelta(weeks=weeks)
    videos = list_videos(limit=500, channel=channel)
    scheduled = []
    for v in videos:
        if v["publish_date"]:
            try:
                pub = datetime.strptime(v["publish_date"], "%Y-%m-%d")
                if pub <= cutoff:
                    scheduled.append(v)
            except ValueError:
                pass
    scheduled.sort(key=lambda x: x["publish_date"])
    return scheduled


def list_by_status(status: str, channel: str = None) -> list[dict]:
    return list_videos(status=status, limit=500, channel=channel)


def get_stats(channel: str = None) -> dict:
    """Return counts by status."""
    videos = list_videos(limit=1000, channel=channel)
    stats: dict = {"total": len(videos)}
    for status in VALID_STATUSES:
        stats[status.lower().replace(" ", "_")] = sum(
            1 for v in videos if v["status"] == status
        )
    return stats


def sync_column_order(channel: str = None) -> dict:
    """Reorder sheet columns to match SHEET_HEADERS, preserving all data."""
    sheet_id, tab_name = _resolve(channel)
    service = _get_service()

    old_last_col = _col_letter(len(SHEET_HEADERS) + 10)
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"{tab_name}!A1:{old_last_col}2000",
    ).execute()
    all_rows = result.get("values", [])

    if not all_rows:
        return {"status": "empty", "message": "Sheet is empty, nothing to reorder"}

    old_headers = all_rows[0]
    new_headers = SHEET_HEADERS

    # Map each old column index → new column index
    old_to_new = {}
    for old_idx, header in enumerate(old_headers):
        try:
            new_idx = new_headers.index(header)
            old_to_new[old_idx] = new_idx
        except ValueError:
            logger.warning(f"Unmapped header '{header}' (column {old_idx + 1}) — data will be dropped")

    new_rows = [list(new_headers)]
    for row in all_rows[1:]:
        if not row or not row[0]:
            continue
        new_row = [""] * len(new_headers)
        for old_idx, value in enumerate(row):
            if old_idx in old_to_new:
                new_row[old_to_new[old_idx]] = value
        new_rows.append(new_row)

    # Clear existing data then write reordered rows
    clear_range = f"{tab_name}!A1:{old_last_col}{len(all_rows) + 1}"
    service.spreadsheets().values().clear(
        spreadsheetId=sheet_id,
        range=clear_range,
    ).execute()

    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"{tab_name}!A1",
        valueInputOption="RAW",
        body={"values": new_rows},
    ).execute()

    logger.info(f"Synced column order: {len(new_rows) - 1} data rows rewritten (channel={channel or 'active'})")
    return {
        "status": "ok",
        "rows_migrated": len(new_rows) - 1,
        "columns": len(new_headers),
        "unmapped": [h for i, h in enumerate(old_headers) if i not in old_to_new],
    }


def apply_status_colors(channel: str = None) -> dict:
    """Apply background colors to all status cells in the sheet."""
    sheet_id, tab_name = _resolve(channel)
    service = _get_service()
    tab_id = _get_tab_id(service, sheet_id, tab_name)
    videos = list_videos(limit=1000, channel=channel)

    col = SHEET_COLUMNS["status"] - 1  # 0-indexed
    requests = []
    for v in videos:
        color = STATUS_COLORS.get(v["status"])
        if not color:
            continue
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": tab_id,
                    "startRowIndex": v["row"] - 1,
                    "endRowIndex": v["row"],
                    "startColumnIndex": col,
                    "endColumnIndex": col + 1,
                },
                "cell": {"userEnteredFormat": {"backgroundColor": color}},
                "fields": "userEnteredFormat.backgroundColor",
            }
        })

    if requests:
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={"requests": requests},
        ).execute()

    logger.info(f"Applied status colors to {len(requests)} rows (channel={channel or 'active'})")
    return {"colored": len(requests), "total": len(videos)}
