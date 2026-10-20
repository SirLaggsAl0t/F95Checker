"""Copy a desktop F95Checker library into the web-owned data dir.

Copies db.sqlite3 and images/ only. Never writes to the source and never
touches the desktop's filters.pkl or imgui.ini.
"""
import argparse
import os
import pathlib
import shutil
import sys


def default_data_dir() -> pathlib.Path:
    if sys.platform.startswith("win"):
        return pathlib.Path(os.environ.get("APPDATA", pathlib.Path.home())) / "f95checker"
    if sys.platform == "darwin":
        return pathlib.Path.home() / "Library" / "Application Support" / "f95checker"
    return pathlib.Path.home() / ".config" / "f95checker"


def web_data_dir() -> pathlib.Path:
    override = os.environ.get("F95CHECKER_DATA_DIR")
    if override:
        return pathlib.Path(override)
    if sys.platform.startswith("win"):
        return pathlib.Path(os.environ.get("APPDATA", pathlib.Path.home())) / "f95checker-web"
    if sys.platform == "darwin":
        return pathlib.Path.home() / "Library" / "Application Support" / "f95checker-web"
    return pathlib.Path.home() / ".config" / "f95checker-web"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from", dest="source", type=pathlib.Path, default=default_data_dir())
    parser.add_argument("--to", dest="target", type=pathlib.Path, default=web_data_dir())
    parser.add_argument("--force", action="store_true", help="overwrite an existing web database")
    args = parser.parse_args()

    source = args.source.resolve()
    target = args.target.resolve()
    if not (source / "db.sqlite3").is_file():
        print(f"No db.sqlite3 in {source}", file=sys.stderr)
        return 1
    if (target / "db.sqlite3").exists() and not args.force:
        print(f"{target / 'db.sqlite3'} already exists; pass --force to overwrite", file=sys.stderr)
        return 1

    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / "db.sqlite3", target / "db.sqlite3")
    if (source / "images").is_dir():
        shutil.copytree(source / "images", target / "images", dirs_exist_ok=True)

    print(f"Copied {source} -> {target}")
    print("Stop the desktop app before running both, or they will overwrite each other.")
    print(f"Start the web app with F95CHECKER_DATA_DIR={target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
