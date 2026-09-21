from __future__ import annotations
import os,subprocess,time
from dataclasses import dataclass
@dataclass(frozen=True)
class ProcessIdentity: pid:int;created:float;executable:str
class ProcessSupervisor:
 def __init__(self):self.owned={}
 def launch(self,executable,*args):
  p=subprocess.Popen([executable,*args],close_fds=True)
  ident=ProcessIdentity(p.pid,time.time(),os.path.abspath(executable));self.owned[p.pid]=ident;return ident
 def is_owned(self,pid):
  x=self.owned.get(pid)
  if not x:return False
  try:return os.path.abspath(self._exe(pid))==x.executable
  except OSError:return False
 def _exe(self,pid):return __import__("psutil").Process(pid).exe()
 def forget(self,pid):self.owned.pop(pid,None)
