"""Shared request validation for the API routes."""
import re

from fastapi import HTTPException

from modules import colors

HEX_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


def bad_request(message: str):
    raise HTTPException(status_code=400, detail=message)


def text_value(key: str, value, max_length: int | None = None) -> str:
    if not isinstance(value, str):
        bad_request(f"{key} must be a string")
    if max_length is not None and len(value) > max_length:
        bad_request(f"{key} is too long")
    return value


def color_value(key: str, value, nullable: bool = False, message: str | None = None):
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not HEX_COLOR.fullmatch(value):
        bad_request(message or f"{key} must be a #rrggbb colour")
    return colors.hex_to_rgba_0_1(value.lower())
