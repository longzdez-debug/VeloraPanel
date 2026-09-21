from __future__ import annotations
from dataclasses import dataclass
from math import sqrt

@dataclass(frozen=True)
class PositionEstimate:
    position: tuple[float,float,float]
    confidence: float
    source: str
    timestamp: float

class LocalizationEngine:
    """Confidence-weighted fusion of externally observed position estimates."""

    def fuse(self, estimates: list[PositionEstimate]) -> PositionEstimate | None:
        valid = [x for x in estimates if x.confidence > 0.0 and len(x.position) == 3]
        if not valid:
            return None
        total = sum(max(0.0, x.confidence) for x in valid)
        if total <= 0:
            return None
        position = tuple(sum(x.position[i] * x.confidence for x in valid) / total for i in range(3))
        spread = sqrt(sum(
            sum(((x.position[i] - position[i]) ** 2) for i in range(3)) * x.confidence
            for x in valid
        ) / total)
        agreement = 1.0 / (1.0 + spread / 100.0)
        confidence = min(1.0, (total / len(valid)) * agreement)
        source = "+".join(x.source for x in valid)
        timestamp = max(x.timestamp for x in valid)
        return PositionEstimate(position, confidence, source, timestamp)
