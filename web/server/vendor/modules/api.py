# VENDORED from modules/ - GUI stripped for the web server; see web/
import asyncio
import configparser
import contextlib
import hashlib
import http.cookies
import json
import os
import pathlib
import re
import shutil
import socket
import ssl
import sys
import tempfile
import time

import aiofiles
import aiohttp
import aiohttp_socks
import aiolimiter
import python_socks

from common.structs import (
    CounterContext,
    DdlFile,
    FileDownload,
    Game,
    MsgBox,
    OldGame,
    Os,
    ProxyType,
    Review,
    SearchResult,
    Status,
    Tag,
    ThreadMatch,
    TimelineEventType,
    Type,
)
from common import parser
# VENDORED: desktop raises these via modules/msgbox.py popups, headless raises plain exceptions
from common import errors
from external import (
    async_thread,
    error,
)
from modules import (
    db,
    globals,
    utils,
)

user_agent = (
    f"F95Checker/{globals.version} "
    f"Python/{sys.version.split(' ')[0]} "
    f"aiohttp/{aiohttp.__version__}"
)

f95_domains = (
    f95_domain := "f95zone.to",
    f95_domain_com := "f95zone.com",
    f95_domain_ninja := "f95zone.ninja"
)
f95_host = "https://" + f95_domain
f95_check_login_fast    = f95_host + "/sam/latest_alpha/"
f95_login_page          = f95_host + "/login/"
f95_notif_endpoint      = f95_host + "/conversations/popup?_xfResponseType=json"
f95_alerts_page         = f95_host + "/account/alerts/"
f95_inbox_page          = f95_host + "/conversations/"
f95_threads_page        = f95_host + "/threads/"
f95_bookmarks_page      = f95_host + "/watched/threads?tab=bookmarks&bm=games&page={page}"
f95_watched_page        = f95_host + "/watched/threads?unread=0&page={page}"
f95_latest_endpoint     = f95_host + "/sam/latest_alpha/latest_data.php?cmd={cmd}&cat={cat}&page={page}&{search}={query}&sort={sort}&rows={rows}&_={ts}"
f95_ddl_endpoint        = f95_host + "/sam/dddl.php"
f95_attachments_hosts = (
    f"https://attachments.{f95_domain}/",
    f"https://attachments.{f95_domain_com}/",
    f95_attachments_host_ninja := f"https://attachments.{f95_domain_ninja}/",
)
f95_not_forum_url_prefixes = (
    f95_host + "/sam/",
)
f95_login_error_messages = (
    b'<a href="/login/" data-xf-click="overlay">Log in or register now.</a>',
    b"<title>Log in | F95zone</title>",
    b'<form action="/login/login" method="post" class="block"',
)
f95_ratelimit_forum_errors = (
    b"<title>429 Too Many Requests</title>",
    b"<h1>429 Too Many Requests</h1>",
    b"<title>Error 429</title>",
    b"<title>DDoS-Guard</title>",
    b"<title>DDOS-GUARD</title>",
)
f95_cloudflare_captcha_messages = (
    b'(function(){window._cf_chl_opt = {',
    b"<title>Just a moment...</title>",
)
f95_temp_error_messages = (
    b'<div id="cf-error-details" class="p-0">',
    b"<b>504 - Gateway Timeout .</b>",
    b"<title>502 Bad Gateway</title>",
    b"<title>Error 502</title>",
    b"An unexpected error occurred. Please try again later.",
    b"An unexpected database error occurred. Please try again later.\n<!--",
    b"<!-- Connection refused -->",
    b"<!-- Too many connections -->",
    b"<p>Automated backups are currently executing. During this time, the site will be unavailable</p>",
    b"<title>F95Zone :: Maintenance</title>",
    b"<title>F95Zone :: Scheduled Maintenance</title>",
    b'<script src="https://static.f95zone.to/assets/SamF95/ErrorPage',
    b'<div class="blockMessage"><p>Please check back in 10 mins</p></div>',
)

api_host = os.environ.get("F95INDEXER_URL") or "https://api.f95checker.dev"
api_fast_check_url = api_host + "/fast?ids={ids}"
api_full_check_url = api_host + "/full/{id}?ts={ts}"
api_fast_check_max_ids = 10

app_update_endpoint = "https://api.github.com/repos/WillyJL/F95Checker/releases/latest"

insecure_ssl_allowed_hosts = (
    f95_attachments_host_ninja,  # Invalid SSL cert but still works and is ran by F95zone
)

updating = False
session: aiohttp.ClientSession = None
ssl_context: ssl.SSLContext = None
# VENDORED: desktop reads this from the Qt webview module after browser login,
# headless server has no webview so it persists the UA pasted with the cookies.
# Cloudflare's cf_clearance cookie is bound to the UA that solved the challenge.
webview_user_agent: str = None


def user_agent_path() -> pathlib.Path:
    return globals.data_path / "browser-user-agent.txt"


def load_user_agent():
    global webview_user_agent
    try:
        webview_user_agent = user_agent_path().read_text("utf-8").strip() or None
    except OSError:
        webview_user_agent = None


def set_user_agent(user_agent: str | None):
    global webview_user_agent
    webview_user_agent = (user_agent or "").strip() or None
    if webview_user_agent:
        user_agent_path().write_text(webview_user_agent, "utf-8")
    else:
        user_agent_path().unlink(missing_ok=True)
