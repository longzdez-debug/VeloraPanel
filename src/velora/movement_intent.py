from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class MovementIntent:
    forward: float = 0.0
    strafe: float = 0.0
    turn: float = 0.0
    jump: bool = False
    crouch: bool = False
    stop: bool = False

    def clamped(self) -> "MovementIntent":
        return MovementIntent(
            forward=max(-1.0, min(1.0, self.forward)),
            strafe=max(-1.0, min(1.0, self.strafe)),
            turn=max(-1.0, min(1.0, self.turn)),
            jump=self.jump, crouch=self.crouch, stop=self.stop,
        )
