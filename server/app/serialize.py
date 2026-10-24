"""Explicit JSON shapes for the API. Never dump dataclasses directly."""
from app.enums import color_hex, enum_ref
from app.images import image_version


def _timestamp(value) -> int:
    return int(getattr(value, "value", value or 0))


def game_summary(game) -> dict:
    version = image_version(game.id)
    return {
        "id": game.id,
        "name": game.name,
        "version": game.version,
        "developer": game.developer,
        "type": enum_ref(game.type),
        "status": enum_ref(game.status),
        "url": game.url,
        "added_on": _timestamp(game.added_on),
        "last_updated": _timestamp(game.last_updated),
        "score": game.score,
        "votes": game.votes,
        "rating": game.rating,
        "finished": game.finished,
        "installed": game.installed,
        "updated": game.updated,
        "archived": game.archived,
        "favourite": bool(game.favourite),
        "labels": [label.id for label in game.labels],
        "tab": game.tab.id if game.tab else None,
        "image_version": version,
        "tags": [enum_ref(tag) for tag in game.tags],
        "unknown_tags": list(game.unknown_tags),
        "has_image": bool(version),
    }


def game_detail(game) -> dict:
    data = game_summary(game)
    data.update({
        "description": game.description,
        "changelog": game.changelog,
        "notes": game.notes,
        "downloads": [
            {"name": name, "links": [{"name": label, "url": url or game.url} for label, url in links]}
            for name, links in game.downloads
        ],
        "reviews_total": game.reviews_total,
        "reviews": [
            {
                "user": review.user,
                "score": review.score,
                "message": review.message,
                "likes": review.likes,
                "timestamp": review.timestamp,
            }
            for review in game.reviews
        ],
        "timeline_events": [
            {
                "game_id": event.game_id,
                "timestamp": _timestamp(event.timestamp),
                "arguments": list(event.arguments),
                "type": enum_ref(event.type),
            }
            for event in sorted(game.timeline_events, key=lambda event: event.timestamp.value, reverse=True)
        ],
        "last_check_version": game.last_check_version,
    })
    return data


def tab_json(tab) -> dict:
    return {
        "id": tab.id,
        "name": tab.name,
        "icon": tab.icon,
        "color": color_hex(tab.color) if tab.color else None,
    }


def label_json(label) -> dict:
    return {
        "id": label.id,
        "name": label.name,
        "color": color_hex(label.color),
    }
