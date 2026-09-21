import shutil
from pathlib import Path

from core.steam_paths import resolve_paths


def run(settings, require_node=True):
    checks = []
    steam, cs2 = resolve_paths(settings.get("SteamPath"), settings.get("CS2Path"))
    checks.append(("Steam executable", bool(steam), str(steam or "not found")))
    checks.append(("CS2 executable", bool(cs2), str(cs2 or "not found")))

    if require_node:
        node = shutil.which("node")
        checks.append(("Node.js", bool(node), str(node or "not found")))

    gsi_path = Path(settings.get("_root", Path.cwd())) / "settings" / "gamestate_integration_fsn.cfg"
    checks.append(("GSI config", gsi_path.is_file(), str(gsi_path)))
    token = settings.get("GSIAuthToken", "")
    checks.append(("GSI token", isinstance(token, str) and len(token) >= 16, "configured" if token else "missing"))
    return [
        {"name": name, "ok": ok, "detail": detail}
        for name, ok, detail in checks
    ]
