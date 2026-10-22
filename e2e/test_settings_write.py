def test_settings_write_and_persist(page, base_url):
    page.goto(f"{base_url}/settings")
    page.get_by_role("heading", name="Settings").wait_for()

    previews = page.get_by_label("Previews")
    before = previews.is_checked()
    previews.click()
    page.get_by_role("button", name="Save settings").click()
    page.get_by_text("Saved").wait_for()

    page.reload()
    previews = page.get_by_label("Previews")
    previews.wait_for()
    assert previews.is_checked() is (not before)

    # Restore so later specs see the default library settings.
    previews.click()
    page.get_by_role("button", name="Save settings").click()
    page.get_by_text("Saved").wait_for()
