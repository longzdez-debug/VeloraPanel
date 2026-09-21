from types import SimpleNamespace

from velora.accounts import AccountStore, AccountProfile
from velora.config import Config
from velora.supervisor import Supervisor


def test_account_profile_updates_persist(tmp_path):
    store = AccountStore(str(tmp_path / "accounts.json"))
    store.save([AccountProfile("a", "Alpha", steam_id="1")])
    sup = Supervisor(Config(data_dir=str(tmp_path)))
    sup.attach_account_store(store)
    account = SimpleNamespace(
        id="a", name="Alpha 2", steam_id="2", enabled=False,
        executable="cs2.exe", launch_args=["-novid"],
        walkbot=SimpleNamespace(enabled=False),
    )
    sup.accounts.append(account)
    sup.pool.add(account)
    sup.save_account_profile("a")
    saved = store.load()[0]
    assert saved.name == "Alpha 2"
    assert saved.steam_id == "2"
    assert saved.enabled is False
    assert saved.walkbot is False
    assert saved.launch_args == ["-novid"]
    assert saved.route_map == "de_dust2"
    assert saved.route_start == "a"
    assert saved.route_goal == "b"
