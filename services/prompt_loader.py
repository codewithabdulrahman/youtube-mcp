from pathlib import Path
from string import Template
from config.settings import BASE_DIR
from services.logger import get_logger

logger = get_logger("prompt_loader")

PROMPT_DIR = BASE_DIR / "prompts"


def _resolve_path(name: str, channel: str) -> Path:
    """Find a prompt file at prompts/<channel>/<name>.md. Each channel must have its own folder."""
    channel_path = PROMPT_DIR / channel / f"{name}.md"
    if channel_path.exists():
        return channel_path

    raise FileNotFoundError(
        f"Prompt '{name}' not found for channel '{channel}'. "
        f"Expected at prompts/{channel}/{name}.md — "
        f"create prompts/{channel}/ and add the required .md files."
    )


def load_prompt(name: str, channel: str) -> str:
    """Load a prompt from prompts/<channel>/<name>.md."""
    path = _resolve_path(name, channel)
    content = path.read_text(encoding="utf-8").strip()
    logger.debug(f"Loaded prompt: {channel}/{name} ({len(content)} chars)")
    return content


def render_prompt(name: str, channel: str, **variables) -> str:
    """Load a prompt and substitute $variable placeholders."""
    template_str = load_prompt(name, channel)
    try:
        return Template(template_str).safe_substitute(**variables)
    except Exception as e:
        logger.error(f"Failed to render prompt {name}: {e}")
        return template_str


def list_prompts(channel: str) -> dict:
    """Return available prompts for a channel."""
    channel_dir = PROMPT_DIR / channel
    if channel_dir.exists():
        prompts = [p.stem for p in channel_dir.glob("*.md")]
        return {"channel": channel, "prompts": sorted(prompts)}
    else:
        return {
            "channel": channel,
            "prompts": [],
            "note": f"No prompt folder found. Create prompts/{channel}/ and add research.md, script.md, visuals.md, thumbnail.md, title.md, description.md.",
        }
