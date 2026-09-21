from __future__ import annotations
import ctypes
import time
from ctypes import wintypes
from .input import NullInput

class WindowsInput(NullInput):
    _user32 = ctypes.windll.user32 if hasattr(ctypes, "windll") else None
    _map = {"forward": 0x57, "back": 0x53, "left": 0x41, "right": 0x44}
    _MOUSE_MOVE = 0x0001
    _MOUSE_LEFTDOWN = 0x0002
    _MOUSE_LEFTUP = 0x0004
    _VK_OEM_3 = 0xC0
    _VK_RETURN = 0x0D

    def __init__(self, enabled: bool = False, guard=None, mouse_turn_counts: int = 320):
        super().__init__()
        self.enabled = bool(enabled)
        self.guard = guard
        self.mouse_turn_counts = max(20, int(mouse_turn_counts))
        self._down: set[str] = set()
        self._attack_down = False

    def _key(self, code: int, down: bool) -> bool:
        if not self.enabled or self._user32 is None:
            return False
        class KI(ctypes.Structure):
            _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                        ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]
        class II(ctypes.Union):
            _fields_ = [("ki", KI)]
        class IN(ctypes.Structure):
            _fields_ = [("type", wintypes.DWORD), ("ii", II)]
        flags = 0 if down else 2
        event = IN(1, II(KI(code, 0, flags, 0, None)))
        return bool(self._user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(IN)))

    def _unicode(self, text: str) -> bool:
        if not self.enabled or self._user32 is None:
            return False
        class KI(ctypes.Structure):
            _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                        ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]
        class II(ctypes.Union):
            _fields_ = [("ki", KI)]
        class IN(ctypes.Structure):
            _fields_ = [("type", wintypes.DWORD), ("ii", II)]
        ok = True
        for ch in text:
            down = IN(1, II(KI(0, ord(ch), 4, 0, None)))
            up = IN(1, II(KI(0, ord(ch), 6, 0, None)))
            ok = bool(self._user32.SendInput(1, ctypes.byref(down), ctypes.sizeof(IN))) and ok
            ok = bool(self._user32.SendInput(1, ctypes.byref(up), ctypes.sizeof(IN))) and ok
        return ok

    def _mouse_button(self, down: bool) -> bool:
        if not self.enabled or self._user32 is None:
            return False
        flags = self._MOUSE_LEFTDOWN if down else self._MOUSE_LEFTUP
        return bool(self._user32.mouse_event(flags, 0, 0, 0, 0))

    def _mouse(self, dx: int) -> bool:
        if not self.enabled or self._user32 is None or dx == 0:
            return False
        class MI(ctypes.Structure):
            _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                        ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                        ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]
        class II(ctypes.Union):
            _fields_ = [("mi", MI)]
        class IN(ctypes.Structure):
            _fields_ = [("type", wintypes.DWORD), ("ii", II)]
        event = IN(0, II(mi=MI(int(dx), 0, 0, self._MOUSE_MOVE, 0, None)))
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

    def _client_origin_size(self):
        if self._user32 is None:
            return None
        hwnd = int(self._user32.GetForegroundWindow())
        if not hwnd:
            return None
        rect = wintypes.RECT()
        if not self._user32.GetClientRect(hwnd, ctypes.byref(rect)):
            return None
        pt = wintypes.POINT(0, 0)
        if not self._user32.ClientToScreen(hwnd, ctypes.byref(pt)):
            return None
        return int(pt.x), int(pt.y), int(rect.right - rect.left), int(rect.bottom - rect.top)

    def click_normalized(self, x: float, y: float) -> bool:
        if not self._permitted() or self._user32 is None:
            return False
        geometry = self._client_origin_size()
        if not geometry:
            return False
        left, top, width, height = geometry
        sx = left + int(max(0.0, min(1.0, float(x))) * max(1, width - 1))
        sy = top + int(max(0.0, min(1.0, float(y))) * max(1, height - 1))
        if not self._user32.SetCursorPos(sx, sy):
            return False
        time.sleep(0.05)
        return self._mouse_button(True) and self._mouse_button(False)

    def console_command(self, command: str) -> bool:
        if not self._permitted():
            return False
        if not self._key(self._VK_OEM_3, True):
            return False
        self._key(self._VK_OEM_3, False)
        time.sleep(0.15)
        if not self._unicode(str(command)):
            self._key(self._VK_OEM_3, True)
            self._key(self._VK_OEM_3, False)
            return False
        self._key(self._VK_RETURN, True)
        self._key(self._VK_RETURN, False)
        time.sleep(0.1)
        self._key(self._VK_OEM_3, True)
        self._key(self._VK_OEM_3, False)
        return True

    def attack(self, down: bool):
        if not self._permitted():
            self._attack_down = False
            return
        desired = bool(down)
        if desired == self._attack_down:
            return
        if self._mouse_button(desired):
            self._attack_down = desired

    def move(self, forward, back, left, right):
        if not self._permitted():
            self.release_all()
            super().release_all()
            return
        super().move(forward, back, left, right)
        wanted = {k for k, v in (("forward", forward), ("back", back), ("left", left), ("right", right)) if v}
        for k in list(self._down):
            if k not in wanted:
                self._key(self._map[k], False)
                self._down.remove(k)
        for k in wanted:
            if k not in self._down and self._key(self._map[k], True):
                self._down.add(k)

    def turn(self, amount):
        if not self._permitted():
            self.release_all()
            return
        value = max(-1.0, min(1.0, float(amount)))
        self._mouse(int(round(value * self.mouse_turn_counts)))

    def release_all(self):
        for k in list(self._down):
            try:
                self._key(self._map[k], False)
            finally:
                self._down.discard(k)
        if self._attack_down:
            try:
                self._mouse_button(False)
            finally:
                self._attack_down = False
        super().release_all()

    def disable(self):
        self.enabled = False
        self.release_all()
