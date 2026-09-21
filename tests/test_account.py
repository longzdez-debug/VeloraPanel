from velora.account import Account
from velora.input import NullInput
from velora.walkbot import WalkBot
from velora.model import AccountState, GsiSnapshot, MatchState

def make_account():
    return Account("a", "A", WalkBot(NullInput()))

def test_account_waits_for_gsi_before_ready():
    a = make_account()
    a.start()
    assert a.fsm.state == AccountState.STARTING
    a.on_gsi(GsiSnapshot(1, activity="playing", health=100))
    assert a.fsm.state == AccountState.MENU

def test_account_enters_match_only_with_map_context():
    a = make_account()
    a.start()
    a.on_gsi(GsiSnapshot(1, activity="playing", health=100, map_name="de_dust2", round_phase="live"))
    assert a.fsm.state == AccountState.IN_MATCH
    assert a.match_state() == MatchState.LIVE

def test_account_detects_round_end_without_leaving_match():
    a = make_account()
    a.start()
    a.on_gsi(GsiSnapshot(1, activity="playing", health=100, map_name="de_dust2", round_phase="live", round_number=1))
    a.on_gsi(GsiSnapshot(2, activity="playing", health=100, map_name="de_dust2", round_phase="over", round_number=1))
    assert a.fsm.state == AccountState.IN_MATCH
    assert a.match_state() == MatchState.ROUND_OVER
