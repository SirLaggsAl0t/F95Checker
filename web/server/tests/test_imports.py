import sqlite3
import time

from fastapi.testclient import TestClient

from app import config
from app.main import app
from common.structs import ThreadMatch
from modules import api

BOOKMARKS = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<html><body>
<a href="https://f95zone.to/threads/bookmark-one.940101/">One</a>
<a href="https://f95zone.to/threads/bookmark-two.940102/">Two</a>
<a href="https://example.com/not-a-thread">Nope</a>
</body></html>
"""


def wait_for(condition, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return
        time.sleep(0.02)
    raise AssertionError("condition not met in time")


def cleanup(*ids):
    connection = sqlite3.connect(config.DB_PATH)
    connection.execute(f"DELETE FROM games WHERE id IN ({','.join('?' * len(ids))})", ids)
    connection.execute(f"DELETE FROM timeline_events WHERE game_id IN ({','.join('?' * len(ids))})", ids)
    connection.commit()
    connection.close()


def test_import_threads_dedupes_and_queues_one_refresh(monkeypatch):
    calls = []

    async def fake_refresh(*games, **kwargs):
        calls.append(([game.id for game in games], kwargs))

    monkeypatch.setattr("app.refresh_job.api.refresh", fake_refresh)
    text = (
        "https://f95zone.to/threads/import-one.940001/\n"
        "https://f95zone.to/threads/import-one.940001/\n"
        "https://f95zone.to/threads/import-two.940002/"
    )
    try:
        with TestClient(app) as client:
            res = client.post("/api/imports/threads", json={"text": text})
            assert res.status_code == 200
            body = res.json()
            assert sorted(game["id"] for game in body["added"]) == [940001, 940002]
            wait_for(lambda: calls)
            assert calls == [([940001, 940002], {"full": True, "notifs": False, "notify": False})]
    finally:
        cleanup(940001, 940002)


def test_import_threads_requires_links():
    with TestClient(app) as client:
        assert client.post("/api/imports/threads", json={"text": "nothing here"}).status_code == 400


def test_import_browser_bookmarks(monkeypatch):
    calls = []

    async def fake_refresh(*games, **kwargs):
        calls.append([game.id for game in games])

    monkeypatch.setattr("app.refresh_job.api.refresh", fake_refresh)
    try:
        with TestClient(app) as client:
            res = client.post("/api/imports/bookmarks", json={"html": BOOKMARKS})
            assert res.status_code == 200
            assert sorted(game["id"] for game in res.json()["added"]) == [940101, 940102]
            wait_for(lambda: calls)
            assert calls == [[940101, 940102]]
    finally:
        cleanup(940101, 940102)


def test_import_f95_watched(monkeypatch):
    calls = []

    async def fake_watched():
        return [ThreadMatch(title="", id=940201), ThreadMatch(title="", id=940201)]

    async def fake_refresh(*games, **kwargs):
        calls.append([game.id for game in games])

    monkeypatch.setattr(api, "import_f95_watched_threads", fake_watched)
    monkeypatch.setattr("app.refresh_job.api.refresh", fake_refresh)
    try:
        with TestClient(app) as client:
            res = client.post("/api/imports/f95-watched")
            assert res.status_code == 200
            assert [game["id"] for game in res.json()["added"]] == [940201]
            wait_for(lambda: calls)
            assert calls == [[940201]]
    finally:
        cleanup(940201)


def test_import_skips_existing_games(monkeypatch):
    async def fake_refresh(*games, **kwargs):
        pass

    monkeypatch.setattr("app.refresh_job.api.refresh", fake_refresh)
    try:
        with TestClient(app) as client:
            first = client.post("/api/imports/threads", json={"text": "threads/first.940301/"})
            assert first.status_code == 200
            second = client.post("/api/imports/threads", json={"text": "threads/first.940301/"})
            assert second.status_code == 200
            assert second.json()["added"] == []
            assert second.json()["skipped"] == [{"id": 940301, "reason": "Already in library"}]
    finally:
        cleanup(940301)
