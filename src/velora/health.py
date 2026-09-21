from __future__ import annotations
from dataclasses import dataclass
from time import monotonic
@dataclass
class Health:
 started:float=monotonic()
 gsi_last:float|None=None
 errors:int=0
 def gsi_age(self):return None if self.gsi_last is None else monotonic()-self.gsi_last
