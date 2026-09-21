from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import subprocess
import time
from .process import ProcessIdentity, ProcessSupervisor
from .steam import APP_ID, find_cs2, find_steam

@dataclass(frozen=True)
class LaunchResult:
    identity: ProcessIdentity
    executable: str
    via_steam: bool = False
    attached: bool = False

class Cs2Launcher:
    def __init__(self, processes=None, startup_timeout: float = 30.0):
        self.processes = processes or ProcessSupervisor()
        self.startup_timeout = max(5.0, float(startup_timeout))

    def resolve(self, configured=""):
        if configured:
            p = Path(configured).expanduser()
            if p.exists():
                return p
        return find_cs2(find_steam())

    def start(self, configured="", args=(), cwd=None, via_steam=False):
        exe = self.resolve(configured)
        if not exe:
            raise FileNotFoundError("CS2 executable was not found")

        existing = self.processes.find_existing(str(exe))
        if existing is not None:
            return LaunchResult(existing, str(exe), attached=True)

        if via_steam:
            steam = find_steam()
            if not steam:
                raise FileNotFoundError("Steam executable was not found")
            launch_started = time.time() - 1.0
            subprocess.Popen(
                [str(steam / "steam.exe"), "-applaunch", str(APP_ID), *args],
                cwd=str(steam),
                close_fds=True,
            )
            deadline = time.monotonic() + self.startup_timeout
            while time.monotonic() < deadline:
                try:
                    ident = self.processes.find_and_claim(str(exe), not_before=launch_started, manage=True)
                    if ident is not None:
                        return LaunchResult(ident, str(exe), True)
                except OSError:
                    pass
                time.sleep(0.25)
            raise TimeoutError("Steam launched, but owned CS2 process was not observed")
        ident = self.processes.launch(str(exe), *args, cwd=cwd or str(exe.parent))
        return LaunchResult(ident, str(exe), False)

    def stop(self, pid):
        return self.processes.terminate(pid)
