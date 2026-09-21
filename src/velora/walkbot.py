from __future__ import annotations
from dataclasses import dataclass
from math import hypot
from time import monotonic
from .fsm import StateMachine
from .model import GsiSnapshot,WalkState
from .movement import Navigator
@dataclass(frozen=True)
class Waypoint:id:str;x:float;y:float;z:float=0.0
@dataclass
class WalkConfig:arrive_radius:float=28.0;stuck_seconds:float=3.0;max_recoveries:int=3
class InputAdapter:
 def release_all(self):pass
 def move(self,forward,back,left,right):pass
class WalkBot:
 def __init__(self,input_adapter,config=None):
  self.input=input_adapter;self.cfg=config or WalkConfig();self.fsm=StateMachine(WalkState.DISABLED);self._configure();self.path=[];self.index=0;self.last_position=None;self.last_progress=monotonic();self.recoveries=0;self.navigator=Navigator()
 def _configure(self):
  s=WalkState
  for a,e,b in [(s.DISABLED,"start",s.INITIALIZING),(s.INITIALIZING,"ready",s.WAITING_FOR_GAME),(s.WAITING_FOR_GAME,"live",s.WAITING_FOR_SPAWN),(s.WAITING_FOR_SPAWN,"spawn",s.NAVIGATING),(s.NAVIGATING,"arrive",s.ARRIVING),(s.ARRIVING,"wait",s.WAITING),(s.WAITING,"next",s.NAVIGATING),(s.NAVIGATING,"stuck",s.STUCK),(s.STUCK,"recover",s.RECOVERING),(s.RECOVERING,"retry",s.NAVIGATING),(s.RECOVERING,"replan",s.REPLANNING),(s.REPLANNING,"planned",s.NAVIGATING)]:self.fsm.allow(a,e,b)
  for a in s:
   if a not in (s.DISABLED,s.STOPPING):self.fsm.allow(a,"stop",s.STOPPING)
  self.fsm.allow(s.STOPPING,"reset",s.DISABLED)
 def start(self):self.fsm.dispatch("start")
 def stop(self):self.input.release_all();self.fsm.dispatch("stop")
 def set_path(self,path):self.path=list(path);self.index=0
 def on_gsi(self,snap:GsiSnapshot):
  if snap.activity!="playing":return
  if self.fsm.state==WalkState.WAITING_FOR_GAME:self.fsm.dispatch("live")
  if self.fsm.state==WalkState.WAITING_FOR_SPAWN and (snap.health or 0)>0:self.fsm.dispatch("spawn")
 def tick(self,position=None):
  if self.fsm.state not in (WalkState.NAVIGATING,WalkState.ARRIVING) or not self.path or position is None:return
  target=self.path[self.index];d=hypot(target.x-position[0],target.y-position[1])
  if d<=self.cfg.arrive_radius:
   self.input.release_all()
   if self.index+1<len(self.path):self.index+=1;self.fsm.dispatch("arrive");self.fsm.dispatch("wait");self.fsm.dispatch("next")
   else:self.fsm.dispatch("arrive")
   return
  now=monotonic()
  if self.last_position and hypot(position[0]-self.last_position[0],position[1]-self.last_position[1])>2:self.last_progress=now;self.recoveries=0
  self.last_position=position
  if now-self.last_progress>=self.cfg.stuck_seconds:self.fsm.dispatch("stuck");self.recoveries+=1;self.input.release_all();return
  c=self.navigator.command(position,(target.x,target.y));self.input.move(c.forward,c.back,c.left,c.right)
