from __future__ import annotations

from dataclasses import dataclass
from math import atan2, degrees, hypot, sqrt
from typing import Iterable


Vec3 = tuple[float, float, float]


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _distance(a: Vec3, b: Vec3) -> float:
    d = _sub(a, b)
    return sqrt(d[0] * d[0] + d[1] * d[1] + d[2] * d[2])


def _angle_delta(target: float, current: float) -> float:
    return (target - current + 180.0) % 360.0 - 180.0


@dataclass(frozen=True)
class AimTarget:
    track_id: str
    position: Vec3
    confidence: float = 1.0
    velocity: Vec3 = (0.0, 0.0, 0.0)
    visible: bool = True
    locked: bool = False


@dataclass(frozen=True)
class AimConfig:
    max_fov_deg: float = 18.0
    min_confidence: float = 0.70
    prediction_seconds: float = 0.055
    smoothing: float = 0.32
    lock_bonus: float = 0.18


@dataclass(frozen=True)
class AimSolution:
    track_id: str
    aim_position: Vec3
    yaw: float
    pitch: float
    yaw_delta: float
    pitch_delta: float
    angular_error: float
    distance: float
    confidence: float
    predicted: bool


class AimSolver:
    """Pure aim geometry.

    This module only calculates a target and the desired angular correction.
    It deliberately has no OS/game input dependency.
    """

    def __init__(self, config: AimConfig | None = None):
        self.cfg = config or AimConfig()

    def select(
        self,
        origin: Vec3,
        view_angles: tuple[float, float],
        targets: Iterable[AimTarget],
    ) -> AimTarget | None:
        current_yaw, current_pitch = view_angles
        candidates: list[tuple[float, AimTarget]] = []
        for target in targets:
            confidence = max(0.0, min(1.0, target.confidence))
            if not target.visible or confidence < self.cfg.min_confidence:
                continue
            d = _sub(target.position, origin)
            horizontal = hypot(d[0], d[1])
            if horizontal < 1e-6 and abs(d[2]) < 1e-6:
                continue
            yaw = degrees(atan2(d[1], d[0]))
            pitch = degrees(atan2(d[2], max(horizontal, 1e-6)))
            yd = _angle_delta(yaw, current_yaw)
            pd = _angle_delta(pitch, current_pitch)
            error = hypot(yd, pd)
            if error > self.cfg.max_fov_deg:
                continue
            score = error / self.cfg.max_fov_deg
            score -= confidence * 0.35
            if target.locked:
                score -= self.cfg.lock_bonus
            candidates.append((score, target))
        if not candidates:
            return None
        candidates.sort(key=lambda item: (item[0], item[1].track_id))
        return candidates[0][1]

    def solve(
        self,
        origin: Vec3,
        view_angles: tuple[float, float],
        target: AimTarget,
        dt: float | None = None,
    ) -> AimSolution:
        prediction = self.cfg.prediction_seconds if dt is None else max(0.0, dt)
        p = (
            target.position[0] + target.velocity[0] * prediction,
            target.position[1] + target.velocity[1] * prediction,
            target.position[2] + target.velocity[2] * prediction,
        )
        d = _sub(p, origin)
        horizontal = hypot(d[0], d[1])
        yaw = degrees(atan2(d[1], d[0]))
        pitch = degrees(atan2(d[2], max(horizontal, 1e-6)))
        yd = _angle_delta(yaw, view_angles[0])
        pd = _angle_delta(pitch, view_angles[1])
        s = max(0.0, min(1.0, self.cfg.smoothing))
        return AimSolution(
            track_id=target.track_id,
            aim_position=p,
            yaw=yaw,
            pitch=pitch,
            yaw_delta=yd * s,
            pitch_delta=pd * s,
            angular_error=hypot(yd, pd),
            distance=_distance(origin, p),
            confidence=max(0.0, min(1.0, target.confidence)),
            predicted=prediction > 0.0 and any(abs(v) > 1e-9 for v in target.velocity),
        )
