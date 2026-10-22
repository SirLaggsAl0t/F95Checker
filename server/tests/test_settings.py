from fastapi.testclient import TestClient

from app.main import app
from common.structs import Tag, TagHighlight, TimelineEventType
from modules import globals


def test_settings_round_trip():
    with TestClient(app) as client:
        before = client.get("/api/settings").json()
        response = client.patch(
            "/api/settings",
            json={
                "style_bg": "#112233",
                "style_corner_radius": 8,
                "previews_enabled": not before["previews_enabled"],
                "bg_refresh_interval": 0,
                "hidden_timeline_events": [1, 2],
                "tags_highlights": {str(int(Tag["2d-game"])): int(TagHighlight.Positive)},
            },
        )
        assert response.status_code == 200, response.text()
        data = response.json()
        assert data["style_bg"] == "#112233"
        assert data["style_corner_radius"] == 8
        assert data["previews_enabled"] is (not before["previews_enabled"])
        assert data["bg_refresh_interval"] == 0
        assert data["hidden_timeline_events"] == [1, 2]
        assert data["tags_highlights"] == {str(int(Tag["2d-game"])): int(TagHighlight.Positive)}
        assert client.get("/api/settings").json()["style_bg"] == "#112233"

        assert globals.settings.hidden_timeline_events == [
            TimelineEventType.GameAdded,
            TimelineEventType.GameLaunched,
        ]
        assert globals.settings.tags_highlights[Tag["2d-game"]] is TagHighlight.Positive


def test_settings_reject_bad_input():
    with TestClient(app) as client:
        assert client.patch("/api/settings", json={"interface_scaling": 2}).status_code == 400
        assert client.patch("/api/settings", json={"style_bg": "red"}).status_code == 400
        assert client.patch("/api/settings", json={"bg_refresh_interval": -1}).status_code == 400
        assert client.patch("/api/settings", json={"previews_enabled": "yes"}).status_code == 400
        assert client.patch("/api/settings", json={"hidden_timeline_events": [999]}).status_code == 400
