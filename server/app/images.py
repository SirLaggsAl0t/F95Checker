"""Browser-decodable cover images and web-only thumbnail cache."""
import asyncio
import time

from PIL import Image, ImageOps

from app import config
from modules import api, globals

# .astc.ktx.zst / .bc7.ktx.zst are not browser-decodable; anything containing
# .zst is skipped on purpose (the desktop may keep it as the only cover).
DECODABLE = {".gif", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".avif"}
PRIORITY = {".gif": 0, ".png": 1, ".jpg": 2, ".jpeg": 3, ".webp": 4, ".bmp": 5, ".avif": 6}
THUMB_WIDTHS = (320, 640)

CACHE_DIR = config.DATA_DIR / "web-cache" / "covers"

_download_sem = asyncio.Semaphore(4)
_negative_cache: dict[str, float] = {}
NEGATIVE_TTL = 60.0


def cover_path(game_id: int):
    """Canonical cover file the browser can decode, or None."""
    paths = [p for p in globals.images_path.glob(f"{game_id}.*") if ".zst" not in p.name and p.suffix.lower() in DECODABLE]
    if not paths:
        return None
    paths.sort(key=lambda p: (PRIORITY[p.suffix.lower()], p.name))
    return paths[0]


async def download(url: str):
    """One shared download semaphore for covers and previews."""
    async with _download_sem:
        return await api.download_image(url)


async def ensure_cover(game):
    """Return a decodable cover path, downloading the image_url once if needed."""
    path = cover_path(game.id)
    if path is not None:
        return path

    url = getattr(game, "image_url", "") or ""
    if not url.startswith(("http://", "https://")):
        return None

    now = time.monotonic()
    if _negative_cache.get(url, 0.0) > now:
        return None

    data, _ = await download(url)
    if not data:
        _negative_cache[url] = now + NEGATIVE_TTL
        return None

    await game.set_image_async(data)
    return cover_path(game.id)


def _make_thumb(source, destination, width: int):
    with Image.open(source) as image:
        image.seek(0)
        image = ImageOps.exif_transpose(image)
        image.thumbnail((width, width * 4), Image.Resampling.LANCZOS)
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
        destination.parent.mkdir(parents=True, exist_ok=True)
        image.save(destination, "WEBP", quality=80)


async def thumb_path(game_id: int, source, width: int):
    stat = source.stat()
    destination = CACHE_DIR / f"{game_id}-{stat.st_mtime_ns}-{stat.st_size}-{width}.webp"
    if not destination.is_file():
        await asyncio.to_thread(_make_thumb, source, destination, width)
        # Drop derivatives from older cover revisions, keep the other width.
        current = f"{game_id}-{stat.st_mtime_ns}-{stat.st_size}-"
        for stale in CACHE_DIR.glob(f"{game_id}-*.webp"):
            if not stale.name.startswith(current):
                try:
                    stale.unlink()
                except OSError:
                    pass
    return destination


def image_version(game_id: int) -> str:
    path = cover_path(game_id)
    if path is None:
        return ""
    stat = path.stat()
    return f"{stat.st_mtime_ns}-{stat.st_size}"
