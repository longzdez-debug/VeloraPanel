from velora.account_pool import AccountPool
from velora.farm import FarmManager
from velora.orchestrator import BatchRuntime, FarmOrchestrator
from velora.resource import ResourceBudget, ResourceManager


def test_orchestrator_snapshot_roundtrip():
    class Account:
        def __init__(self, account_id):
            self.id = account_id
            self.enabled = True

    class SupervisorStub:
        pass

    supervisor = SupervisorStub()
    supervisor.farm = FarmManager(AccountPool([Account("a")]), ResourceManager(ResourceBudget(1, 1)))
    supervisor.get_account = lambda account_id: None
    supervisor.lobbies = type("Lobbies", (), {"lobbies": {}})()
    supervisor.stats = type("Stats", (), {})()

    source = FarmOrchestrator(supervisor)
    source.runtime["b1"] = BatchRuntime("b1", {"a"}, 2, 0.0, "error", "x", {"a"}, 1)
    restored = FarmOrchestrator(supervisor)
    restored.load_snapshot(source.snapshot())

    runtime = restored.runtime["b1"]
    assert runtime.ready == {"a"}
    assert runtime.retries == 2
    assert runtime.game_over_seen == {"a"}
    assert runtime.last_match_counted == 1


def test_xp_baseline_comes_from_first_live_snapshot_not_stats_delta():
    from types import SimpleNamespace

    class Account:
        def __init__(self):
            self.id = "a"
            self.last_xp = 1200

    class SupervisorStub:
        pass

    supervisor = SupervisorStub()
    account = Account()
    supervisor.get_account = lambda account_id: account
    supervisor.pool = AccountPool([account])
    supervisor.stats = type("Stats", (), {"get": lambda self, account_id: SimpleNamespace(xp=37)})()
    supervisor.farm = FarmManager(supervisor.pool, ResourceManager(ResourceBudget(1, 1)))
    orchestrator = FarmOrchestrator(supervisor)
    batch = SimpleNamespace(account_ids=["a"])

    state = supervisor.pool.farm["a"]
    state.xp_before = None
    state.xp_after = None
    orchestrator._update_xp(batch)
    assert state.xp_before == 1200
    assert state.xp_after == 1200

    account.last_xp = 1250
    orchestrator._update_xp(batch)
    assert state.xp_before == 1200
    assert state.xp_after == 1250


def test_recovery_preserves_xp_progress():
    from types import SimpleNamespace

    class Account:
        def __init__(self):
            self.id = "a"
            self.enabled = True
            self.last_xp = 1500
            self.process_id = None
            self.fsm = type("FSM", (), {"state": "offline"})()

    account = Account()
    pool = AccountPool([account])
    resources = ResourceManager(ResourceBudget(1, 1))
    farm = FarmManager(pool, resources)
    batch = farm.create_batch("b", ["a"], target_xp=100)
    batch.state = type(batch.state).ERROR
    state = pool.farm["a"]
    state.xp_before = 1200
    state.xp_after = 1450

    class SupervisorStub:
        def __init__(self):
            self.pool = pool
            self.farm = farm
        def start_batch(self, batch_id):
            return self.farm.start_batch(batch_id)

    supervisor = SupervisorStub()
    orchestrator = FarmOrchestrator(supervisor)
    runtime = BatchRuntime("b", retries=1)
    orchestrator.runtime["b"] = runtime
    runtime.next_retry = 0
    assert orchestrator._recover(batch, runtime, 0) is True
    assert pool.farm["a"].xp_before == 1200
    assert pool.farm["a"].xp_after == 1450
