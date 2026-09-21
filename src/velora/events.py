from __future__ import annotations
import asyncio
from collections import defaultdict
class EventBus:
 def __init__(self): self._handlers=defaultdict(list)
 def on(self,name,handler): self._handlers[name].append(handler)
 async def emit(self,name,payload=None): await asyncio.gather(*(h(payload) for h in self._handlers.get(name,())))
