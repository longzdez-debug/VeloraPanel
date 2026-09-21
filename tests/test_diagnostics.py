from velora.diagnostics import run_checks

def test_diagnostics_accepts_runtime_ports(tmp_path):
    checks = run_checks(str(tmp_path), 0, 0)
    names = {item.name for item in checks}
    assert {"python", "steam", "cs2", "data_dir", "gsi_port", "dashboard_port"} <= names