temp_prefix = "F95Checker-Temp-"
f95_ratelimit_forum = aiolimiter.AsyncLimiter(max_rate=1, time_period=2)
f95_ratelimit_attachments = aiolimiter.AsyncLimiter(max_rate=2, time_period=1)
f95_ratelimit_sleeping = CounterContext()
fast_checks_sem: asyncio.Semaphore = None
full_checks_sem: asyncio.Semaphore = None
fast_checks_counter = 0
full_checks_counter = CounterContext()
images_counter = CounterContext()
downloads: dict[str, FileDownload] = {}
missing_images_interval = 60 * 5
missing_image_recheck_cooldown = 3 * 3600
missing_image_rechecks: dict[int, float] = {}
missing_images_queue: list[Game] = []
processing_games: dict[int, str] = {}


class ProcessingGame:
    """Track which game is being processed, for the bottom bar status."""
    __slots__ = ("game",)

    def __init__(self, game: Game):
        self.game = game

    def __enter__(self):
        processing_games[self.game.id] = self.game.name

    def __exit__(self, *_):
        processing_games.pop(self.game.id, None)

    async def __aenter__(self):
        self.__enter__()

    async def __aexit__(self, *exc):
        self.__exit__(*exc)


def make_session():
    global session
    old_session = session

    # Setup new HTTP session and proxy
    if globals.settings.proxy_type is ProxyType.Disabled:
        connector = None
    else:
        proxy_type = python_socks.ProxyType.HTTP
        match globals.settings.proxy_type:
            case ProxyType.SOCKS4: proxy_type = python_socks.ProxyType.SOCKS4
            case ProxyType.SOCKS5: proxy_type = python_socks.ProxyType.SOCKS5
            case ProxyType.HTTP: proxy_type = python_socks.ProxyType.HTTP
        connector = aiohttp_socks.ProxyConnector(
            proxy_type=proxy_type,
            host=globals.settings.proxy_host,
            port=globals.settings.proxy_port,
            username=globals.settings.proxy_username,
            password=globals.settings.proxy_password,
            loop=async_thread.loop,
        )
    session = aiohttp.ClientSession(
        loop=async_thread.loop,
        connector=connector,
        cookie_jar=aiohttp.DummyCookieJar(loop=async_thread.loop),
        headers={
            "User-Agent": user_agent,
        },
    )

    if old_session:
        if async_thread.loop is not None:
            async_thread.wait(old_session.close())
        else:
            # VENDORED: inline mode can't block on the caller's own loop, fire and forget
            async_thread.run(old_session.close())


@contextlib.contextmanager
def setup():
    global ssl_context

    # Setup SSL context
    if globals.os is Os.Windows:
        # Python SSL module seems to import Windows CA certs fine by itself
        ca_paths = None
    elif globals.os is Os.Linux:
        ca_paths = (
            "/etc/ssl/certs/ca-certificates.crt",                 # Debian/Ubuntu/Gentoo etc.
            "/etc/pki/tls/certs/ca-bundle.crt",                   # Fedora/RHEL 6
            "/etc/ssl/ca-bundle.pem",                             # OpenSUSE
            "/etc/pki/tls/cacert.pem",                            # OpenELEC
            "/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem",  # CentOS/RHEL 7
            "/etc/ssl/cert.pem",                                  # Alpine Linux
        )
    elif globals.os is Os.MacOS:
        ca_paths = (
            "/opt/homebrew/etc/ca-certificates/cert.pem",  # Homebrew
            "/usr/local/etc/openssl/cert.pem",  # Homebrew?
            "/opt/local/etc/openssl/cert.pem",  # MacPorts
            "/opt/local/share/curl/curl-ca-bundle.crt",  # MacPorts
            "/etc/ssl/cert.pem",  # Standard, maybe outdated?
        )
    if ca_paths:
        # Prefer system-provided CA certs
        for ca_path in ca_paths:
            if pathlib.Path(ca_path).is_file():
                break
        else:  # Did not break, so no system CA exists, fallback to certifi
            import certifi
            ca_path = certifi.where()
        ssl_context = ssl.create_default_context(cafile=ca_path)
    else:
        ssl_context = ssl.create_default_context()

    make_session()
    load_user_agent()

    scan_loop = async_thread.run(missing_images_loop())

    try:
        yield
    finally:

        scan_loop.cancel()
        if async_thread.loop is not None:
            async_thread.wait(session.close())
        # VENDORED: inline mode can't block here, the web server lifespan closes the session itself
        cleanup_temp_files()


async def check_host(domain: str):
    try:
        # VENDORED: async_thread.loop is None in inline mode (web server)
        await asyncio.get_running_loop().run_in_executor(None, socket.gethostbyname, domain)
        return True
    except Exception:
        return False


def get_url_domain(url: str):
    return re.search(r"^https?://([^/]+)", url).group(1)


def is_f95zone_url(url: str):
    return bool(re.search(r"^https?://[^/]*\.?(" + r"|".join(re.escape(domain) for domain in f95_domains) + r")/", url))


def cookiedict(cookies: http.cookies.SimpleCookie):
    return {cookie.key: cookie.value for cookie in cookies.values()}


