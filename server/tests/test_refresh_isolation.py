import asyncio
import json

from modules import api, globals


class FakeGame:
    custom = False
    last_check_version = globals.version

    def __init__(self, id: int):
        self.id = id


def test_one_game_failure_does_not_abort_the_rest(monkeypatch):
    good = FakeGame(1)
    bad = FakeGame(2)
    checked = []

    async def fake_fetch(*args, **kwargs):
        return json.dumps({"1": 100, "2": 100})

    async def fake_full_check(game, last_changed, updates, api_errors, missing_threads):
        if game.id == bad.id:
            raise RuntimeError("boom")
        checked.append(game.id)

    monkeypatch.setattr(api, "fetch", fake_fetch)
    monkeypatch.setattr(api, "full_check", fake_full_check)
    globals.refresh_progress = 0
    monkeypatch.setattr(api, "fast_checks_sem", asyncio.Semaphore(1))

    api_errors = {}
    asyncio.run(api.fast_check([good, bad], True, {}, api_errors, []))

    assert checked == [good.id]
    assert api_errors == {bad.id: "RuntimeError: boom"}
    assert globals.refresh_progress == 1
