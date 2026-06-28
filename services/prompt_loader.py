from pathlib import Path
from string import Template
from config.settings import BASE_DIR
from services.logger import get_logger

logger = get_logger("prompt_loader")

PROMPT_DIR = BASE_DIR / "prompts"


def _resolve_path(name: str, channel: str = None) -> Path:
    """
    Find a prompt file. Lookup order:
      1. prompts/<channel>/<name>.md  (channel-specific override)
      2. prompts/<name>.md            (global default)
    """
    if channel:
        channel_path = PROMPT_DIR / channel / f"{name}.md"
        if channel_path.exists():
            return channel_path

    global_path = PROMPT_DIR / f"{name}.md"
    if global_path.exists():
        return global_path

    raise FileNotFoundError(
        f"Prompt '{name}' not found. "
        f"Expected at prompts/{channel}/{name}.md (channel override) "
        f"or prompts/{name}.md (global default)."
    )


def load_prompt(name: str, channel: str = None) -> str:
    """Load a prompt by name. Checks prompts/<channel>/ first, falls back to prompts/."""
    path = _resolve_path(name, channel)
    content = path.read_text(encoding="utf-8").strip()
    source = f"{channel}/{name}" if channel and path.parent.name == channel else name
    logger.debug(f"Loaded prompt: {source} ({len(content)} chars)")
    return content


def render_prompt(name: str, channel: str = None, **variables) -> str:
    """Load a prompt and substitute $variable placeholders."""
    template_str = load_prompt(name, channel=channel)
    try:
        return Template(template_str).safe_substitute(**variables)
    except Exception as e:
        logger.error(f"Failed to render prompt {name}: {e}")
        return template_str


def list_prompts(channel: str = None) -> dict:
    """
    Return available prompts. Shows global defaults and any channel-specific overrides.
    """
    global_prompts = [p.stem for p in PROMPT_DIR.glob("*.md")]
    result: dict = {"global": sorted(global_prompts)}

    if channel:
        channel_dir = PROMPT_DIR / channel
        if channel_dir.exists():
            overrides = [p.stem for p in channel_dir.glob("*.md")]
            result["channel_overrides"] = sorted(overrides)
        else:
            result["channel_overrides"] = []
            result["channel_prompts_dir"] = str(channel_dir)
            result["note"] = f"Create prompts/{channel}/ and add .md files to override defaults for this channel."

    return result
