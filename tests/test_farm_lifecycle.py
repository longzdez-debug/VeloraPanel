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


def test_walkbot_enters_navigation_after_first_live_gsi():
    from velora.model import GsiSnapshot, WalkState
    from velora.walkbot import WalkBot

    class Input:
        def __init__(self):
            self.released = 0
        def release_all(self):
            self.released += 1
        def move(self, forward, back, left, right):
            pass

    inp = Input()
    bot = WalkBot(inp)
    bot.start()
    bot.on_gsi(GsiSnapshot(1.0, activity="playing", round_phase="live", health=100, map_name="de_dust2", position=(0, 0, 0)))
    assert bot.fsm.state == WalkState.NAVIGATING


def test_walkbot_resets_to_waiting_for_game_on_menu():
    from velora.model import GsiSnapshot, WalkState
    from velora.walkbot import WalkBot

    class Input:
        def release_all(self):
            pass
        def move(self, forward, back, left, right):
            pass

    bot = WalkBot(Input())
    bot.start()
    bot.on_gsi(GsiSnapshot(1.0, activity="playing", round_phase="live", health=100, map_name="de_dust2", position=(0, 0, 0)))
    bot.on_gsi(GsiSnapshot(2.0, activity="menu", map_phase="menu"))
    assert bot.fsm.state == WalkState.WAITING_FOR_GAME


def test_gsi_routes_to_matching_steam_account_only():
    from velora.account import Account
    from velora.config import Config
    from velora.model import GsiSnapshot
    from velora.supervisor import Supervisor
    from velora.walkbot import WalkBot

    class Input:
        def release_all(self):
            pass
        def move(self, forward, back, left, right):
            pass

    sup = Supervisor(Config(data_dir="data-test-gsi"))
    a = Account("a", "A", WalkBot(Input()), steam_id="111")
    b = Account("b", "B", WalkBot(Input()), steam_id="222")
    sup.add_account(a)
    sup.add_account(b)

    sup.on_gsi(GsiSnapshot(1.0, activity="playing", round_phase="live", health=100, map_name="de_dust2", steam_id="111"))
    assert a.last_gsi == 1.0
    assert b.last_gsi is None


def test_repeat_batch_is_bounded():
    from velora.account_pool import AccountPool
    from velora.farm import FarmManager, BatchState
    from velora.resource import ResourceBudget, ResourceManager

    class A:
        def __init__(self, id): self.id=id; self.enabled=True

    pool=AccountPool([A("a")])
    fm=FarmManager(pool, ResourceManager(ResourceBudget(max_accounts=1,max_batches=1)))
    batch=fm.create_batch("r",["a"],"manual",repeat=True,max_matches=3)
    assert batch.repeat is True
    assert batch.max_matches == 3
    fm.start_batch("r")
    assert batch.state == BatchState.STARTING


def test_same_map_consecutive_matches_get_new_generation():
    from velora.rounds import MatchTracker
    tracker = MatchTracker()
    tracker.update("de_dust2", "live", 1)
    first = tracker.match_id
    tracker.update("de_dust2", "gameover", 30)
    tracker.update("de_dust2", "live", 1)
    assert tracker.match_id > first


def test_target_xp_baseline_math():
    from velora.account_pool import AccountPool
    from velora.farm import FarmManager
    from velora.resource import ResourceBudget, ResourceManager
    class A:
        def __init__(self, account_id):
            self.id = account_id
            self.enabled = True
    pool = AccountPool([A("a")])
    fm = FarmManager(pool, ResourceManager(ResourceBudget(1, 1)))
    batch = fm.create_batch("xp", ["a"], "deathmatch", target_xp=100)
    pool.farm["a"].xp_before = 1000
    pool.farm["a"].xp_after = 1099
    assert pool.farm["a"].xp_after - pool.farm["a"].xp_before < batch.target_xp
    pool.farm["a"].xp_after = 1100
    assert pool.farm["a"].xp_after - pool.farm["a"].xp_before >= batch.target_xp


def test_farming_batch_survives_snapshot_for_explicit_runtime_recovery():
    from velora.account_pool import AccountPool
    from velora.farm import BatchState, FarmManager
    from velora.resource import ResourceBudget, ResourceManager

    pool = AccountPool([Account("a")])
    fm = FarmManager(pool, ResourceManager(ResourceBudget(1, 1)))
    batch = fm.create_batch("b", ["a"], mode="deathmatch")
    fm.start_batch("b")
    batch.state = BatchState.FARMING
    snapshot = fm.snapshot()

    restored = FarmManager(pool, ResourceManager(ResourceBudget(1, 1)))
    restored.load_snapshot(snapshot)
    assert restored.batches["b"].state == BatchState.FARMING
