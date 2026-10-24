"""Runtime enum metadata for the client.

The vendored enums already carry display metadata as attributes, so there is no
hand-maintained enum copy on the client. Colours are converted from
tuple[float] to CSS hex here, once.
"""
from common.structs import (
    ProxyType,
    Status,
    Tag,
    TagHighlight,
    TimelineEventType,
    Type,
)
from modules.colors import rgba_0_1_to_hex


def color_hex(value) -> str:
    if not value:
        return ""
    hex_color = rgba_0_1_to_hex(tuple(value))
    return hex_color[:7] if hex_color.lower().endswith("ff") else hex_color


def enum_ref(value) -> dict:
    """Value + name + whatever metadata the enum carries."""
    data = {"value": int(value), "name": value.name}
    for attr in ("icon", "color", "text", "display", "template", "category"):
        if hasattr(value, attr):
            item = getattr(value, attr)
            if attr == "color":
                item = color_hex(item)
            elif attr == "category":
                item = item.name
            data[attr] = item
    return data


def all_enums() -> dict:
    result = {}
    for enum in (
        Status,
        Tag,
        TagHighlight,
        TimelineEventType,
        Type,
        ProxyType,
    ):
        result[enum.__name__] = [enum_ref(member) for member in enum]
    return result
