from __future__ import annotations
import os,subprocess
from dataclasses import dataclass
import psutil
@dataclass(frozen=True)
class ProcessIdentity:
 pid:int;created:float;executable:str;cmdline:tuple[str,...]=()
class ProcessSupervisor:
 def __init__(self):self.owned={}
 def launch(self,executable,*args,cwd=None):
  exe=os.path.abspath(executable);p=subprocess.Popen([exe,*args],cwd=cwd or os.path.dirname(exe),close_fds=True)
  ident=ProcessIdentity(p.pid,p.create_time(),exe,tuple([exe,*args]));self.owned[p.pid]=ident;return ident
 def is_owned(self,pid):
  x=self.owned.get(pid)
  if not x:return False
  try:
   p=psutil.Process(pid);return abs(p.create_time()-x.created)<2 and os.path.abspath(p.exe())==x.executable and tuple(p.cmdline())[:len(x.cmdline)]==x.cmdline
  except (psutil.Error,OSError):return False
 def alive(self,pid):return self.is_owned(pid) and psutil.Process(pid).is_running()
 def terminate(self,pid,timeout=5):
  if not self.is_owned(pid):return False
  p=psutil.Process(pid);p.terminate()
  try:p.wait(timeout)
  except psutil.TimeoutExpired:p.kill();p.wait(timeout)
  self.forget(pid);return True
 def status(self,pid):
  if not self.is_owned(pid):return "unknown"
  try:return "running" if psutil.Process(pid).is_running() else "exited"
  except psutil.Error:return "exited"
 def forget(self,pid):self.owned.pop(pid,None)