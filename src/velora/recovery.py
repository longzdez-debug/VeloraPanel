from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class RecoveryPolicy:
    micro_timeout: float = 0.35
    steering_timeout: float = 0.75
    replan_timeout: float = 2.0
    route_switch_timeout: float = 4.0
    relocalize_timeout: float = 5.0
    reset_timeout: float = 8.0

@dataclass(frozen=True)
class RecoveryAction:
    level: int
    name: str
    timeout: float

class RecoveryEngine:
    def __init__(self, policy: RecoveryPolicy | None = None):
        self.policy = policy or RecoveryPolicy()
        self.level = 0
        self.active = False
        self.started_at = 0.0

    def start(self, level: int, now: float):
        self.level = max(0, min(6, int(level)))
        self.active = True
        self.started_at = now

    def finish(self):
        self.active = False

    def action(self) -> RecoveryAction:
        return {
            0: RecoveryAction(0, "micro_correction", self.policy.micro_timeout),
            1: RecoveryAction(1, "steering_correction", self.policy.steering_timeout),
            2: RecoveryAction(2, "local_replan", self.policy.replan_timeout),
            3: RecoveryAction(3, "route_switch", self.policy.route_switch_timeout),
            4: RecoveryAction(4, "relocalize", self.policy.relocalize_timeout),
            5: RecoveryAction(5, "navigation_reset", self.policy.reset_timeout),
            6: RecoveryAction(6, "gameplay_recovery", self.policy.reset_timeout),
        }[self.level]

    def timed_out(self, now: float) -> bool:
        return self.active and now - self.started_at >= self.action().timeout
