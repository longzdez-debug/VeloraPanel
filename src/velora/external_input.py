from __future__ import annotations

from typing import Protocol


class ExternalInput(Protocol):
    """Explicit external-input boundary for OS-level input adapters."""

    def release_all(self) -> None: ...
    def move(self, forward: bool, back: bool, left: bool, right: bool) -> None: ...
