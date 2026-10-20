import types

from fastapi.testclient import TestClient

from app.main import app
from common.structs import TimelineEvent, TimelineEventType, Timestamp
from modules import globals


def test_timeline_is_sorted_and_honours_hidden_events():
    old_hidden = globals.settings.hidden_timeline_events
    game = types.SimpleNamespace(
        name="Game",
        timeline_events=[
            TimelineEvent(5, Timestamp(100), [], TimelineEventType.GameAdded),
            TimelineEvent(5, Timestamp(300), ["1.1"], TimelineEventType.ChangedVersion),
            TimelineEvent(5, Timestamp(200), [], TimelineEventType.RecheckUserReq),
        ],
    )
    globals.settings.hidden_timeline_events = []
    try:
        with TestClient(app) as client:
            globals.settings.hidden_timeline_events = []
            globals.games[5] = game
            events = client.get("/api/timeline").json()
            assert [event["timestamp"] for event in events] == [300, 200, 100]
            assert events[0]["game_name"] == "Game"
            assert events[0]["type"]["name"] == "ChangedVersion"

            globals.settings.hidden_timeline_events = [TimelineEventType.RecheckUserReq]
            events = client.get("/api/timeline").json()
            assert [event["timestamp"] for event in events] == [300, 100]
    finally:
        globals.settings.hidden_timeline_events = old_hidden
        globals.games.pop(5, None)
