import re

from playwright.sync_api import expect

from common.structs import SearchResult


def test_add_game_by_url(page, network, wait_idle):
    page.goto("/")
    page.get_by_label("Thread URL or game name").fill("https://f95zone.to/threads/e2e-add.930001/")
    page.get_by_role("button", name="Add game").click()

    expect(page.get_by_text("1 added")).to_be_visible(timeout=15_000)
    expect(page.get_by_role("link", name=re.compile("e2e-add"))).to_be_visible()

    wait_idle()
    assert sum(1 for ids, _ in network.refresh_calls if 930001 in ids) == 1


def test_search_and_add(page, network, wait_idle):
    network.search_results = [
        SearchResult(title="e2e-search", creator="Dev", url="https://f95zone.to/threads/930003/", id=930003)
    ]
    page.goto("/")
    page.get_by_label("Thread URL or game name").fill("e2e search")
    page.get_by_role("button", name="Search games").click()

    expect(page.get_by_text("e2e-search")).to_be_visible(timeout=15_000)
    page.get_by_role("button", name="Add", exact=True).click()

    expect(page.get_by_text("1 added")).to_be_visible(timeout=15_000)
    expect(page.get_by_role("link", name=re.compile("930003"))).to_be_visible()
    wait_idle()
    assert any(930003 in ids for ids, _ in network.refresh_calls)


def test_refresh_shows_per_game_errors(page, network, add_game, wait_idle):
    game_id = add_game("https://f95zone.to/threads/e2e-refresh.930002/")
    network.errors[game_id] = "RuntimeError: boom"
    network.missing_threads = [game_id]
    calls_before = len(network.refresh_calls)

    page.goto("/")
    page.get_by_role("button", name="Refresh library").click()

    expect(page.get_by_text(f"e2e-refresh: RuntimeError: boom")).to_be_visible(timeout=15_000)
    expect(page.get_by_text(f"Missing threads: {game_id}")).to_be_visible()

    wait_idle()
    assert len(network.refresh_calls) == calls_before + 1
