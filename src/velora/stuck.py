from __future__ import annotations
from dataclasses import dataclass
from math import hypot
from time import monotonic

@dataclass(frozen=True)
class StuckStatus:
    state: str
    no_progress_for: float
    progress_distance: float
    recoveries: int

class StuckDetector:
    def __init__(self, timeout: float = 3.0, min_progress: float = 2.0):
        self.timeout = max(0.1, float(timeout))
        self.min_progress = max(0.0, float(min_progress))
        self._last_position = None
        self._last_progress_at = monotonic()
        self._recoveries = 0

    def update(self, position, now=None) -> StuckStatus:
        now = monotonic() if now is None else now
        progress = 0.0
        if position is not None and self._last_position is not None:
            progress = hypot(position[0] - self._last_position[0], position[1] - self._last_position[1])
            if progress >= self.min_progress:
                self._last_progress_at = now
                self._recoveries = 0
        if position is not None:
            self._last_position = tuple(position)
        age = max(0.0, now - self._last_progress_at)
        state = "stuck" if age >= self.timeout else ("slow" if age >= self.timeout * 0.5 else "moving")
        return StuckStatus(state, age, progress, self._recoveries)

    def mark_recovery(self):
        self._recoveries += 1

    def reset(self):
        self._last_position = None
        self._last_progress_at = monotonic()
        self._recoveries = 0
