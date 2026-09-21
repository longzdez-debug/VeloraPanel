from __future__ import annotations
from dataclasses import asdict,dataclass
from math import hypot
import heapq
@dataclass(frozen=True)
class Node:
 id:str;x:float;y:float;z:float=0.0
@dataclass
class RouteGraph:
 nodes:dict[str,Node]=None
 edges:dict[str,set[str]]=None
 def __post_init__(self):self.nodes=self.nodes or {};self.edges=self.edges or {}
 def add(self,node):self.nodes[node.id]=node;self.edges.setdefault(node.id,set())
 def remove(self,node_id):
  self.nodes.pop(node_id,None);self.edges.pop(node_id,None)
  for e in self.edges.values():e.discard(node_id)
 def connect(self,a,b):
  if a not in self.nodes or b not in self.nodes:raise KeyError("unknown waypoint")
  if a==b:raise ValueError("self edge")
  self.edges[a].add(b);self.edges[b].add(a)
 def validate(self):
  out=[f"isolated:{n}" for n,e in self.edges.items() if not e and len(self.nodes)>1]
  for a,es in self.edges.items():
   for b in es:
    if b not in self.nodes:out.append(f"missing:{a}->{b}")
    elif a not in self.edges.get(b,set()):out.append(f"asymmetric:{a}->{b}")
  return out
 def shortest_path(self,start,goal):
  if start not in self.nodes or goal not in self.nodes:raise KeyError("unknown waypoint")
  q=[(0.0,start)];dist={start:0.0};prev={}
  while q:
   d,u=heapq.heappop(q)
   if d!=dist[u]:continue
   if u==goal:break
   for v in self.edges[u]:
    if v not in self.nodes:continue
    w=hypot(self.nodes[u].x-self.nodes[v].x,self.nodes[u].y-self.nodes[v].y);nd=d+w
    if nd<dist.get(v,float("inf")):dist[v]=nd;prev[v]=u;heapq.heappush(q,(nd,v))
  if goal not in dist:return []
  out=[];u=goal
  while True:
   out.append(self.nodes[u])
   if u==start:break
   u=prev[u]
  return list(reversed(out))
 def to_dict(self):
  return {"nodes":[asdict(n) for n in self.nodes.values()],"edges":[[a,b] for a,es in self.edges.items() for b in sorted(es) if a<b]}
 @classmethod
 def from_dict(cls,data):
  g=cls()
  for n in data.get("nodes",[]):g.add(Node(str(n["id"]),float(n["x"]),float(n["y"]),float(n.get("z",0))))
  for a,b in data.get("edges",[]):g.connect(str(a),str(b))
  return g
class RouteStore:
 def __init__(self,store):self.store=store
 def load(self):return self.store.load({"maps":{}})
 def get(self,map_name):return RouteGraph.from_dict(self.load().get("maps",{}).get(map_name,{}))
 def save(self,map_name,graph):
  data=self.load();data.setdefault("maps",{})[map_name]=graph.to_dict();self.store.save(data)
