import os
import pathlib
import sys
import tempfile

server_dir = pathlib.Path(__file__).resolve().parents[1]
repo_root = server_dir.parents[1]

# The server must only ever see the vendored packages. Running `python -m pytest`
# from the repo root puts it on sys.path, and namespace packages would merge the
# desktop dirs into common/modules/external __path__.
sys.path[:] = [p for p in sys.path if pathlib.Path(p or ".").resolve() != repo_root]

sys.path.insert(0, str(server_dir))              # for app
sys.path.insert(0, str(server_dir / "vendor"))   # for modules/common/external

# Throwaway data dir, before anything imports the vendored modules/globals.py.
# Force it: an inherited F95CHECKER_DATA_DIR (e.g. a real library) would let tests
# migrate and delete files in the user's data dir.
os.environ["F95CHECKER_DATA_DIR"] = tempfile.mkdtemp(prefix="f95checker-test-")
