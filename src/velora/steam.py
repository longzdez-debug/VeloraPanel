from __future__ import annotations
import os
import re
from pathlib import Path

APP_ID = 730
APP_DIR = "Counter-Strike Global Offensive"

def find_steam() -> Path | None:
    candidates = [
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Steam",
        Path(os.environ.get("PROGRAMFILES", "")) / "Steam",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Steam",
    ]
    for p in candidates:
        if (p / "steam.exe").exists():
            return p
    return None

def _library_roots(steam: Path) -> list[Path]:
    roots = [steam]
    vdf = steam / "steamapps" / "libraryfolders.vdf"
    if not vdf.exists():
        return roots
    try:
        text = vdf.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return roots
    for match in re.finditer(r'"path"\s+"([^"]+)"', text):
        p = Path(match.group(1).replace("\\\\", "\\"))
        if p.exists() and p not in roots:
            roots.append(p)
    return roots

def find_cs2(steam: Path | None) -> Path | None:
    if not steam:
        return None
    for root in _library_roots(steam):
        p = root / "steamapps" / "common" / APP_DIR / "game" / "bin" / "win64" / "cs2.exe"
        if p.exists():
            return p
    return None

def find_app_manifest(steam: Path | None, app_id: int = APP_ID) -> Path | None:
    if not steam:
        return None
    for root in _library_roots(steam):
        p = root / "steamapps" / f"appmanifest_{app_id}.acf"
        if p.exists():
            return p
    return None
