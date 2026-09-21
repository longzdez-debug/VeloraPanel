import os
from types import SimpleNamespace

from velora.diagnostics import _port_available, run_checks


def test_diagnostics_accepts_runtime_ports(tmp_path):
    checks = run_checks(str(tmp_path), 0, 0)
    names = {item.name for item in checks}
    assert {"python", "steam", "cs2", "data_dir", "gsi_port", "dashboard_port"} <= names


def test_port_owned_by_current_process_is_healthy(monkeypatch):
    monkeypatch.setattr(
        "velora.diagnostics.psutil.net_connections",
        lambda kind="tcp": [
            SimpleNamespace(laddr=SimpleNamespace(ip="127.0.0.1", port=8765), pid=os.getpid())
        ],
    )

    ok, detail = _port_available("127.0.0.1", 8765)

    assert ok is True
    assert "VELORA PANEL (self)" in detail


def test_port_owned_by_other_process_is_failure(monkeypatch):
    monkeypatch.setattr(
        "velora.diagnostics.psutil.net_connections",
        lambda kind="tcp": [
            SimpleNamespace(laddr=SimpleNamespace(ip="127.0.0.1", port=27100), pid=12345)
        ],
    )

    ok, detail = _port_available("127.0.0.1", 27100)

    assert ok is False
    assert "PID 12345" in detail
