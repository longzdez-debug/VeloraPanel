from __future__ import annotations
from dataclasses import dataclass, field
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
    def record_match(self, account_id: str, *, xp_delta: int = 0, win: bool = False) -> AccountStats:
        s=self.get(account_id); s.matches+=1; s.xp+=xp_delta; s.wins+=int(win); s.losses+=int(not win); s.last_match_at=time(); return s
    def mark_farmed(self, ids): 
        for i in ids:self.get(i).farmed=True
    def mark_collected(self, ids):
        for i in ids:self.get(i).collected=True
    def snapshot(self): return [s.__dict__.copy() for s in self.items.values()]
