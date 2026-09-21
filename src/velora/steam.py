from __future__ import annotations
import os
from pathlib import Path
def find_steam():
 candidates=[Path(os.environ.get("PROGRAMFILES(X86)",""))/"Steam",Path(os.environ.get("PROGRAMFILES",""))/"Steam"]
 for p in candidates:
  if (p/"steam.exe").exists():return p
 return None
def find_cs2(steam:Path|None):
 if not steam:return None
 p=steam/"steamapps/common/Counter-Strike Global Offensive/game/bin/win64/cs2.exe"
 return p if p.exists() else None
