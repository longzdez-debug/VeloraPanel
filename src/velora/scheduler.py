from __future__ import annotations
from dataclasses import dataclass,field
from time import monotonic
@dataclass
class Job:
 id:str;account_id:str;priority:int=0;enabled:bool=True;cooldown:float=0;next_run:float=0;retries:int=0;max_retries:int=3
@dataclass
class Scheduler:
 max_concurrent:int=1;jobs:list[Job]=field(default_factory=list);active:set[str]=field(default_factory=set)
 def add(self,job):self.jobs=[j for j in self.jobs if j.id!=job.id];self.jobs.append(job)
 def mark_active(self,account_id):self.active.add(account_id)
 def mark_done(self,account_id,success=True):
  self.active.discard(account_id)
  for j in self.jobs:
   if j.account_id==account_id:
    j.retries=0 if success else j.retries+1;j.next_run=monotonic()+j.cooldown
 def next(self):
  if len(self.active)>=self.max_concurrent:return None
  now=monotonic();ready=[j for j in self.jobs if j.enabled and j.account_id not in self.active and j.next_run<=now]
  return max(ready,key=lambda j:(j.priority,-j.retries),default=None)
