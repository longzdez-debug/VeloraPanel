from velora.account import Account
from velora.input import NullInput
from velora.walkbot import WalkBot
from velora.model import AccountState,GsiSnapshot

def test_account_waits_for_gsi_before_ready():
 a=Account("a","A",WalkBot(NullInput()))
 a.start()
 assert a.fsm.state==AccountState.STARTING
 a.on_gsi(GsiSnapshot(1,activity="playing",health=100))
 assert a.fsm.state==AccountState.IN_MATCH