@contextlib.asynccontextmanager
async def request(method: str, url: str, read=True, cookies: dict = True, **kwargs):
    timeout = kwargs.pop("timeout", None)
    if not timeout:
        timeout = globals.settings.request_timeout
    retries_kw = kwargs.pop("retries", None)
    retries = globals.settings.max_retries + 1 if retries_kw is None else retries_kw
    soft_retries = 10
    headers = kwargs.pop("headers", None)
    if not headers:
        headers = {}
    insecure_ssl = url.startswith(insecure_ssl_allowed_hosts) or globals.settings.insecure_ssl
    if cookies is True or cookies is None:
        cookies = globals.cookies
    elif cookies is False:
        cookies = {}
    is_forum_request = url.startswith(f95_host) and not url.startswith(f95_not_forum_url_prefixes)
    is_attachments_request = url.startswith(f95_attachments_hosts)
    if_ratelimit_request = is_forum_request or is_attachments_request
    ratelimit_retries = 10
    ratelimit_sleep = 0
    yielded = False
    _can_ratelimit = lambda: if_ratelimit_request and ratelimit_retries > 1
    async def _do_ratelimit():
        nonlocal ratelimit_retries, ratelimit_sleep
        ratelimit_retries -= 1
        with f95_ratelimit_sleeping:
            ratelimit_sleep += 5
            await asyncio.sleep(ratelimit_sleep)
    if is_forum_request and webview_user_agent:
        headers["User-Agent"] = webview_user_agent
    req_opts = dict(
        timeout=timeout,
        allow_redirects=True,
        max_redirects=None,
        ssl=False if insecure_ssl else ssl_context,
        cookies=cookies,
        headers=headers,
    )
    while retries and ratelimit_retries:
        try:
            # Only ratelimit when connecting to F95zone
            if is_forum_request:
                maybe_ratelimit = f95_ratelimit_forum
            elif is_attachments_request:
                maybe_ratelimit = f95_ratelimit_attachments
            else:
                maybe_ratelimit = contextlib.nullcontext()
            if not if_ratelimit_request and url.startswith(f95_host):
                # Don't ratelimit before request, but allow detecting and retrying if ratelimit happens
                if_ratelimit_request = True
            async with maybe_ratelimit, session.request(
                method,
                url,
                **req_opts,
                **kwargs
            ) as req:
                if _can_ratelimit() and req.status == 429:
                    await _do_ratelimit()
                    continue
                if not read:
                    yielded = True
                    yield b"", req
                    break
                res = await req.read()
                if _can_ratelimit() and any(msg in res for msg in f95_ratelimit_forum_errors):
                    await _do_ratelimit()
                    continue
                yielded = True
                yield res, req
            break
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            # A body exception thrown into the generator after yield must not retry
            # (retrying here yields again inside athrow -> RuntimeError, leaked generator)
            if yielded:
                raise
            if globals.settings.ignore_semaphore_timeouts and isinstance(exc, OSError) and exc.errno == 121:
                soft_retries -= 1
                if not soft_retries:
                    raise
                await asyncio.sleep(1)
                continue
            retries -= 1
            if not retries:
                raise
            await asyncio.sleep(0.5)


async def fetch(method: str, url: str, **kwargs):
    async with request(method, url, **kwargs) as (res, _):
        return res


def raise_f95zone_error(res: bytes | dict, return_login=False):
    if isinstance(res, bytes):
        if b'<body data-template="error">' in res:
            try:
                html = parser.html(res)
                message = (
                    html.select_one(".p-body-pageContent .blockMessage")
                    .get_text()
                    .strip()
                )
            except Exception:
                message = None
            if message:
                raise errors.Exc(
                    "Forum error",
                    "The F95zone Forum returned a temporary error with the following message:\n"
                    f"{message}",
                    MsgBox.error
                )
            else:
                raise errors.Exc(
                    "Forum error",
                    "The F95zone Forum returned a temporary error that could not be parsed.",
                    MsgBox.error,
                    more=str(res)
                )
        if any(msg in res for msg in f95_ratelimit_forum_errors):
            raise errors.Exc(
                "Rate limit",
                "F95zone servers are ratelimiting you,\n"
                "please try again later.",
                MsgBox.warn
            )
        if any(msg in res for msg in f95_cloudflare_captcha_messages):
            # VENDORED: desktop opens a webview to solve the captcha here, headless can't
            raise errors.Exc(
                "Cloudflare captcha",
                "F95Checker hit a Cloudflare captcha while connecting to F95zone.\n"
                "\n"
                "Log in through a normal browser to solve it, then retry.",
                MsgBox.warn
            )
        if any(msg in res for msg in f95_temp_error_messages) or not res:
            raise errors.Exc(
                "Server downtime",
                "F95zone servers are currently unreachable,\n"
                "please retry in a few minutes.",
                MsgBox.warn
            )
        if any(msg in res for msg in f95_login_error_messages):
            if return_login:
                return False
            raise errors.Exc(
                "Login expired",
                "Your F95zone login session has expired,\n"
                "press try again to login.",
                MsgBox.warn
            )
        return True
    elif isinstance(res, dict):
        if res.get("status") == "error":
            more = json.dumps(res, indent=4)
            if msg := res.get("msg"):
                raise errors.Exc(
                    "API error",
                    "The F95zone API returned an 'error' status with the following message:\n"
                    f"{msg}",
                    MsgBox.error,
                    more=more
                )
            if errs := res.get("errors", []):
                if "Cookies are required to use this site. You must accept them to continue using the site." in errs:
                    if return_login:
                        return False
                    raise errors.Exc(
                        "Login expired",
                        "Your F95zone login session has expired,\n"
                        "press try again to login.",
                        MsgBox.warn
                    )
                raise errors.Exc(
                    "API error",
                    "The F95zone API returned an 'error' status with the following messages:\n"
                    " - " + "\n - ".join(errs),
                    MsgBox.error,
                    more=more
                )
            raise errors.Exc(
                "API error",
                "The F95zone API returned an 'error' status.",
                MsgBox.error,
                more=more
            )
        return True


