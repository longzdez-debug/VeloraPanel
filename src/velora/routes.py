from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class Node: id:str;x:float;y:float;z:float=0.0
class RouteGraph:
 def __init__(self):self.nodes={};self.edges={}
 def add(self,node):self.nodes[node.id]=node;self.edges.setdefault(node.id,set())
 def connect(self,a,b):
  if a not in self.nodes or b not in self.nodes:raise KeyError("unknown waypoint")
  self.edges[a].add(b);self.edges[b].add(a)
 def validate(self):
  return [n for n,e in self.edges.items() if not e]
