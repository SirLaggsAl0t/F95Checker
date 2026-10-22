from playwright.sync_api import expect


def test_import_threads_and_queue_refresh(page, network, wait_idle):
    page.goto("/import")
    page.get_by_label("Thread links").fill(
        "https://f95zone.to/threads/e2e-import.930020/\n"
        "https://f95zone.to/threads/e2e-import.930020/\n"
        "https://f95zone.to/threads/e2e-import-two.930021/"
    )
    page.get_by_role("button", name="Import thread links").click()

    expect(page.get_by_text("Found 3, added 2, skipped 0.")).to_be_visible(timeout=15_000)
    wait_idle()
    batches = [ids for ids, _ in network.refresh_calls if 930020 in ids and 930021 in ids]
    assert len(batches) == 1


def test_import_bookmarks_file(page, network, wait_idle):
    page.goto("/import")
    page.get_by_label("Bookmarks HTML file").set_input_files(
        files=[
            {
                "name": "bookmarks.html",
                "mimeType": "text/html",
                "buffer": b'<a href="https://f95zone.to/threads/e2e-bookmark.930030/">One</a>',
            }
        ]
    )

    expect(page.get_by_text("Found 1, added 1, skipped 0.")).to_be_visible(timeout=15_000)
    wait_idle()
    assert any(930030 in ids for ids, _ in network.refresh_calls)
