from __future__ import annotations
from dataclasses import dataclass, field
from time import monotonic

@dataclass
class Job:
    id: str
    account_id: str
    priority: int = 0
    enabled: bool = True
    cooldown: float = 0.0
    next_run: float = 0.0
    retries: int = 0
    max_retries: int = 3
    active: bool = False
    def snapshot(self):
        return {"id":self.id,"account_id":self.account_id,"priority":self.priority,"enabled":self.enabled,"cooldown":self.cooldown,"next_run":self.next_run,"retries":self.retries,"max_retries":self.max_retries}
    @classmethod
    def from_snapshot(cls,x):
        return cls(str(x["id"]),str(x["account_id"]),int(x.get("priority",0)),bool(x.get("enabled",True)),max(0.0,float(x.get("cooldown",0))),max(0.0,float(x.get("next_run",0))),max(0,int(x.get("retries",0))),max(0,int(x.get("max_retries",3))))

@dataclass
class Scheduler:
    jobs:list[Job]=field(default_factory=list)
    max_concurrent:int=1
    def add(self,job): self.jobs=[x for x in self.jobs if x.id!=job.id];self.jobs.append(job)
    def remove(self,job_id): self.jobs=[x for x in self.jobs if x.id!=job_id]
    def get(self,job_id): return next((x for x in self.jobs if x.id==job_id),None)
    def mark_active(self,job_id):
        j=self.get(job_id)
        if j:j.active=True
    def mark_done(self,job_id,success=True):
        j=self.get(job_id)
        if not j:return
        j.active=False;now=monotonic()
        if success:j.retries=0;j.next_run=now+max(0,j.cooldown)
        else:j.retries+=1;j.next_run=now+min(300,2**min(j.retries,8))
    def next(self,now=None):
        now=monotonic() if now is None else now
        if sum(x.active for x in self.jobs)>=max(1,self.max_concurrent):return None
        ready=[x for x in self.jobs if x.enabled and not x.active and x.next_run<=now and x.retries<=x.max_retries]
        return max(ready,key=lambda x:(x.priority,-x.next_run),default=None)
    def snapshot(self): return [x.snapshot() for x in self.jobs]
    def load_snapshot(self,items):
        self.jobs.clear()
        for x in items or []:
            try:self.add(Job.from_snapshot(x))
            except (KeyError,TypeError,ValueError):pass
