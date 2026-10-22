import email.utils
import hashlib
import pathlib

import aiofiles
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, Response

from app import images
from modules import globals, utils

router = APIRouter(prefix="/api", tags=["images"])

MEDIA_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".avif": "image/avif",
}


def _media_type(path: pathlib.Path) -> str:
    return MEDIA_TYPES.get(path.suffix.lower(), "application/octet-stream")


def _not_modified(request: Request, etag: str, mtime: float) -> bool:
    if request.headers.get("if-none-match") == etag:
        return True
    since = request.headers.get("if-modified-since")
    if since:
        try:
            return mtime <= email.utils.parsedate_to_datetime(since).timestamp()
        except (TypeError, ValueError):
            pass
    return False


def _image_response(request: Request, path: pathlib.Path, etag: str, cache_control: str):
    stat = path.stat()
    headers = {
        "ETag": etag,
        "Cache-Control": cache_control,
        "Content-Disposition": "inline",
    }
    if _not_modified(request, etag, stat.st_mtime):
        return Response(status_code=304, headers=headers)
    headers["Last-Modified"] = email.utils.formatdate(stat.st_mtime, usegmt=True)
    return FileResponse(path, media_type=_media_type(path), headers=headers)


def _get_game(game_id: int):
    game = globals.games.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.get("/images/{game_id}")
async def cover(game_id: int, request: Request, w: int | None = None):
    if w is not None and w not in images.THUMB_WIDTHS:
        raise HTTPException(status_code=400, detail="w must be 320 or 640")
    game = _get_game(game_id)
    path = await images.ensure_cover(game)
    if path is None:
        raise HTTPException(status_code=404, detail="No image")

    if w is not None:
        path = await images.thumb_path(game_id, path, w)
    stat = path.stat()
    etag = f'"{game_id}-{stat.st_mtime_ns}-{stat.st_size}-{w or "orig"}"'
    # Covers are replaced on refresh, so always revalidate.
    return _image_response(request, path, etag, "no-cache")


def _preview_digest(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


def _preview_dir(game_id: int) -> pathlib.Path:
    return globals.images_path / "previews" / str(game_id)


def _preview_file(game_id: int, digest: str):
    paths = list(_preview_dir(game_id).glob(f"{digest}.*"))
    paths.sort(key=lambda path: path.suffix.lower() in images.DECODABLE, reverse=True)
    return paths[0] if paths else None


@router.get("/games/{game_id}/previews")
async def previews(game_id: int):
    # Phase 5 flag: routes exist now, the gallery UI comes later.
    if not globals.settings.previews_enabled:
        raise HTTPException(status_code=404, detail="Previews disabled")
    game = _get_game(game_id)
    return [
        {"index": index, "url": f"/api/games/{game_id}/previews/{index}"}
        for index, _ in enumerate(game.previews_urls)
    ]


@router.get("/games/{game_id}/previews/{index}")
async def preview(game_id: int, index: int, request: Request):
    if not globals.settings.previews_enabled:
        raise HTTPException(status_code=404, detail="Previews disabled")
    game = _get_game(game_id)
    if not 0 <= index < len(game.previews_urls):
        raise HTTPException(status_code=404, detail="Preview not found")

    url = game.previews_urls[index]
    digest = _preview_digest(url)
    path = _preview_file(game_id, digest)
    if path is None and url.startswith(("http://", "https://")):
        data, _ = await images.download(url)
        if data:
            directory = _preview_dir(game_id)
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / f"{digest}.{utils.image_ext(data)}"
            async with aiofiles.open(path, "wb") as file:
                await file.write(data)
    if path is None:
        raise HTTPException(status_code=404, detail="Preview not found")

    stat = path.stat()
    etag = f'"{digest}-{stat.st_size}"'
    # Content-addressed file names never change.
    return _image_response(request, path, etag, "public, max-age=31536000, immutable")
