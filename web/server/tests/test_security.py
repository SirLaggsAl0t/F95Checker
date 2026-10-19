import asyncio
import pathlib

from fastapi.responses import FileResponse
from fastapi.testclient import TestClient

from app import main
from app.main import app


def test_cross_origin_mutation_rejected():
    with TestClient(app) as client:
        res = client.post("/api/anything", headers={"Origin": "http://evil.test"})
        assert res.status_code == 403


def test_same_origin_mutation_reaches_routing():
    with TestClient(app) as client:
        res = client.post("/api/anything", headers={"Origin": "http://testserver"})
        assert res.status_code == 405  # middleware let it through; no POST route exists yet


def test_spa_fallback_stays_inside_dist(tmp_path, monkeypatch):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("spa")
    (dist / "app.js").write_text("js")
    (tmp_path / "secret.txt").write_text("secret")
    monkeypatch.setattr(main, "client_dist", dist)

    served = asyncio.run(main.spa_fallback("app.js"))
    assert isinstance(served, FileResponse)
    assert pathlib.Path(served.path) == dist / "app.js"

    escaped = asyncio.run(main.spa_fallback("../secret.txt"))
    assert isinstance(escaped, FileResponse)
    assert pathlib.Path(escaped.path) == dist / "index.html"

    unknown = asyncio.run(main.spa_fallback("nope.js"))
    assert isinstance(unknown, FileResponse)
    assert pathlib.Path(unknown.path) == dist / "index.html"
