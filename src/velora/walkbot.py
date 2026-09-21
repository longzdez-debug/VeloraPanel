from __future__ import annotations
from dataclasses import dataclass
from math import hypot
from time import monotonic
from typing import Callable
from .fsm import StateMachine
from .model import GsiSnapshot,WalkState
from .movement import Navigator
from .decision import DecisionEngine
from .steering import Steering
from .movement_controller import MovementController
from .movement_intent import MovementIntent
from .world import WorldModel
from .gsi_normalizer import GsiNormalizer
from .replay import ReplaySession
from .navigation import NavGraph, NavigationGoal
from .external_input import ExternalInput
from .recovery_coordinator import RecoveryCoordinator

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

class WalkBot:
 def __init__(self,input_adapter:ExternalInput,config=None,replan:Callable[[tuple[float,float,float]],bool]|None=None,replay:ReplaySession|None=None,nav_graph:NavGraph|None=None):
  self.input=input_adapter;self.cfg=config or WalkConfig();self.replan=replan
  self.fsm=StateMachine(WalkState.DISABLED);self._configure()
  self.path:list[Waypoint]=[];self.index=0
  self.last_position=None;self.last_forward=None;self.last_gsi=None
  self.progress_position=None;self.last_progress=monotonic();self.recoveries=0
  self.recovery_until=0.0;self.recovery_started=0.0
  self.navigator=Navigator();self.steering=Steering();self.movement_controller=MovementController(input_adapter);self.decision_engine=DecisionEngine();self.enabled=True
  self.world=WorldModel()
  self.gsi_normalizer=GsiNormalizer()
  self.replay=replay
  self.last_tick=None
  self.last_command=None
  self.recovery_reason=None
  self.nav_graph=nav_graph
  self.navigation_goal:NavigationGoal|None=None
  self.last_decision=None
  self.recovery_coordinator=RecoveryCoordinator(self.cfg.max_recoveries)

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
  self.recovery_coordinator.reset()
  self.world.update_navigation(path=tuple(w.id for w in self.path), progress=0.0, target_area=self.path[-1].id if self.path else None)
  self.progress_position=None;self.last_progress=monotonic();self.recovery_reason=None

 def plan_to(self,goal:NavigationGoal):
  self.navigation_goal=goal
  if self.nav_graph is None or goal.target_area is None:
   return False
  position=self.last_position
  if position is None:
   return False
  start=self.nav_graph.nearest(position,self.cfg.arrive_radius*10)
  if start is None:
   return False
  areas=self.nav_graph.astar(start.id,goal.target_area)
  if not areas:
   return False
  self.set_path([Waypoint(a,self.nav_graph.areas[a].center[0],self.nav_graph.areas[a].center[1],self.nav_graph.areas[a].center[2]) for a in areas])
  self.world.update_navigation(target_area=goal.target_area, path=tuple(areas), progress=0.0)
  return True

 def telemetry(self):
  now=monotonic();position=self.last_position
  target=self.path[self.index] if self.path and 0<=self.index<len(self.path) else None
  distance=None if position is None or target is None else hypot(target.x-position[0],target.y-position[1])
  age=None if self.last_gsi is None else max(0.0,now-self.last_gsi)
  progress_age=max(0.0,now-self.last_progress) if self.progress_position is not None else None
  return {"state":getattr(self.fsm.state,"value",str(self.fsm.state)),"enabled":bool(self.enabled),
   "position":list(position) if position is not None else None,"target_node":target.id if target else None,
   "target_position":[target.x,target.y,target.z] if target else None,"path_index":self.index,"path_length":len(self.path),
   "progress_percent":round((self.index/max(1,len(self.path)-1))*100,1) if self.path else 0.0,
   "distance_to_target":round(distance,2) if distance is not None else None,"stuck_count":self.recoveries,
   "max_recoveries":self.cfg.max_recoveries,"recovery_active":self.fsm.state==WalkState.RECOVERING,
   "recovery_reason":self.recovery_reason,
   "recovery_level":self.recovery_coordinator.level,"last_gsi_age":round(age,3) if age is not None else None,
   "last_progress_age":round(progress_age,3) if progress_age is not None else None,
   "last_tick_age":None if self.last_tick is None else round(max(0.0,now-self.last_tick),3),
   "last_command":self.last_command,"position_confidence":self.world.snapshot().localization.position.confidence,
   "localization_status":self.world.snapshot().localization.status,
   "navigation_goal":self.navigation_goal.target_area if self.navigation_goal else None,
   "decision_action":None if self.last_decision is None else self.last_decision.action,
   "decision_reason":None if self.last_decision is None else self.last_decision.reason,
   "decision_confidence":None if self.last_decision is None else round(self.last_decision.confidence,3),
   "vision_frame_id":self.world.snapshot().vision.frame_id,
   "vision_observation_count":self.world.snapshot().vision.observation_count,
   "vision_confidence":self.world.snapshot().vision.confidence}

 def replan_from_position(self,position):
  if self.replan is None:return False
  if self.fsm.state not in (WalkState.STUCK,WalkState.RECOVERING,WalkState.NAVIGATING):return False
  try:
   if self.fsm.state==WalkState.NAVIGATING:self.fsm.dispatch("stuck")
   if self.fsm.state==WalkState.STUCK:self.fsm.dispatch("recover")
   ok=bool(self.replan(position))
   if ok:self.fsm.dispatch("replan");self.fsm.dispatch("planned");self.progress_position=position;self.last_progress=monotonic()
   else:self.stop()
   return ok
  except Exception:
   self.stop();return False

 def on_gsi(self,snap:GsiSnapshot):
  self.gsi_normalizer.publish(snap,self.world)
  if self.replay:self.replay.record("WalkBot.GsiUpdated",snap.received_at,{"map":snap.map_name,"activity":snap.activity,"health":snap.health,"position":list(snap.position) if snap.position else None})
  self.last_gsi=monotonic();self.last_position=snap.position or self.last_position;self.last_forward=snap.forward or self.last_forward
  if snap.position is not None:
   self.world.update_navigation(progress=self.world.snapshot().navigation.progress, position_confidence=self.world.snapshot().localization.position.confidence)
  activity=(snap.activity or "").lower();phase=(snap.round_phase or snap.map_phase or "").lower()
  live=activity in {"playing","live"} and phase in {"live","playing","freezetime","halftime","intermission"}
  if not live or (snap.health is not None and snap.health<=0):
   self.input.release_all()
   if activity in {"menu","mainmenu"} or phase in {"menu","mainmenu","postgame","gameover","game_over"}:
    if self.fsm.state not in (WalkState.DISABLED,WalkState.INITIALIZING,WalkState.WAITING_FOR_GAME):self.fsm.dispatch("reset_game")
   return
  if self.fsm.state==WalkState.INITIALIZING:self.fsm.dispatch("ready")
  if self.fsm.state==WalkState.WAITING_FOR_GAME:self.fsm.dispatch("live")
  if self.fsm.state==WalkState.WAITING_FOR_SPAWN and (snap.health or 0)>0:self.fsm.dispatch("spawn")

 def _recovery_tick(self,now):
  if now>=self.recovery_until:
   self.input.release_all()
   if self.last_position is not None and self.replan and self.replan_from_position(self.last_position):return
   if self.recoveries>=self.cfg.max_recoveries:self.stop();return
   self.fsm.dispatch("retry");self.last_progress=now;return
  elapsed=now-self.recovery_started
  if self.recovery_coordinator.level>=4:self.movement_controller.stop()
  elif elapsed<self.cfg.recovery_side_seconds:self.movement_controller.apply(MovementIntent(strafe=1.0))
  else:self.movement_controller.apply(MovementIntent(forward=1.0,strafe=1.0))

 def tick(self,position=None):
  now=monotonic();self.last_tick=now
  if not self.enabled or self.last_gsi is None or now-self.last_gsi>self.cfg.gsi_timeout:self.input.release_all();return
  if self.fsm.state==WalkState.RECOVERING:self._recovery_tick(now);return
  if self.fsm.state not in (WalkState.NAVIGATING,WalkState.ARRIVING) or not self.path:return
  position=position or self.last_position
  if position is None:return
  self.last_position=position;target=self.path[self.index]
  nearest = self.nav_graph.nearest(position, self.cfg.arrive_radius * 2) if self.nav_graph is not None else None
  current_area = nearest.id if nearest is not None else self.world.snapshot().localization.nav_area
  self.world.update_navigation(current_area=current_area, progress=(self.index/max(1,len(self.path)-1)) if self.path else 0.0)
  d=hypot(target.x-position[0],target.y-position[1])
  if d<=self.cfg.arrive_radius:
   self.input.release_all()
   if self.index+1<len(self.path):self.index+=1;self.fsm.dispatch("arrive");self.fsm.dispatch("wait");self.fsm.dispatch("next")
   else:self.fsm.dispatch("arrive")
   self.progress_position=position;self.last_progress=now;return
  if self.progress_position is None:self.progress_position=position;self.last_progress=now
  elif hypot(position[0]-self.progress_position[0],position[1]-self.progress_position[1])>2:self.progress_position=position;self.last_progress=now;self.recoveries=0
  if now-self.last_progress>=self.cfg.stuck_seconds:
   self.input.release_all()
   progress_age=now-self.last_progress
   loc=self.world.snapshot().localization.position
   recovery=self.recovery_coordinator.observe("stuck",progress_age,loc.confidence,now)
   if recovery is None:return
   self.recoveries=self.recovery_coordinator.count;self.recovery_reason=recovery.reason
   if recovery.action=="navigation_reset":self.stop();return
   if self.fsm.state==WalkState.NAVIGATING:self.fsm.dispatch("stuck")
   if self.fsm.state==WalkState.STUCK:self.fsm.dispatch("recover")
   self.recovery_started=now;self.recovery_until=now+self.cfg.recovery_seconds
   if self.replay:self.replay.record("WalkBot.RecoveryDecision",now,{"level":recovery.level,"action":recovery.action,"reason":recovery.reason})
   return
  decision_goal=self.navigation_goal or NavigationGoal("waypoint", target_position=(target.x,target.y,target.z), reason="path_waypoint")
  decision=self.decision_engine.decide(self.world.snapshot(), decision_goal)
  self.last_decision=decision
  if decision.action != "move_to_target":
   self.movement_controller.stop()
   self.last_command={"forward":False,"back":False,"left":False,"right":False}
   return
  if self.last_forward is not None:
   intent=self.steering.steer(position,self.last_forward,(target.x,target.y,target.z))
   c=self.movement_controller.apply(intent)
  else:
   legacy=self.navigator.command(position,(target.x,target.y),self.last_forward)
   c=self.movement_controller.apply(MovementIntent(
    forward=1.0 if legacy.forward else -1.0 if legacy.back else 0.0,
    strafe=1.0 if legacy.right else -1.0 if legacy.left else 0.0))
  self.last_command={"forward":bool(c.forward),"back":bool(c.back),"left":bool(c.left),"right":bool(c.right)}
  if self.replay:self.replay.record("WalkBot.MovementCommand",now,self.last_command | {"decision":decision.action,"reason":decision.reason})
