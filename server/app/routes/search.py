from fastapi import APIRouter

from modules import api, globals

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search")
async def search(q: str, category: str = "games", search: str = "search", page: int = 1):
    query = api.latest_updates_search_sanitize_query(q)
    if not query:
        return []
    results = await api.latest_updates_search(category, search, query, page=page)
    return [
        {
            "id": result.id,
            "title": result.title,
            "creator": result.creator,
            "in_list": result.id in globals.games,
        }
        for result in results
    ]
