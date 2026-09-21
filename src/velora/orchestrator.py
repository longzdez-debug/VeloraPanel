from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic

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


class FarmOrchestrator:
    """Closed-loop batch controller.

    It owns recovery and state progression, while platform-specific lobby
    automation remains behind the existing lobby adapter.
    """

    def __init__(self, supervisor):
        self.s = supervisor
        self.runtime: dict[str, BatchRuntime] = {}
        self.max_retries = 3
        self.retry_delay = 5.0
        self.ready_timeout = 90.0

    def _rt(self, batch) -> BatchRuntime:
        return self.runtime.setdefault(batch.id, BatchRuntime(batch.id))

    def _fail(self, batch, message: str, now: float) -> None:
        runtime = self._rt(batch)
        runtime.retries += 1
        runtime.last_error = message
        batch.errors.append(message)
        if runtime.retries > self.max_retries:
            self.s.farm.finish_batch(batch.id, False)
            return
        runtime.next_retry = now + self.retry_delay * (2 ** (runtime.retries - 1))
        for account_id in batch.account_ids:
            try:
                self.s.stop_account(account_id)
            except Exception:
                pass
        batch.state = BatchState.ERROR

    def _all_live(self, batch) -> bool:
        return all(
            (account := self.s.get_account(account_id)) is not None
            and account.fsm.state == AccountState.IN_MATCH
            for account_id in batch.account_ids
        )

    def _all_game_over(self, batch, runtime: BatchRuntime) -> bool:
        for account_id in batch.account_ids:
            account = self.s.get_account(account_id)
            if account is None:
                return False
            if account.match_state() == MatchState.GAME_OVER:
                runtime.game_over_seen.add(account_id)
        return len(runtime.game_over_seen) == batch.size

    def _recover(self, batch, runtime: BatchRuntime, now: float) -> None:
        if now < runtime.next_retry:
            return
        if runtime.retries > self.max_retries:
            return
        try:
            self.s.start_batch(batch.id)
            runtime.ready.clear()
            runtime.game_over_seen.clear()
            batch.errors.append(f"recovery attempt #{runtime.retries}")
            runtime.last_error = None
        except Exception as exc:
            runtime.next_retry = now + self.retry_delay
            runtime.last_error = str(exc)

    def tick(self, now: float | None = None) -> bool:
        now = monotonic() if now is None else now
        changed = False

        for batch in list(self.s.farm.batches.values()):
            runtime = self._rt(batch)

            if batch.state in (BatchState.FINISHED, BatchState.STOPPING):
                continue

            if batch.state == BatchState.ERROR:
                self._recover(batch, runtime, now)
                runtime.last_state = batch.state.value
                changed = True
                continue

            accounts = [self.s.get_account(account_id) for account_id in batch.account_ids]
            if any(account is None or not account.enabled for account in accounts):
                self._fail(batch, "batch contains unavailable account", now)
                changed = True
                continue

            if batch.state in (BatchState.STARTING, BatchState.WAITING_FOR_READY):
                for account in accounts:
                    if (
                        account.last_gsi is not None
                        and account.fsm.state
                        in (AccountState.MENU, AccountState.QUEUING, AccountState.IN_MATCH)
                    ):
                        if account.id not in runtime.ready:
                            runtime.ready.add(account.id)
                            batch.director.player_ready()
                            changed = True

                if batch.director.state == MatchDirectorState.LOBBY_READY:
                    if batch.id not in self.s.lobbies.lobbies:
                        try:
                            self.s.create_lobby(batch.id, batch.account_ids)
                        except Exception:
                            pass
                    if batch.state != BatchState.WAITING_FOR_READY:
                        self.s.farm.mark_ready(batch.id)
                        changed = True
                    if batch.director.state == MatchDirectorState.LOBBY_READY:
                        try:
                            self.s.ready_lobby(batch.id, "orchestrated")
                        except Exception:
                            pass
                        if batch.director.state == MatchDirectorState.LOBBY_READY:
                            try:
                                self.s.farm.start_search(batch.id)
                                changed = True
                            except RuntimeError as exc:
                                runtime.last_error = str(exc)

            if batch.director.state == MatchDirectorState.SEARCHING and self._all_live(batch):
                try:
                    self.s.farm.match_found(batch.id)
                    batch.director.start_farming()
                    changed = True
                except RuntimeError as exc:
                    runtime.last_error = str(exc)

            if batch.state == BatchState.FARMING and self._all_game_over(batch, runtime):
                batch.scenario.complete_match()
                runtime.last_match_counted += 1
                self.s.stats.record_match(
                    batch.account_ids[0],
                    match_count=1,
                )
                batch.director.finish()
                self.s.farm.finish_batch(batch.id, True)
                changed = True

            # A batch with a live farm but a dead/non-ready account must not hang forever.
            if batch.state in (
                BatchState.STARTING,
                BatchState.WAITING_FOR_READY,
                BatchState.FARMING,
            ):
                dead = [
                    account.id
                    for account in accounts
                    if account.process_id is None
                    or account.fsm.state == AccountState.ERROR
                ]
                if dead:
                    self._fail(batch, f"account recovery required: {', '.join(dead)}", now)
                    changed = True

            runtime.last_state = batch.state.value

        return changed

    def snapshot(self) -> list[dict]:
        now = monotonic()
        return [
            {
                "batch_id": runtime.batch_id,
                "ready": sorted(runtime.ready),
                "retries": runtime.retries,
                "retry_after": max(0.0, runtime.next_retry - now),
                "last_state": runtime.last_state,
                "last_error": runtime.last_error,
                "game_over_seen": sorted(runtime.game_over_seen),
                "last_match_counted": runtime.last_match_counted,
            }
            for runtime in self.runtime.values()
        ]

    def load_snapshot(self, items: list[dict] | None) -> None:
        now = monotonic()
        for value in items or []:
            try:
                self.runtime[str(value["batch_id"])] = BatchRuntime(
                    batch_id=str(value["batch_id"]),
                    ready=set(value.get("ready", [])),
                    retries=int(value.get("retries", 0)),
                    next_retry=now + max(0.0, float(value.get("retry_after", 0.0))),
                    last_state=str(value.get("last_state", "")),
                    last_error=value.get("last_error"),
                    game_over_seen=set(value.get("game_over_seen", [])),
                    last_match_counted=int(value.get("last_match_counted", 0)),
                )
            except (KeyError, TypeError, ValueError):
                continue
