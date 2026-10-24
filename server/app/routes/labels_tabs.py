from fastapi import APIRouter, HTTPException

from app.serialize import label_json, tab_json
from app.validate import bad_request, color_value, text_value
from common.structs import Label, Tab
from modules import db, globals

router = APIRouter(prefix="/api", tags=["labels_tabs"])


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


async def create_entity(create, update, json_fn, payload, allowed, color_nullable=False):
    changes = name_changes(payload or {}, allowed, color_nullable)
    entity = await create()
    if changes:
        for key, value in changes.items():
            setattr(entity, key, value)
        await update(entity, *changes)
    await db.save()
    return json_fn(entity)


async def update_entity(cls, entity_id, payload, update, json_fn, allowed, color_nullable=False):
    entity = cls.get(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"{cls.__name__} not found")
    changes = name_changes(payload, allowed, color_nullable)
    if changes:
        for key, value in changes.items():
            setattr(entity, key, value)
        await update(entity, *changes)
        await db.save()
    return json_fn(entity)


@router.get("/tabs")
async def list_tabs():
    # Real tabs only; the client prepends the synthetic default tab.
    return [tab_json(tab) for tab in sorted(Tab.instances, key=lambda tab: tab.position)]


@router.get("/labels")
async def list_labels():
    return [label_json(label) for label in sorted(Label.instances, key=lambda label: label.position)]


@router.post("/labels", status_code=201)
async def create_label(payload: dict | None = None):
    return await create_entity(db.create_label, db.update_label, label_json, payload, {"name", "color"})


@router.patch("/labels/{label_id}")
async def update_label(label_id: int, payload: dict):
    return await update_entity(Label, label_id, payload, db.update_label, label_json, {"name", "color"})


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
    return await create_entity(
        db.create_tab, db.update_tab, tab_json, payload, {"name", "icon", "color"}, color_nullable=True
    )


@router.patch("/tabs/{tab_id}")
async def update_tab(tab_id: int, payload: dict):
    return await update_entity(
        Tab, tab_id, payload, db.update_tab, tab_json, {"name", "icon", "color"}, color_nullable=True
    )


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
