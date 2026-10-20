"""Browser login window.

The desktop app embeds QtWebEngine so the user can log in and solve the
Cloudflare challenge; headless HTTP clients can't. The web server opens a real
Chrome window instead, then stores the resulting cookies and UA.

Chrome, not Playwright's Firefox: Firefox always reports navigator.webdriver,
so the Turnstile challenge never passes.
"""
import asyncio
import time

from modules import api, db, globals

LOGIN_URL = "https://f95zone.to/login/"
DOMAIN = "https://f95zone.to"
TIMEOUT = 300  # seconds the window may stay open
SETTLE = 2     # let Cloudflare finish writing its cookies before harvesting
PROFILE = "login-browser"
BROWSER_CHANNEL = "msedge"  # Edge is preinstalled on Windows


class BrowserLogin:
    def __init__(self):
        self.state = "idle"  # idle | running | done | error
        self.error: str | None = None
        self._task: asyncio.Task | None = None

    def status(self) -> dict:
        return {"state": self.state, "error": self.error}

    def start(self) -> dict:
        if self.state != "running":
            self.state = "running"
            self.error = None
            self._task = asyncio.create_task(self._run())
        return self.status()

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run(self):
        try:
            cookies, user_agent = await self._login()
        except asyncio.CancelledError:
            self.state = "idle"
            raise
        except Exception as exc:
            self.state = "error"
            self.error = str(exc) or type(exc).__name__
            return
        await db.update_cookies(cookies)
        await db.save()
        api.set_user_agent(user_agent)
        self.state = "done"

    async def _login(self) -> tuple[dict, str]:
        from playwright.async_api import async_playwright

        async with async_playwright() as pw:
            # Persistent profile keeps cf_clearance for the next attempt
            context = await pw.chromium.launch_persistent_context(
                str(globals.data_path / PROFILE),
                channel=BROWSER_CHANNEL,
                headless=False,
                ignore_default_args=["--enable-automation"],
                args=["--disable-blink-features=AutomationControlled"],
            )
            try:
                page = context.pages[0] if context.pages else await context.new_page()
                # Read the UA before navigating so a closed window can't lose it
                user_agent = await page.evaluate("navigator.userAgent")
                await page.goto(LOGIN_URL, wait_until="domcontentloaded")

                deadline = time.monotonic() + TIMEOUT
                while True:
                    cookies = {c["name"]: c["value"] for c in await context.cookies(DOMAIN)}
                    if cookies.get("xf_user"):
                        break
                    if page.is_closed():
                        raise RuntimeError("The browser was closed before logging in")
                    if time.monotonic() > deadline:
                        raise TimeoutError("Timed out waiting for the F95zone login")
                    await asyncio.sleep(1)

                await asyncio.sleep(SETTLE)
                cookies = {c["name"]: c["value"] for c in await context.cookies(DOMAIN)}
                return cookies, user_agent
            finally:
                await context.close()


browser_login = BrowserLogin()
