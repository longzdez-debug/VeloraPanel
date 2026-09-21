from __future__ import annotations

import time
from typing import Protocol


class MatchmakingAdapter(Protocol):
    def start(self, mode: str = "deathmatch") -> bool: ...
    def stop(self) -> None: ...


class NullMatchmaking:
    def start(self, mode: str = "deathmatch") -> bool:
        return False

    def stop(self) -> None:
        return None


class WindowsMatchmaking:
    """Foreground-only CS2 menu automation.

    This deliberately uses normal OS mouse input and never touches CS2 memory,
    DLLs, or anti-cheat interfaces. Coordinates are normalized to the current
    CS2 client area so window size changes do not require hard-coded pixels.
    """

    MODE_ALIASES = {
        "deathmatch": "deathmatch",
        "arms_race": "arms_race",
        "competitive": "competitive",
        "2v2": "wingman",
        "2v2_random": "wingman",
        "5v5": "competitive",
        "5v5_shuffle": "competitive",
        "casual": "casual",
    }

    def __init__(self, input_adapter, play_x: float = 0.50, play_y: float = 0.075,
                 go_x: float = 0.91, go_y: float = 0.91, settle: float = 1.0):
        self.input = input_adapter
        self.play_x = float(play_x)
        self.play_y = float(play_y)
        self.go_x = float(go_x)
        self.go_y = float(go_y)
        self.settle = max(0.25, float(settle))
        self._last_start = 0.0

    def start(self, mode: str = "deathmatch") -> bool:
        now = time.monotonic()
        if now - self._last_start < 5.0:
            return False
        normalized = self.MODE_ALIASES.get(str(mode).lower(), "deathmatch")
        click = getattr(self.input, "click_normalized", None)
        if not callable(click):
            return False
        # Current CS2 exposes official matchmaking mode preferences through
        # ui_playsettings_mode_official_v20. We use the existing preference for
        # deathmatch and keep non-DM modes conservative rather than guessing
        # their tab coordinates.
        if normalized != "deathmatch":
            command = getattr(self.input, "console_command", None)
            if not callable(command):
                return False
            if not command(f"ui_playsettings_mode_official_v20 {normalized}"):
                return False
            time.sleep(0.25)
        if not click(self.play_x, self.play_y):
            return False
        time.sleep(self.settle)
        if not click(self.go_x, self.go_y):
            return False
        self._last_start = now
        return True

    def stop(self) -> None:
        return None
