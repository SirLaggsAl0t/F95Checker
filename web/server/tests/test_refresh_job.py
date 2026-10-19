import asyncio
import time

from fastapi.testclient import TestClient

from app.main import app
from app.refresh_job import RefreshJob, job
from modules import globals


def wait_for(condition, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return
        time.sleep(0.02)
    raise AssertionError("condition not met in time")


def test_status_snapshots_errors_and_missing_threads(monkeypatch):
    import types

    globals.games[2] = types.SimpleNamespace(name="Two")

    async def fake_refresh(*games, **kwargs):
        globals.api_errors["RuntimeError: boom"] = {2}
        globals.missing_threads.update([3])

    monkeypatch.setattr("app.refresh_job.api.refresh", fake_refresh)

    async def scenario():
        local = RefreshJob()
        local.start()
        try:
            local.enqueue([1, 2], full=True)
            await asyncio.to_thread(wait_for, lambda: local.last_result is not None)
            return local.status()
        finally:
            await local.stop()

    try:
        status = asyncio.run(scenario())
    finally:
        globals.games.pop(2, None)
    assert status["state"] == "idle"
    assert status["errors"] == [{"game_id": 2, "name": "Two", "msg": "RuntimeError: boom"}]
    assert status["missing_threads"] == [3]


def test_fatal_run_error_is_one_job_error(monkeypatch):
    async def fake_refresh(*games, **kwargs):
        raise RuntimeError("fatal")

    monkeypatch.setattr("app.refresh_job.api.refresh", fake_refresh)
    with TestClient(app) as client:
        client.post("/api/refresh")
        wait_for(lambda: client.get("/api/refresh/status").json()["last_result"] is not None)
        status = client.get("/api/refresh/status").json()
    assert status["state"] == "idle"
    assert status["errors"] == [{"game_id": None, "name": None, "msg": "RuntimeError: fatal"}]


def test_manual_refresh_conflict_while_running(monkeypatch):
    monkeypatch.setattr(job, "running", True)
    with TestClient(app) as client:
        res = client.post("/api/refresh")
    assert res.status_code == 409


def test_refresh_queue_merges_pending_adds():
    async def scenario():
        local = RefreshJob()
        local.queue = asyncio.Queue()
        local.enqueue([1], full=True)
        local.enqueue([2, 1], full=True)
        local.enqueue([3], full=False)
        requests = [local.queue.get_nowait() for _ in range(2)]
        return requests

    first, second = asyncio.run(scenario())
    assert first.ids == [1, 2]
    assert first.full is True
    assert second.ids == [3]
    assert second.full is False
