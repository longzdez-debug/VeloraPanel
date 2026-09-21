from .domain import SupervisorState,MatchState,AccountState,GameState
from .fsm import Event
class Supervisor:
    def __init__(self,walkbot):
        self.walkbot=walkbot;self.state=SupervisorState.STOPPED;self.account=AccountState.UNKNOWN;self.match=MatchState.WAITING
    def start(self):self.state=SupervisorState.STARTING;self.walkbot.start();self.state=SupervisorState.RUNNING
    def update(self,game:GameState):
        if self.state not in {SupervisorState.RUNNING,SupervisorState.DEGRADED}:return
        self.walkbot.ctx.game=game
        if not game.connected or not game.in_game:
            self.match=MatchState.WAITING;self.walkbot.fsm.dispatch(Event.GAME_LOST,self.walkbot.ctx)
        elif game.round_phase in {"live","playing"}:
            self.match=MatchState.LIVE
            if self.walkbot.fsm.state.name=="WAITING_FOR_GAME":self.walkbot.fsm.dispatch(Event.GAME_READY,self.walkbot.ctx)
            if game.alive and self.walkbot.fsm.state.name=="WAITING_FOR_SPAWN":self.walkbot.fsm.dispatch(Event.SPAWNED,self.walkbot.ctx)
            self.walkbot.fsm.dispatch(Event.TICK,self.walkbot.ctx)
        self.walkbot.update()
    def stop(self):self.state=SupervisorState.STOPPING;self.walkbot.stop();self.state=SupervisorState.STOPPED
