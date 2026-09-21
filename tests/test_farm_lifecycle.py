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


def test_manual_mode_allows_multi_account_batches():
    from velora.account_pool import AccountPool
    from velora.farm import FarmManager
    from velora.resource import ResourceBudget, ResourceManager

    pool = AccountPool([Account(str(i)) for i in range(3)])
    farm = FarmManager(pool, ResourceManager(ResourceBudget(3, 1)))
    batch = farm.create_batch("manual-many", ["0", "1", "2"], mode="manual")
    farm.start_batch("manual-many")
    assert batch.size == 3
    assert batch.scenario.current.required_players == 3

def test_duplicate_round_updates_count_once_and_overtime_continues():
    from velora.rounds import MatchTracker, RoundState
    tracker = MatchTracker()
    tracker.update("de_dust2", "live", 1)
    tracker.update("de_dust2", "live", 1)
    assert tracker.rounds_seen == 1
    tracker.update("de_dust2", "over", 1)
    assert tracker.state == RoundState.OVER
    tracker.update("de_dust2", "live", 2)
    tracker.update("de_dust2", "live", 2)
    assert tracker.rounds_seen == 2
    tracker.update("de_dust2", "halftime", 2)
    assert tracker.state == RoundState.HALFTIME
    tracker.update("de_dust2", "live", 3)
    assert tracker.rounds_seen == 3


def test_round_over_does_not_end_account_match_but_map_gameover_does():
    from velora.account import Account
    from velora.model import AccountState, GsiSnapshot
    from velora.walkbot import WalkBot

    class Input:
        def release_all(self): pass
        def move(self, forward, back, left, right): pass

    account = Account("a", "A", WalkBot(Input()))
    account.start()
    account.on_gsi(GsiSnapshot(1.0, activity="playing", map_name="de_dust2", map_phase="live", round_phase="live", round_number=1))
    assert account.fsm.state == AccountState.IN_MATCH
    account.on_gsi(GsiSnapshot(2.0, activity="playing", map_name="de_dust2", map_phase="live", round_phase="over", round_number=1))
    assert account.fsm.state == AccountState.IN_MATCH
    account.on_gsi(GsiSnapshot(3.0, activity="playing", map_name="de_dust2", map_phase="live", round_phase="freezetime", round_number=2))
    assert account.fsm.state == AccountState.IN_MATCH
    assert account.match_rounds == 2
    account.on_gsi(GsiSnapshot(4.0, activity="playing", map_name="de_dust2", map_phase="gameover", round_phase="gameover", round_number=30, player_team="CT", team_score=16, opponent_score=12))
    assert account.fsm.state == AccountState.MENU
    assert account.last_match_result is True


def test_terminal_gsi_latch_ignores_stale_live_snapshot_until_queue():
    from velora.account import Account
    from velora.model import AccountState, GsiSnapshot
    from velora.walkbot import WalkBot

    class Input:
        def release_all(self): pass
        def move(self, forward, back, left, right): pass

    account = Account("a", "A", WalkBot(Input()))
    account.start()
    account.on_gsi(GsiSnapshot(1.0, activity="playing", map_name="de_dust2", map_phase="live", round_phase="live", round_number=1))
    account.on_gsi(GsiSnapshot(2.0, activity="playing", map_name="de_dust2", map_phase="gameover", round_phase="gameover", round_number=30, player_team="CT", team_score=16, opponent_score=12))
    assert account.fsm.state == AccountState.MENU
    account.on_gsi(GsiSnapshot(3.0, activity="playing", map_name="de_dust2", map_phase="live", round_phase="live", round_number=30))
    assert account.fsm.state == AccountState.MENU
    account.on_gsi(GsiSnapshot(4.0, activity="queue"))
    assert account.fsm.state == AccountState.QUEUING
    account.on_gsi(GsiSnapshot(5.0, activity="playing", map_name="de_dust2", map_phase="live", round_phase="live", round_number=1))
    assert account.fsm.state == AccountState.IN_MATCH


def test_new_match_does_not_reuse_previous_result_or_score():
    from velora.account import Account
    from velora.model import GsiSnapshot
    from velora.orchestrator import BatchRuntime, FarmOrchestrator
    from velora.walkbot import WalkBot

    class Input:
        def release_all(self): pass
        def move(self, forward, back, left, right): pass

    account = Account("a", "A", WalkBot(Input()))
    account.start()
    account.on_gsi(GsiSnapshot(1.0, activity="playing", map_name="de_dust2", map_phase="live", round_phase="live", round_number=1))
    account.on_gsi(GsiSnapshot(2.0, activity="playing", map_name="de_dust2", map_phase="gameover", round_phase="gameover", round_number=30, player_team="CT", team_score=16, opponent_score=12))
    assert account.last_match_result is True

    class S:
        def get_account(self, account_id): return account
    orchestrator = FarmOrchestrator(S())
    batch = type("B", (), {"id": "b", "account_ids": ["a"]})()
    runtime = BatchRuntime("b", match_generation={"a": 0})
    account.match_terminal_latched = False
    account.on_gsi(GsiSnapshot(3.0, activity="queue"))
    account.on_gsi(GsiSnapshot(4.0, activity="playing", map_name="de_dust2", map_phase="live", round_phase="live", round_number=1))
    assert orchestrator._capture_match(batch, runtime, 0.0) is True
    assert account.last_match_result is None
    assert account.last_score is None
    assert account.last_opponent_score is None


def test_gsi_freshness_uses_wall_clock():
    from velora.account import Account
    from velora.walkbot import WalkBot
    from time import monotonic

    class Input:
        def release_all(self): pass
        def move(self, forward, back, left, right): pass

    account = Account("a", "A", WalkBot(Input()))
    account.last_gsi = monotonic() - 10
    assert account.gsi_age(now=monotonic()) >= 9.9
    assert account.gsi_stale(5, now=monotonic()) is True
    account.last_gsi = monotonic()
    assert account.gsi_stale(5, now=monotonic()) is False


def test_supervisor_restores_orchestrator_runtime(tmp_path):
    from velora.config import Config
    from velora.supervisor import Supervisor
    from velora.orchestrator import BatchRuntime

    data_dir = str(tmp_path / "velora")
    first = Supervisor(Config(data_dir=data_dir))
    first.orchestrator.runtime["b"] = BatchRuntime("b", retries=2, last_error="recovering")
    first._save_farm()

    second = Supervisor(Config(data_dir=data_dir))
    assert "b" in second.orchestrator.runtime
    assert second.orchestrator.runtime["b"].retries == 2
    assert second.orchestrator.runtime["b"].last_error == "recovering"


def test_menu_transition_marks_active_match_game_over():
    from velora.account import Account
    from velora.model import AccountState, MatchState, GsiSnapshot
    from velora.walkbot import WalkBot

    class Input:
        def release_all(self): pass
        def move(self, forward, back, left, right): pass

    account = Account("a", "A", WalkBot(Input()))
    account.start()
    account.on_gsi(GsiSnapshot(1.0, activity="playing", map_name="de_dust2", map_phase="live", round_phase="live", round_number=1))
    account.on_gsi(GsiSnapshot(2.0, activity="menu", map_name="de_dust2", map_phase="menu", round_number=1))
    assert account.fsm.state == AccountState.MENU
    assert account.match_state() == MatchState.GAME_OVER
