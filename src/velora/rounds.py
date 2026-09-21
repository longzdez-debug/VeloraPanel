from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class RoundState(str, Enum):
    UNKNOWN = "unknown"
    LIVE = "live"
    OVER = "over"
    HALFTIME = "halftime"
    GAME_OVER = "game_over"

@dataclass
class MatchTracker:
    state: RoundState = RoundState.UNKNOWN
    map_name: str | None = None
    round_number: int | None = None
    match_id: int = 0
    rounds_seen: int = 0
    last_counted_round: int | None = None

    def update(self, map_name, phase, round_number=None):
        previous = self.state
        if map_name and self.map_name and map_name != self.map_name:
            self.match_id += 1
            self.round_number = None
        self.map_name = map_name or self.map_name
        if round_number is not None:
            self.round_number = round_number
        p = (phase or "").lower()
        if p in {"live", "playing"}:
            self.state = RoundState.LIVE
        elif p in {"freezetime", "halftime", "intermission"}:
            self.state = RoundState.HALFTIME
        elif p in {"over", "postgame"}:
            self.state = RoundState.OVER
        elif p in {"gameover", "game_over"}:
            self.state = RoundState.GAME_OVER
        elif p in {"warmup"}:
            self.state = RoundState.UNKNOWN

        # A live transition after a terminal/non-live state is a new match
        # even when the map name is unchanged. This gives the orchestrator a
        # stable per-account generation without inventing a provider field.
        if self.state == RoundState.LIVE and previous in {
            RoundState.UNKNOWN, RoundState.GAME_OVER
        }:
            self.match_id += 1
            self.rounds_seen = 0
            self.last_counted_round = None

        if self.round_number is not None and self.round_number != self.last_counted_round:
            self.rounds_seen += 1
            self.last_counted_round = self.round_number
        return self.state

    def reset(self):
        self.state = RoundState.UNKNOWN
        self.map_name = None
        self.round_number = None
        self.match_id += 1
        self.rounds_seen = 0
        self.last_counted_round = None
