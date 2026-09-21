from velora.domain import WalkBotState,FsmContext
from velora.fsm import StateMachine,Transition,Event
def test_fsm_transition_and_history():
    m=StateMachine(WalkBotState.DISABLED,[Transition(WalkBotState.DISABLED,Event.START,WalkBotState.INITIALIZING)])
    assert m.dispatch(Event.START,FsmContext());assert m.state==WalkBotState.INITIALIZING;assert m.history[-1][0]==WalkBotState.DISABLED
def test_invalid_transition_is_noop():
    m=StateMachine(WalkBotState.DISABLED,[]);assert not m.dispatch(Event.STOP);assert m.state==WalkBotState.DISABLED
