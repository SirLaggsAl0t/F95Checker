import types

import app.serialize as serialize
from common.structs import Datestamp, Status, Tag, TimelineEvent, TimelineEventType, Type


def make_game():
    return types.SimpleNamespace(
        id=7,
        custom=False,
        name="Test Game",
        version="1.2",
        developer="Dev",
        type=Type.RenPy,
        status=Status.Completed,
        url="https://f95zone.to/threads/7",
        added_on=Datestamp(1_700_000_000),
        last_updated=Datestamp(1_700_000_100),
        last_full_check=1_700_000_200,
        last_check_version="1.1",
        last_launched=Datestamp(0),
        playtime=1.0,
        score=4.5,
        votes=12,
        rating=4,
        finished="True",
        installed="True",
        updated=False,
        archived=False,
        favourite=False,
        executables=[],
        launch_wrapper={},
        description="desc",
        changelog="changes",
        tags=(Tag["2d-game"], Tag.romance),
        unknown_tags=["mystery"],
        unknown_tags_flag=True,
        labels=[types.SimpleNamespace(id=2), types.SimpleNamespace(id=1)],
        tab=types.SimpleNamespace(id=3),
        notes="note",
        image_url="https://example.test/cover.png",
        previews_urls=["https://example.test/a.png"],
        downloads=(("Mega", [("Mirror", "https://example.test/file")]), ("Bad", [("No url", "")])),
        reviews_total=1,
        reviews=[types.SimpleNamespace(user="u", score=5, message="m", likes=2, timestamp=1_700_000_300)],
        timeline_events=[
            TimelineEvent(7, Datestamp(1_700_000_000), [], TimelineEventType.GameAdded),
            TimelineEvent(7, Datestamp(1_700_000_400), ["1.2"], TimelineEventType.ChangedVersion),
        ],
    )


def test_summary_shape_and_enums(monkeypatch):
    monkeypatch.setattr(serialize, "image_version", lambda game_id: "mtime-size")
    summary = serialize.game_summary(make_game())

    assert summary["status"]["value"] == 2
    assert summary["status"]["color"] == "#00dd00"
    assert summary["type"]["name"] == "RenPy"
    assert summary["tags"][1] == {"value": 104, "name": "romance", "text": "romance"}
    assert summary["labels"] == [2, 1]
    assert summary["tab"] == 3
    assert summary["favourite"] is False
    assert summary["added_on"] == 1_700_000_000
    assert summary["has_image"] is True
    assert summary["image_version"] == "mtime-size"


def test_detail_additions(monkeypatch):
    monkeypatch.setattr(serialize, "image_version", lambda game_id: "")
    detail = serialize.game_detail(make_game())

    assert detail["has_image"] is False
    assert detail["downloads"][0] == {"name": "Mega", "links": [{"name": "Mirror", "url": "https://example.test/file"}]}
    assert detail["downloads"][1]["links"][0]["url"] == "https://f95zone.to/threads/7"
    assert [event["type"]["name"] for event in detail["timeline_events"]] == ["ChangedVersion", "GameAdded"]
    assert detail["timeline_events"][0]["type"]["icon"] == "star"
