from __future__ import annotations
import os,re
from pathlib import Path
def find_steam():
 candidates=[Path(os.environ.get("PROGRAMFILES(X86)",""))/"Steam",Path(os.environ.get("PROGRAMFILES",""))/"Steam",Path(os.environ.get("LOCALAPPDATA",""))/"Steam"]
 for p in candidates:
  if (p/"steam.exe").exists():return p
 return None
def _libraries(steam):
 out=[steam]
 vdf=steam/"steamapps/libraryfolders.vdf"
 if vdf.exists():
  text=vdf.read_text(encoding="utf-8",errors="ignore")
  for m in re.finditer(r'"path"\s+"([^"]+)"',text):
   p=Path(m.group(1).replace("\\\\","\\"))
   if p not in out:out.append(p)
 return out
def find_cs2(steam:Path|None):
 if not steam:return None
 for lib in _libraries(steam):
  p=lib/"steamapps/common/Counter-Strike Global Offensive/game/bin/win64/cs2.exe"
  if p.exists():return p
 return None
def find_app_manifest(steam:Path|None,appid=730):
 if not steam:return None
 for lib in _libraries(steam):
  p=lib/"steamapps"/f"appmanifest_{appid}.acf"
  if p.exists():return p
 return None
