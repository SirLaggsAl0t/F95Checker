import typing

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import images, refresh_job
from app.serialize import game_detail, game_summary
from common.structs import Label, Status, Tab, ThreadMatch, Type
from modules import db, globals, utils

router = APIRouter(prefix="/api/games", tags=["games"])

EDITABLE = {
    "name", "version", "developer", "type", "status", "rating", "notes",
    "installed", "finished", "archived", "updated", "favourite", "tab", "labels",
}


class AddGamesRequest(BaseModel):
    url: str | None = None
    id: int | None = None
    ids: list[int] | None = None


class ConvertRequest(BaseModel):
    id: int


def get_or_404(game_id: int):
    game = globals.games.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


def bad_request(message: str):
    raise HTTPException(status_code=400, detail=message)


def validate_patch(payload: dict) -> dict:
    unknown = set(payload) - EDITABLE
    if unknown:
        bad_request(f"Unknown field(s): {', '.join(sorted(unknown))}")
    changes: dict[str, typing.Any] = {}
    for key, value in payload.items():
        if key in ("name", "version", "developer", "notes"):
            if not isinstance(value, str):
                bad_request(f"{key} must be a string")
        elif key in ("type", "status"):
            enum = Type if key == "type" else Status
            try:
                value = enum(value)
            except (ValueError, TypeError):
                bad_request(f"Unknown {key} value")
        elif key == "rating":
            if type(value) is not int or not 0 <= value <= 5:
                bad_request("rating must be an integer from 0 to 5")
        elif key in ("installed", "finished"):
            if not isinstance(value, str):
                bad_request(f"{key} must be a string")
        elif key in ("archived", "updated", "favourite"):
            if not isinstance(value, bool):
                bad_request(f"{key} must be a boolean")
        elif key == "tab":
            if value is None:
                pass
            elif Tab.get(value) is None:
                bad_request("Unknown tab")
            else:
                value = Tab.get(value)
        elif key == "labels":
            if not isinstance(value, list) or any(type(item) is not int for item in value):
                bad_request("labels must be a list of label ids")
            labels = [Label.get(item) for item in value]
            if any(label is None for label in labels) or len(set(value)) != len(value):
                bad_request("Unknown or duplicate label")
            value = sorted(labels, key=lambda label: label.position)
        changes[key] = value
    return changes


@router.get("")
async def list_games():
    games = sorted(globals.games.values(), key=lambda game: game.name.casefold())
    return [game_summary(game) for game in games]


async def add_games_by_threads(threads: list[ThreadMatch]):
    """Add every thread not already in the library, then queue one refresh."""
    added = []
    skipped = []
    seen = set()
    for thread in threads:
        game_id = thread.id
        if game_id <= 0 or game_id in seen:
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
    return added, skipped


@router.post("", status_code=201)
async def add_games(payload: AddGamesRequest):
    threads = []
    if payload.url:
        threads += utils.extract_thread_matches(payload.url)
    if payload.id is not None:
        threads.append(ThreadMatch(title="", id=payload.id))
    for game_id in payload.ids or []:
        threads.append(ThreadMatch(title="", id=game_id))
    if not any(thread.id > 0 for thread in threads):
        raise HTTPException(status_code=400, detail="No thread id found")

    added, skipped = await add_games_by_threads(threads)
    return {"added": [game_summary(game) for game in added], "skipped": skipped}


@router.post("/custom", status_code=201)
async def add_custom_game():
    game_id = await db.create_game(custom=True)
    await db.load_games(game_id)
    await db.save()
    return game_summary(globals.games[game_id])


@router.post("/{game_id}/convert")
async def convert_game(game_id: int, payload: ConvertRequest):
    game = get_or_404(game_id)
    if payload.id in globals.games:
        raise HTTPException(status_code=409, detail="Game already in library")
    await db.update_game_id(game, payload.id)
    game.custom = False
    game.status = Status.Unchecked
    await db.update_game(game, "custom", "status")
    await db.save()
    return game_summary(game)


@router.patch("/{game_id}")
async def update_game(game_id: int, payload: dict):
    game = get_or_404(game_id)
    changes = validate_patch(payload)
    for key, value in changes.items():
        setattr(game, key, value)
    keys = list(changes)
    if "version" in changes or "installed" in changes:
        game.updated = bool(game.installed) and game.installed != game.version
        keys.append("updated")
    if keys:
        await db.update_game(game, *keys)
        await db.save()
    return game_summary(game)


@router.delete("/{game_id}", status_code=204)
async def delete_game(game_id: int):
    game = get_or_404(game_id)
    game.delete_images(cover_only=False)
    for thumb in images.CACHE_DIR.glob(f"{game_id}-*.webp"):
        try:
            thumb.unlink()
        except OSError:
            pass
    await db.delete_timeline_events(game_id)
    await db.delete_game(game_id)
    globals.games.pop(game_id, None)
    await db.save()


@router.get("/{game_id}")
async def get_game(game_id: int):
    return game_detail(get_or_404(game_id))
