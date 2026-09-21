from __future__ import annotations
import os, subprocess
from dataclasses import dataclass
import psutil

@dataclass(frozen=True)
class ProcessIdentity:
    pid: int
    created: float
    executable: str
    cmdline: tuple[str, ...] = ()

class ProcessSupervisor:
    def __init__(self):
        self.owned = {}

    def launch(self, executable, *args, cwd=None):
        exe = os.path.abspath(executable)
        p = subprocess.Popen([exe, *args], cwd=cwd or os.path.dirname(exe), close_fds=True)
        ident = ProcessIdentity(p.pid, p.create_time(), exe, tuple([exe, *args]))
        self.owned[p.pid] = ident
        return ident

    def claim(self, pid: int, executable: str) -> ProcessIdentity | None:
        try:
            p = psutil.Process(pid)
            exe = os.path.abspath(p.exe())
            expected = os.path.abspath(executable)
            if exe != expected:
                return None
            ident = ProcessIdentity(pid, p.create_time(), exe, tuple(p.cmdline()))
            self.owned[pid] = ident
            return ident
        except (psutil.Error, OSError):
            return None

    def find_and_claim(self, executable: str, not_before: float | None = None) -> ProcessIdentity | None:
        expected = os.path.abspath(executable)
        candidates = []
        for p in psutil.process_iter(["pid", "exe", "create_time"]):
            try:
                if p.pid in self.owned:
                    continue
                if not p.info["exe"] or os.path.abspath(p.info["exe"]) != expected:
                    continue
                created = float(p.info.get("create_time") or 0.0)
                if not_before is not None and created < not_before:
                    continue
                candidates.append((created, p.pid))
            except (psutil.Error, OSError, TypeError, ValueError):
                continue
        for _, pid in sorted(candidates, reverse=True):
            ident = self.claim(pid, expected)
            if ident is not None:
                return ident
        return None

    def is_owned(self, pid):
        x = self.owned.get(pid)
        if not x:
            return False
        try:
            p = psutil.Process(pid)
            return abs(p.create_time() - x.created) < 2 and os.path.abspath(p.exe()) == x.executable and tuple(p.cmdline())[:len(x.cmdline)] == x.cmdline
        except (psutil.Error, OSError):
            return False

    def alive(self, pid):
        if not self.is_owned(pid):
            return False
        try:
            return psutil.Process(pid).is_running()
        except (psutil.Error, OSError):
            return False

    def terminate(self, pid, timeout=5):
        if not self.is_owned(pid):
            return False
        p = psutil.Process(pid)
        p.terminate()
        try:
            p.wait(timeout)
        except psutil.TimeoutExpired:
            p.kill()
            p.wait(timeout)
        self.forget(pid)
        return True

    def status(self, pid):
        if not self.is_owned(pid):
            return "unknown"
        try:
            return "running" if psutil.Process(pid).is_running() else "exited"
        except psutil.Error:
            return "exited"

    def forget(self, pid):
        self.owned.pop(pid, None)
