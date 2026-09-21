from dataclasses import dataclass,field
from .fsm import StateMachine
from .model import AccountState,GsiSnapshot
@dataclass
class Account:
 id:str;name:str;walkbot:object;steam_id:str|None=None;enabled:bool=True;process_id:int|None=None;executable:str="";launch_args:list[str]=field(default_factory=list);last_gsi:float|None=None;errors:list[str]=field(default_factory=list);route_map:str|None=None;route_start:str|None=None;route_goal:str|None=None
 def __post_init__(self):
  self.fsm=StateMachine(AccountState.OFFLINE);s=AccountState
  for x,e,y in [(s.OFFLINE,"start",s.STARTING),(s.STARTING,"ready",s.MENU),(s.MENU,"queue",s.QUEUING),(s.QUEUING,"match",s.IN_MATCH),(s.IN_MATCH,"stop",s.STOPPING),(s.ERROR,"reset",s.OFFLINE),(s.STOPPING,"reset",s.OFFLINE)]:self.fsm.allow(x,e,y)
  for x in (s.STARTING,s.MENU,s.QUEUING,s.IN_MATCH):self.fsm.allow(x,"error",s.ERROR)
 def start(self):
  if self.enabled:self.fsm.dispatch("start");self.walkbot.start()
 def on_ready(self):self.fsm.dispatch("ready")
 def on_gsi(self,snap:GsiSnapshot):
  if self.steam_id and snap.steam_id and snap.steam_id!=self.steam_id:return
  self.last_gsi=snap.received_at
  if snap.activity=="playing" and self.fsm.state==AccountState.QUEUING:self.fsm.dispatch("match")
  self.walkbot.on_gsi(snap)
 def stop(self):
  self.walkbot.stop()
  if self.fsm.state not in (AccountState.OFFLINE,AccountState.STOPPING):self.fsm.dispatch("stop")
  if self.fsm.state==AccountState.STOPPING:self.fsm.dispatch("reset")
