from __future__ import annotations

from dataclasses import dataclass, field
from time import time


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

    def snapshot(self) -> dict:
        return {
            "id": self.id,
            "account_id": self.account_id,
            "priority": self.priority,
            "enabled": self.enabled,
            "cooldown": self.cooldown,
            "next_run": self.next_run,
            "retries": self.retries,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_snapshot(cls, value: dict) -> "Job":
        next_run = max(0.0, float(value.get("next_run", 0.0)))
        # Older Velora versions persisted time.monotonic(). Those values are
        # process-local and cannot safely survive a restart.
        if 0.0 < next_run < 1_000_000_000.0:
            next_run = 0.0
        return cls(
            id=str(value["id"]),
            account_id=str(value["account_id"]),
            priority=int(value.get("priority", 0)),
            enabled=bool(value.get("enabled", True)),
            cooldown=max(0.0, float(value.get("cooldown", 0.0))),
            next_run=next_run,
            retries=max(0, int(value.get("retries", 0))),
            max_retries=max(0, int(value.get("max_retries", 3))),
        )


@dataclass
class Scheduler:
    jobs: list[Job] = field(default_factory=list)
    max_concurrent: int = 1

    def add(self, job: Job) -> None:
        self.jobs = [item for item in self.jobs if item.id != job.id]
        self.jobs.append(job)

    def remove(self, job_id: str) -> None:
        self.jobs = [item for item in self.jobs if item.id != job_id]

    def get(self, job_id: str) -> Job | None:
        return next((item for item in self.jobs if item.id == job_id), None)

    def mark_active(self, job_id: str) -> None:
        job = self.get(job_id)
        if job:
            job.active = True

    def mark_done(self, job_id: str, success: bool = True, now: float | None = None) -> None:
        job = self.get(job_id)
        if not job:
            return
        job.active = False
        now = time() if now is None else now
        if success:
            job.retries = 0
            job.next_run = now + max(0.0, job.cooldown)
        else:
            job.retries += 1
            job.next_run = now + min(300.0, 2.0 ** min(job.retries, 8))

    def next(self, now: float | None = None) -> Job | None:
        now = time() if now is None else now
        if sum(item.active for item in self.jobs) >= max(1, self.max_concurrent):
            return None
        ready = [
            item
            for item in self.jobs
            if item.enabled
            and not item.active
            and item.next_run <= now
            and item.retries <= item.max_retries
        ]
        return max(ready, key=lambda item: (item.priority, -item.next_run), default=None)

    def snapshot(self) -> list[dict]:
        return [item.snapshot() for item in self.jobs]

    def load_snapshot(self, items: list[dict] | None) -> None:
        self.jobs.clear()
        for value in items or []:
            try:
                self.add(Job.from_snapshot(value))
            except (KeyError, TypeError, ValueError):
                continue
