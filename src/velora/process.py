from __future__ import annotations
import subprocess
from dataclasses import dataclass
@dataclass(frozen=True)
class ProcessIdentity: pid:int; executable:str|None=None
class ProcessSupervisor:
    def __init__(self,command:list[str]):self.command=command;self.process=None
    def start(self)->ProcessIdentity:
        if self.process and self.process.poll() is None:return ProcessIdentity(self.process.pid)
        self.process=subprocess.Popen(self.command);return ProcessIdentity(self.process.pid,self.command[0] if self.command else None)
    def stop(self)->None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:self.process.kill()
        self.process=None
