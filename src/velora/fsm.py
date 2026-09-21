from __future__ import annotations
from dataclasses import dataclass
from typing import Callable,Generic,TypeVar
S=TypeVar("S"); E=TypeVar("E")
@dataclass(frozen=True)
class Transition(Generic[S,E]):
    source:S; event:E; target:S
    guard:Callable[[object],bool]=lambda _:True
    action:Callable[[object],None]=lambda _:None
class StateMachine(Generic[S,E]):
    def __init__(self,initial:S,transitions:list[Transition[S,E]],on_enter=None,on_exit=None):
        self.state=initial; self._transitions=transitions; self._on_enter=on_enter or {}; self._on_exit=on_exit or {}; self.history=[]
    def dispatch(self,event:E,context=None)->bool:
        for t in self._transitions:
            if t.source==self.state and t.event==event and t.guard(context):
                old=self.state; self._on_exit.get(old,lambda _:None)(context); t.action(context); self.state=t.target
                self.history.append((old,event,self.state)); self._on_enter.get(self.state,lambda _:None)(context); return True
        return False
class Event:
    START="start"; STOP="stop"; TICK="tick"; GAME_READY="game_ready"; GAME_LOST="game_lost"; SPAWNED="spawned"; ARRIVED="arrived"; STUCK="stuck"; RECOVERED="recovered"; REPLAN="replan"; MATCH_LIVE="match_live"; ROUND_OVER="round_over"; GAME_OVER="game_over"; ERROR="error"; RESET="reset"
