from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import time

from .account_pool import AccountPool, FarmStatus
from .resource import ResourceManager
from .match_director import MatchDirector
from .scenario import ScenarioEngine


class FarmMode(str, Enum):
    MANUAL = "manual"
    WINGMAN_2V2 = "2v2"
    WINGMAN_RANDOM = "2v2_random"
    COMPETITIVE_5V5 = "5v5"
    COMPETITIVE_SHUFFLE = "5v5_shuffle"
    DEATHMATCH = "deathmatch"
    ARMS_RACE = "arms_race"
    ARMORY = "armory"


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
    created_at: float = field(default_factory=time)
    started_at: float | None = None
    finished_at: float | None = None
    errors: list[str] = field(default_factory=list)
    director: MatchDirector = field(default_factory=MatchDirector)
    scenario: ScenarioEngine = field(default_factory=ScenarioEngine)

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
        required = {"2v2": 4, "2v2_random": 4, "5v5": 10, "5v5_shuffle": 10}.get(mode)
        if required is not None and len(account_ids) != required:
            raise ValueError(f"{mode} requires exactly {required} accounts")
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
        if any(not self.pool.get(account_id) or not getattr(self.pool.get(account_id), "enabled", True)
               for account_id in batch.account_ids):
            self.resources.stop_batch(batch.id)
            raise RuntimeError("batch contains disabled or unavailable account")
        batch.scenario.load(batch.mode)
        if batch.scenario.current.required_players > 1 and batch.size != batch.scenario.current.required_players:
            self.resources.stop_batch(batch.id)
            raise ValueError(f"{batch.mode} requires {batch.scenario.current.required_players} accounts")
        batch.director.prepare(batch.size)
        batch.state = BatchState.SELECTING
        batch.started_at = time()
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
        batch.finished_at = time()
        if success:
            for account_id in batch.account_ids:
                self.pool.mark(account_id, FarmStatus.COMPLETED)
        self.resources.stop_batch(batch.id)
        return batch

    def stop_batch(self, batch_id: str) -> FarmBatch:
        batch = self.batches[batch_id]
        batch.state = BatchState.STOPPING
        batch.finished_at = time()
        self.resources.stop_batch(batch.id)
        for account_id in batch.account_ids:
            if self.pool.farm[account_id].status == FarmStatus.IN_PROGRESS:
                self.pool.mark(account_id, FarmStatus.PARTIAL)
        return batch

    def player_ready(self, batch_id: str) -> FarmBatch:
        batch = self.batches[batch_id]
        batch.director.player_ready()
        if batch.director.state.value == "lobby_ready":
            batch.state = BatchState.WAITING_FOR_READY
        elif batch.director.state.value == "waiting_for_players":
            batch.state = BatchState.WAITING_FOR_READY
        return batch

    def start_search(self, batch_id: str) -> FarmBatch:
        batch = self.batches[batch_id]
        batch.director.start_search()
        return batch

    def match_found(self, batch_id: str, match_id: int | None = None) -> FarmBatch:
        batch = self.batches[batch_id]
        batch.director.match_found(match_id)
        batch.state = BatchState.FARMING
        batch.scenario.start()
        return batch

    def load_snapshot(self, items: list[dict]) -> None:
        for item in items or []:
            try:
                b=FarmBatch(str(item["id"]),[str(x) for x in item.get("account_ids",[])],str(item.get("mode","manual")),item.get("target_xp"))
                b.state=BatchState(str(item.get("state",BatchState.IDLE.value)))
                b.created_at=item.get("created_at",b.created_at); b.started_at=item.get("started_at"); b.finished_at=item.get("finished_at")
                b.errors=list(item.get("errors",[]))[-20:]
                b.director.expected_players=int(item.get("expected_players",b.size)); b.director.ready_players=int(item.get("ready_players",0)); b.director.match_id=item.get("match_id")
                self.batches[b.id]=b
            except (KeyError,ValueError,TypeError):
                continue

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
            "match_director": b.director.state.value,
            "ready_players": b.director.ready_players,
            "expected_players": b.director.expected_players,
            "match_id": b.director.match_id,
        } for b in self.batches.values()]
