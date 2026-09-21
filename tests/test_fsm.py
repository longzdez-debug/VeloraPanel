from velora.fsm import StateMachine
def test_deterministic_transition():
 sm=StateMachine("a");sm.allow("a","go","b");assert sm.dispatch("go").target=="b";assert sm.dispatch("go") is None
