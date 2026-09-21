from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MatchDirectorState(str, Enum):
    IDLE = "idle"
    PREPARING = "preparing"
    WAITING_FOR_PLAYERS = "waiting_for_players"
    LOBBY_READY = "lobby_ready"
    SEARCHING = "searching"
    MATCH_FOUND = "match_found"
    FARMING = "farming"
    FINISHED = "finished"
    ERROR = "error"


@dataclass
class MatchDirector:
    """Pure orchestration state for a batch.

    It intentionally does not automate Steam/CS2 UI or bypass game protections.
    A future platform-specific lobby adapter can feed these transitions.
    """

    state: MatchDirectorState = MatchDirectorState.IDLE
    expected_players: int = 0
    ready_players: int = 0
    match_id: int | None = None
    error: str | None = None

    def prepare(self, expected_players: int) -> None:
        if expected_players <= 0:
            raise ValueError("expected_players must be positive")
        self.expected_players = expected_players
        self.ready_players = 0
        self.match_id = None
        self.error = None
        self.state = MatchDirectorState.PREPARING

    def player_ready(self) -> None:
        if self.state not in (
            MatchDirectorState.PREPARING,
            MatchDirectorState.WAITING_FOR_PLAYERS,
        ):
            return
        self.state = MatchDirectorState.WAITING_FOR_PLAYERS
        self.ready_players = min(self.expected_players, self.ready_players + 1)
        if self.ready_players >= self.expected_players:
            self.state = MatchDirectorState.LOBBY_READY

    def start_search(self) -> None:
        if self.state != MatchDirectorState.LOBBY_READY:
            raise RuntimeError("lobby is not ready")
        self.state = MatchDirectorState.SEARCHING

    def match_found(self, match_id: int | None = None) -> None:
        if self.state != MatchDirectorState.SEARCHING:
            raise RuntimeError("match search is not active")
        self.match_id = match_id
        self.state = MatchDirectorState.MATCH_FOUND

    def start_farming(self) -> None:
        if self.state != MatchDirectorState.MATCH_FOUND:
            raise RuntimeError("match has not been found")
        self.state = MatchDirectorState.FARMING

    def finish(self) -> None:
        self.state = MatchDirectorState.FINISHED

    def fail(self, message: str) -> None:
        self.error = message
        self.state = MatchDirectorState.ERROR

    def reset(self) -> None:
        self.__init__()
