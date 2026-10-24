import sqlite3
import time

from fastapi.testclient import TestClient

from app import config
from app.main import app
from common.structs import SearchResult
from modules import api, globals


def wait_for(condition, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return
        time.sleep(0.02)
    raise AssertionError("condition not met in time")


def test_add_games_enqueues_one_full_refresh(monkeypatch):
    calls = []

    async def fake_refresh(*games, **kwargs):
        calls.append(([game.id for game in games], kwargs))

    monkeypatch.setattr("app.refresh_job.api.refresh", fake_refresh)
    game_id = 910001
    with TestClient(app) as client:
        res = client.post("/api/games", json={"url": f"https://f95zone.to/threads/test-game.{game_id}/"})
        assert res.status_code == 201
        body = res.json()
        assert [game["id"] for game in body["added"]] == [game_id]
        assert body["added"][0]["name"] == "test-game"
        assert body["skipped"] == []

        wait_for(lambda: client.get("/api/refresh/status").json()["last_result"] is not None)

        dupe = client.post("/api/games", json={"ids": [game_id, game_id]})
        assert dupe.status_code == 201
        assert dupe.json()["added"] == []
        assert dupe.json()["skipped"] == [{"id": game_id, "reason": "Already in library"}]

        assert calls == [([game_id], {"full": True, "notifs": False, "notify": False})]

    # Keep the shared test database empty for the read-only route tests.
    connection = sqlite3.connect(config.DB_PATH)
    connection.execute("DELETE FROM games WHERE id=?", (game_id,))
    connection.commit()
    connection.close()


def test_add_games_requires_a_thread(monkeypatch):
    with TestClient(app) as client:
        res = client.post("/api/games", json={"url": "not a thread"})
    assert res.status_code == 400


def test_search_marks_library_games(monkeypatch):
    async def fake_search(category, search, query, page=1):
        return [SearchResult(title="Found", creator="Dev", url="https://f95zone.to/threads/1/", id=920001)]

    monkeypatch.setattr(api, "latest_updates_search", fake_search)
    with TestClient(app) as client:
        res = client.get("/api/search", params={"q": "found game"})
    assert res.status_code == 200
    assert res.json() == [{
        "id": 920001,
        "title": "Found",
        "creator": "Dev",
        "in_list": False,
    }]


def test_search_stopword_only_query_returns_empty(monkeypatch):
    async def fail(*args, **kwargs):
        raise AssertionError("search should not be called")

    monkeypatch.setattr(api, "latest_updates_search", fail)
    with TestClient(app) as client:
        assert client.get("/api/search", params={"q": "the a is"}).json() == []
