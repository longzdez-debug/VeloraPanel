from __future__ import annotations
from dataclasses import dataclass
from math import atan2,degrees,hypot
@dataclass(frozen=True)
class MovementCommand: forward:bool=False; back:bool=False; left:bool=False; right:bool=False
@dataclass
class MovementConfig: dead_zone:float=8.0
class Navigator:
 def __init__(self,cfg=None):self.cfg=cfg or MovementConfig()
 def command(self,position,target)->MovementCommand:
  dx,dy=target[0]-position[0],target[1]-position[1]
  if hypot(dx,dy)<=self.cfg.dead_zone:return MovementCommand()
  if abs(dx)>=abs(dy):return MovementCommand(right=dx>0,left=dx<0)
  return MovementCommand(forward=dy>0,back=dy<0)
