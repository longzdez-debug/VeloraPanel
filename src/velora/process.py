from dataclasses import dataclass
from pathlib import Path
import subprocess,time
@dataclass(frozen=True)
class ProcessIdentity:pid:int;created:float;executable:str
class ProcessSupervisor:
 def __init__(self):self._owned={}
 def launch(self,key,executable,args=None,cwd=None):
  p=subprocess.Popen([executable,* (args or [])],cwd=cwd);i=ProcessIdentity(p.pid,time.time(),str(Path(executable).resolve()));self._owned[key]=i;return i
 def owned(self,key):return self._owned.get(key)
 def forget(self,key):self._owned.pop(key,None)
