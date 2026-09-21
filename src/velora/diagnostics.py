from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import os
import socket

import psutil

from .steam import find_cs2, find_steam


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str


def _port_owner(host: str, port: int) -> int | None:
    try:
        for conn in psutil.net_connections(kind="tcp"):
            if not conn.laddr or conn.laddr.port != port:
                continue
            if host not in {"0.0.0.0", "::"}:
                address = conn.laddr.ip
                if address not in {host, "0.0.0.0", "::"}:
                    continue
            return conn.pid
    except (psutil.Error, OSError):
        return None
    return None


def _port_available(host: str, port: int) -> tuple[bool, str]:
    owner = _port_owner(host, port)
    if owner == os.getpid():
        return True, f"{host}:{port} is in use by VELORA PANEL (self)"
    if owner:
        return False, f"{host}:{port} is already in use by PID {owner}"

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(0.25)
        result = sock.connect_ex((host, port))
        if result == 0:
            return False, f"{host}:{port} is already in use"
        return True, f"{host}:{port} is available"
    except OSError as exc:
        return False, str(exc)
    finally:
        sock.close()


def run_checks(data_dir="data", gsi_port=27100, dashboard_port=8765, host="127.0.0.1"):
    steam = find_steam()
    cs2 = find_cs2(steam)
    data_path = Path(data_dir)
    gsi_ok, gsi_detail = _port_available(host, int(gsi_port))
    dashboard_ok, dashboard_detail = _port_available(host, int(dashboard_port))
    return [
        Check("python", True, "runtime available"),
        Check("steam", steam is not None, str(steam or "not found")),
        Check("cs2", cs2 is not None, str(cs2 or "not found")),
        Check("data_dir", data_path.exists(), str(data_path.resolve())),
        Check("gsi_port", gsi_ok, gsi_detail),
        Check("dashboard_port", dashboard_ok, dashboard_detail),
    ]


def as_dict(checks):
    return [asdict(x) for x in checks]
