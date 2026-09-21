from __future__ import annotations
from dataclasses import dataclass
from math import hypot
import heapq
@dataclass(frozen=True)
class Node:id:str;x:float;y:float;z:float=0.0
class RouteGraph:
 def __init__(self):self.nodes={};self.edges={}
 def add(self,node):self.nodes[node.id]=node;self.edges.setdefault(node.id,set())
 def connect(self,a,b):
  if a not in self.nodes or b not in self.nodes:raise KeyError("unknown waypoint")
  if a==b:raise ValueError("self edge")
  self.edges[a].add(b);self.edges[b].add(a)
 def validate(self):
  return [n for n,e in self.edges.items() if not e]
 def shortest_path(self,start,goal):
  if start not in self.nodes or goal not in self.nodes:raise KeyError("unknown waypoint")
  q=[(0,start)];dist={start:0};prev={}
  while q:
   d,u=heapq.heappop(q)
   if d!=dist[u]:continue
   if u==goal:break
   for v in self.edges[u]:
    w=hypot(self.nodes[u].x-self.nodes[v].x,self.nodes[u].y-self.nodes[v].y)
    nd=d+w
    if nd<dist.get(v,float("inf")):dist[v]=nd;prev[v]=u;heapq.heappush(q,(nd,v))
  if goal not in dist:return []
  out=[];u=goal
  while True:
   out.append(self.nodes[u])
   if u==start:break
   u=prev[u]
  return list(reversed(out))
