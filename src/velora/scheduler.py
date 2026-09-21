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

@dataclass
class Scheduler:
    jobs: list[Job] = field(default_factory=list)
    max_concurrent: int = 1

    def add(self, job: Job) -> None:
        self.jobs = [x for x in self.jobs if x.id != job.id]
        self.jobs.append(job)

    def remove(self, job_id: str) -> None:
        self.jobs = [x for x in self.jobs if x.id != job_id]

    def mark_active(self, job_id: str) -> None:
        for job in self.jobs:
            if job.id == job_id:
                job.active = True

    def mark_done(self, job_id: str, success: bool = True) -> None:
        now = monotonic()
        for job in self.jobs:
            if job.id == job_id:
                job.active = False
                if success:
                    job.retries = 0
                    job.next_run = now + max(0.0, job.cooldown)
                else:
                    job.retries += 1
                    job.next_run = now + min(300.0, 2.0 ** min(job.retries, 8))

    def next(self, now: float | None = None) -> Job | None:
        now = monotonic() if now is None else now
        if sum(j.active for j in self.jobs) >= self.max_concurrent:
            return None
        ready = [j for j in self.jobs if j.enabled and not j.active and j.next_run <= now and j.retries <= j.max_retries]
        return max(ready, key=lambda j: (j.priority, -j.next_run), default=None)
