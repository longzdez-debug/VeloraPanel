from __future__ import annotations
from dataclasses import dataclass
import random

@dataclass(frozen=True)
class BehaviourProfile:
    name: str = "balanced"
    route_preference: float = 0.5
    look_around_probability: float = 0.08
    stop_probability: float = 0.03
    turn_variance: float = 0.08
    seed: int = 0

class BehaviourSampler:
    def __init__(self, profile: BehaviourProfile | None = None):
        self.profile = profile or BehaviourProfile()
        self._random = random.Random(self.profile.seed)

    def bounded_turn_offset(self) -> float:
        return max(-self.profile.turn_variance, min(self.profile.turn_variance, self._random.uniform(-self.profile.turn_variance, self.profile.turn_variance)))

    def should_look_around(self) -> bool:
        return self._random.random() < max(0.0, min(1.0, self.profile.look_around_probability))

    def should_stop(self) -> bool:
        return self._random.random() < max(0.0, min(1.0, self.profile.stop_probability))
