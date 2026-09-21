from __future__ import annotations
from dataclasses import asdict,dataclass
from .storage import JsonStore
@dataclass
class AccountProfile:
 id:str;name:str;steam_id:str="";enabled:bool=True;walkbot:bool=True;executable:str="";launch_args:list[str]=None
 def __post_init__(self):self.launch_args=list(self.launch_args or [])
class AccountStore:
 def __init__(self,path):self.store=JsonStore(path)
 def load(self):return [AccountProfile(**x) for x in (self.store.load([]) or [])]
 def save(self,items):self.store.save([asdict(x) for x in items])
 def upsert(self,p):
  xs=[x for x in self.load() if x.id!=p.id];xs.append(p);self.save(xs)
