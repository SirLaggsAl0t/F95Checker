import io
import types

from fastapi.testclient import TestClient
from PIL import Image

from app import config
from app.main import app
from modules import globals


def png_bytes(size=(64, 48), color=(200, 30, 30)):
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, "PNG")
    return buffer.getvalue()


def test_cover_served_and_thumb_cached():
    with TestClient(app) as client:
        (globals.images_path / "7.png").write_bytes(png_bytes())
        globals.games[7] = types.SimpleNamespace(id=7, image_url="")

        original = client.get("/api/images/7")
        assert original.status_code == 200
        assert original.headers["content-type"] == "image/png"
        assert original.headers["cache-control"] == "no-cache"
        etag = original.headers["etag"]
        assert client.get("/api/images/7", headers={"If-None-Match": etag}).status_code == 304

        thumb = client.get("/api/images/7?w=320")
        assert thumb.status_code == 200
        assert thumb.headers["content-type"] == "image/webp"
        cached = list((config.DATA_DIR / "web-cache" / "covers").glob("7-*-320.webp"))
        assert len(cached) == 1
        assert client.get("/api/images/7?w=640").status_code == 200
        assert len(list((config.DATA_DIR / "web-cache" / "covers").glob("7-*.webp"))) == 2


def test_zst_only_cover_is_404():
    with TestClient(app) as client:
        (globals.images_path / "8.astc.ktx.zst").write_bytes(b"not an image")
        globals.games[8] = types.SimpleNamespace(id=8, image_url="")
        assert client.get("/api/images/8").status_code == 404


def test_bad_thumb_width_rejected():
    with TestClient(app) as client:
        globals.games[9] = types.SimpleNamespace(id=9, image_url="")
        assert client.get("/api/images/9?w=123").status_code == 400


def test_missing_game_is_404():
    with TestClient(app) as client:
        assert client.get("/api/images/999").status_code == 404
