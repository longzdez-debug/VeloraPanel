import os
import re
from pathlib import Path


APP_ID = "730"
_DEFAULT_STEAM_RELATIVE = Path("steamapps") / "common" / "Counter-Strike Global Offensive"


def _registry_steam_path():
    try:
        import winreg

        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            for key_name in (
                r"Software\Valve\Steam",
                r"Software\WOW6432Node\Valve\Steam",
            ):
                try:
                    with winreg.OpenKey(hive, key_name) as key:
                        value, _ = winreg.QueryValueEx(key, "SteamPath")
                        if value:
                            return Path(value)
                except (FileNotFoundError, OSError):
                    continue
    except ImportError:
        pass
    return None


def discover_steam_path():
    candidates = []
    registry_path = _registry_steam_path()
    if registry_path:
        candidates.append(registry_path)
    for env_name in ("PROGRAMFILES(X86)", "PROGRAMFILES"):
        root = os.environ.get(env_name)
        if root:
            candidates.append(Path(root) / "Steam")
    for candidate in candidates:
        executable = candidate / "steam.exe"
        if executable.is_file():
            return executable
    return None


def _library_paths(steam_root):
    paths = [Path(steam_root)]
    manifest = Path(steam_root) / "steamapps" / "libraryfolders.vdf"
    if not manifest.is_file():
        return paths
    try:
        text = manifest.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return paths
    for raw_path in re.findall(r'"path"\s*"([^"]+)"', text, flags=re.IGNORECASE):
        paths.append(Path(raw_path.replace("\\\\", "\\")))
    return list(dict.fromkeys(paths))


def discover_cs2_path(steam_path=None):
    steam_root = Path(steam_path).parent if steam_path else None
    if steam_root is None or not steam_root.is_dir():
        discovered = discover_steam_path()
        steam_root = discovered.parent if discovered else None
    if steam_root is None:
        return None

    for library in _library_paths(steam_root):
        candidate = library / _DEFAULT_STEAM_RELATIVE
        if (candidate / "game" / "bin" / "win64" / "cs2.exe").is_file():
            return candidate
    return None


def resolve_paths(steam_path=None, cs2_path=None):
    steam = Path(steam_path) if steam_path else discover_steam_path()
    if steam and steam.is_dir():
        steam = steam / "steam.exe"
    if not steam or not steam.is_file():
        steam = discover_steam_path()
    cs2 = Path(cs2_path) if cs2_path else None
    if not cs2 or not (cs2 / "game" / "bin" / "win64" / "cs2.exe").is_file():
        cs2 = discover_cs2_path(steam)
    if steam and not (steam / "steam.exe" if steam.is_dir() else steam).is_file():
        steam = None
    if cs2 and not (cs2 / "game" / "bin" / "win64" / "cs2.exe").is_file():
        cs2 = None
    return steam, cs2
