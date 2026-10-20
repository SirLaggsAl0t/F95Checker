import sqlite3

from fastapi.testclient import TestClient

from app import config
from app.main import app
from common.structs import Label, Status, Tab, Type
from modules import globals


def fake_refresh(monkeypatch):
    async def _refresh(*games, **kwargs):
        return None

    monkeypatch.setattr("app.refresh_job.api.refresh", _refresh)


def add_game(client, game_id: int, slug: str = "edit-test"):
    response = client.post("/api/games", json={"url": f"https://f95zone.to/threads/{slug}.{game_id}/"})
    assert response.status_code == 201, response.text
    return game_id


def row(game_id: int):
    connection = sqlite3.connect(config.DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        return connection.execute("SELECT * FROM games WHERE id=?", (game_id,)).fetchone()
    finally:
        connection.close()


def test_patch_round_trip_persists(monkeypatch):
    fake_refresh(monkeypatch)
    game_id = 940001
    with TestClient(app) as client:
        try:
            add_game(client, game_id)
            label = client.post("/api/labels", json={"name": "Favourite", "color": "#ff0000"}).json()
            tab = client.post("/api/tabs", json={"name": "Main"}).json()

            response = client.patch(f"/api/games/{game_id}", json={
                "name": "Edited game",
                "version": "2.0",
                "developer": "Dev",
                "type": int(Type.RenPy),
                "status": int(Status.Completed),
                "rating": 4,
                "notes": "Some notes",
                "installed": "2.0",
                "archived": True,
                "favourite": True,
                "labels": [label["id"]],
                "tab": tab["id"],
            })
            assert response.status_code == 200, response.text
            body = response.json()
            assert body["name"] == "Edited game"
            assert body["rating"] == 4
            assert body["installed"] == "2.0"
            assert body["updated"] is False
            assert body["labels"] == [label["id"]]
            assert body["tab"] == tab["id"]

            stored = row(game_id)
            assert stored["name"] == "Edited game"
            assert stored["installed"] == "2.0"
            assert stored["updated"] == 0
            assert stored["rating"] == 4
            assert stored["archived"] == 1
            assert stored["favourite"] == 1
            assert stored["labels"] == f"[{label['id']}]"
            assert stored["tab"] == tab["id"]

            # installed behind version flips `updated`, same rule as Game.__post_init__
            response = client.patch(f"/api/games/{game_id}", json={"installed": "1.0"})
            assert response.status_code == 200
            assert response.json()["updated"] is True
            assert row(game_id)["updated"] == 1

            assert client.get(f"/api/games/{game_id}").json()["notes"] == "Some notes"

            for bad in (
                {"colour": "red"},
                {"status": 999},
                {"tab": 999},
                {"rating": 6},
                {"labels": [999]},
                {"archived": "yes"},
                {"favourite": "yes"},
            ):
                assert client.patch(f"/api/games/{game_id}", json=bad).status_code == 400, bad
        finally:
            client.delete(f"/api/games/{game_id}")
            for item in list(Label.instances):
                client.delete(f"/api/labels/{item.id}")
            for item in list(Tab.instances):
                client.delete(f"/api/tabs/{item.id}")


def test_delete_game_removes_cascades(monkeypatch):
    fake_refresh(monkeypatch)
    game_id = 940002
    with TestClient(app) as client:
        try:
            add_game(client, game_id)
            thumb = config.DATA_DIR / "web-cache" / "covers" / f"{game_id}-1-1-320.webp"
            thumb.parent.mkdir(parents=True, exist_ok=True)
            thumb.write_bytes(b"thumb")

            assert client.delete(f"/api/games/{game_id}").status_code == 204
            assert client.get(f"/api/games/{game_id}").status_code == 404
            assert row(game_id) is None
            assert not thumb.exists()
            assert game_id not in globals.games
        finally:
            client.delete(f"/api/games/{game_id}")


def test_label_and_tab_delete_side_effects(monkeypatch):
    fake_refresh(monkeypatch)
    game_id = 940003
    with TestClient(app) as client:
        try:
            add_game(client, game_id)
            one = client.post("/api/labels", json={"name": "One"}).json()
            two = client.post("/api/labels", json={"name": "Two"}).json()
            tab = client.post("/api/tabs", json={"name": "Main"}).json()

            ordered = client.put("/api/labels/order", json={"ids": [two["id"], one["id"]]})
            assert ordered.status_code == 200, ordered.text
            assert [item["id"] for item in ordered.json()] == [two["id"], one["id"]]
            assert [item["position"] for item in ordered.json()] == [0, 1]

            client.patch(f"/api/games/{game_id}", json={"labels": [one["id"], two["id"]], "tab": tab["id"]})
            assert client.get(f"/api/games/{game_id}").json()["labels"] == [two["id"], one["id"]]

            assert client.delete(f"/api/labels/{one['id']}").status_code == 204
            game = client.get(f"/api/games/{game_id}").json()
            assert game["labels"] == [two["id"]]
            assert row(game_id)["labels"] == f"[{two['id']}]"

            assert client.delete(f"/api/tabs/{tab['id']}").status_code == 204
            game = client.get(f"/api/games/{game_id}").json()
            assert game["tab"] is None
            assert row(game_id)["tab"] is None
        finally:
            client.delete(f"/api/games/{game_id}")
            for item in list(Label.instances):
                client.delete(f"/api/labels/{item.id}")
            for item in list(Tab.instances):
                client.delete(f"/api/tabs/{item.id}")


def test_custom_game_can_be_renamed_and_converted(monkeypatch):
    fake_refresh(monkeypatch)
    with TestClient(app) as client:
        created = client.post("/api/games/custom")
        assert created.status_code == 201, created.text
        game_id = created.json()["id"]
        assert created.json()["custom"] is True

        assert client.patch(f"/api/games/{game_id}", json={"name": "My mod"}).json()["name"] == "My mod"

        new_id = 940004
        converted = client.post(f"/api/games/{game_id}/convert", json={"id": new_id})
        try:
            assert converted.status_code == 200, converted.text
            assert converted.json()["id"] == new_id
            assert converted.json()["custom"] is False
            assert client.get(f"/api/games/{game_id}").status_code == 404
            assert client.get(f"/api/games/{new_id}").json()["name"] == "My mod"
            assert row(new_id)["custom"] == 0
        finally:
            client.delete(f"/api/games/{new_id}")
