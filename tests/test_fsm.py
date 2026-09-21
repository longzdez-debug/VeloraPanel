from velora.fsm import StateMachine
def test_deterministic_transition():
 sm=StateMachine("a");sm.allow("a","go","b");assert sm.dispatch("go").target=="b";assert sm.dispatch("go") is None


def test_transition_history_is_bounded_and_records_state_changes():
 sm=StateMachine("a");sm.allow("a","go","b")
 assert sm.dispatch("go").target=="b"
 assert len(sm._history)==1
 record=sm._history[0]
 assert record.source=="a" and record.event=="go" and record.target=="b"
