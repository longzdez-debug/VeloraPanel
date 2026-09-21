from pathlib import Path
import sys


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


ROOT = project_root()
SETTINGS_DIR = ROOT / "settings"
RUNTIME_PATH = ROOT / "runtime.json"
LOGPASS_PATH = ROOT / "logpass.txt"
MAFILES_DIR = ROOT / "mafiles"
