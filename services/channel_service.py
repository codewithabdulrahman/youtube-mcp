"""
Channel registry — stores and resolves per-channel Google Sheet / Drive config.

channels.json is auto-bootstrapped from .env on first use so existing setups
keep working without any migration.
"""
import json
from pathlib import Path
from services.logger import get_logger

logger = get_logger("channel_service")

CHANNELS_PATH = Path(__file__).parent.parent / "config" / "channels.json"


def _load() -> dict:
    if CHANNELS_PATH.exists():
        return json.loads(CHANNELS_PATH.read_text())
    return _bootstrap()


def _bootstrap() -> dict:
    """Create initial channels.json from existing .env values."""
    from config.settings import GOOGLE_SHEET_ID, GOOGLE_DRIVE_FOLDER
    data = {
        "active": "default",
        "channels": {
            "default": {
                "display_name": "Default Channel",
                "sheet_id": GOOGLE_SHEET_ID,
                "sheet_tab": "Videos",
                "drive_folder_id": GOOGLE_DRIVE_FOLDER,
            }
        },
    }
    _save(data)
    logger.info("Bootstrapped channels.json from env vars")
    return data


def _save(data: dict):
    CHANNELS_PATH.write_text(json.dumps(data, indent=2))


def list_channels() -> list[dict]:
    """Return all channels with an is_active flag."""
    data = _load()
    active = data["active"]
    return [
        {"name": k, **v, "is_active": k == active}
        for k, v in data["channels"].items()
    ]


def get_active_channel_name() -> str:
    return _load()["active"]


def get_channel_config(channel: str = None) -> dict:
    """Return config for a named channel, or the active channel if None."""
    data = _load()
    name = channel or data["active"]
    if name not in data["channels"]:
        available = list(data["channels"].keys())
        raise ValueError(f"Unknown channel '{name}'. Available: {available}")
    return {"name": name, **data["channels"][name]}


def set_active_channel(name: str) -> dict:
    data = _load()
    if name not in data["channels"]:
        available = list(data["channels"].keys())
        raise ValueError(f"Unknown channel '{name}'. Available: {available}")
    data["active"] = name
    _save(data)
    logger.info(f"Active channel set to '{name}'")
    return {"active": name, **data["channels"][name]}


def add_channel(
    name: str,
    display_name: str,
    sheet_id: str,
    drive_folder_id: str,
    sheet_tab: str = "Videos",
    youtube_channel_id: str = "",
) -> dict:
    """
    Register a new channel. sheet_id is the Google Spreadsheet ID.
    drive_folder_id is the root Drive folder for this channel's content.
    youtube_channel_id is the YouTube channel ID (UCxxxxxxxx) — needed for Analytics API.
    """
    data = _load()
    slug = name.lower().replace(" ", "_")
    if slug in data["channels"]:
        raise ValueError(f"Channel '{slug}' already exists. Use update_channel to modify it.")
    data["channels"][slug] = {
        "display_name": display_name,
        "sheet_id": sheet_id,
        "sheet_tab": sheet_tab,
        "drive_folder_id": drive_folder_id,
        "youtube_channel_id": youtube_channel_id,
    }
    _save(data)
    logger.info(f"Added channel '{slug}' ({display_name})")
    return {"name": slug, **data["channels"][slug]}


def update_channel(name: str, **fields) -> dict:
    """Update one or more fields of an existing channel config."""
    data = _load()
    if name not in data["channels"]:
        raise ValueError(f"Unknown channel '{name}'")
    allowed = {"display_name", "sheet_id", "sheet_tab", "drive_folder_id", "youtube_channel_id", "token_file"}
    for k, v in fields.items():
        if k not in allowed:
            raise ValueError(f"Unknown field '{k}'. Allowed: {allowed}")
        data["channels"][name][k] = v
    _save(data)
    return {"name": name, **data["channels"][name]}


def remove_channel(name: str) -> dict:
    """Remove a channel. Cannot remove the active channel."""
    data = _load()
    if name not in data["channels"]:
        raise ValueError(f"Unknown channel '{name}'")
    if data["active"] == name:
        raise ValueError(f"Cannot remove the active channel '{name}'. Switch active channel first.")
    deleted = data["channels"].pop(name)
    _save(data)
    logger.info(f"Removed channel '{name}'")
    return {"removed": name, **deleted}
