import asyncio

from common.structs import Game
from external import imagehelper
from modules import api, globals

PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


class FakeGame:
    id = 4242
    preview_images = []
    previews_loading = False
    previews_loaded = False
    preview_load_future = None

    def __init__(self):
        self.image = imagehelper.ImageHelper(globals.images_path, glob=f"{self.id}.*")

    delete_images = Game.delete_images
    unload_previews = Game.unload_previews
    refresh_image = Game.refresh_image
    cancel_preview_loading = Game.cancel_preview_loading
    set_image_async = Game.set_image_async


def test_set_image_async_headless():
    game = FakeGame()
    asyncio.run(game.set_image_async(PNG))
    assert (globals.images_path / "4242.png").is_file()
    # reload() must tolerate the missing compression thread
    asyncio.run(game.set_image_async(b""))


def test_delete_images_headless():
    game = FakeGame()
    asyncio.run(game.set_image_async(PNG))
    game.delete_images(cover_only=False)
    assert not (globals.images_path / "4242.png").exists()


def test_check_host_inline():
    assert asyncio.run(api.check_host("localhost")) is True
