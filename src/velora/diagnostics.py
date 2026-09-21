from dataclasses import asdict,dataclass
from pathlib import Path
from .steam import find_cs2,find_steam

@dataclass(frozen=True)
class Check:
 name:str
 ok:bool
 detail:str

def run_checks(data_dir="data",gsi_port=27100,dashboard_port=8765):
 steam=find_steam();cs2=find_cs2(steam)
 return [
  Check("python",True,"runtime available"),
  Check("steam",steam is not None,str(steam or "not found")),
  Check("cs2",cs2 is not None,str(cs2 or "not found")),
  Check("data_dir",Path(data_dir).exists(),str(Path(data_dir).resolve())),
  Check("gsi_port",True,f"configured:{gsi_port}"),
  Check("dashboard_port",True,f"configured:{dashboard_port}"),
 ]

def as_dict(checks):return [asdict(x) for x in checks]
