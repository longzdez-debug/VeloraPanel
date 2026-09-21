from __future__ import annotations

from dataclasses import dataclass
from time import time


@dataclass
class AccountStats:
    account_id: str
    xp: int = 0
    level: int = 0
    matches: int = 0
    wins: int = 0
    losses: int = 0
    farmed: bool = False
    collected: bool = False
    last_match_at: float | None = None


class StatsStore:
    def __init__(self):
        self.items: dict[str, AccountStats] = {}

    def get(self, account_id: str) -> AccountStats:
        return self.items.setdefault(account_id, AccountStats(account_id))

    def record_match(
        self,
        account_id: str,
        *,
        xp_delta: int = 0,
        win: bool | None = None,
        match_count: int = 1,
    ) -> AccountStats:
        stats = self.get(account_id)
        stats.matches += max(1, int(match_count))
        stats.xp += int(xp_delta)
        if win is True:
            stats.wins += 1
        elif win is False:
            stats.losses += 1
        stats.last_match_at = time()
        return stats

    def mark_farmed(self, ids) -> None:
        for account_id in ids:
            self.get(account_id).farmed = True

    def mark_collected(self, ids) -> None:
        for account_id in ids:
            self.get(account_id).collected = True

    def snapshot(self) -> list[dict]:
        return [stats.__dict__.copy() for stats in self.items.values()]

    def load_snapshot(self, items: list[dict] | None) -> None:
        self.items.clear()
        for value in items or []:
            try:
                stats = AccountStats(
                    account_id=str(value["account_id"]),
                    xp=int(value.get("xp", 0)),
                    level=int(value.get("level", 0)),
                    matches=int(value.get("matches", 0)),
                    wins=int(value.get("wins", 0)),
                    losses=int(value.get("losses", 0)),
                    farmed=bool(value.get("farmed", False)),
                    collected=bool(value.get("collected", False)),
                    last_match_at=value.get("last_match_at"),
                )
                self.items[stats.account_id] = stats
            except (KeyError, TypeError, ValueError):
                continue