def raise_api_error(res: bytes | dict):
    if isinstance(res, bytes):
        if any(msg in res for msg in (
            b"<title>api.f95checker.dev | 502: Bad gateway</title>",
            b"<title>api.f95checker.dev | 521: Web server is down</title>",
        )):
            raise errors.Exc(
                "Server downtime",
                "The F95Checker Cache API is currently unreachable,\n"
                "please retry in a few minutes.",
                MsgBox.warn
            )
        return True
    elif isinstance(res, dict):
        return True


async def is_logged_in():
    res = await fetch("GET", f95_check_login_fast)
    raise_f95zone_error(res)
    return b'<pre>Sorry, you have to be <a href="/login">logged in</a> to access this page</a></pre>' not in res


async def assert_login():
    # VENDORED: desktop opens a Qt webview login window; the web server accepts
    # pasted cookies instead (Phase 4), so this only reports the current state
    if not await is_logged_in():
        return False
    return True


async def download_webpage(url: str):
    if not await assert_login():
        return
    res = await fetch("GET", url)
    html = parser.html(res)
    for elem in html.find_all():
        for key, value in elem.attrs.items():
            if isinstance(value, str) and value.startswith("/"):
                elem.attrs[key] = f95_host + value
    with tempfile.NamedTemporaryFile("wb", prefix=temp_prefix, suffix=".html", delete=False) as f:
        f.write(html.prettify(encoding="utf-8"))
    return pathlib.Path(f.name).as_uri()


async def download_image(url: str, timeout: int = None):
    if timeout is None:
        timeout = globals.settings.image_timeout
    with images_counter:
        while True:
            try:
                # Fail fast: single attempt, caller-controlled timeout so slow CDNs can't stall
                res = await fetch("GET", url, timeout=timeout, retries=1, raise_for_status=True)
            except aiohttp.ClientResponseError as exc:
                if exc.status < 400:
                    raise  # Not error status
                if url.startswith("https://i.imgur.com"):
                    url = "blocked"
                else:
                    url = "dead"
                res = b""
            except aiohttp.ClientConnectorError as exc:
                # Try alternative F95zone hosts (-1 because we're checking to then use the next link)
                changed_host = False
                for host_i in range(len(f95_attachments_hosts) - 1):
                    if url.startswith(f95_attachments_hosts[host_i]):
                        url = f95_attachments_hosts[host_i + 1] + url.removeprefix(f95_attachments_hosts[host_i])
                        changed_host = True
                        break
                if changed_host:
                    continue
                if not isinstance(exc.os_error, socket.gaierror):
                    raise  # Not a dead host
                if is_f95zone_url(url):
                    raise  # Not a foreign host, raise normal connection error message
                if (await check_host(f95_domain)) and not (await check_host(get_url_domain(url))):
                    # Link is actually dead
                    url = "dead"
                    res = b""
                else:
                    raise  # Foreign host might not actually be dead
            break  # Loop is only to retry with `continue`
    return res, url


def cleanup_temp_files():
    for item in pathlib.Path(tempfile.gettempdir()).glob(f"{temp_prefix}*"):
        try:
            item.unlink()
        except Exception:
            pass


def plan_missing_image_repairs(games, now: float):
    """Split games with a missing cover file into direct re-downloads and thread re-checks."""
    fetch: list[Game] = []
    recheck: list[Game] = []
    for game in games:
        if game.custom or not game.image.missing:
            continue
        if game.archived and not globals.settings.refresh_archived_games:
            continue
        if (game.image_url or "").startswith("http"):
            fetch.append(game)
        elif now - missing_image_rechecks.get(game.id, 0) > missing_image_recheck_cooldown:
            recheck.append(game)
    return fetch, recheck


def queue_missing_images(games):
    """Queue games whose cover file is missing for sequential background repair."""
    queued = {game.id for game in missing_images_queue}
    for game in games:
        if game.id in queued:
            continue
        if game.image.missing and (game.image_url or "").startswith("http"):
            missing_images_queue.append(game)
            queued.add(game.id)


async def repair_game(game: Game):
    with ProcessingGame(game):
        try:
            data, url = await download_image(game.image_url)
        except Exception:
            return  # Transient failure, next scan re-queues this game
        await game.set_image_async(data)
        if url != game.image_url:
            # Link was marked "dead"/"blocked", stop retrying it directly
            game.image_url = url
            await db.update_game(game, "image_url")


async def missing_images_loop():
    # VENDORED: disabled headless; the web server fetches covers on demand
    if globals.gui is None:
        return
    next_scan = 0.0
    while True:
        await asyncio.sleep(1)
        try:
            now = time.time()
            if now >= next_scan:
                # Initial scan runs as soon as GUI is up, then on every interval
                next_scan = now + missing_images_interval
                if not utils.is_refreshing():
                    fetch, recheck = plan_missing_image_repairs(games=globals.games.values(), now=now)
                    queue_missing_images(fetch)
                    for game in recheck:
                        missing_image_rechecks[game.id] = now
            # Repair queued games one at a time, bottom bar shows each game
            while missing_images_queue and not utils.is_refreshing():
                game = missing_images_queue.pop(0)
                if not game.image.missing:
                    continue
                await repair_game(game)
        except Exception:
            # Transient network or disk failure, retry next tick
            pass


