from fastapi import APIRouter

from app.enums import color_hex
from app.validate import bad_request, color_value
from common.structs import ProxyType, Tag, TagHighlight, TimelineEventType
from modules import api, db, globals

router = APIRouter(prefix="/api/settings", tags=["settings"])


# Web-relevant subset only. Desktop-only fields stay server-side.
def _bool(key, value):
    if not isinstance(value, bool):
        bad_request(f"{key} must be a boolean")
    return value


def _string(key, value):
    if not isinstance(value, str):
        bad_request(f"{key} must be a string")
    return value


def _integer(low: int, high: int):
    def convert(key, value):
        if type(value) is not int or not low <= value <= high:
            bad_request(f"{key} must be an integer from {low} to {high}")
        return value
    return convert


def _color(key, value):
    return color_value(key, value, message=f"{key} must be a #rrggbb or #rrggbbaa colour")


def _proxy_type(key, value):
    try:
        return ProxyType(value)
    except (ValueError, TypeError):
        bad_request("Unknown proxy_type")


def _timeline_events(key, value):
    if not isinstance(value, list):
        bad_request("hidden_timeline_events must be a list")
    try:
        events = [TimelineEventType(item) for item in value]
    except (ValueError, TypeError):
        bad_request("Unknown timeline event type")
    return sorted(set(events), key=int)


def _tag_highlights(key, value):
    if not isinstance(value, dict):
        bad_request("tags_highlights must be an object")
    try:
        return {
            Tag(int(tag)): TagHighlight(int(highlight))
            for tag, highlight in value.items()
        }
    except (ValueError, TypeError):
        bad_request("Unknown tag or tag highlight")


CONVERTERS = {
    "refresh_archived_games": _bool,
    "refresh_completed_games": _bool,
    "check_notifs": _bool,
    "max_connections": _integer(1, 64),
    "max_retries": _integer(0, 20),
    "request_timeout": _integer(1, 300),
    "image_timeout": _integer(1, 300),
    "previews_enabled": _bool,
    "bg_refresh_interval": _integer(0, 1440),
    "confirm_on_remove": _bool,
    "mark_installed_after_add": _bool,
    "default_tab_is_new": _bool,
    "hidden_timeline_events": _timeline_events,
    "highlight_tags": _bool,
    "tags_highlights": _tag_highlights,
    "style_bg": _color,
    "style_text": _color,
    "proxy_type": _proxy_type,
    "proxy_host": _string,
    "proxy_port": _integer(0, 65535),
    "insecure_ssl": _bool,
}
KEYS = tuple(CONVERTERS)


def _value(key):
    value = getattr(globals.settings, key)
    converter = CONVERTERS[key]
    if converter is _color:
        return color_hex(value)
    if converter is _timeline_events:
        return [int(item) for item in value]
    if converter is _tag_highlights:
        return {int(tag): int(highlight) for tag, highlight in value.items()}
    if converter is _proxy_type:
        return int(value)
    return value


@router.get("")
async def get_settings():
    return {key: _value(key) for key in KEYS}


@router.patch("")
async def update_settings(payload: dict):
    unknown = set(payload) - set(KEYS)
    if unknown:
        bad_request(f"Unknown setting(s): {', '.join(sorted(unknown))}")

    changes = {key: CONVERTERS[key](key, value) for key, value in payload.items()}
    for key, value in changes.items():
        setattr(globals.settings, key, value)
    if changes:
        await db.update_settings(*changes)
        await db.save()
    if "proxy_type" in changes or "proxy_host" in changes or "proxy_port" in changes:
        api.make_session()
    return {key: _value(key) for key in KEYS}
