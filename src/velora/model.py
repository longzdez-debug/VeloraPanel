from __future__ import annotations
from dataclasses import dataclass,field
from enum import Enum
from typing import Any
class AccountState(str,Enum):
 OFFLINE="offline"; STARTING="starting"; MENU="menu"; QUEUING="queuing"; IN_MATCH="in_match"; STOPPING="stopping"; ERROR="error"
class MatchState(str,Enum): UNKNOWN="unknown"; WAITING="waiting"; LIVE="live"; ROUND_OVER="round_over"; GAME_OVER="game_over"
class WalkState(str,Enum):
 DISABLED="disabled"; INITIALIZING="initializing"; WAITING_FOR_GAME="waiting_for_game"; WAITING_FOR_SPAWN="waiting_for_spawn"; NAVIGATING="navigating"; ARRIVING="arriving"; WAITING="waiting"; STUCK="stuck"; RECOVERING="recovering"; REPLANNING="replanning"; STOPPING="stopping"; FAULT="fault"
class EventType(str,Enum):
 TICK="tick"; GSI="gsi"; START="start"; STOP="stop"; PAUSE="pause"; RESUME="resume"; RESET="reset"; ERROR="error"
@dataclass(frozen=True)
class GsiSnapshot:
 received_at:float; provider_timestamp:int|None=None; map_name:str|None=None; map_phase:str|None=None; round_phase:str|None=None; activity:str|None=None; health:int|None=None; steam_id:str|None=None
 position:tuple[float,float,float]|None=None; forward:tuple[float,float,float]|None=None; round_number:int|None=None
 raw:dict[str,Any]=field(default_factory=dict)

 @property
 def match_key(self): return (self.map_name,self.round_number,self.steam_id)
@dataclass
class RuntimeStatus:
 account:AccountState=AccountState.OFFLINE; match:MatchState=MatchState.UNKNOWN; walkbot:WalkState=WalkState.DISABLED; last_gsi:float|None=None; errors:int=0
