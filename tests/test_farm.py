from velora.account_pool import AccountPool, FarmStatus
from velora.farm import BatchState, FarmManager
from velora.resource import ResourceBudget, ResourceManager


class A:
    def __init__(self, id):
        self.id = id
        self.enabled = True


def test_farm_batch_supports_ten_accounts():
    pool = AccountPool([A(str(i)) for i in range(10)])
    farm = FarmManager(pool, ResourceManager(ResourceBudget(max_accounts=10, max_batches=1)))
    batch = farm.create_batch("b1", [str(i) for i in range(10)], mode="5v5")
    farm.start_batch("b1")
    assert batch.size == 10
    assert batch.state == BatchState.STARTING
    assert all(pool.farm[str(i)].status == FarmStatus.IN_PROGRESS for i in range(10))


def test_multiple_batches_are_resource_limited():
    pool = AccountPool([A(str(i)) for i in range(20)])
    resources = ResourceManager(ResourceBudget(max_accounts=20, max_batches=2))
    farm = FarmManager(pool, resources)
    farm.create_batch("b1", [str(i) for i in range(10)])
    farm.create_batch("b2", [str(i) for i in range(10, 20)])
    farm.start_batch("b1")
    farm.start_batch("b2")
    assert len(resources.active_batches) == 2
    try:
        farm.create_batch("b3", ["0"])
        assert False
    except RuntimeError:
        pass
