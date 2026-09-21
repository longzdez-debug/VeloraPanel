from __future__ import annotations
from dataclasses import dataclass
from math import atan2,degrees
from .domain import Vector3,MovementIntent
@dataclass(frozen=True)
class Waypoint:
    id:str; position:Vector3; radius:float=24.0
class WaypointGraph:
    def __init__(self,waypoints:list[Waypoint],edges:dict[str,list[str]]|None=None):
        self.nodes={w.id:w for w in waypoints}; self.edges=edges or {w.id:[] for w in waypoints}
    def nearest(self,p:Vector3)->Waypoint|None: return min(self.nodes.values(),key=lambda w:w.position.distance(p),default=None)
    def shortest_path(self,start:str,goal:str)->list[str]:
        if start not in self.nodes or goal not in self.nodes:return []
        q=[start]; prev={start:None}
        while q:
            n=q.pop(0)
            if n==goal:break
            for nxt in self.edges.get(n,[]):
                if nxt not in prev:prev[nxt]=n;q.append(nxt)
        if goal not in prev:return []
        out=[]; cur=goal
        while cur is not None:out.append(cur);cur=prev[cur]
        return out[::-1]
class Navigator:
    def __init__(self,graph:WaypointGraph):self.graph=graph;self.path=[];self.index=0
    def plan(self,current:Vector3,goal:Vector3)->bool:
        a=self.graph.nearest(current);b=self.graph.nearest(goal)
        if not a or not b:return False
        self.path=self.graph.shortest_path(a.id,b.id);self.index=0;return bool(self.path)
    def intent(self,current:Vector3,yaw:float)->MovementIntent:
        if not self.path or self.index>=len(self.path):return MovementIntent(brake=True)
        target=self.graph.nodes[self.path[self.index]]
        if current.distance(target.position)<=target.radius:
            self.index+=1
            if self.index>=len(self.path):return MovementIntent(brake=True)
            target=self.graph.nodes[self.path[self.index]]
        desired=degrees(atan2(target.position.y-current.y,target.position.x-current.x))
        return MovementIntent(forward=True,yaw=desired if abs((desired-yaw+180)%360-180)>4 else None)
