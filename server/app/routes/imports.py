"""Import games from pasted threads, bookmarks HTML, or F95zone bookmarks/watched."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.routes.games import add_games_by_threads
from app.serialize import game_summary
from modules import api, utils

router = APIRouter(prefix="/api/imports", tags=["imports"])


class ThreadsImport(BaseModel):
    text: str


class BookmarksImport(BaseModel):
    html: str


async def _import(threads) -> dict:
    added, skipped = await add_games_by_threads(threads)
    return {
        "found": len(threads),
        "added": [game_summary(game) for game in added],
        "skipped": skipped,
    }


@router.post("/threads")
async def import_threads(payload: ThreadsImport):
    threads = utils.extract_thread_matches(payload.text)
    if not threads:
        raise HTTPException(status_code=400, detail="No thread links found")
    return await _import(threads)


@router.post("/bookmarks")
async def import_bookmarks(payload: BookmarksImport):
    threads = await api.import_browser_bookmarks(payload.html)
    if not threads:
        raise HTTPException(status_code=400, detail="No thread links found")
    return await _import(threads)


@router.post("/f95-bookmarks")
async def import_f95_bookmarks():
    threads = await api.import_f95_bookmarks()
    return await _import(threads)


@router.post("/f95-watched")
async def import_f95_watched():
    threads = await api.import_f95_watched_threads()
    return await _import(threads)
