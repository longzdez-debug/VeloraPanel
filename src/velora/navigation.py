from __future__ import annotations
from dataclasses import dataclass
from heapq import heappush, heappop
from math import hypot

@dataclass(frozen=True)
class NavArea:
    id: str
    center: tuple[float, float, float]
    bounds: tuple[float, float, float, float] | None = None
    flags: frozenset[str] = frozenset()
    metadata: tuple[tuple[str, str], ...] = ()

@dataclass(frozen=True)
class NavEdge:
    source: str
    target: str
    distance: float
    flags: frozenset[str] = frozenset()

class NavGraph:
    def __init__(self):
        self.areas: dict[str, NavArea] = {}
        self.edges: dict[str, list[NavEdge]] = {}

    def add_area(self, area: NavArea):
        self.areas[area.id] = area
        self.edges.setdefault(area.id, [])

    def connect(self, source: str, target: str, *, bidirectional: bool = True, flags=()):
        if source not in self.areas or target not in self.areas:
            raise KeyError("unknown nav area")
        a, b = self.areas[source], self.areas[target]
        d = hypot(a.center[0] - b.center[0], a.center[1] - b.center[1])
        self.edges[source].append(NavEdge(source, target, d, frozenset(flags)))
        if bidirectional:
            self.edges[target].append(NavEdge(target, source, d, frozenset(flags)))

    def nearest(self, position, max_distance: float | None = None) -> NavArea | None:
        if not self.areas:
            return None
        p = (float(position[0]), float(position[1]), float(position[2]) if len(position) > 2 else 0.0)
        area = min(self.areas.values(), key=lambda x: hypot(x.center[0] - p[0], x.center[1] - p[1]))
        d = hypot(area.center[0] - p[0], area.center[1] - p[1])
        return None if max_distance is not None and d > max_distance else area

    def astar(self, start: str, goal: str, cost=None) -> list[str]:
        if start not in self.areas or goal not in self.areas:
            return []
        cost = cost or (lambda edge: edge.distance)
        open_set = [(0.0, 0.0, start)]
        g = {start: 0.0}
        previous: dict[str, str] = {}
        while open_set:
            _, current_g, current = heappop(open_set)
            if current_g != g.get(current):
                continue
            if current == goal:
                break
            for edge in self.edges.get(current, ()):
                tentative = current_g + float(cost(edge))
                if tentative < g.get(edge.target, float("inf")):
                    g[edge.target] = tentative
                    previous[edge.target] = current
                    goal_area = self.areas[goal]
                    h = hypot(goal_area.center[0] - self.areas[edge.target].center[0], goal_area.center[1] - self.areas[edge.target].center[1])
                    heappush(open_set, (tentative + h, tentative, edge.target))
        if goal not in g:
            return []
        path = [goal]
        while path[-1] != start:
            path.append(previous[path[-1]])
        path.reverse()
        return path

@dataclass(frozen=True)
class NavigationGoal:
    kind: str
    target_area: str | None = None
    target_position: tuple[float, float, float] | None = None
    reason: str = ""
