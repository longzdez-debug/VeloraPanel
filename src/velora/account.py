from dataclasses import dataclass
from .fsm import StateMachine
from .model import AccountState,GsiSnapshot
@dataclass
class Account:
 id:str;name:str;walkbot:object;steam_id:str|None=None
 def __post_init__(self):
  self.fsm=StateMachine(AccountState.OFFLINE);s=AccountState
  for a,e,b in [(s.OFFLINE,"start",s.STARTING),(s.STARTING,"ready",s.MENU),(s.MENU,"queue",s.QUEUING),(s.QUEUING,"match",s.IN_MATCH),(s.IN_MATCH,"stop",s.STOPPING),(s.ERROR,"reset",s.OFFLINE),(s.STOPPING,"reset",s.OFFLINE)]:self.fsm.allow(a,e,b)
  for a in (s.STARTING,s.MENU,s.QUEUING,s.IN_MATCH):self.fsm.allow(a,"error",s.ERROR)
 def on_gsi(self,snap:GsiSnapshot):
  if self.steam_id and snap.steam_id and snap.steam_id!=self.steam_id:return
  if snap.activity=="playing":
   if self.fsm.state==AccountState.QUEUING:self.fsm.dispatch("match")
  self.walkbot.on_gsi(snap)
 def stop(self):
  self.walkbot.stop()
  if self.fsm.state not in (AccountState.OFFLINE,AccountState.STOPPING):
   self.fsm.dispatch("stop")
  if self.fsm.state==AccountState.STOPPING:self.fsm.dispatch("reset")
