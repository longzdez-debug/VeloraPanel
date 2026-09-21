from __future__ import annotations
from dataclasses import dataclass
from math import atan2,degrees,hypot
@dataclass(frozen=True)
class MovementCommand:
 forward:bool=False;back:bool=False;left:bool=False;right:bool=False
@dataclass
class MovementConfig: dead_zone:float=8.0;steer_angle:float=20.0
class Navigator:
 def __init__(self,cfg=None):self.cfg=cfg or MovementConfig()
 @staticmethod
 def _angle(x,y):return degrees(atan2(y,x))
 @staticmethod
 def _norm(a):return (a+180)%360-180
 def command(self,position,target,forward=None)->MovementCommand:
  dx,dy=target[0]-position[0],target[1]-position[1]
  if hypot(dx,dy)<=self.cfg.dead_zone:return MovementCommand()
  desired=self._angle(dx,dy)
  if forward is None:return MovementCommand(right=dx>0,left=dx<0) if abs(dx)>=abs(dy) else MovementCommand(forward=dy>0,back=dy<0)
  heading=self._angle(forward[0],forward[1])
  rel=self._norm(desired-heading)
  f=abs(rel)<=70; b=abs(rel)>=110
  r=20<=rel<=160; l=-160<=rel<=-20
  return MovementCommand(forward=f,back=b,left=l,right=r)
