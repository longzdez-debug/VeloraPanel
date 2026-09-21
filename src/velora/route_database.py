from __future__ import annotations
from dataclasses import dataclass
import random
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
        bucket = self.routes.setdefault(route.map_name, [])
        bucket[:] = [item for item in bucket if item.route_id != route.route_id]
        bucket.append(route)

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

    def import_graph(self, map_name: str, graph: RouteGraph, route_id: str = "default", weight: float = 1.0, tags=()) -> RouteEntry:
        """Bridge the persisted RouteGraph into the richer route metadata layer."""
        entry = RouteEntry(
            route_id=str(route_id),
            map_name=str(map_name),
            nodes=tuple(graph.nodes.values()),
            weight=float(weight),
            tags=frozenset(str(x) for x in tags),
        )
        self.routes.setdefault(entry.map_name, [])
        self.routes[entry.map_name] = [x for x in self.routes[entry.map_name] if x.route_id != entry.route_id]
        self.routes[entry.map_name].append(entry)
        return entry

    def import_store(self, store, map_name: str, route_id: str = "default", weight: float = 1.0, tags=()):
        """Load one persisted waypoint graph into the route metadata layer."""
        graph = store.get(map_name)
        return self.import_graph(map_name, graph, route_id=route_id, weight=weight, tags=tags)

    def fallback(self, route: RouteEntry) -> RouteEntry | None:
        if not route.recovery_route:
            return None
        return next((x for x in self.routes.get(route.map_name, ()) if x.route_id == route.recovery_route), None)
