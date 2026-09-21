from velora.account_pool import AccountPool
from velora.farm import BatchState, FarmManager
from velora.resource import ResourceBudget, ResourceManager


class Account:
    def __init__(self, account_id):
        self.id = account_id
        self.enabled = True


def test_single_player_mode_has_strict_size():
    pool = AccountPool([Account("a")])
    farm = FarmManager(pool, ResourceManager(ResourceBudget(1, 1)))
    batch = farm.create_batch("b", ["a"], mode="deathmatch")
    assert batch.size == 1


def test_restart_recovery_converts_active_batch_to_error():
    pool = AccountPool([Account("a")])
    farm = FarmManager(pool, ResourceManager(ResourceBudget(1, 1)))
    farm.create_batch("b", ["a"], mode="deathmatch")
    farm.start_batch("b")
    snapshot = farm.snapshot()

    restored = FarmManager(pool, ResourceManager(ResourceBudget(1, 1)))
    restored.load_snapshot(snapshot)
    assert restored.batches["b"].state == BatchState.ERROR
    assert restored.batches["b"].errors
