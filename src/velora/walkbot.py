from __future__ import annotations
from dataclasses import dataclass
from math import hypot
from time import monotonic
from typing import Callable
from .fsm import StateMachine
from .model import GsiSnapshot,WalkState
from .movement import Navigator

@dataclass(frozen=True)
class Waypoint:
 id:str
 x:float
 y:float
 z:float=0.0

@dataclass
class WalkConfig:
 arrive_radius:float=28.0
 stuck_seconds:float=3.0
 max_recoveries:int=3
 gsi_timeout:float=3.0
 recovery_seconds:float=0.45
 recovery_side_seconds:float=0.22

class InputAdapter:
 def release_all(self): pass
 def move(self,forward,back,left,right): pass

class WalkBot:
 def __init__(self,input_adapter,config=None,replan:Callable[[tuple[float,float,float]],bool]|None=None):
  self.input=input_adapter;self.cfg=config or WalkConfig();self.replan=replan
  self.fsm=StateMachine(WalkState.DISABLED);self._configure()
  self.path:list[Waypoint]=[];self.index=0
  self.last_position=None;self.last_forward=None;self.last_gsi=None
  self.progress_position=None;self.last_progress=monotonic();self.recoveries=0
  self.recovery_until=0.0;self.recovery_started=0.0
  self.navigator=Navigator();self.enabled=True

 def _configure(self):
  s=WalkState
  transitions=[(s.DISABLED,"start",s.INITIALIZING),(s.INITIALIZING,"ready",s.WAITING_FOR_GAME),
   (s.WAITING_FOR_GAME,"live",s.WAITING_FOR_SPAWN),(s.WAITING_FOR_SPAWN,"spawn",s.NAVIGATING),
   (s.NAVIGATING,"arrive",s.ARRIVING),(s.ARRIVING,"wait",s.WAITING),(s.WAITING,"next",s.NAVIGATING),
   (s.NAVIGATING,"stuck",s.STUCK),(s.STUCK,"recover",s.RECOVERING),
   (s.RECOVERING,"replan",s.REPLANNING),(s.RECOVERING,"retry",s.NAVIGATING),
   (s.REPLANNING,"planned",s.NAVIGATING)]
  for a in (s.WAITING_FOR_SPAWN,s.NAVIGATING,s.ARRIVING,s.WAITING,s.STUCK,s.RECOVERING,s.REPLANNING): self.fsm.allow(a,"reset_game",s.WAITING_FOR_GAME)
  for a,e,b in transitions:self.fsm.allow(a,e,b)
  for a in s:
   if a not in (s.DISABLED,s.STOPPING): self.fsm.allow(a,"stop",s.STOPPING)
  self.fsm.allow(s.STOPPING,"reset",s.DISABLED)

 def start(self):
  self.enabled=True
  if self.fsm.state==WalkState.DISABLED:self.fsm.dispatch("start")

 def emergency_stop(self):
  self.enabled=False;self.input.release_all()

 def stop(self):
  self.enabled=False;self.input.release_all()
  if self.fsm.state!=WalkState.DISABLED:self.fsm.dispatch("stop")
  if self.fsm.state==WalkState.STOPPING:self.fsm.dispatch("reset")

 def set_path(self,path):
  self.path=list(path);self.index=0;self.recoveries=0
  self.progress_position=None;self.last_progress=monotonic()

 def replan_from_position(self,position):
  if self.replan is None:return False
  if self.fsm.state not in (WalkState.STUCK,WalkState.RECOVERING,WalkState.NAVIGATING):return False
  try:
   if self.fsm.state==WalkState.NAVIGATING:self.fsm.dispatch("stuck")
   if self.fsm.state==WalkState.STUCK:self.fsm.dispatch("recover")
   ok=bool(self.replan(position))
   if ok:
    self.fsm.dispatch("replan");self.fsm.dispatch("planned")
    self.progress_position=position;self.last_progress=monotonic()
   else:
    self.stop()
   return ok
  except Exception:
   self.stop()
   return False

 def on_gsi(self,snap:GsiSnapshot):
  self.last_gsi=monotonic();self.last_position=snap.position or self.last_position
  self.last_forward=snap.forward or self.last_forward
  activity=(snap.activity or "").lower()
  phase=(snap.round_phase or snap.map_phase or "").lower()
  live=activity in {"playing","live"} and phase in {"live","playing","freezetime","halftime","intermission"}
  if not live or (snap.health is not None and snap.health<=0):
   self.input.release_all()
   if activity in {"menu","mainmenu"} or phase in {"menu","mainmenu","postgame","gameover","game_over"}:
    if self.fsm.state not in (WalkState.DISABLED,WalkState.INITIALIZING,WalkState.WAITING_FOR_GAME): self.fsm.dispatch("reset_game")
   return
  if self.fsm.state==WalkState.INITIALIZING:self.fsm.dispatch("ready")
  if self.fsm.state==WalkState.WAITING_FOR_GAME:self.fsm.dispatch("live")
  if self.fsm.state==WalkState.WAITING_FOR_SPAWN and (snap.health or 0)>0:self.fsm.dispatch("spawn")
 def _recovery_tick(self,now):
  if now>=self.recovery_until:
   self.input.release_all()
   if self.last_position is not None and self.replan and self.replan_from_position(self.last_position): return
   if self.recoveries>=self.cfg.max_recoveries:self.stop();return
   self.fsm.dispatch("retry");self.last_progress=now;return
  elapsed=now-self.recovery_started
  if elapsed<self.cfg.recovery_side_seconds:self.input.move(False,False,True,False)
  else:self.input.move(True,False,False,True)

 def tick(self,position=None):
  now=monotonic()
  if not self.enabled or self.last_gsi is None or now-self.last_gsi>self.cfg.gsi_timeout:
   self.input.release_all();return
  if self.fsm.state==WalkState.RECOVERING:
   self._recovery_tick(now);return
  if self.fsm.state not in (WalkState.NAVIGATING,WalkState.ARRIVING) or not self.path:return
  position=position or self.last_position
  if position is None:return
  self.last_position=position
  target=self.path[self.index];d=hypot(target.x-position[0],target.y-position[1])
  if d<=self.cfg.arrive_radius:
   self.input.release_all()
   if self.index+1<len(self.path):
    self.index+=1;self.fsm.dispatch("arrive");self.fsm.dispatch("wait");self.fsm.dispatch("next")
   else:self.fsm.dispatch("arrive")
   self.progress_position=position;self.last_progress=now;return
  if self.progress_position is None:self.progress_position=position;self.last_progress=now
  elif hypot(position[0]-self.progress_position[0],position[1]-self.progress_position[1])>2:
   self.progress_position=position;self.last_progress=now;self.recoveries=0
  if now-self.last_progress>=self.cfg.stuck_seconds:
   self.input.release_all()
   self.recoveries+=1
   if self.recoveries>self.cfg.max_recoveries:self.stop();return
   self.fsm.dispatch("stuck");self.fsm.dispatch("recover")
   self.recovery_started=now;self.recovery_until=now+self.cfg.recovery_seconds;return
  c=self.navigator.command(position,(target.x,target.y),self.last_forward)
  self.input.move(c.forward,c.back,c.left,c.right)
