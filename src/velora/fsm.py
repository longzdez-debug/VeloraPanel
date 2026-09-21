from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic,TypeVar
S=TypeVar("S"); E=TypeVar("E")
@dataclass(frozen=True)
class Transition(Generic[S,E]): source:S; event:E; target:S
class StateMachine(Generic[S,E]):
 def __init__(self,initial:S): self.state=initial; self._table={}; self._hooks={}
 def allow(self,source,event,target,hook:Callable|None=None):
  self._table[(source,event)]=target
  if hook: self._hooks.setdefault((source,event),[]).append(hook)
 def dispatch(self,event):
  target=self._table.get((self.state,event))
  if target is None:return None
  old=self.state; self.state=target
  for hook in self._hooks.get((old,event),[]):hook(old,target,event)
  return Transition(old,event,target)
 def can(self,event): return (self.state,event) in self._table
