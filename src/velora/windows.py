from __future__ import annotations
import os,subprocess
from pathlib import Path
class WindowsInput:
 """Windows input backend. Kept behind the WalkBot adapter boundary."""
 def __init__(self): self._down=set()
 def release_all(self):
  self._down.clear()
 def move(self,forward,back,left,right):
  desired={k for k,v in {"w":forward,"s":back,"a":left,"d":right}.items() if v}
  self._down=desired
