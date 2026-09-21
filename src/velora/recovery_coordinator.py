from __future__ import annotations
from dataclasses import dataclass
from math import hypot
from time import monotonic

@dataclass(frozen=True)
class RecoveryDecision:
 level:int
 action:str
 reason:str

class RecoveryCoordinator:
 def __init__(self,max_recoveries:int=3):
  self.max_recoveries=max(0,int(max_recoveries));self.count=0;self.level=0;self.started=0.0

 def observe(self,state:str,progress_age:float|None,localization_confidence:float,now:float|None=None)->RecoveryDecision|None:
  now=monotonic() if now is None else now
  if state not in {"stuck","slow"}: return None
  if progress_age is None or progress_age < 3.0:return None
  if self.count>=self.max_recoveries:return RecoveryDecision(6,"navigation_reset","recovery_limit")
  self.count+=1;self.level=min(6,self.count)
  self.started=now
  if localization_confidence < 0.35:
   self.level=max(self.level,4)
   return RecoveryDecision(self.level,"relocalize","low_localization_confidence")
  if self.level==1:return RecoveryDecision(1,"micro_correction","no_progress")
  if self.level==2:return RecoveryDecision(2,"local_replan","no_progress")
  return RecoveryDecision(min(3,self.level),"route_switch","repeated_no_progress")

 def reset(self):
  self.count=0;self.level=0;self.started=0.0
