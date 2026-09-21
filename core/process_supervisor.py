"""Safe Steam/CS2 process and window correlation helpers."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import psutil
import win32gui
import win32process


@dataclass(frozen=True)
class ProcessBinding:
    steam_pid: int
    steam_create_time: float
    cs2_pid: int
    cs2_create_time: float


def _same_process(process: psutil.Process, pid: int, create_time: float | None = None) -> bool:
    try:
        if process.pid != int(pid) or not process.is_running():
            return False
        if create_time is not None and abs(process.create_time() - float(create_time)) > 0.01:
            return False
        return True
    except (TypeError, ValueError, psutil.Error):
        return False


def is_expected_process(
    pid: int | None,
    expected_name: str,
    create_time: float | None = None,
    executable: str | None = None,
) -> bool:
    if not pid:
        return False
    try:
        process = psutil.Process(int(pid))
        if not _same_process(process, int(pid), create_time):
            return False
        if process.name().lower() != expected_name.lower():
            return False
        if executable:
            return Path(process.exe()).resolve() == Path(executable).resolve()
        return True
    except (OSError, psutil.Error, TypeError, ValueError):
        return False


def find_cs2_child(steam_pid: int, cs2_executable: str | None = None) -> psutil.Process | None:
    """Return a CS2 child of the specific Steam process, never an unrelated instance."""
    if not is_expected_process(steam_pid, "steam.exe"):
        return None
    try:
        steam = psutil.Process(int(steam_pid))
        children = steam.children(recursive=True)
    except (psutil.Error, TypeError, ValueError):
        return None

    for child in children:
        try:
            if child.name().lower() != "cs2.exe":
                continue
            if cs2_executable and Path(child.exe()).resolve() != Path(cs2_executable).resolve():
                continue
            return child
        except (OSError, psutil.Error):
            continue
    return None


def wait_for_cs2_child(
    steam_pid: int,
    timeout: float,
    cs2_executable: str | None = None,
    poll_interval: float = 0.5,
) -> psutil.Process | None:
    deadline = time.monotonic() + max(0.1, timeout)
    while time.monotonic() < deadline:
        child = find_cs2_child(steam_pid, cs2_executable)
        if child is not None:
            return child
        time.sleep(max(0.1, poll_interval))
    return None


def make_binding(steam: psutil.Process, cs2: psutil.Process) -> ProcessBinding:
    return ProcessBinding(
        steam_pid=steam.pid,
        steam_create_time=steam.create_time(),
        cs2_pid=cs2.pid,
        cs2_create_time=cs2.create_time(),
    )


def find_main_window(pid: int) -> int:
    candidates = []

    def callback(hwnd, _):
        try:
            if not win32gui.IsWindowVisible(hwnd) or not win32gui.IsWindowEnabled(hwnd):
                return True
            if win32gui.GetParent(hwnd) != 0:
                return True
            _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
            if window_pid != pid:
                return True
            rect = win32gui.GetWindowRect(hwnd)
            area = max(0, rect[2] - rect[0]) * max(0, rect[3] - rect[1])
            if area > 0:
                candidates.append((area, hwnd))
        except (OSError, RuntimeError):
            pass
        return True

    win32gui.EnumWindows(callback, None)
    return max(candidates, default=(0, 0))[1]
