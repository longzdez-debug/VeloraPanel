from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
class RoundState(str,Enum): UNKNOWN="unknown"; LIVE="live"; OVER="over"; HALFTIME="halftime"
@dataclass
class MatchTracker:
 state:RoundState=RoundState.UNKNOWN;map_name:str|None=None;round_number:int|None=None;match_id:int=0
 def update(self,map_name,phase,round_number=None):
  new_map=map_name and map_name!=self.map_name
  if new_map:self.match_id+=1
  self.map_name=map_name or self.map_name
  if round_number is not None:self.round_number=round_number
  p=(phase or "").lower()
  if p in {"live","playing"}:self.state=RoundState.LIVE
  elif p in {"over"}:self.state=RoundState.OVER
  elif p in {"halftime","gameover"}:self.state=RoundState.HALFTIME
  elif p in {"freezetime","warmup","waiting"}:self.state=RoundState.OVER
  return self.state
 def reset(self):self.state=RoundState.UNKNOWN;self.map_name=None;self.round_number=None;self.match_id+=1
