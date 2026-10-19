from playwright.sync_api import expect


def test_edit_game_persists(page, add_game, wait_idle):
    game_id = add_game("https://f95zone.to/threads/e2e-edit.930010/")

    page.goto(f"/games/{game_id}")
    page.get_by_text("Edit game").click()
    page.get_by_label("Name", exact=True).fill("Edited e2e")
    page.get_by_label("Version", exact=True).fill("9.9")
    page.get_by_role("button", name="Rate 4 stars").click()
    page.get_by_role("group", name="Installed").get_by_role("button", name="Yes").click()
    page.get_by_label("Notes").fill("Notes from e2e")

    expect(page.get_by_role("button", name="Save changes")).to_be_enabled(timeout=15_000)
    page.get_by_role("button", name="Save changes").click()
    expect(page.get_by_role("heading", name="Edited e2e")).to_be_visible(timeout=15_000)
    expect(page.get_by_text("Saved", exact=True)).to_be_visible()

    page.reload()
    expect(page.get_by_role("heading", name="Edited e2e")).to_be_visible(timeout=15_000)
    expect(page.get_by_text("9.9")).to_be_visible()
    expect(page.get_by_text("4 / 5")).to_be_visible()
    expect(page.get_by_role("paragraph").filter(has_text="Notes from e2e")).to_be_visible()
    wait_idle()
