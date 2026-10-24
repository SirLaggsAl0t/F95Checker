import os
import pathlib
import sys

# Bind host: 127.0.0.1 by default, set F95WEB_HOST=0.0.0.0 to expose on the LAN
HOST = os.environ.get("F95WEB_HOST", "127.0.0.1")
PORT = int(os.environ.get("F95WEB_PORT", "8642"))

# HTTP Basic auth, disabled unless both are set
USERNAME = os.environ.get("F95WEB_USERNAME") or None
PASSWORD = os.environ.get("F95WEB_PASSWORD") or None
# Fail closed: one credential set would otherwise disable auth and expose the LAN
if bool(USERNAME) != bool(PASSWORD):
    raise RuntimeError("Set both F95WEB_USERNAME and F95WEB_PASSWORD, or neither")

# Dev autoreload
RELOAD = os.environ.get("F95WEB_RELOAD", "") not in ("", "0", "false")

# Browser login opens a real window; it needs a desktop, so it is off in the container
BROWSER_LOGIN = os.environ.get("F95BROWSER_LOGIN", "") not in ("0", "false")

# Web-owned data dir, outside the repo: db.connect() rejects a DB inside self_path.
# Must be set before importing the vendored modules/globals.py.
if sys.platform.startswith("win"):
    _default_data_dir = pathlib.Path(os.environ.get("APPDATA", pathlib.Path.home())) / "f95checker-web"
    _desktop_data_dir = pathlib.Path(os.environ.get("APPDATA", pathlib.Path.home())) / "f95checker"
elif sys.platform == "darwin":
    _default_data_dir = pathlib.Path.home() / "Library" / "Application Support" / "f95checker-web"
    _desktop_data_dir = pathlib.Path.home() / "Library" / "Application Support" / "f95checker"
else:
    _default_data_dir = pathlib.Path.home() / ".config" / "f95checker-web"
    _desktop_data_dir = pathlib.Path.home() / ".config" / "f95checker"

DATA_DIR = pathlib.Path(os.environ.setdefault("F95CHECKER_DATA_DIR", str(_default_data_dir))).resolve()
DB_PATH = DATA_DIR / "db.sqlite3"
# Sharing the desktop dir is possible but unsupported: both processes cache in memory.
SHARED_WITH_DESKTOP = DATA_DIR == _desktop_data_dir.resolve()

DATA_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / "images").mkdir(exist_ok=True)
(DATA_DIR / "web-cache").mkdir(exist_ok=True)

# F95INDEXER_URL is read by the vendored modules/api.py (defaults to https://api.f95checker.dev)
