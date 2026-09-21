from __future__ import annotations
from dataclasses import dataclass
from .navigation import NavigationGoal
from .world import WorldSnapshot

@dataclass(frozen=True)
class Decision:
    action: str
    goal: NavigationGoal | None
    reason: str
    confidence: float

class DecisionEngine:
    """Chooses what navigation should do; never emits keyboard input."""

    def decide(self, world: WorldSnapshot, goal: NavigationGoal | None = None) -> Decision:
        loc = world.localization
        health = world.player.health.value
        if health is not None and health <= 0:
            return Decision("wait", None, "player_not_alive", 1.0)
        if loc.status == "unknown" or not loc.position.valid:
            return Decision("relocalize", None, "localization_unavailable", 1.0 - loc.position.confidence)
        if goal is not None:
            return Decision("move_to_target", goal, goal.reason or "explicit_goal", loc.position.confidence)
        return Decision("hold", None, "no_navigation_goal", 1.0)
