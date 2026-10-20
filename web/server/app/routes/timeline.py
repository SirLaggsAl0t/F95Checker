from fastapi import APIRouter

from app.enums import enum_ref
from modules import globals

router = APIRouter(prefix="/api/timeline", tags=["timeline"])


@router.get("")
async def get_timeline():
    hidden = set(globals.settings.hidden_timeline_events)
    events = [
        {
            "game_id": event.game_id,
            "game_name": game.name,
            "timestamp": int(event.timestamp.value),
            "arguments": list(event.arguments),
            "type": enum_ref(event.type),
        }
        for game in globals.games.values()
        for event in game.timeline_events
        if event.type not in hidden
    ]
    events.sort(key=lambda event: event["timestamp"], reverse=True)
    return events
