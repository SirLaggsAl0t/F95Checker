from fastapi import APIRouter

from app.enums import color_hex
from modules import globals

router = APIRouter(prefix="/api/settings", tags=["settings"])

# Web-relevant subset only. Desktop-only fields stay server-side.
KEYS = (
    "refresh_archived_games",
    "refresh_completed_games",
    "check_notifs",
    "max_connections",
    "max_retries",
    "request_timeout",
    "image_timeout",
    "previews_enabled",
    "bg_refresh_interval",
    "confirm_on_remove",
    "mark_installed_after_add",
    "default_tab_is_new",
    "hidden_timeline_events",
    "highlight_tags",
    "tags_highlights",
    "style_accent",
    "style_alt_bg",
    "style_bg",
    "style_border",
    "style_corner_radius",
    "style_text",
    "style_text_dim",
    "proxy_type",
    "proxy_host",
    "proxy_port",
    "insecure_ssl",
)

COLOR_KEYS = {"style_accent", "style_alt_bg", "style_bg", "style_border", "style_text", "style_text_dim"}


def _value(key):
    value = getattr(globals.settings, key)
    if key in COLOR_KEYS:
        return color_hex(value)
    if key == "hidden_timeline_events":
        return [int(item) for item in value]
    if key == "tags_highlights":
        return {int(tag): int(highlight) for tag, highlight in value.items()}
    if key == "proxy_type":
        return int(value)
    return value


@router.get("")
async def get_settings():
    return {key: _value(key) for key in KEYS}
