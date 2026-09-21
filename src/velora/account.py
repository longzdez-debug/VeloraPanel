from __future__ import annotations
from dataclasses import dataclass, field
from .fsm import StateMachine
from .model import AccountState, GsiSnapshot, MatchState
from .rounds import MatchTracker, RoundState

@dataclass
class Account:
    id: str
    name: str
    walkbot: object
    steam_id: str | None = None
    enabled: bool = True
    process_id: int | None = None
    executable: str = ""
    launch_args: list[str] = field(default_factory=list)
    last_gsi: float | None = None
    errors: list[str] = field(default_factory=list)
    route_map: str | None = None
    route_start: str | None = None
    route_goal: str | None = None
    restart_count: int = 0
    next_restart_at: float = 0.0
    started_at: float | None = None
    last_xp: int | None = None
    last_match_result: bool | None = None
    last_score: int | None = None
    last_opponent_score: int | None = None
    match_rounds: int = 0

    def __post_init__(self):
        self.fsm = StateMachine(AccountState.OFFLINE)
        self.match = MatchTracker()
        s = AccountState
        for a, e, b in [
            (s.OFFLINE, "start", s.STARTING),
            (s.STARTING, "ready", s.MENU),
            (s.MENU, "queue", s.QUEUING),
            (s.QUEUING, "warmup", s.QUEUING),
            (s.QUEUING, "match", s.IN_MATCH),
            (s.IN_MATCH, "round_end", s.IN_MATCH),
            (s.IN_MATCH, "game_over", s.MENU),
            (s.IN_MATCH, "stop", s.STOPPING),
            (s.MENU, "stop", s.STOPPING),
            (s.QUEUING, "stop", s.STOPPING),
            (s.STARTING, "stop", s.STOPPING),
            (s.ERROR, "reset", s.OFFLINE),
            (s.STOPPING, "reset", s.OFFLINE),
        ]:
            self.fsm.allow(a, e, b)
        for a in (s.STARTING, s.MENU, s.QUEUING, s.IN_MATCH):
            self.fsm.allow(a, "error", s.ERROR)

    def start(self):
        if not self.enabled:
            return
        if self.fsm.state == AccountState.ERROR:
            self.fsm.dispatch("reset")
        if self.fsm.state == AccountState.OFFLINE:
            self.fsm.dispatch("start")
        self.walkbot.start()

    def on_ready(self):
        if self.fsm.state == AccountState.STARTING:
            self.fsm.dispatch("ready")
            # A successful GSI handshake means the current restart streak is over.
            self.restart_count = 0
            self.next_restart_at = 0.0

    def _is_menu(self, snap: GsiSnapshot) -> bool:
        activity = (snap.activity or "").lower()
        map_phase = (snap.map_phase or "").lower()
        round_phase = (snap.round_phase or "").lower()
        return activity in {"menu", "mainmenu"} or map_phase in {"menu", "mainmenu"}

    def _is_queue(self, snap: GsiSnapshot) -> bool:
        activity = (snap.activity or "").lower()
        phase = f"{snap.map_phase or ''} {snap.round_phase or ''}".lower()
        return activity in {"queue", "queued", "matchmaking"} or "matchmaking" in phase or "queued" in phase

    def _is_live(self, snap: GsiSnapshot) -> bool:
        activity = (snap.activity or "").lower()
        phase = (snap.map_phase or "").lower()
        return activity in {"playing", "live"} and bool(snap.map_name or snap.round_phase) and phase not in {"menu", "mainmenu", "loading", "gameover", "game_over", "postgame"}

    def on_gsi(self, snap: GsiSnapshot):
        if self.steam_id and snap.steam_id and snap.steam_id != self.steam_id:
            return
        self.last_gsi = snap.received_at
        if snap.xp is not None:
            self.last_xp = snap.xp
        map_phase = (snap.map_phase or "").lower()
        round_phase = (snap.round_phase or "").lower()
        terminal_phases = {"gameover", "game_over", "postgame"}
        phase = map_phase or round_phase
        if map_phase not in terminal_phases and round_phase in terminal_phases:
            phase = round_phase
        if phase in terminal_phases and snap.team_score is not None and snap.opponent_score is not None and snap.team_score != snap.opponent_score:
            self.last_score = snap.team_score
            self.last_opponent_score = snap.opponent_score
            self.last_match_result = snap.team_score > snap.opponent_score
        self.on_ready()
        previous = self.match.state
        match_phase = map_phase or round_phase
        if map_phase not in terminal_phases and round_phase in terminal_phases:
            match_phase = round_phase
        self.match.update(snap.map_name, match_phase, snap.round_number)
        self.match_rounds = self.match.rounds_seen

        if self.match.state == RoundState.GAME_OVER and self.fsm.state == AccountState.IN_MATCH:
            self.fsm.dispatch("game_over")
            self.walkbot.input.release_all()

        if self._is_queue(snap) and self.fsm.state == AccountState.MENU:
            self.fsm.dispatch("queue")
        elif self._is_live(snap):
            if self.fsm.state == AccountState.MENU:
                self.fsm.dispatch("queue")
            if self.fsm.state == AccountState.QUEUING:
                self.fsm.dispatch("match")
        elif self._is_menu(snap) and self.fsm.state == AccountState.IN_MATCH:
            self.fsm.dispatch("game_over")
            self.walkbot.input.release_all()
        elif previous == RoundState.LIVE and self.match.state == RoundState.OVER:
            if self.fsm.state == AccountState.IN_MATCH:
                self.fsm.dispatch("round_end")

        self.walkbot.on_gsi(snap)

    def gsi_age(self, now=None) -> float | None:
        if self.last_gsi is None: return None
        from time import monotonic
        return max(0.0, (monotonic() if now is None else now) - self.last_gsi)

    def gsi_stale(self, timeout: float, now=None) -> bool:
        age = self.gsi_age(now)
        return age is None or age > timeout

    @property
    def match_identity(self):
        return (self.match.match_id, self.match.map_name, self.match.round_number)

    def match_state(self) -> MatchState:
        return {
            RoundState.UNKNOWN: MatchState.UNKNOWN,
            RoundState.LIVE: MatchState.LIVE,
            RoundState.HALFTIME: MatchState.WAITING,
            RoundState.OVER: MatchState.ROUND_OVER,
            RoundState.GAME_OVER: MatchState.GAME_OVER,
        }[self.match.state]

    def stop(self):
        self.walkbot.stop()
        self.restart_count = 0
        self.next_restart_at = 0.0
        if self.fsm.state not in (AccountState.OFFLINE, AccountState.STOPPING):
            self.fsm.dispatch("stop")
        if self.fsm.state == AccountState.STOPPING:
            self.fsm.dispatch("reset")
