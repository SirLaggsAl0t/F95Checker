import asyncio
import pathlib
import sys
import types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from modules import globals  # Mirrors app boot order, breaks the api/gui import cycle
from modules import api


def game(id, image_url, missing=True, custom=False, archived=False):
    return types.SimpleNamespace(
        id=id,
        image_url=image_url,
        custom=custom,
        archived=archived,
        image=types.SimpleNamespace(missing=missing),
    )


def main():
    globals.settings = types.SimpleNamespace(refresh_archived_games=False)
    api.missing_image_rechecks.clear()
    now = 100_000.0

    fetch, recheck = api.plan_missing_image_repairs(
        [
            game(1, "https://attachments.f95zone.to/x.jpg"),  # Plain URL -> re-download
            game(2, ""),                                      # No URL -> thread re-check
            game(3, "missing"),                               # Thread has no image -> thread re-check
            game(4, "dead"),                                  # Dead link -> thread re-check
            game(5, "https://x/y.jpg", custom=True),          # Custom games skipped
            game(6, "https://x/y.jpg", archived=True),        # Archived skipped
            game(7, "https://x/y.jpg", missing=False),        # Image present, skipped
        ],
        now,
    )
    assert [g.id for g in fetch] == [1], [g.id for g in fetch]
    assert [g.id for g in recheck] == [2, 3, 4], [g.id for g in recheck]

    # Cooldown suppresses repeat rechecks, expired cooldown does not
    api.missing_image_rechecks.update(
        {
            2: now - 10,
            3: now - 10,
            4: now - api.missing_image_recheck_cooldown - 1,
        }
    )
    _, recheck = api.plan_missing_image_repairs(
        [game(2, ""), game(3, "missing"), game(4, "dead")], now
    )
    assert [g.id for g in recheck] == [4], [g.id for g in recheck]

    # ProcessingGame tracks current game and clears it, sync and async
    g = game(9, "")
    g.name = "Test Game"
    with api.ProcessingGame(g):
        assert api.processing_games == {9: "Test Game"}, api.processing_games
    assert not api.processing_games, api.processing_games
    async def check_async():
        async with api.ProcessingGame(g):
            assert api.processing_games == {9: "Test Game"}, api.processing_games
        assert not api.processing_games, api.processing_games
    asyncio.run(check_async())

    # Queue only takes missing games with http url, deduped by id
    api.missing_images_queue.clear()
    api.queue_missing_images([
        game(10, "https://x/y.jpg"),                    # queued
        game(11, "https://x/y.jpg", missing=False),     # image present, skipped
        game(12, "missing"),                            # no usable url, skipped
        game(10, "https://x/y.jpg"),                    # duplicate id, skipped
    ])
    assert [g.id for g in api.missing_images_queue] == [10], [g.id for g in api.missing_images_queue]

    print("ok")


if __name__ == "__main__":
    main()
