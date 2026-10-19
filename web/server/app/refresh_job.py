"""Single-worker refresh queue. api.refresh() is not reentrant, so every run
(adds, imports, manual button, background) goes through this one queue."""
import asyncio
import dataclasses
import time

from external import error
from modules import api, globals


@dataclasses.dataclass
class RefreshRequest:
    ids: list[int] | None = None  # None = the whole library
    full: bool = False


class RefreshJob:
    def __init__(self):
        self.queue: asyncio.Queue[RefreshRequest] | None = None
        self._task: asyncio.Task | None = None
        self._pending: RefreshRequest | None = None
        self.running = False
        self.started: float | None = None
        self.errors: list[dict] = []
        self.missing_threads: list[int] = []
        self.last_result: dict | None = None

    def start(self):
        self.queue = asyncio.Queue()
        self._task = asyncio.create_task(self._worker())

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    def enqueue(self, ids: list[int] | None = None, full: bool = False):
        if ids is not None:
            ids = list(dict.fromkeys(ids))
        # Merge into a request still waiting in the queue: one run per batch of adds.
        if (self._pending is not None and ids is not None and self._pending.ids is not None
                and self._pending.full == full):
            self._pending.ids = list(dict.fromkeys(self._pending.ids + ids))
            return
        request = RefreshRequest(ids, full)
        self._pending = request
        self.queue.put_nowait(request)

    def status(self) -> dict:
        last_successful = getattr(globals.settings, "last_successful_refresh", 0)
        return {
            "state": "running" if self.running else "idle",
            "progress": globals.refresh_progress,
            "total": globals.refresh_total,
            "started": self.started,
            "errors": self.errors,
            "missing_threads": self.missing_threads,
            "last_result": self.last_result,
            "last_successful_refresh": int(getattr(last_successful, "value", last_successful) or 0),
        }

    async def _worker(self):
        while True:
            request = await self.queue.get()
            if request is self._pending:
                self._pending = None
            self.running = True
            self.started = time.time()
            try:
                await self._run(request)
            finally:
                self.running = False
                self.queue.task_done()

    async def _run(self, request: RefreshRequest):
        games = None
        if request.ids is not None:
            games = [globals.games[id] for id in request.ids if id in globals.games]
            if not games:
                return
        globals.refresh_progress = 0
        globals.refresh_total = 0
        globals.api_errors.clear()
        globals.missing_threads.clear()
        self.errors = []
        self.missing_threads = []
        updated_before = set(globals.updates)
        try:
            if games is None:
                await api.refresh(full=request.full, notifs=False, notify=False)
            else:
                await api.refresh(*games, full=request.full, notifs=False, notify=False)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            # Fatal run failure has no game; report it as one job-level error.
            self.errors = [{"game_id": None, "name": None, "msg": error.text(exc)}]
        finally:
            self.errors.extend(
                {
                    "game_id": game_id,
                    "name": globals.games[game_id].name if game_id in globals.games else "",
                    "msg": msg,
                }
                for msg, ids in globals.api_errors.items()
                for game_id in sorted(ids)
            )
            self.missing_threads = sorted(globals.missing_threads)
            self.last_result = {
                "updated": sorted(set(globals.updates) - updated_before),
                "finished_at": int(time.time()),
            }


job = RefreshJob()
