from fastapi import APIRouter

from app.enums import all_enums

router = APIRouter(prefix="/api/enums", tags=["enums"])


@router.get("")
async def get_enums():
    return all_enums()
