# VENDORED from modules/ - GUI stripped for the web server; see web/
from concurrent.futures import Future
import os as _os
import pathlib
import re
import shlex
import shutil
import sys

from common.structs import (
    Browser,
    Game,
    OldGame,
    Os,
    Popup,
    Settings,
)

# Copy version info and main globals
version = None
release = None
build_number = None
version_name = None
rpc_port = None
rpc_url = None
frozen = None
self_path = None
debug = None
def _():
    global version, release, build_number, version_name, rpc_port, rpc_url, frozen, self_path, debug
    from common.meta import version, release, build_number, version_name, rpc_port, rpc_url, frozen, self_path, debug
_()

# VENDORED: desktop imports MainGUI here to avoid a circular import;
# headless server has no GUI, the `if globals.gui:` guards below handle None
gui = None

# Configure data paths
os = None
data_path = None
images_path = None
def _():
    global os, data_path, images_path
    # VENDORED: web server can point at another data dir (shared with desktop by default)
    if override := _os.environ.get("F95CHECKER_DATA_DIR"):
        data_path = pathlib.Path(override)
        data_path.mkdir(parents=True, exist_ok=True)
        images_path = data_path / "images"
        images_path.mkdir(parents=True, exist_ok=True)
        os = Os.Windows if sys.platform.startswith("win") else Os.Linux if sys.platform.startswith("linux") else Os.MacOS
        return
    home = pathlib.Path.home()
    if sys.platform.startswith("win"):
        os = Os.Windows
        data_path = "AppData/Roaming/f95checker"
    elif sys.platform.startswith("linux"):
        os = Os.Linux
        if (home / ".f95checker").exists() and not (home / ".config/f95checker").exists():
            (home / ".config").mkdir(parents=True, exist_ok=True)
            shutil.move(home / ".f95checker", home / ".config/f95checker")
        data_path = ".config/f95checker"
    elif sys.platform.startswith("darwin"):
        os = Os.MacOS
        data_path = "Library/Application Support/f95checker"
    else:
        print("Your system is not officially supported at the moment!\n"
            "You can let me know on the tool thread or on GitHub, or you can try porting yourself ;)")
        sys.exit(1)
    data_path = home / data_path
    data_path.mkdir(parents=True, exist_ok=True)
    images_path = data_path / "images"
    images_path.mkdir(parents=True, exist_ok=True)
_()

# Discover available browsers
def _():
    if os is Os.Windows:
        import winreg
        for registry in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                browsers = winreg.OpenKey(registry, "SOFTWARE\\Clients\\StartMenuInternet")
                try:
                    i = 0
                    while True:
                        key = winreg.EnumKey(browsers, i)
                        try:
                            name = winreg.QueryValue(browsers, key)
                            args = shlex.split(winreg.QueryValue(browsers, key + "\\shell\\open\\command"))
                            if args and shutil.which(args[0]) and pathlib.Path(shutil.which(args[0])).exists():
                                Browser.add(name, args=args)
                        except Exception:
                            pass  # Non-standard key
                        i += 1
                except OSError:
                    pass  # Stop iteration
            except FileNotFoundError:
                pass  # Key doesn't exist
    elif os is Os.Linux:
        import configparser
        for xdg_dir in _os.environ.get("XDG_DATA_DIRS", "/usr/share/").split(":"):
            try:
                if not xdg_dir:
                    continue
                app_dir = pathlib.Path(xdg_dir) / "applications"
                apps_file = app_dir / "mimeinfo.cache"
                if not apps_file.is_file():
                    continue
                raw = apps_file.read_bytes()
                apps = []
                for match in re.finditer(rb"x-scheme-handler/https?=(.+)", raw):
                    for app in match.group(1).split(b";"):
                        app = str(app, encoding="utf-8")
                        if app and app not in apps:
                            apps.append(app)
                for app in apps:
                    try:
                        app_file = app_dir / app
                        if not app_file.is_file():
                            continue
                        parser = configparser.RawConfigParser()
                        parser.read(app_file)
                        name = parser.get("Desktop Entry", "Name")
                        args = [arg for arg in shlex.split(parser.get("Desktop Entry", "Exec")) if not (len(arg) == 2 and arg.startswith("%"))]
                        if args and shutil.which(args[0]) and pathlib.Path(shutil.which(args[0])).exists():
                            Browser.add(name, args=args)
                    except Exception:
                        pass
            except Exception:
                pass
    elif os is Os.MacOS:
        import plistlib
        app_dir = pathlib.Path("/Applications")
        empty = []
        matches = ["http", "https"]
        for app in app_dir.glob("*.app"):
            try:
                app_file = app / "Contents/Info.plist"
                if not app_file.is_file():
                    continue
                parser = plistlib.loads(app_file.read_bytes())
                found = False
                for handler in parser.get("CFBundleURLTypes", empty):
                    for scheme in handler.get("CFBundleURLSchemes", empty):
                        if scheme in matches:
                            name = parser["CFBundleName"]
                            args = [app / f"Contents/MacOS/{parser['CFBundleExecutable']}"]
                            if args and shutil.which(args[0]) and pathlib.Path(shutil.which(args[0])).exists():
                                Browser.add(name, args=args)
                            found = True
                            break
                    if found:
                        break
            except Exception:
                pass
_()

# Variables
refresh_total = 0
# VENDORED: was `gui: MainGUI = None`, headless has no MainGUI type
refresh_progress = 0
last_update_check = 0.0
settings: Settings = None
refresh_task: Future = None
games: dict[int, Game] = None
cookies: dict[str, str] = None
popup_stack: list[Popup] = []
api_errors: dict[str, set[int]] = {}
missing_threads: set[int] = set()
updates: dict[int, OldGame] = {}
popup_stack_changed: bool = False
updates_sorted_ids: list[int] = []
