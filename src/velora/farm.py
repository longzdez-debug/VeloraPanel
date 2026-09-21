from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import monotonic

from .account_pool import AccountPool, FarmStatus
from .resource import ResourceManager


class BatchState(str, Enum):
    IDLE = "idle"
    SELECTING = "selecting_accounts"
    STARTING = "starting_accounts"
    WAITING_FOR_READY = "waiting_for_ready"
    FARMING = "farming"
    FINISHED = "finished"
    ERROR = "error"
    STOPPING = "stopping"


@dataclass
class FarmBatch:
    id: str
    account_ids: list[str]
    mode: str = "manual"
    target_xp: int | None = None
    state: BatchState = BatchState.IDLE
    created_at: float = field(default_factory=monotonic)
    started_at: float | None = None
    finished_at: float | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.account_ids)


class FarmManager:
    """Batch orchestration state, deliberately independent from CS2 lobby automation."""

    def __init__(self, pool: AccountPool, resources: ResourceManager):
        self.pool = pool
        self.resources = resources
        self.batches: dict[str, FarmBatch] = {}

    def create_batch(self, batch_id: str, account_ids: list[str], mode: str = "manual", target_xp: int | None = None) -> FarmBatch:
        if batch_id in self.batches:
            raise ValueError(f"batch already exists: {batch_id}")
        if not account_ids:
            raise ValueError("batch requires at least one account")
        if len(set(account_ids)) != len(account_ids):
            raise ValueError("batch contains duplicate accounts")
        missing = [x for x in account_ids if self.pool.get(x) is None]
        if missing:
            raise KeyError(f"unknown accounts: {', '.join(missing)}")
        if not self.resources.can_start_batch(batch_id):
            raise RuntimeError("batch resource capacity reached")
        batch = FarmBatch(batch_id, list(account_ids), mode, target_xp)
        self.batches[batch_id] = batch
        return batch

    def start_batch(self, batch_id: str) -> FarmBatch:
        batch = self.batches[batch_id]
        if batch.state not in (BatchState.IDLE, BatchState.ERROR):
            return batch
        if not self.resources.start_batch(batch.id):
            raise RuntimeError("batch resource capacity reached")
        batch.state = BatchState.SELECTING
        batch.started_at = monotonic()
        for account_id in batch.account_ids:
            self.pool.mark(account_id, FarmStatus.IN_PROGRESS, target_xp=batch.target_xp)
        batch.state = BatchState.STARTING
        return batch

    def mark_ready(self, batch_id: str) -> FarmBatch:
        batch = self.batches[batch_id]
        if batch.state == BatchState.STARTING:
            batch.state = BatchState.WAITING_FOR_READY
        return batch

    def mark_farming(self, batch_id: str) -> FarmBatch:
        batch = self.batches[batch_id]
        if batch.state in (BatchState.STARTING, BatchState.WAITING_FOR_READY):
            batch.state = BatchState.FARMING
        return batch

    def finish_batch(self, batch_id: str, success: bool = True) -> FarmBatch:
        batch = self.batches[batch_id]
        batch.state = BatchState.FINISHED if success else BatchState.ERROR
        batch.finished_at = monotonic()
        if success:
            for account_id in batch.account_ids:
                self.pool.mark(account_id, FarmStatus.COMPLETED)
        self.resources.stop_batch(batch.id)
        return batch

    def stop_batch(self, batch_id: str) -> FarmBatch:
        batch = self.batches[batch_id]
        batch.state = BatchState.STOPPING
        batch.finished_at = monotonic()
        self.resources.stop_batch(batch.id)
        for account_id in batch.account_ids:
            if self.pool.farm[account_id].status == FarmStatus.IN_PROGRESS:
                self.pool.mark(account_id, FarmStatus.PARTIAL)
        return batch

    def snapshot(self) -> list[dict]:
        return [{
            "id": b.id,
            "state": b.state.value,
            "mode": b.mode,
            "account_ids": list(b.account_ids),
            "size": b.size,
            "target_xp": b.target_xp,
            "started_at": b.started_at,
            "finished_at": b.finished_at,
            "errors": list(b.errors[-5:]),
        } for b in self.batches.values()]
