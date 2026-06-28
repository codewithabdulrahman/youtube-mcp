from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from services.google_auth import get_credentials
from services.channel_service import get_channel_config
from config.settings import (
    DRIVE_RESEARCH_FOLDER, DRIVE_SCRIPTS_FOLDER,
    DRIVE_THUMBNAILS_FOLDER, DRIVE_ASSETS_FOLDER, DRIVE_PUBLISHED_FOLDER
)
from services.logger import get_logger

logger = get_logger("drive_service")

_folder_cache: dict[str, str] = {}


def _get_service():
    return build("drive", "v3", credentials=get_credentials())


def _root_folder(channel: str = None) -> str:
    """Return the root Drive folder ID for the given channel (or active channel)."""
    return get_channel_config(channel)["drive_folder_id"]


def get_or_create_folder(name: str, parent_id: str = None, channel: str = None) -> str:
    """Return folder ID, creating it if it doesn't exist."""
    resolved_parent = parent_id or _root_folder(channel)
    cache_key = f"{resolved_parent}:{name}"
    if cache_key in _folder_cache:
        return _folder_cache[cache_key]

    service = _get_service()

    query_parts = [
        f"name='{name}'",
        "mimeType='application/vnd.google-apps.folder'",
        "trashed=false",
    ]
    if resolved_parent:
        query_parts.append(f"'{resolved_parent}' in parents")

    result = service.files().list(
        q=" and ".join(query_parts),
        fields="files(id, name)",
    ).execute()

    files = result.get("files", [])
    if files:
        folder_id = files[0]["id"]
        _folder_cache[cache_key] = folder_id
        return folder_id

    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if resolved_parent:
        metadata["parents"] = [resolved_parent]

    folder = service.files().create(
        body=metadata,
        fields="id",
    ).execute()

    folder_id = folder["id"]
    _folder_cache[cache_key] = folder_id
    logger.info(f"Created Drive folder: {name} ({folder_id})")
    return folder_id


def ensure_drive_structure(channel: str = None):
    """Create the full YouTube folder structure in Drive for the given channel."""
    root = _root_folder(channel)
    for folder_name in [
        DRIVE_RESEARCH_FOLDER, DRIVE_SCRIPTS_FOLDER,
        DRIVE_THUMBNAILS_FOLDER, DRIVE_ASSETS_FOLDER, DRIVE_PUBLISHED_FOLDER
    ]:
        get_or_create_folder(folder_name, root, channel=channel)
    logger.info(f"Drive folder structure verified (channel={channel or 'active'})")


def get_folder_id(folder_type: str, channel: str = None) -> str:
    """Get folder ID by type: research, scripts, thumbnails, assets, published."""
    mapping = {
        "research": DRIVE_RESEARCH_FOLDER,
        "scripts": DRIVE_SCRIPTS_FOLDER,
        "thumbnails": DRIVE_THUMBNAILS_FOLDER,
        "assets": DRIVE_ASSETS_FOLDER,
        "published": DRIVE_PUBLISHED_FOLDER,
    }
    folder_name = mapping.get(folder_type.lower())
    if not folder_name:
        raise ValueError(f"Unknown folder type: {folder_type}. Use: {list(mapping.keys())}")
    return get_or_create_folder(folder_name, _root_folder(channel), channel=channel)


def move_file_to_folder(file_id: str, folder_id: str):
    """Move a file to a specific folder."""
    service = _get_service()
    file = service.files().get(fileId=file_id, fields="parents").execute()
    previous_parents = ",".join(file.get("parents", []))
    service.files().update(
        fileId=file_id,
        addParents=folder_id,
        removeParents=previous_parents,
        fields="id, parents",
    ).execute()
    logger.debug(f"Moved file {file_id} to folder {folder_id}")


def list_files(folder_id: str = None, file_type: str = None, limit: int = 50, channel: str = None) -> list[dict]:
    """List files in a Drive folder."""
    service = _get_service()
    resolved_folder = folder_id or _root_folder(channel)

    query_parts = [f"'{resolved_folder}' in parents", "trashed=false"]
    if file_type:
        mime_map = {
            "doc": "application/vnd.google-apps.document",
            "sheet": "application/vnd.google-apps.spreadsheet",
            "folder": "application/vnd.google-apps.folder",
        }
        mime = mime_map.get(file_type, file_type)
        query_parts.append(f"mimeType='{mime}'")

    result = service.files().list(
        q=" and ".join(query_parts),
        fields="files(id, name, mimeType, createdTime, webViewLink)",
        pageSize=limit,
        orderBy="createdTime desc",
    ).execute()

    return result.get("files", [])
