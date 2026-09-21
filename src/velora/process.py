from __future__ import annotations
import os,subprocess,time
from dataclasses import dataclass
@dataclass(frozen=True)
class ProcessIdentity:
 pid:int;created:float;executable:str;cmdline:tuple[str,...]=()
class ProcessSupervisor:
 def __init__(self):self.owned:dict[int,ProcessIdentity]={}
 def launch(self,executable,*args,cwd=None):
  exe=os.path.abspath(executable);p=subprocess.Popen([exe,*args],cwd=cwd,close_fds=True)
  created=self._created(p.pid);cmd=tuple(p.args if isinstance(p.args,list) else [str(p.args)])
  ident=ProcessIdentity(p.pid,created,exe,cmd);self.owned[p.pid]=ident;return ident
 def _created(self,pid):
  try:return float(__import__("psutil").Process(pid).create_time())
  except Exception:return time.time()
 def is_owned(self,pid):
  x=self.owned.get(pid)
  if not x:return False
  try:
   p=__import__("psutil").Process(pid)
   return abs(p.create_time()-x.created)<1.0 and os.path.abspath(p.exe())==x.executable and tuple(p.cmdline())[:1]==x.cmdline[:1]
  except Exception:return False
 def terminate(self,pid,timeout=5.0):
  if not self.is_owned(pid):return False
  p=__import__("psutil").Process(pid);p.terminate()
  try:p.wait(timeout)
  except __import__("psutil").TimeoutExpired:p.kill();p.wait(timeout)
  self.forget(pid);return True
 def status(self,pid):
  if not self.is_owned(pid):return "not_owned"
  try:
   p=__import__("psutil").Process(pid);return "running" if p.is_running() else "exited"
  except Exception:return "exited"
 def forget(self,pid):self.owned.pop(pid,None)
