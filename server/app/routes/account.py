"""F95zone account: pasted cookies and unread notification counts.

The desktop opens a Qt webview to log in; the web app accepts the Cookie header
copied from a logged-in browser instead.
"""
import http.cookies
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.browser_login import browser_login
from modules import api, db

router = APIRouter(prefix="/api/account", tags=["account"])


class CookiesPayload(BaseModel):
    cookies: str
    user_agent: str | None = None


@router.get("/status")
async def account_status():
    return {
        "logged_in": await api.is_logged_in(),
    }


@router.get("/notifs")
async def account_notifs():
    counts = await api.notif_counts()
    if counts is None:
        raise HTTPException(status_code=401, detail="Not logged in to F95zone")
    alerts, inbox = counts
    return {"alerts": alerts, "inbox": inbox, "checked_at": int(time.time())}


@router.post("/cookies")
async def set_cookies(payload: CookiesPayload):
    jar = http.cookies.SimpleCookie()
    try:
        jar.load(payload.cookies)
    except http.cookies.CookieError:
        raise HTTPException(status_code=400, detail="Could not parse the cookie header")
    cookies = api.cookiedict(jar)
    if not cookies.get("xf_user"):
        raise HTTPException(status_code=400, detail="The cookie header must include xf_user")

    # Cloudflare checks the UA against cf_clearance, so verify with the pasted one
    previous_user_agent = api.webview_user_agent
    if payload.user_agent is not None:
        api.set_user_agent(payload.user_agent)

    await db.update_cookies(cookies)
    await db.save()
    if not await api.is_logged_in():
        await db.update_cookies({})
        await db.save()
        if payload.user_agent is not None:
            api.set_user_agent(previous_user_agent)
        raise HTTPException(status_code=401, detail="Those cookies did not log in to F95zone")
    return {"logged_in": True}


@router.delete("/cookies", status_code=204)
async def clear_cookies():
    await db.update_cookies({})
    await db.save()
    api.set_user_agent(None)


@router.post("/browser-login")
async def start_browser_login():
    return browser_login.start()


@router.get("/browser-login")
async def browser_login_status():
    return browser_login.status()
