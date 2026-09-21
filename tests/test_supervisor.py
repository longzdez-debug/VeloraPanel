from types import SimpleNamespace

from velora.config import Config
from velora.farm import BatchState
from velora.model import AccountState
from velora.supervisor import Supervisor


def test_shutdown_does_not_persist_active_farming_batch(tmp_path):
    sup = Supervisor(Config(data_dir=str(tmp_path)))
    account = SimpleNamespace(id="a", enabled=True, process_id=None, fsm=SimpleNamespace(state=AccountState.OFFLINE), walkbot=SimpleNamespace(stop=lambda: None, replan=None), stop=lambda: None)
    sup.add_account(account)
    batch = sup.create_batch("b", ["a"], mode="manual")
    batch.state = BatchState.FARMING
    sup.stop()
    restored = Supervisor(Config(data_dir=str(tmp_path)))
    assert restored.farm.batches["b"].state == BatchState.IDLE


def test_delete_terminal_batch_removes_runtime_and_persists(tmp_path):
    sup = Supervisor(Config(data_dir=str(tmp_path)))
    account = SimpleNamespace(
        id="a", enabled=True, process_id=None,
        fsm=SimpleNamespace(state=AccountState.OFFLINE),
        walkbot=SimpleNamespace(stop=lambda: None, replan=None),
        stop=lambda: None,
    )
    sup.add_account(account)
    batch = sup.create_batch("b", ["a"], mode="manual")
    batch.state = BatchState.ERROR
    sup.orchestrator.runtime["b"] = SimpleNamespace(match_key=("de_dust2", 1, 1))
    sup.delete_batch("b")
    assert "b" not in sup.farm.batches
    assert "b" not in sup.orchestrator.runtime
    restored = Supervisor(Config(data_dir=str(tmp_path)))
    assert "b" not in restored.farm.batches



def test_direct_farming_recovery_claim_is_not_double_acquired(tmp_path):
    sup = Supervisor(Config(data_dir=str(tmp_path)))
    account = SimpleNamespace(
        id="a", enabled=True, process_id=None,
        fsm=SimpleNamespace(state=AccountState.OFFLINE),
        walkbot=SimpleNamespace(stop=lambda: None, replan=None),
        stop=lambda: None,
    )
    sup.add_account(account)
    batch = sup.create_batch("b", ["a"], mode="manual")
    batch.state = BatchState.FARMING
    sup.orchestrator.runtime["b"] = type("Runtime", (), {
        "match_key": ("de_dust2", 1, 1), "recovery_claimed": False
    })()
    sup.recover_batch("b")
    assert sup.orchestrator.runtime["b"].recovery_claimed is True
    assert sup.resources.snapshot()["accounts_in_use"] == 1


def test_remove_account_clears_window_guard(tmp_path):
    sup = Supervisor(Config(data_dir=str(tmp_path)))
    account = SimpleNamespace(
        id="a", enabled=True, process_id=None,
        fsm=SimpleNamespace(state=AccountState.OFFLINE),
        walkbot=SimpleNamespace(stop=lambda: None, replan=None),
        stop=lambda: None,
    )
    guard = SimpleNamespace(bind=lambda pid: None)
    sup.add_account(account)
    sup.bind_window_guard("a", guard)
    sup.remove_account("a")
    assert "a" not in sup.window_guards
