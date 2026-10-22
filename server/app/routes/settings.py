import re

from fastapi import APIRouter, HTTPException

from app.enums import color_hex
from common.structs import ProxyType, Tag, TagHighlight, TimelineEventType
from modules import api, colors, db, globals

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
BOOL_KEYS = {
    "refresh_archived_games",
    "refresh_completed_games",
    "check_notifs",
    "previews_enabled",
    "confirm_on_remove",
    "mark_installed_after_add",
    "default_tab_is_new",
    "highlight_tags",
    "insecure_ssl",
}
INT_RANGES = {
    "max_connections": (1, 64),
    "max_retries": (0, 20),
    "request_timeout": (1, 300),
    "image_timeout": (1, 300),
    "bg_refresh_interval": (0, 1440),
    "style_corner_radius": (0, 40),
    "proxy_port": (0, 65535),
}
PROXY_KEYS = {"proxy_type", "proxy_host", "proxy_port"}
HEX_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


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


def _bad(message: str):
    raise HTTPException(status_code=400, detail=message)


def _convert(key, value):
    if key in COLOR_KEYS:
        if not isinstance(value, str) or not HEX_COLOR.match(value):
            _bad(f"{key} must be a #rrggbb or #rrggbbaa colour")
        return colors.hex_to_rgba_0_1(value.lower())
    if key in BOOL_KEYS:
        if not isinstance(value, bool):
            _bad(f"{key} must be a boolean")
        return value
    if key in INT_RANGES:
        low, high = INT_RANGES[key]
        if type(value) is not int or not low <= value <= high:
            _bad(f"{key} must be an integer from {low} to {high}")
        return value
    if key == "proxy_type":
        try:
            return ProxyType(value)
        except (ValueError, TypeError):
            _bad("Unknown proxy_type")
    if key == "proxy_host":
        if not isinstance(value, str):
            _bad("proxy_host must be a string")
        return value
    if key == "hidden_timeline_events":
        if not isinstance(value, list):
            _bad("hidden_timeline_events must be a list")
        try:
            events = [TimelineEventType(item) for item in value]
        except (ValueError, TypeError):
            _bad("Unknown timeline event type")
        return sorted(set(events), key=int)
    if key == "tags_highlights":
        if not isinstance(value, dict):
            _bad("tags_highlights must be an object")
        try:
            return {
                Tag(int(tag)): TagHighlight(int(highlight))
                for tag, highlight in value.items()
            }
        except (ValueError, TypeError):
            _bad("Unknown tag or tag highlight")
    _bad(f"Unknown setting: {key}")


@router.get("")
async def get_settings():
    return {key: _value(key) for key in KEYS}


@router.patch("")
async def update_settings(payload: dict):
    unknown = set(payload) - set(KEYS)
    if unknown:
        _bad(f"Unknown setting(s): {', '.join(sorted(unknown))}")

    changes = {key: _convert(key, value) for key, value in payload.items()}
    for key, value in changes.items():
        setattr(globals.settings, key, value)
    if changes:
        await db.update_settings(*changes)
        await db.save()
    if PROXY_KEYS & set(changes):
        api.make_session()
    return {key: _value(key) for key in KEYS}
