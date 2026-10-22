import asyncio
import json

from app.main import exc_handler
from common.errors import Exc
from common.structs import MsgBox


def test_exc_envelope():
    response = asyncio.run(exc_handler(None, Exc("Bad input", "URL is invalid", MsgBox.error, more="detail")))
    assert response.status_code == 400
    body = json.loads(response.body)
    assert body == {
        "detail": {"title": "Bad input", "msg": "URL is invalid", "more": "detail", "level": "error"},
    }