def latest_updates_search_sanitize_query(query: str):
    redis_stopwords = (
        "a",
        "is",
        "the",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "but",
        "by",
        "for",
        "if",
        "in",
        "into",
        "it",
        "no",
        "not",
        "of",
        "on",
        "or",
        "such",
        "that",
        "their",
        "then",
        "there",
        "these",
        "they",
        "this",
        "to",
        "was",
        "will",
        "with",
    )
    query = re.sub(r"’s |'s ", " ", query)
    query = query.encode("ascii", errors="replace").decode()
    query = re.sub(r"\.+ | \.+", " ", query)
    for char in "?&/':;-.+!~(),*":
        query = query.replace(char, " ")
    query = re.sub(r"\s+", " ", query).strip()
    words = query.split(" ")
    for stopword in redis_stopwords:
        for word in words.copy():
            if word.lower() == stopword:
                words.remove(word)
    query = ""
    while words:
        append = f"{' ' if query else ''}{words.pop(0)}"
        if len(query + append) > 30:
            append = append[: 30 - len(query)]
            if len(append) > 3 and append.strip().lower() not in redis_stopwords:
                query += append
            break
        query += append
    return query


async def latest_updates_search(category: str, search: str, query: str, sort="likes", count=15, page=1):
    res = await fetch("GET", f95_latest_endpoint.format(
        cmd="list",
        cat=category,
        page=page,
        search=search,
        query=query,
        sort=sort,
        rows=count,
        ts=int(time.time()),
    ))
    raise_f95zone_error(res)
    res = json.loads(res)
    raise_f95zone_error(res)
    results = []
    for result in res["msg"]["data"]:
        results.append(SearchResult(
            title=result["title"],
            creator=result["creator"],
            url=f95_threads_page + str(result["thread_id"]),
            id=int(result["thread_id"]),
        ))
    return results


# VENDORED: import helpers return the extracted threads instead of adding games
# and popping dialogs; the web server turns them into one queued refresh (Phase 4)
async def import_url_shortcut(file: str | pathlib.Path) -> list[ThreadMatch]:
    parser = configparser.RawConfigParser()
    try:
        parser.read(file)
        return utils.extract_thread_matches(parser.get("InternetShortcut", "URL"))
    except Exception:
        return []


async def import_browser_bookmarks(file: str | pathlib.Path) -> list[ThreadMatch]:
    async with aiofiles.open(file, "rb") as f:
        raw = await f.read()
    html = parser.html(raw)
    threads = []
    for bookmark in html.find_all(lambda elem: "href" in getattr(elem, "attrs", "")):
        threads += utils.extract_thread_matches(bookmark.get("href"))
    return threads


async def import_f95_bookmarks() -> list[ThreadMatch]:
    globals.refresh_total = 1
    globals.refresh_progress = 0
    page = 1
    threads = []
    while True:
        globals.refresh_total += 1
        res = await fetch("GET", f95_bookmarks_page.format(page=page))
        raise_f95zone_error(res)
        html = parser.html(res)
        bookmarks = html.find(parser.is_class("p-body-pageContent")).find(parser.is_class("structItemContainer"))
        globals.refresh_progress += 1
        if not bookmarks:
            break
        page += 1
        for title in bookmarks.find_all(parser.is_class("structItem-title")):
            threads += utils.extract_thread_matches(title.get("uix-data-href"))
    return threads


async def import_f95_watched_threads() -> list[ThreadMatch]:
    globals.refresh_total = 1
    globals.refresh_progress = 0
    page = 1
    threads = []
    while True:
        globals.refresh_total += 1
        res = await fetch("GET", f95_watched_page.format(page=page))
        raise_f95zone_error(res)
        html = parser.html(res)
        watched = html.find(parser.is_class("p-body-pageContent")).find(parser.is_class("structItemContainer"))
        globals.refresh_progress += 1
        if not watched:
            break
        page += 1
        for title in watched.find_all(parser.is_class("structItem-title")):
            threads += utils.extract_thread_matches(title.get("uix-data-href"))
    return threads


def last_check_before(before_version: str, checked_version: str):
    checked = (checked_version or "0").split(".")
    before = before_version.split(".")
    if len(before) > len(checked):
        checked += ["0" for _ in range(len(before) - len(checked))]
    elif len(checked) > len(before):
        before += ["0" for _ in range(len(checked) - len(before))]
    is_before = False
    for ch, bf in zip(checked, before):
        if ch == bf:
            continue  # Ignore this field if same on both versions
        is_before = int(ch) < int(bf)
        break  # If field is smaller then its before
    return is_before


async def fast_check(games: list[Game], full: bool, updates: dict[int, OldGame], api_errors: dict[int, str], missing_threads: list[int]):
    games = list(filter(lambda game: not game.custom, games))

    global fast_checks_counter
    fast_checks_counter += len(games)
    try:
        async with fast_checks_sem:
            res = None
            try:
                res = await fetch("GET", api_fast_check_url.format(ids=",".join(str(game.id) for game in games)), timeout=120, cookies=False)
                raise_api_error(res)
                last_changes = json.loads(res)
                raise_api_error(last_changes)
            except Exception as exc:
                if isinstance(exc, errors.Exc) or not res:
                    raise exc
                raise errors.Exc(
                    "Fast check error",
                    "Something went wrong checking some of your games:\n"
                    f"{error.text()}\n"
                    "\n"
                    "Click below to see the response body and traceback.\n"
                    "Please submit a bug report on F95zone or GitHub including these.",
                    MsgBox.error,
                    more=f"Response body:\n{str(res)[:10000]}\n\n{error.traceback()}",
                )
    finally:
        fast_checks_counter -= len(games)

    full_queue: list[tuple[Game, int]] = []
    for game in games:
        last_changed = last_changes.get(str(game.id), 0)
        assert last_changed > 0, "Invalid last_changed from fast check API"
        check_new_enums = False
        if globals.version != game.last_check_version:
            check_new_enums = (
                Tag.unknown in game.tags or
                game.type is Type.Unknown or
                game.status is Status.Unknown
            )

        this_full = full or (
            check_new_enums or
            game.status is Status.Unchecked or
            last_changed > game.last_full_check or
            (game.image.missing and (game.image_url.startswith("http") or not game.image_url)) or
            last_check_before("10.1.1", game.last_check_version)  # Switch away from HEAD requests, new version parsing
        )
        if not this_full:
            globals.refresh_progress += 1
            continue

        full_queue.append((game, last_changed))

    tasks: list[asyncio.Task] = []
    try:
        tasks = [asyncio.create_task(full_check(game, ts, updates, api_errors, missing_threads)) for game, ts in full_queue]
        # VENDORED: one game's failure must not abort the whole refresh; record it
        # against that game and let the other full checks finish
        results = await asyncio.gather(*tasks, return_exceptions=True)
    except BaseException:
        for task in tasks:
            task.cancel()
        raise
    for (game, _), result in zip(full_queue, results):
        if isinstance(result, BaseException):
            api_errors[game.id] = error.text(result) if isinstance(result, Exception) else (str(result) or type(result).__name__)
            globals.refresh_progress += 1


