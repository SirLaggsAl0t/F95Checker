from fastapi import APIRouter, HTTPException

from app.refresh_job import job

router = APIRouter(prefix="/api/refresh", tags=["refresh"])


@router.post("", status_code=202)
async def start_refresh():
    if job.running:
        raise HTTPException(status_code=409, detail="A refresh is already running")
    job.enqueue()
    return {"queued": True}


@router.get("/status")
async def refresh_status():
    return job.status()
