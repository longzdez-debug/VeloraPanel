from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from time import monotonic

class SupervisorState(str, Enum):
    STOPPED="stopped"; STARTING="starting"; RUNNING="running"; DEGRADED="degraded"; STOPPING="stopping"
class AccountState(str, Enum):
    UNKNOWN="unknown"; READY="ready"; LAUNCHING="launching"; IN_GAME="in_game"; ERROR="error"
class MatchState(str, Enum):
    WAITING="waiting"; LIVE="live"; ROUND_OVER="round_over"; GAME_OVER="game_over"
class WalkBotState(str, Enum):
    DISABLED="disabled"; INITIALIZING="initializing"; WAITING_FOR_GAME="waiting_for_game"; WAITING_FOR_SPAWN="waiting_for_spawn"; CALIBRATING="calibrating"; NAVIGATING="navigating"; ARRIVING="arriving"; WAITING="waiting"; STUCK="stuck"; RECOVERING="recovering"; REPLANNING="replanning"; STOPPING="stopping"

@dataclass(frozen=True)
class Vector3:
    x: float; y: float; z: float
    def distance(self, other:"Vector3")->float:
        return ((self.x-other.x)**2+(self.y-other.y)**2+(self.z-other.z)**2)**0.5

@dataclass(frozen=True)
class GameState:
    connected: bool=False; in_game: bool=False; alive: bool=False; team: str|None=None
    map_name: str|None=None; round_number: int|None=None; round_phase: str|None=None
    position: Vector3|None=None; velocity: Vector3=Vector3(0,0,0)
    view_yaw: float=0.0; view_pitch: float=0.0; updated_at: float=field(default_factory=monotonic); sequence:int=0

@dataclass(frozen=True)
class MovementIntent:
    forward:bool=False; back:bool=False; left:bool=False; right:bool=False; jump:bool=False
    crouch:bool=False; walk:bool=False; brake:bool=False; yaw:float|None=None; pitch:float|None=None

@dataclass
class FsmContext:
    game:GameState=field(default_factory=GameState)
    intent:MovementIntent=field(default_factory=MovementIntent)
    errors:list[str]=field(default_factory=list)
    metadata:dict[str,object]=field(default_factory=dict)
