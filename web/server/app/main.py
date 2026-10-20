import asyncio
import base64
import contextlib
import logging
import pathlib
import secrets
import socket
import urllib.parse

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse

from app import config
from app.browser_login import browser_login
from app.refresh_job import job
from app.routes import account, enums, games, images, imports, labels_tabs, refresh, search, settings, timeline
from common.errors import Exc
from modules import api, db

logger = logging.getLogger("f95web")

client_dist = pathlib.Path(__file__).resolve().parents[2] / "client" / "dist"


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. async_thread stays in inline mode (never call setup()): coroutines run on the uvicorn loop
    # 2. Open the shared SQLite database (same data dir as the desktop app by default)
    await db.connect()
    await db.load()
    # 3. aiohttp session, SSL context and rate limiters
    with api.setup():
        # 4. Background commit loop
        save_task = asyncio.create_task(db.save_loop())
        job.start()
        try:
            log_urls()
            yield
        finally:
            await job.stop()
            await browser_login.stop()
            save_task.cancel()
    # api.setup() can't block on session close in inline mode, close it here
    if api.session and not api.session.closed:
        await api.session.close()
    await db.close()


app = FastAPI(title="F95Checker Web", lifespan=lifespan)


def auth_ok(authorization: str | None) -> bool:
    if not (config.USERNAME and config.PASSWORD):
        return True  # Auth disabled
    if not authorization or not authorization.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(authorization[6:]).decode()
    except Exception:
        return False
    user, _, password = decoded.partition(":")
    return secrets.compare_digest(user, config.USERNAME) and secrets.compare_digest(password, config.PASSWORD)


def same_origin(request: Request) -> bool:
    # DNS rebinding / CSRF hardening: a browser-supplied Origin or Referer must match
    # our Host. Absent headers (curl, tests) are allowed.
    source = request.headers.get("origin") or request.headers.get("referer")
    if not source:
        return True
    return urllib.parse.urlsplit(source).netloc == request.headers.get("host", "")


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.method not in ("GET", "HEAD", "OPTIONS") and not same_origin(request):
        return JSONResponse({"detail": "Cross-origin request rejected"}, status_code=403)
    if not auth_ok(request.headers.get("authorization")):
        return JSONResponse(
            {"detail": "Unauthorized"},
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="F95Checker"'},
        )
    return await call_next(request)


@app.get("/api/health")
async def health():
    return {
        "ok": True,
        "data_dir": str(config.DATA_DIR),
        "db_path": str(config.DB_PATH),
        "shared_with_desktop": config.SHARED_WITH_DESKTOP,
    }


@app.exception_handler(Exc)
async def exc_handler(request: Request, exc: Exc):
    level = exc.level.name if exc.level is not None else None
    return JSONResponse(
        {"detail": {"title": exc.title, "msg": exc.msg, "more": exc.more, "level": level}},
        status_code=400,
    )


app.include_router(games.router)
app.include_router(labels_tabs.router)
app.include_router(settings.router)
app.include_router(enums.router)
app.include_router(images.router)
app.include_router(refresh.router)
app.include_router(search.router)
app.include_router(account.router)
app.include_router(imports.router)
app.include_router(timeline.router)


def log_urls():
    urls = []
    try:
        for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
            if not ip.startswith("127."):
                urls.append(f"http://{ip}:{config.PORT}")
    except OSError:
        pass
    logger.info("F95Checker web server reachable at http://%s:%s%s",
                config.HOST, config.PORT, f" and {', '.join(urls)}" if urls else "")
    if config.HOST not in ("127.0.0.1", "localhost", "::1") and not (config.USERNAME and config.PASSWORD):
        logger.warning(
            "Binding to %s exposes the app on the LAN but F95WEB_USERNAME/F95WEB_PASSWORD are not set! "
            "The library contains NSFW metadata and F95zone cookies.", config.HOST,
        )


# SPA static serving, registered LAST so /api/* wins
@app.get("/{path:path}", include_in_schema=False)
async def spa_fallback(path: str):
    if path == "api" or path.startswith("api/"):
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    if not client_dist.is_dir():
        return JSONResponse({"detail": "Client not built, run `npm run build` in web/client"}, status_code=404)
    root = client_dist.resolve()
    file = client_dist / path
    try:
        resolved = file.resolve()
        resolved.relative_to(root)
    except (ValueError, OSError):
        resolved = None
    if resolved is not None and path and resolved.is_file():
        return FileResponse(resolved)
    return FileResponse(client_dist / "index.html")
