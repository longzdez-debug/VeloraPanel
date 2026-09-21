from __future__ import annotations
from dataclasses import dataclass
from .model import GsiSnapshot
from .world import (
    GameState, ObservationValue, OrientationState, PlayerState, RoundState, WorldModel
)

@dataclass(frozen=True)
class NormalizedGsi:
    received_at: float
    game: GameState
    player: PlayerState
    orientation: OrientationState
    round: RoundState

class GsiNormalizer:
    """Converts source-specific GSI snapshots into WorldModel state."""

    source = "gsi"

    @staticmethod
    def _value(value, timestamp, confidence=1.0):
        return ObservationValue(value, timestamp, GsiNormalizer.source, confidence, value is not None)

    def normalize(self, snap: GsiSnapshot) -> NormalizedGsi:
        ts = snap.received_at
        position_confidence = 0.95 if snap.position is not None else 0.0
        forward_confidence = 0.95 if snap.forward is not None else 0.0
        game = GameState(
            map_name=self._value(snap.map_name, ts),
            map_phase=self._value(snap.map_phase, ts),
            round_phase=self._value(snap.round_phase, ts),
            activity=self._value(snap.activity, ts),
            round_number=self._value(snap.round_number, ts),
            team_score=self._value(snap.team_score, ts),
            opponent_score=self._value(snap.opponent_score, ts),
        )
        player = PlayerState(
            steam_id=self._value(snap.steam_id, ts),
            health=self._value(snap.health, ts),
            team=self._value(snap.player_team, ts),
            xp=self._value(snap.xp, ts),
            position=self._value(snap.position, ts, position_confidence),
        )
        orientation = OrientationState(
            forward=self._value(snap.forward, ts, forward_confidence)
        )
        round_state = RoundState(
            phase=self._value(snap.round_phase, ts),
            number=self._value(snap.round_number, ts),
        )
        return NormalizedGsi(ts, game, player, orientation, round_state)

    def publish(self, snap: GsiSnapshot, world: WorldModel) -> NormalizedGsi:
        normalized = self.normalize(snap)
        world.update(
            game=normalized.game,
            player=normalized.player,
            orientation=normalized.orientation,
            round=normalized.round,
        )
        world.update_localization(
            position=normalized.player.position,
            orientation=normalized.orientation.forward,
            status="localized" if normalized.player.position.valid else "unknown",
        )
        return normalized