async def full_check(game: Game, last_changed: int, updates: dict[int, OldGame], api_errors: dict[int, str], missing_threads: list[int]):
    async with full_checks_counter, full_checks_sem, ProcessingGame(game):

        async with request("GET", api_full_check_url.format(id=game.id, ts=last_changed), timeout=globals.settings.request_timeout * 2, cookies=False) as (res, req):
            raise_api_error(res)
            thread = json.loads(res)
            raise_api_error(thread)
            url = f95_threads_page + str(game.id)

        api_error = thread.get("INDEX_ERROR")

        # If there is thread data, regardless of cache api errors, save it
        if "name" in thread:
            # Redis only allows string values, so API only gives str for simplicity
            try:
                thread["type"] = Type(int(thread["type"]))
            except ValueError:
                thread["type"] = Type.Unknown
            try:
                thread["status"] = Status(int(thread["status"]))
            except ValueError:
                thread["status"] = Status.Unknown
            thread["last_updated"] = int(thread["last_updated"])
            thread["score"] = float(thread["score"])
            thread["votes"] = int(thread["votes"])
            thread["tags"] = json.loads(thread["tags"])
            for i in range(len(thread["tags"])):
                try:
                    thread["tags"][i] = Tag(thread["tags"][i])
                except ValueError:
                    thread["tags"][i] = Tag.unknown
            thread["tags"] = tuple(thread["tags"])
            thread["unknown_tags"] = json.loads(thread["unknown_tags"])
            thread["downloads"] = json.loads(thread["downloads"])
            for _, links in thread["downloads"]:
                for link_i, link_pair in enumerate(links):
                    links[link_i] = tuple(link_pair)
            thread["previews_urls"] = json.loads(thread.get("previews_urls", "[]"))
            thread["downloads"] = tuple(thread["downloads"])
            thread["reviews_total"] = int(thread.get("reviews_total", "0"))
            thread["reviews"] = json.loads(thread.get("reviews", "[]"))
            thread["reviews"] = [Review(**review) for review in thread["reviews"]]

            old_name = game.name
            old_version = game.version
            old_status = game.status

            version = thread["version"]
            if not version:
                version = "N/A"

            if old_status is not Status.Unchecked:
                if game.developer != thread["developer"]:
                    game.add_timeline_event(TimelineEventType.ChangedDeveloper, game.developer, thread["developer"])

                if game.type != thread["type"]:
                    game.add_timeline_event(TimelineEventType.ChangedType, game.type.name, thread["type"].name)

                if game.tags != thread["tags"]:
                    if difference := [tag.text for tag in thread["tags"] if tag not in game.tags]:
                        game.add_timeline_event(TimelineEventType.TagsAdded, ", ".join(difference))
                    if difference := [tag.text for tag in game.tags if tag not in thread["tags"]]:
                        game.add_timeline_event(TimelineEventType.TagsRemoved, ", ".join(difference))

                if game.score != thread["score"]:
                    if game.score < thread["score"]:
                        game.add_timeline_event(TimelineEventType.ScoreIncreased, game.score, game.votes, thread["score"], thread["votes"])
                    else:
                        game.add_timeline_event(TimelineEventType.ScoreDecreased, game.score, game.votes, thread["score"], thread["votes"])

            breaking_name_parsing    = last_check_before("9.6.4",  game.last_check_version)  # Skip name change in update popup
            breaking_version_parsing = last_check_before("10.1.1", game.last_check_version)  # Skip update popup and keep installed/finished checkboxes
            breaking_keep_old_image  = last_check_before("9.0",    game.last_check_version)  # Keep existing image files

            last_full_check = last_changed
            last_check_version = globals.version

            # Skip update popup and don't reset finished/installed checkboxes if refreshing with braking changes
            finished = game.finished
            installed = game.installed
            updated = game.updated
            if breaking_version_parsing or old_status is Status.Unchecked:
                if old_version == finished:
                    finished = version  # Is breaking and was previously finished, mark again as finished
                if old_version == installed:
                    installed = version  # Is breaking and was previously installed, mark again as installed
                old_version = version  # Don't include version change in popup for simple parsing adjustments
            else:
                if version != old_version:
                    if not game.archived:
                        updated = True

            # Don't include name change in popup for simple parsing adjustments
            if breaking_name_parsing:
                old_name = thread["name"]

            fetch_image = game.image.missing
            if game.image_url != "custom" and not breaking_keep_old_image:
                fetch_image = fetch_image or (thread["image_url"] != game.image_url)

            unknown_tags_flag = game.unknown_tags_flag
            if len(thread["unknown_tags"]) > 0 and game.unknown_tags != thread["unknown_tags"]:
                unknown_tags_flag = True

            async def update_game():
                game.name = thread["name"]
                game.version = version
                game.developer = thread["developer"]
                game.type = thread["type"]
                game.status = thread["status"]
                game.url = url
                game.last_updated = thread["last_updated"]
                # If there was a cache api error, don't update full check timestamp, so it will be
                # retried and show the warning on next refresh until error is gone
                if not api_error:
                    game.last_full_check = last_full_check
                game.last_check_version = last_check_version
                game.score = thread["score"]
                game.votes = thread["votes"]
                game.finished = finished
                game.installed = installed
                game.updated = updated
                game.description = thread["description"]
                game.changelog = thread["changelog"]
                game.tags = thread["tags"]
                game.unknown_tags = thread["unknown_tags"]
                game.unknown_tags_flag = unknown_tags_flag
                if fetch_image:
                    game.image_url = thread["image_url"]
                game.previews_urls = thread["previews_urls"]
                game.downloads = thread["downloads"]
                game.reviews_total = thread["reviews_total"]
                game.reviews = thread["reviews"]

                changed_name = thread["name"] != old_name
                changed_status = thread["status"] != old_status
                changed_version = version != old_version

                if old_status is not Status.Unchecked:
                    if changed_name:
                        game.add_timeline_event(TimelineEventType.ChangedName, old_name, game.name)
                    if changed_status:
                        game.add_timeline_event(TimelineEventType.ChangedStatus, old_status.name, game.status.name)
                    if changed_version:
                        game.add_timeline_event(TimelineEventType.ChangedVersion, old_version, game.version)

                if not game.archived and old_status is not Status.Unchecked and (
                    changed_name or changed_status or changed_version
                ):
                    old_game = OldGame(
                        id=game.id,
                        name=old_name,
                        version=old_version,
                        status=old_status,
                    )
                    updates[game.id] = old_game

            if fetch_image and thread["image_url"] and thread["image_url"].startswith("http"):
                data = b""
                ok = False
                try:
                    data, thread["image_url"] = await download_image(thread["image_url"])
                    ok = True
                except Exception:
                    # Slow or dead CDN must not stall or kill the whole refresh
                    pass
                if ok:
                    async def set_image_and_update_game():
                        await game.set_image_async(data)
                        await update_game()
                    await asyncio.shield(set_image_and_update_game())
                else:
                    await asyncio.shield(update_game())
            else:
                await asyncio.shield(update_game())

        if api_error:
            if api_error == "THREAD_MISSING":
                if not game.archived:
                    missing_threads.append(game.id)
            else:
                api_errors[game.id] = api_error

        globals.refresh_progress += 1


