from __future__ import annotations
import os
from dataclasses import dataclass
from .process import ProcessSupervisor

@dataclass(frozen=True)
class ForegroundInfo:
    hwnd: int
    pid: int

class Cs2WindowGuard:
    """Allow input only while the owned CS2 process owns the foreground window."""

    def __init__(self, processes: ProcessSupervisor, require_foreground: bool = True):
        self.processes = processes
        self.require_foreground = require_foreground
        self.pid: int | None = None
        self._user32 = None
        if os.name == "nt":
            import ctypes
            self._user32 = ctypes.windll.user32

    def bind(self, pid: int | None) -> None:
        self.pid = pid

    def foreground(self) -> ForegroundInfo | None:
        if self._user32 is None:
            return None
        hwnd = int(self._user32.GetForegroundWindow())
        if not hwnd:
            return None
        import ctypes
        pid = ctypes.c_ulong()
        self._user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return ForegroundInfo(hwnd, int(pid.value))

    def allowed(self) -> bool:
        pid = self.pid
        if pid is None or not self.processes.is_owned(pid):
            return False
        if not self.require_foreground:
            return True
        info = self.foreground()
        return info is not None and info.pid == pid
