from __future__ import annotations
from dataclasses import dataclass
from math import exp

@dataclass(frozen=True)
class HeatmapConfig:
    half_life: float = 20.0
    max_value: float = 1.0

class Heatmap:
    def __init__(self, config: HeatmapConfig | None = None):
        self.config = config or HeatmapConfig()
        self._values: dict[str, tuple[float, float]] = {}

    def add(self, area: str, amount: float, now: float):
        current = self.value(area, now)
        self._values[area] = (min(self.config.max_value, max(0.0, current + amount)), now)

    def value(self, area: str, now: float) -> float:
        item = self._values.get(area)
        if item is None:
            return 0.0
        value, timestamp = item
        half_life = max(0.001, self.config.half_life)
        decayed = value * exp(-0.69314718056 * max(0.0, now - timestamp) / half_life)
        if decayed < 1e-6:
            self._values.pop(area, None)
            return 0.0
        return decayed

    def snapshot(self, now: float) -> dict[str, float]:
        return {area: self.value(area, now) for area in tuple(self._values)}

class EvidenceMap:
    def __init__(self, config: HeatmapConfig | None = None):
        self.enemy = Heatmap(config)
        self.activity = Heatmap(config)
        self.visited = Heatmap(config)
        self.danger = Heatmap(config)
        self.interest = Heatmap(config)