async def notif_counts(retry=False):
    """Return (alerts, inbox) unread counts, or None if not logged in."""
    res = None
    try:
        res = await fetch("GET", f95_notif_endpoint)
        raise_f95zone_error(res)
        res = json.loads(res)
        if "visitor" not in res:
            if retry:
                raise errors.Exc(
                    "Notifs check error",
                    "The F95zone notification endpoint returned an unknown response",
                    MsgBox.error,
                    more=json.dumps(res, indent=4)
                )
            if not await assert_login():
                return None
            return await notif_counts(retry=True)
        alerts = int(res["visitor"]["alerts_unread"].replace(",", "").replace(".", ""))
        inbox  = int(res["visitor"]["conversations_unread"].replace(",", "").replace(".", ""))
        return alerts, inbox
    except Exception as exc:
        if isinstance(exc, errors.Exc) or not res:
            raise exc
        raise errors.Exc(
            "Notifs check error",
            "Something went wrong checking your unread notifications:\n"
            f"{error.text()}\n"
            "\n"
            "Click below to see the response body and traceback.\n"
            "Please submit a bug report on F95zone or GitHub including these.",
            MsgBox.error,
            more=f"Response body:\n{str(res)[:10000]}\n\n{error.traceback()}",
        )


async def check_notifs(standalone=True, retry=False):
    # VENDORED: desktop pops a dialog + OS notification here; headless only reports counts
    if standalone:
        globals.refresh_total = 1
        globals.refresh_progress = 0
    counts = await notif_counts(retry=retry)
    globals.refresh_progress += 1
    return counts


