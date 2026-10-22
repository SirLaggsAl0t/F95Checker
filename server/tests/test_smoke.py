from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        res = client.get("/api/health")
        assert res.status_code == 200
        body = res.json()
        assert body["ok"] is True
        assert body["data_dir"]
        assert body["db_path"].endswith("db.sqlite3")


def test_unknown_api_is_json_404():
    with TestClient(app) as client:
        res = client.get("/api/does-not-exist")
        assert res.status_code == 404
        assert res.json() == {"detail": "Not Found"}


def test_enums():
    with TestClient(app) as client:
        res = client.get("/api/enums")
        assert res.status_code == 200
        body = res.json()
        assert {"DisplayMode", "Status", "Tag", "TimelineEventType", "Type", "FilterMode", "MsgBox"} <= body.keys()
        assert body["Status"][0] == {"value": 1, "name": "Normal", "icon": "lightning_bolt_circle", "color": "#f2f2f2"}


def test_auth(monkeypatch):
    from app import config
    monkeypatch.setattr(config, "USERNAME", "user")
    monkeypatch.setattr(config, "PASSWORD", "hunter2")
    with TestClient(app) as client:
        res = client.get("/api/health")
        assert res.status_code == 401
        assert res.headers["WWW-Authenticate"] == 'Basic realm="F95Checker"'
        res = client.get("/api/health", auth=("user", "hunter2"))
        assert res.status_code == 200
