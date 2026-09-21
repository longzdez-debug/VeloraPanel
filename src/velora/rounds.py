from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
class RoundState(str,Enum): UNKNOWN="unknown"; LIVE="live"; OVER="over"; HALFTIME="halftime"
@dataclass
class MatchTracker:
 state:RoundState=RoundState.UNKNOWN
 map_name:str|None=None
 round_number:int|None=None
 def update(self,map_name,phase,round_number=None):
  self.map_name=map_name or self.map_name
  if round_number is not None:self.round_number=round_number
  p=(phase or "").lower()
  if p in {"live","playing"}:self.state=RoundState.LIVE
  elif p in {"over","freezetime","halftime"}:self.state=RoundState.OVER if p=="over" else RoundState.HALFTIME
  return self.state
