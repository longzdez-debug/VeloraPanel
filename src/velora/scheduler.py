from dataclasses import dataclass,field
@dataclass
class Job: id:str;account_id:str;priority:int=0;enabled:bool=True
@dataclass
class Scheduler:
 jobs:list[Job]=field(default_factory=list)
 def add(self,job):self.jobs.append(job)
 def next(self):
  ready=[j for j in self.jobs if j.enabled]
  return max(ready,key=lambda j:j.priority,default=None)
