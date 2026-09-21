from __future__ import annotations

from dataclasses import dataclass
from .replay import ReplaySession


@dataclass(frozen=True)
class ReplayRunResult:
    session_id: str
    event_count: int
    kinds: dict[str, int]


class ReplayRunner:
    """Offline replay utility; never emits external input."""

    def run(self, session: ReplaySession) -> ReplayRunResult:
        summary = session.summary()
        return ReplayRunResult(
            session_id=summary["session_id"],
            event_count=summary["event_count"],
            kinds=dict(summary["kinds"]),
        )
