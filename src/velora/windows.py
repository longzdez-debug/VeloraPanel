from __future__ import annotations
import ctypes
from ctypes import wintypes
from .input import NullInput

class WindowsInput(NullInput):
    _user32 = ctypes.windll.user32 if hasattr(ctypes, "windll") else None
    _map = {"forward": 0x57, "back": 0x53, "left": 0x41, "right": 0x44}

    def __init__(self, enabled: bool = False, guard=None):
        super().__init__()
        self.enabled = bool(enabled)
        self.guard = guard
        self._down: set[str] = set()

    def _key(self, code: int, down: bool) -> bool:
        if not self.enabled or self._user32 is None:
            return False

        class KI(ctypes.Structure):
            _fields_ = [
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
            ]

        class II(ctypes.Union):
            _fields_ = [("ki", KI)]

        class IN(ctypes.Structure):
            _fields_ = [("type", wintypes.DWORD), ("ii", II)]

        flags = 0 if down else 2
        event = IN(1, II(KI(code, 0, flags, 0, None)))
        return bool(self._user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(IN)))

    def _permitted(self) -> bool:
        if not self.enabled:
            return False
        if self.guard is None:
            return True
        try:
            return bool(self.guard.allowed())
        except Exception:
            return False

    def move(self, forward, back, left, right):
        if not self._permitted():
            self.release_all()
            super().release_all()
            return

        super().move(forward, back, left, right)
        wanted = {
            k for k, v in (
                ("forward", forward), ("back", back), ("left", left), ("right", right)
            ) if v
        }
        for k in list(self._down):
            if k not in wanted:
                self._key(self._map[k], False)
                self._down.remove(k)
        for k in wanted:
            if k not in self._down and self._key(self._map[k], True):
                self._down.add(k)

    def release_all(self):
        for k in list(self._down):
            try:
                self._key(self._map[k], False)
            finally:
                self._down.discard(k)
        super().release_all()

    def disable(self):
        self.enabled = False
        self.release_all()
