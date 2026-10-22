import asyncio
import json
import os
import pathlib
import socket
import sys
import tempfile
import threading
import time

import pytest

server_dir = pathlib.Path(__file__).resolve().parents[1] / "server"
repo_root = server_dir.parent

# Same isolation as server/tests/conftest.py: the server must only see the
# vendored packages, never whatever the repo root puts on sys.path.
sys.path[:] = [p for p in sys.path if pathlib.Path(p or ".").resolve() != repo_root]
sys.path.insert(0, str(server_dir))
sys.path.insert(0, str(server_dir / "vendor"))

# Throwaway data dir before the vendored modules/globals.py is imported.
os.environ["F95CHECKER_DATA_DIR"] = tempfile.mkdtemp(prefix="f95checker-e2e-")

from app.main import app  # noqa: E402
from common.structs import SearchResult  # noqa: E402
from modules import api, globals  # noqa: E402

client_dist = server_dir.parent / "client" / "dist"


class FakeNetwork:
    """Server-layer network mock: no F95zone or indexer requests in e2e."""

    def __init__(self):
        self.refresh_calls: list[tuple[list[int], dict]] = []
        self.errors: dict[int, str] = {}
        self.missing_threads: list[int] = []
        self.search_results: list[SearchResult] = []

    async def refresh(self, *games, **kwargs):
        ids = [game.id for game in games] or list(globals.games)
        self.refresh_calls.append((ids, kwargs))
        globals.refresh_total = len(ids)
        globals.refresh_progress = 0
        for _ in ids:
            await asyncio.sleep(0.05)
            globals.refresh_progress += 1
        globals.api_errors.clear()
        globals.missing_threads.clear()
        for game_id, message in self.errors.items():
            globals.api_errors.setdefault(message, set()).add(game_id)
        globals.missing_threads.update(self.missing_threads)

    async def latest_updates_search(self, category, search, query, sort="likes", count=15, page=1):
        return list(self.search_results)


@pytest.fixture(scope="session")
def network():
    fake = FakeNetwork()
    # refresh_job looks these up on the modules.api object on every call.
    api.refresh = fake.refresh
    api.latest_updates_search = fake.latest_updates_search
    return fake


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def server(network):
    if not (client_dist / "index.html").is_file():
        pytest.skip("client not built: run `pnpm run build` in client")
    import uvicorn

    port = _free_port()
    http_server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    )
    thread = threading.Thread(target=http_server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 15
    while not http_server.started:
        if time.monotonic() > deadline:
            raise RuntimeError("e2e server did not start")
        time.sleep(0.02)
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        http_server.should_exit = True
        thread.join(timeout=10)


@pytest.fixture(scope="session")
def base_url(server):
    return server


@pytest.fixture
def add_game(base_url, page):
    def status():
        return page.request.get(f"{base_url}/api/refresh/status").json()

    def _add(thread_url: str) -> int:
        before = status()["started"]
        response = page.request.post(
            f"{base_url}/api/games",
            data=json.dumps({"url": thread_url}),
            headers={"Content-Type": "application/json"},
        )
        assert response.ok, response.text()
        game_id = response.json()["added"][0]["id"]
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            current = status()
            if current["state"] == "idle" and current["started"] != before:
                return game_id
            time.sleep(0.05)
        raise AssertionError("add refresh did not finish")

    return _add


@pytest.fixture
def wait_idle(base_url, page):
    def _wait(timeout=15.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if page.request.get(f"{base_url}/api/refresh/status").json()["state"] == "idle":
                return
            time.sleep(0.05)
        raise AssertionError("refresh did not finish")

    return _wait
