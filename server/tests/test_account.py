import asyncio
import pathlib
import time

from fastapi.testclient import TestClient

from app.main import app
from app.browser_login import browser_login
from modules import api, globals

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def test_notif_counts_parse_fixture(monkeypatch):
    async def fake_fetch(method, url, **kwargs):
        return (FIXTURES / "notifs.json").read_bytes()

    monkeypatch.setattr(api, "fetch", fake_fetch)
    assert asyncio.run(api.notif_counts()) == (1234, 5)


def test_notifs_route_returns_counts(monkeypatch):
    async def fake_counts():
        return 2, 3

    monkeypatch.setattr(api, "notif_counts", fake_counts)
    with TestClient(app) as client:
        res = client.get("/api/account/notifs")
    assert res.status_code == 200
    body = res.json()
    assert body["alerts"] == 2
    assert body["inbox"] == 3
    assert abs(body["checked_at"] - time.time()) < 5


def test_notifs_route_requires_login(monkeypatch):
    async def fake_counts():
        return None

    monkeypatch.setattr(api, "notif_counts", fake_counts)
    with TestClient(app) as client:
        res = client.get("/api/account/notifs")
    assert res.status_code == 401


def test_cookie_paste_verifies_and_persists(monkeypatch):
    async def logged_in():
        return True

    monkeypatch.setattr(api, "is_logged_in", logged_in)
    with TestClient(app) as client:
        res = client.post("/api/account/cookies", json={"cookies": "xf_user=abc; xf_session=def"})
        assert res.status_code == 200
        assert globals.cookies == {"xf_user": "abc", "xf_session": "def"}

        assert client.get("/api/account/status").json()["logged_in"] is True

        assert client.delete("/api/account/cookies").status_code == 204
        assert globals.cookies == {}


def test_cookie_paste_requires_xf_user(monkeypatch):
    async def logged_in():
        return True

    monkeypatch.setattr(api, "is_logged_in", logged_in)
    with TestClient(app) as client:
        res = client.post("/api/account/cookies", json={"cookies": "xf_session=def"})
    assert res.status_code == 400


def test_cookie_paste_clears_invalid_cookies(monkeypatch):
    async def not_logged_in():
        return False

    monkeypatch.setattr(api, "is_logged_in", not_logged_in)
    with TestClient(app) as client:
        res = client.post("/api/account/cookies", json={"cookies": "xf_user=bogus"})
    assert res.status_code == 401
    assert globals.cookies == {}


def test_cookie_paste_saves_user_agent(monkeypatch, tmp_path):
    ua_file = tmp_path / "browser-user-agent.txt"
    monkeypatch.setattr(api, "user_agent_path", lambda: ua_file)
    monkeypatch.setattr(api, "webview_user_agent", None)

    async def logged_in():
        return True

    monkeypatch.setattr(api, "is_logged_in", logged_in)
    with TestClient(app) as client:
        res = client.post(
            "/api/account/cookies",
            json={"cookies": "xf_user=abc", "user_agent": "TestAgent/1.0"},
        )
        assert res.status_code == 200
        assert api.webview_user_agent == "TestAgent/1.0"
        assert ua_file.read_text("utf-8") == "TestAgent/1.0"

        assert client.delete("/api/account/cookies").status_code == 204
        assert api.webview_user_agent is None
        assert not ua_file.exists()


def test_browser_login_stores_cookies_and_user_agent(monkeypatch, tmp_path):
    ua_file = tmp_path / "browser-user-agent.txt"
    monkeypatch.setattr(api, "user_agent_path", lambda: ua_file)
    monkeypatch.setattr(api, "webview_user_agent", None)

    async def fake_login():
        return {"xf_user": "abc", "cf_clearance": "xyz"}, "Firefox/157.0"

    monkeypatch.setattr(browser_login, "_login", fake_login)
    monkeypatch.setattr(browser_login, "state", "idle")

    with TestClient(app) as client:
        assert client.post("/api/account/browser-login").status_code == 200
        for _ in range(50):
            body = client.get("/api/account/browser-login").json()
            if body["state"] != "running":
                break
            time.sleep(0.1)
        assert body == {"state": "done", "error": None}
        assert globals.cookies["xf_user"] == "abc"
        assert api.webview_user_agent == "Firefox/157.0"
        assert ua_file.read_text("utf-8") == "Firefox/157.0"


def test_account_status(monkeypatch):
    async def logged_in():
        return True

    monkeypatch.setattr(api, "is_logged_in", logged_in)
    with TestClient(app) as client:
        # db.load() repopulates globals.cookies on startup, so set it after.
        globals.cookies["xf_user"] = "abc"
        try:
            assert client.get("/api/account/status").json() == {"logged_in": True}
        finally:
            globals.cookies.pop("xf_user", None)
