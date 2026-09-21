from __future__ import annotations
from .walkbot import InputAdapter

class NullInput(InputAdapter):
    def __init__(self):
        self.last = (False, False, False, False)

    def release_all(self):
        self.last = (False, False, False, False)

    def move(self, forward, back, left, right):
        self.last = (bool(forward), bool(back), bool(left), bool(right))
