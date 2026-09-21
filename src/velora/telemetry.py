from __future__ import annotations
from dataclasses import asdict, dataclass
from time import monotonic
import uuid

@dataclass(frozen=True)
class WalkBotTelemetry:
    correlation_id: str
    state: str
    current_route: str | None
    current_nav_area: str | None
    target_nav_area: str | None
    position_confidence: float
    vision_confidence: float
    gsi_confidence: float
    path_length: int
    progress: float
    recovery_level: int
    frame_latency: float | None
    decision_latency: float | None
    input_latency: float | None
    timestamp: float

    def to_dict(self):
        return asdict(self)

class TelemetryContext:
    def __init__(self, correlation_id: str | None = None):
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.started_at = monotonic()

    def new_correlation(self):
        self.correlation_id = str(uuid.uuid4())
        self.started_at = monotonic()
        return self.correlation_id
