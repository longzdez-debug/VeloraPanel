from __future__ import annotations
from dataclasses import asdict, dataclass, field
import json
import uuid

@dataclass(frozen=True)
class ReplayEvent:
    timestamp: float
    kind: str
    payload: dict = field(default_factory=dict)
    correlation_id: str = ""

class ReplaySession:
    def __init__(self, session_id: str | None = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.events: list[ReplayEvent] = []

    def record(self, kind: str, timestamp: float, payload: dict | None = None, correlation_id: str | None = None):
        event = ReplayEvent(timestamp, kind, dict(payload or {}), correlation_id or self.session_id)
        self.events.append(event)
        return event

    def to_dict(self):
        return {"session_id": self.session_id, "events": [asdict(x) for x in self.events]}

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.to_dict(), handle, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str):
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        session = cls(str(data["session_id"]))
        session.events = [
            ReplayEvent(float(x["timestamp"]), str(x["kind"]), dict(x.get("payload", {})), str(x.get("correlation_id", "")))
            for x in data.get("events", [])
        ]
        return session

    def iter_events(self):
        return iter(self.events)
