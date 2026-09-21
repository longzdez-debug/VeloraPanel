from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class FarmStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PARTIAL = "partial"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class AccountFarmState:
    account_id: str
    status: FarmStatus = FarmStatus.NOT_STARTED
    target_xp: int | None = None
    xp_before: int | None = None
    xp_after: int | None = None
    matches_played: int = 0
    farm_seconds: float = 0.0
    last_farm_at: float | None = None
    errors: int = 0


class AccountPool:
    """Owns account selection policy without owning the account FSM itself."""

    def __init__(self, accounts: Iterable[object] = ()):
        self.accounts: dict[str, object] = {}
        self.farm: dict[str, AccountFarmState] = {}
        self.add_many(accounts)

    def add(self, account: object) -> None:
        account_id = str(account.id)
        self.accounts[account_id] = account
        self.farm.setdefault(account_id, AccountFarmState(account_id))

    def add_many(self, accounts: Iterable[object]) -> None:
        for account in accounts:
            self.add(account)

    def remove(self, account_id: str) -> None:
        self.accounts.pop(account_id, None)
        self.farm.pop(account_id, None)

    def get(self, account_id: str) -> object | None:
        return self.accounts.get(account_id)

    def all(self) -> list[object]:
        return list(self.accounts.values())

    def enabled(self) -> list[object]:
        return [a for a in self.accounts.values() if getattr(a, "enabled", True)]

    def select(self, account_ids: Iterable[str] | None = None, limit: int | None = None) -> list[object]:
        if account_ids is None:
            selected = self.enabled()
        else:
            selected = [self.accounts[x] for x in account_ids if x in self.accounts and getattr(self.accounts[x], "enabled", True)]
        selected.sort(key=lambda a: (self.farm[str(a.id)].status == FarmStatus.COMPLETED, str(a.id)))
        return selected if limit is None else selected[:max(0, limit)]

    def select_unfarmed(self, limit: int | None = None) -> list[object]:
        selected = [a for a in self.enabled() if self.farm[str(a.id)].status != FarmStatus.COMPLETED]
        selected.sort(key=lambda a: (self.farm[str(a.id)].last_farm_at is not None, str(a.id)))
        return selected if limit is None else selected[:max(0, limit)]

    def mark(self, account_id: str, status: FarmStatus, **updates) -> AccountFarmState:
        state = self.farm[account_id]
        state.status = status
        for key, value in updates.items():
            if hasattr(state, key):
                setattr(state, key, value)
        return state
