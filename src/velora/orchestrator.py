from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic, time

from .farm import BatchState
from .match_director import MatchDirectorState
from .model import AccountState, MatchState


@dataclass
class BatchRuntime:
    batch_id: str
    ready: set[str] = field(default_factory=set)
    retries: int = 0
    next_retry: float = 0.0
    last_state: str = ""
    last_error: str | None = None
    game_over_seen: set[str] = field(default_factory=set)
    last_match_counted: int = 0
    ready_since: float | None = None
    search_since: float | None = None
    match_key: tuple | None = None
    match_started_at: float | None = None
    match_generation: dict[str, int] = field(default_factory=dict)

class FarmOrchestrator:
    def __init__(self, supervisor):
        self.s = supervisor
        self.runtime: dict[str, BatchRuntime] = {}
        self.max_retries = 3
        self.retry_delay = 5.0
        self.ready_timeout = 90.0
        self.search_timeout = 180.0
        self.match_grace = 8.0

    def _rt(self, batch):
        return self.runtime.setdefault(batch.id, BatchRuntime(batch.id))

    def _fail(self, batch, message, now):
        runtime = self._rt(batch)
        runtime.retries += 1
        runtime.last_error = message
        batch.errors.append(message)
        for account_id in batch.account_ids:
            try:
                self.s.stop_account(account_id)
            except Exception:
                pass
        self.s.farm.finish_batch(batch.id, False) if runtime.retries > self.max_retries else self.s.farm.stop_batch(batch.id)
        if runtime.retries <= self.max_retries:
            batch.state = BatchState.ERROR
            runtime.next_retry = now + self.retry_delay * (2 ** (runtime.retries - 1))

    def _all_live(self, batch):
        return all(
            (account := self.s.get_account(account_id)) is not None
            and account.fsm.state == AccountState.IN_MATCH
            for account_id in batch.account_ids
        )

    def _capture_match(self, batch, runtime, now):
        accounts = [self.s.get_account(x) for x in batch.account_ids]
        if any(a is None for a in accounts):
            return False
        identities = [a.match_identity for a in accounts]
        if any(key[1] is None or key[0] <= runtime.match_generation.get(a.id, -1) for a, key in zip(accounts, identities)):
            return False
        maps = {key[1] for key in identities}
        rounds = {key[2] for key in identities if key[2] is not None}
        generations = {key[0] for key in identities}
        if len(maps) != 1 or (len(rounds) > 1) or (len(generations) != 1):
            return False
        runtime.match_key = (next(iter(maps)), next(iter(rounds)) if rounds else None, next(iter(generations)))
        runtime.match_started_at = time()
        return True

    def _target_reached(self, batch):
        if batch.target_xp is None:
            return False
        target = int(batch.target_xp)
        if target <= 0:
            return True
        return all(
            self.s.pool.farm[a].xp_before is not None
            and self.s.pool.farm[a].xp_after is not None
            and self.s.pool.farm[a].xp_after - self.s.pool.farm[a].xp_before >= target
            for a in batch.account_ids
        )

    def _update_xp(self, batch):
        for account_id in batch.account_ids:
            account = self.s.get_account(account_id)
            state = self.s.pool.farm[account_id]
            if account and account.last_xp is not None:
                state.xp_after = account.last_xp

    def _all_game_over(self, batch, runtime):
        for account_id in batch.account_ids:
            account = self.s.get_account(account_id)
            if account and account.match_state() == MatchState.GAME_OVER:
                runtime.game_over_seen.add(account_id)
        return bool(runtime.match_key) and len(runtime.game_over_seen) == batch.size

    def _recover(self, batch, runtime, now):
        if now < runtime.next_retry or runtime.retries > self.max_retries:
            return False
        try:
            self.s.start_batch(batch.id)
            runtime.ready.clear()
            runtime.game_over_seen.clear()
            runtime.match_key = None
            runtime.match_started_at = None
            runtime.match_generation.clear()
            runtime.ready_since = now
            runtime.search_since = None
            runtime.last_error = None
            return True
        except Exception as exc:
            runtime.next_retry = now + self.retry_delay
            runtime.last_error = str(exc)
            return False

    def tick(self, now=None):
        now = monotonic() if now is None else now
        changed = False
        for batch in list(self.s.farm.batches.values()):
            runtime = self._rt(batch)
            if batch.state in (BatchState.FINISHED, BatchState.STOPPING, BatchState.IDLE):
                continue

            if batch.state == BatchState.ERROR:
                if self._recover(batch, runtime, now):
                    changed = True
                continue

            accounts = [self.s.get_account(x) for x in batch.account_ids]
            if any(a is None or not a.enabled for a in accounts):
                self._fail(batch, "batch contains unavailable account", now)
                changed = True
                continue

            if batch.state in (BatchState.STARTING, BatchState.WAITING_FOR_READY):
                if runtime.ready_since is None:
                    runtime.ready_since = now
                for account in accounts:
                    if (
                        account.last_gsi is not None
                        and account.fsm.state in (AccountState.MENU, AccountState.QUEUING, AccountState.IN_MATCH)
                        and account.id not in runtime.ready
                    ):
                        runtime.ready.add(account.id)
                        self.s.farm.player_ready(batch.id)
                        changed = True

                if len(runtime.ready) < batch.size and now - runtime.ready_since > self.ready_timeout:
                    self._fail(batch, "ready timeout", now)
                    changed = True
                    continue

                if batch.director.state == MatchDirectorState.LOBBY_READY:
                    if batch.size not in (4, 10):
                        self._fail(batch, "unsupported lobby size for automated mode", now)
                        changed = True
                        continue
                    if batch.id not in self.s.lobbies.lobbies:
                        try:
                            self.s.create_lobby(batch.id, batch.account_ids)
                        except Exception as exc:
                            self._fail(batch, f"lobby create failed: {exc}", now)
                            changed = True
                            continue
                    try:
                        self.s.ready_lobby(batch.id, "orchestrated")
                        self.s.farm.start_search(batch.id)
                        runtime.ready_since = None
                        runtime.search_since = now
                        runtime.match_key = None
                        runtime.match_started_at = None
                        runtime.match_generation = {
                            a.id: getattr(a.match, "match_id", 0) for a in accounts
                        }
                        changed = True
                    except Exception as exc:
                        self._fail(batch, f"search start failed: {exc}", now)
                        changed = True

            if batch.director.state == MatchDirectorState.SEARCHING:
                search_since = runtime.search_since
                if search_since is None:
                    runtime.search_since = now
                    search_since = now
                if self._all_live(batch) and runtime.match_key is None:
                    if self._capture_match(batch, runtime, now):
                        try:
                            self.s.farm.match_found(batch.id, runtime.match_key)
                            runtime.game_over_seen.clear()
                            changed = True
                        except Exception as exc:
                            self._fail(batch, f"match transition failed: {exc}", now)
                            changed = True
                    elif now - search_since > self.match_grace:
                        self._fail(batch, "match identity could not be correlated", now)
                        changed = True
                elif now - search_since > self.search_timeout:
                    self._fail(batch, "match search timeout", now)
                    changed = True
                    continue

            if batch.state == BatchState.FARMING and self._all_game_over(batch, runtime):
                batch.scenario.complete_match()
                runtime.last_match_counted += 1
                self._update_xp(batch)
                duration = max(0.0, time() - (runtime.match_started_at or batch.started_at or time()))
                finished_at = time()
                for account_id in batch.account_ids:
                    self.s.stats.record_match(account_id, match_count=1)
                    state = self.s.pool.farm[account_id]
                    state.matches_played += 1
                    state.farm_seconds += duration
                    state.last_farm_at = finished_at
                target_reached = self._target_reached(batch)
                if target_reached or (batch.max_matches is not None and runtime.last_match_counted >= batch.max_matches):
                    batch.director.finish()
                    self.s.farm.finish_batch(batch.id, True)
                elif batch.repeat:
                    batch.director.reset()
                    batch.scenario.reset()
                    runtime.ready.clear()
                    runtime.game_over_seen.clear()
                    runtime.match_key = None
                    runtime.match_started_at = None
                    runtime.match_generation.clear()
                    runtime.ready_since = now
                    runtime.search_since = None
                    batch.state = BatchState.WAITING_FOR_READY
                else:
                    batch.director.finish()
                    self.s.farm.finish_batch(batch.id, True)
                changed = True

            self._update_xp(batch)
            stale = [account.id for account in accounts if account.gsi_stale(getattr(self.s.config, "gsi_timeout", 8.0), now)]
            if stale and batch.state == BatchState.FARMING:
                self._fail(batch, "GSI heartbeat lost: " + ", ".join(stale), now)
                changed = True
                continue

            dead = [
                account.id for account in accounts
                if account.process_id is None or account.fsm.state == AccountState.ERROR
            ]
            if dead and batch.state in (BatchState.STARTING, BatchState.WAITING_FOR_READY, BatchState.FARMING):
                self._fail(batch, f"account recovery required: {', '.join(dead)}", now)
                changed = True

            runtime.last_state = batch.state.value
        return changed

    def snapshot(self):
        now = monotonic()
        return [{
            "batch_id": r.batch_id, "ready": sorted(r.ready),
            "retries": r.retries, "retry_after": max(0.0, r.next_retry - now),
            "last_state": r.last_state, "last_error": r.last_error,
            "game_over_seen": sorted(r.game_over_seen),
            "last_match_counted": r.last_match_counted,
            "ready_age": max(0.0, now - r.ready_since) if r.ready_since else 0.0,
            "search_age": max(0.0, now - r.search_since) if r.search_since else 0.0,
            "match_key": list(r.match_key) if r.match_key is not None else None,
            "match_started_age": max(0.0, now - r.match_started_at) if r.match_started_at else 0.0,
            "match_generation": dict(r.match_generation),
        } for r in self.runtime.values()]

    def load_snapshot(self, items):
        now = monotonic()
        for value in items or []:
            try:
                ready_age = max(0.0, float(value.get("ready_age", 0.0)))
                match_key = value.get("match_key")
                self.runtime[str(value["batch_id"])] = BatchRuntime(
                    batch_id=str(value["batch_id"]),
                    ready=set(value.get("ready", [])),
                    retries=int(value.get("retries", 0)),
                    next_retry=now + max(0.0, float(value.get("retry_after", 0.0))),
                    last_state=str(value.get("last_state", "")),
                    last_error=value.get("last_error"),
                    game_over_seen=set(value.get("game_over_seen", [])),
                    last_match_counted=int(value.get("last_match_counted", 0)),
                    ready_since=now - ready_age if ready_age else None,
                    search_since=now - max(0.0, float(value.get("search_age", 0.0))) if value.get("search_age") else None,
                    match_key=tuple(match_key) if match_key else None,
                    match_started_at=now - max(0.0, float(value.get("match_started_age", 0.0))) if value.get("match_started_age") else None,
                    match_generation={str(k): int(v) for k, v in value.get("match_generation", {}).items()},
                )
            except (KeyError, TypeError, ValueError):
                continue
