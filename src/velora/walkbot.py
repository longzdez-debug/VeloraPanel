from .domain import FsmContext,WalkBotState
from .fsm import StateMachine,Transition,Event
from .input import InputController
from .navigation import Navigator
from .recovery import StuckDetector
class WalkBot:
    def __init__(self,navigator:Navigator,input_controller:InputController,stuck:StuckDetector):
        self.ctx=FsmContext();self.navigator=navigator;self.input=input_controller;self.stuck=stuck;self.fsm=StateMachine(WalkBotState.DISABLED,self._transitions())
    def _transitions(self):
        T=Transition;E=Event
        return [T(WalkBotState.DISABLED,E.START,WalkBotState.INITIALIZING),T(WalkBotState.INITIALIZING,E.GAME_READY,WalkBotState.WAITING_FOR_SPAWN),T(WalkBotState.WAITING_FOR_SPAWN,E.SPAWNED,WalkBotState.CALIBRATING),T(WalkBotState.CALIBRATING,E.TICK,WalkBotState.NAVIGATING),T(WalkBotState.NAVIGATING,E.ARRIVED,WalkBotState.ARRIVING),T(WalkBotState.NAVIGATING,E.STUCK,WalkBotState.STUCK),T(WalkBotState.STUCK,E.RECOVERED,WalkBotState.RECOVERING),T(WalkBotState.RECOVERING,E.REPLAN,WalkBotState.REPLANNING),T(WalkBotState.REPLANNING,E.TICK,WalkBotState.NAVIGATING),T(WalkBotState.ARRIVING,E.TICK,WalkBotState.WAITING),T(WalkBotState.WAITING,E.REPLAN,WalkBotState.REPLANNING),T(WalkBotState.NAVIGATING,E.GAME_LOST,WalkBotState.WAITING_FOR_GAME),T(WalkBotState.WAITING,E.GAME_LOST,WalkBotState.WAITING_FOR_GAME),T(WalkBotState.INITIALIZING,E.STOP,WalkBotState.STOPPING),T(WalkBotState.NAVIGATING,E.STOP,WalkBotState.STOPPING),T(WalkBotState.WAITING,E.STOP,WalkBotState.STOPPING),T(WalkBotState.STOPPING,E.TICK,WalkBotState.DISABLED)]
    def start(self):self.fsm.dispatch(Event.START,self.ctx)
    def update(self):
        if self.ctx.game.position and self.fsm.state==WalkBotState.NAVIGATING:
            self.ctx.intent=self.navigator.intent(self.ctx.game.position,self.ctx.game.view_yaw);self.input.apply(self.ctx.intent)
            if self.stuck.update(self.ctx.game.position):self.fsm.dispatch(Event.STUCK,self.ctx)
        elif self.fsm.state in {WalkBotState.WAITING_FOR_GAME,WalkBotState.DISABLED}:self.input.release_all()
    def stop(self):self.fsm.dispatch(Event.STOP,self.ctx);self.input.release_all()
