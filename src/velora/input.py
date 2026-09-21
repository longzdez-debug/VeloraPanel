from __future__ import annotations

from .external_input import ExternalInput


class NullInput(ExternalInput):
    """Safe no-op input adapter used by tests and headless runs."""

    def __init__(self):
        self.last = (False, False, False, False)
        self.attacking = False

    def release_all(self):
        self.last = (False, False, False, False)
        self.attacking = False

    def move(self, forward, back, left, right):
        self.last = (bool(forward), bool(back), bool(left), bool(right))

    def turn(self, amount):
        return None

    def attack(self, down: bool):
        self.attacking = bool(down)

    def click_normalized(self, x: float, y: float) -> bool:
        return False

    def console_command(self, command: str) -> bool:
        return False
