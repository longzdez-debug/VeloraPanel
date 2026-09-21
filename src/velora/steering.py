from __future__ import annotations
from dataclasses import dataclass
from math import atan2, degrees, hypot
from .movement_intent import MovementIntent

@dataclass(frozen=True)
class SteeringConfig:
    turn_dead_zone: float = 8.0
    full_turn_angle: float = 90.0
    forward_angle: float = 65.0

class Steering:
    def __init__(self, config: SteeringConfig | None = None):
        self.config = config or SteeringConfig()

    @staticmethod
    def _angle(x, y):
        return degrees(atan2(y, x))

    @staticmethod
    def _normalize(angle):
        return (angle + 180.0) % 360.0 - 180.0

    def steer(self, position, forward, target) -> MovementIntent:
        dx, dy = target[0] - position[0], target[1] - position[1]
        distance = hypot(dx, dy)
        if distance <= 0.001:
            return MovementIntent(stop=True)
        desired = self._angle(dx, dy)
        heading = self._angle(forward[0], forward[1])
        error = self._normalize(desired - heading)
        turn = 0.0 if abs(error) <= self.config.turn_dead_zone else max(-1.0, min(1.0, error / self.config.full_turn_angle))
        forward_amount = 1.0 if abs(error) <= self.config.forward_angle else 0.25
        strafe = max(-1.0, min(1.0, error / 90.0))
        return MovementIntent(forward=forward_amount, strafe=strafe, turn=turn).clamped()
