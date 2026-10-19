from fastapi import APIRouter

from app.serialize import label_json, tab_json
from common.structs import Label, Tab

router = APIRouter(prefix="/api", tags=["labels_tabs"])


@router.get("/tabs")
async def list_tabs():
    # Real tabs only; the client prepends the synthetic default tab.
    return [tab_json(tab) for tab in sorted(Tab.instances, key=lambda tab: tab.position)]


@router.get("/labels")
async def list_labels():
    return [label_json(label) for label in sorted(Label.instances, key=lambda label: label.position)]
