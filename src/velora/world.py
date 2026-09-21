from __future__ import annotations
from dataclasses import dataclass, field, replace
from threading import RLock
from time import monotonic
from typing import Any, Generic, TypeVar

T = TypeVar("T")

@dataclass(frozen=True)
class ObservationValue(Generic[T]):
    value: T | None
    timestamp: float
    source: str
    confidence: float
    valid: bool = True

    def fresh(self, now: float | None = None, max_age: float = 3.0) -> bool:
        if not self.valid:
            return False
        current = monotonic() if now is None else now
        return current - self.timestamp <= max(0.0, max_age)

@dataclass(frozen=True)
class GameState:
    map_name: ObservationValue[str] = field(default_factory=lambda: ObservationValue(None, 0.0, "unknown", 0.0, False))
    map_phase: ObservationValue[str] = field(default_factory=lambda: ObservationValue(None, 0.0, "unknown", 0.0, False))
    round_phase: ObservationValue[str] = field(default_factory=lambda: ObservationValue(None, 0.0, "unknown", 0.0, False))
    activity: ObservationValue[str] = field(default_factory=lambda: ObservationValue(None, 0.0, "unknown", 0.0, False))
    round_number: ObservationValue[int] = field(default_factory=lambda: ObservationValue(None, 0.0, "unknown", 0.0, False))
    team_score: ObservationValue[int] = field(default_factory=lambda: ObservationValue(None, 0.0, "unknown", 0.0, False))
    opponent_score: ObservationValue[int] = field(default_factory=lambda: ObservationValue(None, 0.0, "unknown", 0.0, False))

@dataclass(frozen=True)
class PlayerState:
    steam_id: ObservationValue[str] = field(default_factory=lambda: ObservationValue(None, 0.0, "unknown", 0.0, False))
    health: ObservationValue[int] = field(default_factory=lambda: ObservationValue(None, 0.0, "unknown", 0.0, False))
    team: ObservationValue[str] = field(default_factory=lambda: ObservationValue(None, 0.0, "unknown", 0.0, False))
    xp: ObservationValue[int] = field(default_factory=lambda: ObservationValue(None, 0.0, "unknown", 0.0, False))
    position: ObservationValue[tuple[float, float, float]] = field(default_factory=lambda: ObservationValue(None, 0.0, "unknown", 0.0, False))

@dataclass(frozen=True)
class OrientationState:
    forward: ObservationValue[tuple[float, float, float]] = field(default_factory=lambda: ObservationValue(None, 0.0, "unknown", 0.0, False))

@dataclass(frozen=True)
class RoundState:
    phase: ObservationValue[str] = field(default_factory=lambda: ObservationValue(None, 0.0, "unknown", 0.0, False))
    number: ObservationValue[int] = field(default_factory=lambda: ObservationValue(None, 0.0, "unknown", 0.0, False))

@dataclass(frozen=True)
class NavigationState:
    current_area: str | None = None
    target_area: str | None = None
    path: tuple[str, ...] = ()
    progress: float = 0.0
    position_confidence: float = 0.0

@dataclass(frozen=True)
class VisionState:
    frame_id: int = 0
    timestamp: float = 0.0
    observation_count: int = 0
    confidence: float = 0.0

@dataclass(frozen=True)
class EvidenceState:
    enemy_heat: dict[str, float] = field(default_factory=dict)
    activity_heat: dict[str, float] = field(default_factory=dict)
    visited_heat: dict[str, float] = field(default_factory=dict)
    danger_heat: dict[str, float] = field(default_factory=dict)
    interest_heat: dict[str, float] = field(default_factory=dict)

@dataclass(frozen=True)
class LocalizationState:
    position: ObservationValue[tuple[float, float, float]] = field(default_factory=lambda: ObservationValue(None, 0.0, "unknown", 0.0, False))
    orientation: ObservationValue[tuple[float, float, float]] = field(default_factory=lambda: ObservationValue(None, 0.0, "unknown", 0.0, False))
    nav_area: str | None = None
    status: str = "unknown"

@dataclass(frozen=True)
class WorldSnapshot:
    game: GameState = field(default_factory=GameState)
    player: PlayerState = field(default_factory=PlayerState)
    orientation: OrientationState = field(default_factory=OrientationState)
    round: RoundState = field(default_factory=RoundState)
    navigation: NavigationState = field(default_factory=NavigationState)
    vision: VisionState = field(default_factory=VisionState)
    localization: LocalizationState = field(default_factory=LocalizationState)
    evidence: EvidenceState = field(default_factory=EvidenceState)
    updated_at: float = 0.0

class WorldModel:
    """Single authoritative state store for WalkBot decision making."""

    def __init__(self):
        self._lock = RLock()
        self._snapshot = WorldSnapshot(updated_at=monotonic())

    def snapshot(self) -> WorldSnapshot:
        with self._lock:
            return self._snapshot

    def update(self, **changes: Any) -> WorldSnapshot:
        with self._lock:
            self._snapshot = replace(self._snapshot, **changes, updated_at=monotonic())
            return self._snapshot

    def update_player(self, **changes: Any) -> WorldSnapshot:
        with self._lock:
            self._snapshot = replace(self._snapshot, player=replace(self._snapshot.player, **changes), updated_at=monotonic())
            return self._snapshot

    def update_game(self, **changes: Any) -> WorldSnapshot:
        with self._lock:
            self._snapshot = replace(self._snapshot, game=replace(self._snapshot.game, **changes), updated_at=monotonic())
            return self._snapshot

    def update_orientation(self, **changes: Any) -> WorldSnapshot:
        with self._lock:
            self._snapshot = replace(self._snapshot, orientation=replace(self._snapshot.orientation, **changes), updated_at=monotonic())
            return self._snapshot

    def update_localization(self, **changes: Any) -> WorldSnapshot:
        with self._lock:
            self._snapshot = replace(self._snapshot, localization=replace(self._snapshot.localization, **changes), updated_at=monotonic())
            return self._snapshot

    def update_navigation(self, **changes: Any) -> WorldSnapshot:
        with self._lock:
            self._snapshot = replace(self._snapshot, navigation=replace(self._snapshot.navigation, **changes), updated_at=monotonic())
            return self._snapshot
