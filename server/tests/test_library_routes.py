import types

from fastapi.testclient import TestClient

from app.main import app
from common.structs import Label, Status, Tab, Tag, Type
from modules import globals


def test_library_routes():
    with TestClient(app) as client:
        assert client.get("/api/games").json() == []
        assert client.get("/api/tabs").json() == []
        assert client.get("/api/labels").json() == []
        settings = client.get("/api/settings").json()
        assert settings["previews_enabled"] in (True, False)
        assert "style_bg" in settings
        assert "interface_scaling" not in settings


def test_game_detail_and_labels():
    with TestClient(app) as client:
        game = types.SimpleNamespace(
            id=5,
            custom=False,
            name="Zeta",
            version="1",
            developer="Dev",
            type=Type.Others,
            status=Status.Normal,
            url="",
            added_on=types.SimpleNamespace(value=1),
            last_updated=types.SimpleNamespace(value=1),
            last_full_check=0,
            last_check_version="",
            last_launched=types.SimpleNamespace(value=0),
            playtime=0,
            score=0,
            votes=0,
            rating=0,
            finished="",
            installed="",
            updated=False,
            archived=False,
            favourite=False,
            executables=[],
            launch_wrapper={},
            description="",
            changelog="",
            tags=(Tag["2d-game"],),
            unknown_tags=[],
            unknown_tags_flag=False,
            labels=[],
            tab=None,
            notes="",
            image_url="",
            previews_urls=[],
            downloads=(),
            reviews_total=0,
            reviews=[],
            timeline_events=[],
        )
        globals.games[5] = game
        Tab.add(Tab(3, "Main", "\uf0001", None, 0))
        Label.add(Label(2, "Favorite", (1.0, 0.0, 0.0, 1.0), 0))

        tabs = client.get("/api/tabs").json()
        assert tabs[0]["name"] == "Main"
        labels = client.get("/api/labels").json()
        assert labels[0] == {"id": 2, "name": "Favorite", "color": "#ff0000"}

        detail = client.get("/api/games/5")
        assert detail.status_code == 200
        assert detail.json()["name"] == "Zeta"
        assert detail.json()["tags"][0]["text"] == "2d game"
        assert client.get("/api/games/999").status_code == 404
