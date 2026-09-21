from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .process import ProcessIdentity,ProcessSupervisor
from .steam import find_cs2,find_steam
@dataclass(frozen=True)
class LaunchResult:
 identity:ProcessIdentity
 executable:str
class Cs2Launcher:
 def __init__(self,processes=None):self.processes=processes or ProcessSupervisor()
 def resolve(self,configured=""):
  if configured:
   p=Path(configured).expanduser()
   if p.exists():return p
  return find_cs2(find_steam())
 def start(self,configured="",args=(),cwd=None):
  exe=self.resolve(configured)
  if not exe:raise FileNotFoundError("CS2 executable was not found")
  ident=self.processes.launch(str(exe),*args,cwd=cwd or str(exe.parent))
  return LaunchResult(ident,str(exe))
 def stop(self,pid):return self.processes.terminate(pid)
