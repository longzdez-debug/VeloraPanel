from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
from .steam import find_steam,find_cs2
@dataclass(frozen=True)
class Check:
 name:str;ok:bool;detail:str
def run_checks(data_dir="data"):
 steam=find_steam();cs2=find_cs2(steam)
 return [Check("python",True,"runtime available"),Check("steam",steam is not None,str(steam or "not found")),Check("cs2",cs2 is not None,str(cs2 or "not found")),Check("data_dir",Path(data_dir).exists(),str(Path(data_dir).resolve()))]
def as_dict(checks):return [asdict(x) for x in checks]
