from types import SimpleNamespace\n\nfrom velora.config import Config
from velora.farm import BatchState
from velora.supervisor import Supervisor


def test_shutdown_does_not_persist_active_farming_batch(tmp_path):
    sup = Supervisor(Config(data_dir=str(tmp_path)))
    account = SimpleNamespace(id="a", enabled=True)
    sup.add_account(account)
    batch = sup.create_batch("b", ["a"], mode="manual")
    batch.state = BatchState.FARMING
    sup.stop()
    restored = Supervisor(Config(data_dir=str(tmp_path)))
    assert restored.farm.batches["b"].state == BatchState.IDLE
