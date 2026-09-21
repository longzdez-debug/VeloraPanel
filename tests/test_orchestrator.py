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
