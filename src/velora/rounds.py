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

    def update(self, map_name, phase, round_number=None):
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
        return self.state

    def reset(self):
        self.state = RoundState.UNKNOWN
        self.map_name = None
        self.round_number = None
        self.match_id += 1
