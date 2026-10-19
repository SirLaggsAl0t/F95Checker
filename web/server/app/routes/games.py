from fastapi import APIRouter, HTTPException

from app.serialize import game_detail, game_summary
from modules import globals

router = APIRouter(prefix="/api/games", tags=["games"])


@router.get("")
async def list_games():
    games = sorted(globals.games.values(), key=lambda game: game.name.casefold())
    return [game_summary(game) for game in games]


@router.get("/{game_id}")
async def get_game(game_id: int):
    game = globals.games.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return game_detail(game)
