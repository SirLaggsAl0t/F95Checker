# NEW for the web server — equivalent of the desktop modules/msgbox.py Exc class,
# without any GUI; the HTTP layer catches it directly.
from common.structs import MsgBox


class Exc(Exception):
    __slots__ = ("title", "msg", "level", "buttons", "more",)

    def __init__(self, title: str, msg: str, level: MsgBox = None, buttons: dict = True, more: str = None):
        self.title = title
        self.msg = msg
        self.level = level
        self.buttons = buttons
        self.more = more
        super().__init__(f"{title}: {msg}")
