from __future__ import annotations
from dataclasses import dataclass, field
import random
from .navigation import NavGraph, NavigationGoal
from .routes import Node, RouteGraph

@dataclass(frozen=True)
class RouteEntry:
    route_id: str
    map_name: str
    nodes: tuple[Node, ...]
    weight: float = 1.0
    tags: frozenset[str] = frozenset()
    entry_conditions: tuple[tuple[str,str], ...] = ()
    exit_conditions: tuple[tuple[str,str], ...] = ()
    recovery_route: str | None = None

@dataclass
class RouteSelectionConfig:
    deterministic: bool = True
    seed: int = 0

class RouteDatabase:
    """Route metadata layer over the existing persistent waypoint graph."""

    def __init__(self, config: RouteSelectionConfig | None = None):
        self.config = config or RouteSelectionConfig()
        self.routes: dict[str, list[RouteEntry]] = {}
        self._random = random.Random(self.config.seed)

    def add(self, route: RouteEntry):
        self.routes.setdefault(route.map_name, []).append(route)

    def candidates(self, map_name: str, tags=()):
        required = set(tags)
        return [r for r in self.routes.get(map_name, ()) if required.issubset(r.tags)]

    def select(self, map_name: str, tags=()) -> RouteEntry | None:
        candidates = self.candidates(map_name, tags)
        if not candidates:
            return None
        if self.config.deterministic:
            return max(candidates, key=lambda r: (r.weight, r.route_id))
        total = sum(max(0.0, r.weight) for r in candidates)
        if total <= 0:
            return candidates[0]
        point = self._random.random() * total
        for route in candidates:
            point -= max(0.0, route.weight)
            if point <= 0:
                return route
        return candidates[-1]

    def fallback(self, route: RouteEntry) -> RouteEntry | None:
        if not route.recovery_route:
            return None
        return next((x for x in self.routes.get(route.map_name, ()) if x.route_id == route.recovery_route), None)