async def refresh(*games: Game, full=False, notifs=True, notify=True, force_archived=False, force_completed=False):
    fast_queue: list[list[Game]] = [[]]
    for game in (games or globals.games.values()):
        if game.custom:
            continue
        if not games:
            if game.archived and not globals.settings.refresh_archived_games and not force_archived:
                continue
            if not game.image.missing:
                if game.status is Status.Completed and not globals.settings.refresh_completed_games and not force_completed:
                    continue
        if len(fast_queue[-1]) == api_fast_check_max_ids:
            fast_queue.append([])
        fast_queue[-1].append(game)

    notifs = notifs and globals.settings.check_notifs
    globals.refresh_progress += 1
    globals.refresh_total += sum(len(chunk) for chunk in fast_queue) + bool(notifs)
    updates: dict[int, OldGame] = {}
    api_errors: dict[int, str] = {}
    missing_threads: list[int] = []

    global fast_checks_sem, full_checks_sem, fast_checks_counter
    fast_checks_sem = asyncio.Semaphore(1)
    full_checks_sem = asyncio.Semaphore(globals.settings.max_connections)
    fast_checks_counter = 0
    tasks: list[asyncio.Task] = []
    try:
        tasks = [asyncio.create_task(fast_check(chunk, full, updates, api_errors, missing_threads)) for chunk in fast_queue]
        await asyncio.gather(*tasks)
    except BaseException:
        for task in tasks:
            task.cancel()
        fast_checks_sem = None
        full_checks_sem = None
        fast_checks_counter = 0
        raise
    fast_checks_sem = None
    full_checks_sem = None
    fast_checks_counter = 0

    # VENDORED: desktop merges and pops update notifications here; headless only
    # accumulates the update dict (the refresh job reads it from globals)
    if updates:
        globals.updates.update(updates)
        globals.updates_sorted_ids = sorted(globals.updates.keys(), key=lambda id: globals.games[id].type.category.value)

    # Don't merge with previous errors, we only care about latest ones,
    # previous errors might have disappeared since then
    globals.api_errors.clear()
    globals.missing_threads.clear()

    for id, api_error in api_errors.items():
        if api_error not in globals.api_errors:
            globals.api_errors[api_error] = set()
        globals.api_errors[api_error].add(id)
    globals.missing_threads.update(missing_threads)
    # VENDORED: desktop pops error/missing-thread dialogs here; the refresh job
    # reads globals.api_errors and globals.missing_threads instead

    if notifs:
        await check_notifs(standalone=False)

    if not games:
        globals.settings.last_successful_refresh.update(time.time())
        await db.update_settings("last_successful_refresh")


async def download_file(download: FileDownload):
    try:
        download.path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(download.path, "wb") as file:
            download.progress = 0
            download.total = None
            download.cancel = False
            download.error = None
            download.traceback = None
            download.state = download.State.Downloading
            download.start = time.time()

            can_resume = None
            while True:
                if can_resume and download.total:
                    headers = {"Range": f"bytes={download.progress}-{download.total}"}
                else:
                    headers = None

                async with request(
                    "GET", download.url,
                    cookies=download.cookies,
                    headers=headers,
                    timeout=3600 * 24,
                    read=False,
                ) as (_, req):
                    if can_resume is None:
                        can_resume = req.headers.get("Accept-Ranges") == "bytes"
                    if download.total is None:
                        download.total = req.content_length

                    try:
                        while True:
                            try:
                                rv = await asyncio.wait_for(req.content.readchunk(), timeout=0.25)
                                if rv == (b"", False):
                                    break
                                (chunk, _) = rv
                            except (asyncio.TimeoutError, TimeoutError):
                                chunk = None
                            if download.cancel:
                                download.error = "Interrupted by user"
                                return
                            if chunk:
                                download.progress += await file.write(chunk)
                                download.current = time.time()
                    except aiohttp.ClientPayloadError as exc:
                        if "ContentLengthError" in str(exc):
                            continue
                        raise
                break  # Loop is only to resume with `continue`

        if download.checksum:
            download.state = download.State.Verifying
            def _file_checksum_sync():
                with open(download.path, "rb") as file:
                    return hashlib.file_digest(file, download.checksum[0]).hexdigest()
            checksum = await asyncio.get_event_loop().run_in_executor(None, _file_checksum_sync)
            if checksum.lower() != download.checksum[1].lower():
                download.error = f"{download.checksum[0].upper()} checksum mismatch"
                return

        if globals.settings.downloads_extract and (archive_format := shutil._find_unpack_format(str(download.path))):
            download.state = download.State.Extracting
            download.extracted = download.path.with_suffix("")
            await asyncio.get_event_loop().run_in_executor(
                None,
                shutil.unpack_archive,
                download.path,
                download.extracted,
                archive_format,
            )

    except Exception:
        download.error = error.text()
        download.traceback = error.traceback()
    finally:
        download.state = download.State.Stopped


async def ddl_file_list(thread_id: int, retry=False):
    res = await fetch("POST", f95_ddl_endpoint, params={"raw": 1}, data={
        "thread_id": thread_id,
    })
    raise_f95zone_error(res)
    res = json.loads(res)
    if res["status"] == "error":
        if res["msg"] == "Not logged in" and not retry:
            if not await assert_login():
                return False
            return await ddl_file_list(thread_id, retry=True)
        if res["msg"] == "Not a donor":
            return "You don't have access to F95zone Donor DDL Service!"
    raise_f95zone_error(res)
    results = res["msg"]
    sections = results["files"]
    results["files"] = {}

    for section, files in sections.items():
        parsed = []
        for title, file in files.items():
            if not isinstance(file, dict):
                parsed.append(DdlFile(
                    thread_id=thread_id,
                    id="",
                    title=title,
                    filename=file,
                    size=0,
                    date="",
                    sha1="",
                ))
                continue
            parsed.append(DdlFile(
                thread_id=thread_id,
                id=file["file_id"],
                title=title,
                filename=file["filename"],
                size=int(file["size"]),
                date=file["date"],
                sha1=file["hash"],
            ))
        if match := re.match(r"\[SPOILER=(.+)\]", section):
            section = match.group(1)
        results["files"][section] = parsed
    return results


async def ddl_file_link(session_id: str, file: DdlFile):
    res = await fetch("POST", f95_ddl_endpoint, params={"raw": 1}, data={
        "thread_id": file.thread_id,
        "file": file.id,
        "session": session_id,
    })
    raise_f95zone_error(res)
    res = json.loads(res)
    raise_f95zone_error(res)
    link = res["msg"]["url"]
    cookies = res["msg"]["cookie"]
    return link, cookies
