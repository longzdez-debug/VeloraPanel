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
    repeat: bool = False
    max_matches: int | None = None
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
    """Owns durable batch state and resource claims; platform automation stays outside."""

    def __init__(self, pool: AccountPool, resources: ResourceManager):
        self.pool = pool
        self.resources = resources
        self.batches: dict[str, FarmBatch] = {}

    def create_batch(self, batch_id, account_ids, mode="manual", target_xp=None, repeat=False, max_matches=None):
        if batch_id in self.batches:
            raise ValueError(f"batch already exists: {batch_id}")
        if not account_ids:
            raise ValueError("batch requires at least one account")
        if len(set(account_ids)) != len(account_ids):
            raise ValueError("batch contains duplicate accounts")
        missing = [x for x in account_ids if self.pool.get(x) is None]
        if missing:
            raise KeyError(f"unknown accounts: {', '.join(missing)}")
        self._validate_mode(mode, len(account_ids))
        if not self.resources.can_start_batch(batch_id):
            raise RuntimeError("batch resource capacity reached")
        if max_matches is not None and int(max_matches) < 1:
            raise ValueError("max_matches must be >= 1")
        batch = FarmBatch(batch_id, list(account_ids), mode, target_xp, repeat=bool(repeat), max_matches=None if max_matches is None else int(max_matches))
        self.batches[batch_id] = batch
        return batch

    @staticmethod
    def _validate_mode(mode, size):
        required = {
            "2v2": 4, "2v2_random": 4,
            "5v5": 10, "5v5_shuffle": 10,
            "deathmatch": 1, "arms_race": 1, "armory": 1, "manual": 1,
        }.get(mode)
        if required is None:
            raise ValueError(f"unsupported farm mode: {mode}")
        if size != required:
            raise ValueError(f"{mode} requires exactly {required} accounts")

    def start_batch(self, batch_id):
        batch = self.batches[batch_id]
        if batch.state not in (BatchState.IDLE, BatchState.ERROR):
            return batch
        self._validate_mode(batch.mode, batch.size)
        if not self.resources.start_batch(batch.id):
            raise RuntimeError("batch resource capacity reached")
        if any(not self.pool.get(a) or not getattr(self.pool.get(a), "enabled", True) for a in batch.account_ids):
            self.resources.stop_batch(batch.id)
            raise RuntimeError("batch contains disabled or unavailable account")
        try:
            batch.scenario.load(batch.mode)
            if batch.scenario.current.required_players != batch.size:
                raise ValueError(f"{batch.mode} requires {batch.scenario.current.required_players} accounts")
            batch.director.prepare(batch.size)
        except Exception:
            self.resources.stop_batch(batch.id)
            raise
        batch.state = BatchState.STARTING
        batch.started_at = time()
        batch.finished_at = None
        batch.errors.clear()
        for account_id in batch.account_ids:
            self.pool.mark(account_id, FarmStatus.IN_PROGRESS, target_xp=batch.target_xp)
        return batch

    def mark_ready(self, batch_id):
        batch = self.batches[batch_id]
        if batch.state == BatchState.STARTING:
            batch.state = BatchState.WAITING_FOR_READY
        return batch

    def mark_farming(self, batch_id):
        batch = self.batches[batch_id]
        if batch.state in (BatchState.STARTING, BatchState.WAITING_FOR_READY):
            batch.state = BatchState.FARMING
        return batch

    def finish_batch(self, batch_id, success=True):
        batch = self.batches[batch_id]
        batch.state = BatchState.FINISHED if success else BatchState.ERROR
        batch.finished_at = time()
        for account_id in batch.account_ids:
            if success:
                self.pool.mark(account_id, FarmStatus.COMPLETED)
            else:
                self.pool.mark(account_id, FarmStatus.ERROR)
        self.resources.stop_batch(batch.id)
        return batch

    def stop_batch(self, batch_id):
        batch = self.batches[batch_id]
        batch.state = BatchState.STOPPING
        batch.finished_at = time()
        self.resources.stop_batch(batch.id)
        for account_id in batch.account_ids:
            if self.pool.farm[account_id].status == FarmStatus.IN_PROGRESS:
                self.pool.mark(account_id, FarmStatus.PARTIAL)
        return batch

    def player_ready(self, batch_id):
        batch = self.batches[batch_id]
        batch.director.player_ready()
        if batch.director.state.value in ("lobby_ready", "waiting_for_players"):
            batch.state = BatchState.WAITING_FOR_READY
        return batch

    def start_search(self, batch_id):
        batch = self.batches[batch_id]
        batch.director.start_search()
        return batch

    def match_found(self, batch_id, match_id=None):
        batch = self.batches[batch_id]
        batch.director.match_found(match_id)
        batch.director.start_farming()
        batch.state = BatchState.FARMING
        batch.scenario.start()
        return batch

    def load_snapshot(self, items):
        for item in items or []:
            try:
                b = FarmBatch(
                    str(item["id"]),
                    [str(x) for x in item.get("account_ids", [])],
                    str(item.get("mode", "manual")),
                    item.get("target_xp"),
                    bool(item.get("repeat", False)),
                    item.get("max_matches"),
                )
                b.state = BatchState(str(item.get("state", BatchState.IDLE.value)))
                b.created_at = item.get("created_at", b.created_at)
                b.started_at = item.get("started_at")
                b.finished_at = item.get("finished_at")
                b.errors = list(item.get("errors", []))[-20:]
                b.director.expected_players = int(item.get("expected_players", b.size))
                b.director.ready_players = int(item.get("ready_players", 0))
                b.director.match_id = item.get("match_id")
                saved_director = item.get("match_director", "idle")
                try:
                    b.director.state = type(b.director.state)(saved_director)
                except ValueError:
                    b.director.state = type(b.director.state).IDLE
                # A process restart cannot safely resume an in-flight lobby/search.
                # Convert it to recoverable ERROR instead of pretending the old
                # Steam/CS2 state still exists.
                if b.state not in (BatchState.IDLE, BatchState.FINISHED, BatchState.STOPPING):
                    b.state = BatchState.ERROR
                    b.director.fail("recovery required after process restart")
                    b.errors.append("recovery required after process restart")
                self.batches[b.id] = b
            except (KeyError, ValueError, TypeError):
                continue

    def snapshot(self):
        return [{
            "id": b.id, "state": b.state.value, "mode": b.mode,
            "account_ids": list(b.account_ids), "size": b.size,
            "target_xp": b.target_xp, "repeat": b.repeat, "max_matches": b.max_matches, "created_at": b.created_at,
            "started_at": b.started_at, "finished_at": b.finished_at,
            "errors": list(b.errors[-20:]),
            "match_director": b.director.state.value,
            "ready_players": b.director.ready_players,
            "expected_players": b.director.expected_players,
            "match_id": b.director.match_id,
        } for b in self.batches.values()]
