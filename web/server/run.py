import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))            # for app
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "vendor"))  # for modules/common/external

import uvicorn

from app.config import HOST, PORT, RELOAD

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=RELOAD)
