from __future__ import annotations
from dataclasses import dataclass
from .movement_intent import MovementIntent

@dataclass(frozen=True)
class MovementOutput:
    forward: bool
    back: bool
    left: bool
    right: bool

class MovementController:
    """Last domain boundary before the existing external InputAdapter."""

    def __init__(self, input_adapter):
        self.input = input_adapter

    @staticmethod
    def translate(intent: MovementIntent) -> MovementOutput:
        value = intent.clamped()
        if value.stop:
            return MovementOutput(False, False, False, False)
        return MovementOutput(
            forward=value.forward > 0.2,
            back=value.forward < -0.2,
            left=value.strafe < -0.2,
            right=value.strafe > 0.2,
        )

    def apply(self, intent: MovementIntent) -> MovementOutput:
        output = self.translate(intent)
        self.input.move(output.forward, output.back, output.left, output.right)
        return output

    def stop(self):
        self.input.release_all()
