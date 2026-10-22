import re

from fastapi import APIRouter, HTTPException

from app.serialize import label_json, tab_json
from common.structs import Label, Tab
from modules import colors, db, globals

router = APIRouter(prefix="/api", tags=["labels_tabs"])

HEX = re.compile(r"^#([0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


def bad_request(message: str):
    raise HTTPException(status_code=400, detail=message)


def color_value(key: str, value, nullable=False):
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not HEX.fullmatch(value):
        bad_request(f"{key} must be a #rrggbb colour")
    return colors.hex_to_rgba_0_1(value)


def text_value(key: str, value, max_length=None):
    if not isinstance(value, str):
        bad_request(f"{key} must be a string")
    if max_length is not None and len(value) > max_length:
        bad_request(f"{key} is too long")
    return value


def name_changes(payload: dict, allowed: set[str], color_nullable=False) -> dict:
    unknown = set(payload) - allowed
    if unknown:
        bad_request(f"Unknown field(s): {', '.join(sorted(unknown))}")
    changes = {}
    for key, value in payload.items():
        if key == "name":
            changes[key] = text_value(key, value, max_length=64)
        elif key == "icon":
            changes[key] = text_value(key, value, max_length=8)
        elif key == "color":
            changes[key] = color_value(key, value, nullable=color_nullable)
        else:
            bad_request(f"Unknown field: {key}")
    return changes


def ordered_instances(cls, ids: list[int]):
    if not isinstance(ids, list) or any(type(item) is not int for item in ids):
        bad_request("ids must be a list of ids")
    existing = {item.id for item in cls.instances}
    if len(ids) != len(existing) or set(ids) != existing:
        bad_request("ids must list every existing id exactly once")
    return [cls.get(item) for item in ids]


@router.get("/tabs")
async def list_tabs():
    # Real tabs only; the client prepends the synthetic default tab.
    return [tab_json(tab) for tab in sorted(Tab.instances, key=lambda tab: tab.position)]


@router.get("/labels")
async def list_labels():
    return [label_json(label) for label in sorted(Label.instances, key=lambda label: label.position)]


@router.post("/labels", status_code=201)
async def create_label(payload: dict | None = None):
    changes = name_changes(payload or {}, {"name", "color"})
    label = await db.create_label()
    for key, value in changes.items():
        setattr(label, key, value)
    if changes:
        await db.update_label(label, *changes)
    await db.save()
    return label_json(label)


@router.patch("/labels/{label_id}")
async def update_label(label_id: int, payload: dict):
    label = Label.get(label_id)
    if label is None:
        raise HTTPException(status_code=404, detail="Label not found")
    changes = name_changes(payload, {"name", "color"})
    for key, value in changes.items():
        setattr(label, key, value)
    if changes:
        await db.update_label(label, *changes)
        await db.save()
    return label_json(label)


@router.delete("/labels/{label_id}", status_code=204)
async def delete_label(label_id: int):
    label = Label.get(label_id)
    if label is None:
        raise HTTPException(status_code=404, detail="Label not found")
    await db.delete_label(label)
    for game in globals.games.values():
        await db.update_game(game, "labels")
    await db.save()


@router.put("/labels/order")
async def order_labels(payload: dict):
    ids = payload.get("ids")
    Label.instances[:] = ordered_instances(Label, ids)
    Label.update_positions()
    await db.update_label_positions()
    await db.save()
    return [label_json(label) for label in Label.instances]


@router.post("/tabs", status_code=201)
async def create_tab(payload: dict | None = None):
    changes = name_changes(payload or {}, {"name", "icon", "color"}, color_nullable=True)
    tab = await db.create_tab()
    for key, value in changes.items():
        setattr(tab, key, value)
    if changes:
        await db.update_tab(tab, *changes)
    await db.save()
    return tab_json(tab)


@router.patch("/tabs/{tab_id}")
async def update_tab(tab_id: int, payload: dict):
    tab = Tab.get(tab_id)
    if tab is None:
        raise HTTPException(status_code=404, detail="Tab not found")
    changes = name_changes(payload, {"name", "icon", "color"}, color_nullable=True)
    for key, value in changes.items():
        setattr(tab, key, value)
    if changes:
        await db.update_tab(tab, *changes)
        await db.save()
    return tab_json(tab)


@router.delete("/tabs/{tab_id}", status_code=204)
async def delete_tab(tab_id: int):
    tab = Tab.get(tab_id)
    if tab is None:
        raise HTTPException(status_code=404, detail="Tab not found")
    affected = [game for game in globals.games.values() if game.tab is tab]
    await db.delete_tab(tab)
    for game in affected:
        await db.update_game(game, "tab")
    await db.save()


@router.put("/tabs/order")
async def order_tabs(payload: dict):
    ids = payload.get("ids")
    Tab.instances[:] = ordered_instances(Tab, ids)
    Tab.update_positions()
    for tab in Tab.instances:
        await db.update_tab(tab, "position")
    await db.save()
    return [tab_json(tab) for tab in Tab.instances]
