from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import refresh_job
from app.serialize import game_detail, game_summary
from common.structs import ThreadMatch
from modules import db, globals, utils

router = APIRouter(prefix="/api/games", tags=["games"])


class AddGamesRequest(BaseModel):
    url: str | None = None
    id: int | None = None
    ids: list[int] | None = None


@router.get("")
async def list_games():
    games = sorted(globals.games.values(), key=lambda game: game.name.casefold())
    return [game_summary(game) for game in games]


@router.post("", status_code=201)
async def add_games(payload: AddGamesRequest):
    threads = []
    if payload.url:
        threads += utils.extract_thread_matches(payload.url)
    if payload.id is not None:
        threads.append(ThreadMatch(title="", id=payload.id))
    for game_id in payload.ids or []:
        threads.append(ThreadMatch(title="", id=game_id))
    threads = [thread for thread in threads if thread.id > 0]
    if not threads:
        raise HTTPException(status_code=400, detail="No thread id found")

    added = []
    skipped = []
    seen = set()
    for thread in threads:
        game_id = thread.id
        if game_id in seen:
            continue
        seen.add(game_id)
        if game_id in globals.games:
            skipped.append({"id": game_id, "reason": "Already in library"})
            continue
        await db.create_game(thread)
        await db.load_games(game_id)
        game = globals.games[game_id]
        if globals.settings.mark_installed_after_add:
            game.installed = game.version
            await db.update_game(game, "installed")
        added.append(game)
    await db.save()

    if added:
        refresh_job.job.enqueue([game.id for game in added], full=True)
    return {"added": [game_summary(game) for game in added], "skipped": skipped}


@router.get("/{game_id}")
async def get_game(game_id: int):
    game = globals.games.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return game_detail(game)
