from __future__ import annotations
from .domain import GameState,Vector3
class GameStateNormalizer:
    def __init__(self): self._sequence=0
    def from_gsi(self,payload:dict)->GameState:
        player=payload.get("player") or {}; mp=payload.get("map") or {}; pos=player.get("position"); vel=player.get("velocity") or {}
        self._sequence+=1
        return GameState(connected=True,in_game=bool(mp),alive=str(player.get("state","")).lower() not in {"dead",""},team=player.get("team"),map_name=mp.get("name"),round_number=mp.get("round"),round_phase=mp.get("phase"),position=Vector3(*pos) if isinstance(pos,list) and len(pos)==3 else None,velocity=Vector3(float(vel.get("x",0)),float(vel.get("y",0)),float(vel.get("z",0))),view_yaw=float(player.get("yaw",0) or 0),view_pitch=float(player.get("pitch",0) or 0),sequence=self._sequence)
