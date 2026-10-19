# VENDORED from modules/ - GUI stripped for the web server; see web/
import functools
import io
import random
import re
import string

from PIL import Image

from common.structs import (
    ThreadMatch,
)
from modules import (
    api,
    globals,
)

# VENDORED: no GUI modules headless; the GUI-only functions below (popup,
# push_popup, text_context, ...) are never called by the server
imgui = None
glfw = None


@functools.cache
def bayesian_average(avg_rating, num_votes):
    W, C = 100, 0
    return ((num_votes * avg_rating) + (W * C)) / (num_votes + W)


def rand_num_str(len=8):
    return "".join((random.choice('0123456789') for _ in range(len)))


def clean_str(text: str):
    clean_charset = string.ascii_letters + string.digits + " "
    clean_text = "".join(char for char in text.replace("&", "and") if char in clean_charset)
    clean_text = re.sub(r"\s+", r" ", clean_text).strip()
    return clean_text


# https://stackoverflow.com/a/1094933
# Edited to always return at most 4 digit characters, eg:
#  1.0MiB
# 10.0MiB
#  100MiB
# 1000MiB
# Makes it trivial to align by left-padding to 7 characters
def sizeof_fmt(num, suffix="B"):
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            if num < 100.0:
                num = round(num, 1)
            else:
                num = int(num)
            return f"{num}{unit}{suffix}"
        num /= 1024.0
    if num < 100.0:
        num = round(num, 1)
    else:
        num = int(num)
    return f"{num}Yi{suffix}"


@functools.cache
def map_range(in_value: float, in_start: float, in_end: float, out_start: float, out_end: float):
    in_value -= in_start
    in_end -= in_start
    in_start = 0.0
    out_range = out_end - out_start
    out_value = ((in_value / in_end) * out_range) + out_start
    return out_value


def image_ext(data: bytes):
    try:
        ext = str(Image.open(io.BytesIO(data)).format or "img").lower()
    except Exception:
        ext = "img"
    return ext


def custom_id():
    if globals.games:
        return min(min(game.id for game in globals.games.values()), 0) - 1
    else:
        return -1


def is_uri(text: str):
    # See https://www.rfc-editor.org/rfc/rfc3986#section-3.1
    return bool(re.search(r"^[A-Za-z][A-Za-z0-9\+\-\.]*://", text))


def is_refreshing():
    if globals.refresh_task and not globals.refresh_task.done():
        return True
    return False


@functools.cache
def clean_thread_url(url: str):
    thread = re.search(r"threads/([^/]*)", url).group(1)
    return f"{api.f95_threads_page}{thread}/"


def extract_thread_matches(text: str) -> list[ThreadMatch]:
    matches = []
    if not isinstance(text, str):
        return matches
    for match in re.finditer(r"threads/(?:([^\./]*)\.)?(\d+)", text):
        matches.append(ThreadMatch(title=match.group(1) or "", id=int(match.group(2))))
    return matches


# VENDORED: desktop popup helpers (popup, push_popup, text_context, geometry)
# are deleted headless; the web server returns errors as HTTP responses
