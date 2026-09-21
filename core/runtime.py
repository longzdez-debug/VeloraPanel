import psutil

from core.paths import RUNTIME_PATH
from core.storage import read_json, write_json


def _valid_process(pid, expected_name, create_time=None):
    try:
        process = psutil.Process(int(pid))
        if not process.is_running() or process.name().lower() != expected_name:
            return False
        if create_time is not None:
            return abs(process.create_time() - float(create_time)) <= 0.01
        return True
    except (TypeError, ValueError, psutil.Error):
        return False


def prune_runtime() -> list:
    entries = read_json(RUNTIME_PATH, [])
    if not isinstance(entries, list):
        raise RuntimeError("runtime.json must contain a list")

    valid = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        steam_pid = entry.get("SteamPid")
        cs2_pid = entry.get("CS2Pid")
        if (
            _valid_process(steam_pid, "steam.exe", entry.get("SteamCreateTime"))
            and _valid_process(cs2_pid, "cs2.exe", entry.get("CS2CreateTime"))
        ):
            valid.append(entry)

    if valid != entries:
        write_json(RUNTIME_PATH, valid)
    return valid
