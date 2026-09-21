from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceBudget:
    max_accounts: int = 1
    max_batches: int = 1


class ResourceManager:
    """Deterministic concurrency gate; OS metrics can be added later without changing callers."""

    def __init__(self, budget: ResourceBudget | None = None):
        self.budget = budget or ResourceBudget()
        self.active_accounts: set[str] = set()
        self.active_batches: set[str] = set()

    def can_start_account(self, account_id: str) -> bool:
        return account_id in self.active_accounts or len(self.active_accounts) < self.budget.max_accounts

    def start_account(self, account_id: str) -> bool:
        if not self.can_start_account(account_id):
            return False
        self.active_accounts.add(account_id)
        return True

    def stop_account(self, account_id: str) -> None:
        self.active_accounts.discard(account_id)

    def can_start_batch(self, batch_id: str) -> bool:
        return batch_id in self.active_batches or len(self.active_batches) < self.budget.max_batches

    def start_batch(self, batch_id: str) -> bool:
        if not self.can_start_batch(batch_id):
            return False
        self.active_batches.add(batch_id)
        return True

    def stop_batch(self, batch_id: str) -> None:
        self.active_batches.discard(batch_id)

    def snapshot(self) -> dict:
        return {
            "active_accounts": len(self.active_accounts),
            "active_batches": len(self.active_batches),
            "max_accounts": self.budget.max_accounts,
            "max_batches": self.budget.max_batches,
        }
