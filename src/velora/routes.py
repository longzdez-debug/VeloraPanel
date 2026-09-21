from __future__ import annotations
from dataclasses import asdict,dataclass
from math import dist,hypot
import heapq

@dataclass(frozen=True)
class Node:
 id:str
 x:float
 y:float
 z:float=0.0

class RouteGraph:
 def __init__(self):
  self.nodes:dict[str,Node]={}
  self.edges:dict[str,set[str]]={}

 def add(self,node:Node):
  self.nodes[node.id]=node
  self.edges.setdefault(node.id,set())

 def remove(self,node_id:str):
  self.nodes.pop(node_id,None)
  self.edges.pop(node_id,None)
  for edges in self.edges.values():
   edges.discard(node_id)

 def connect(self,a:str,b:str):
  if a not in self.nodes or b not in self.nodes: raise KeyError("unknown waypoint")
  if a==b: raise ValueError("self edge")
  self.edges[a].add(b); self.edges[b].add(a)

 def validate(self)->list[str]:
  problems=[f"isolated:{n}" for n,e in self.edges.items() if not e and len(self.nodes)>1]
  for a,edges in self.edges.items():
   for b in edges:
    if b not in self.nodes: problems.append(f"missing:{a}->{b}")
    elif a not in self.edges.get(b,set()): problems.append(f"asymmetric:{a}->{b}")
  return problems

 def nearest_node(self,position:tuple[float,float,float]|tuple[float,float],max_distance:float|None=None)->Node|None:
  if not self.nodes: return None
  p=(float(position[0]),float(position[1]),float(position[2]) if len(position)>2 else 0.0)
  node=min(self.nodes.values(),key=lambda n:dist((n.x,n.y,n.z),p))
  return None if max_distance is not None and dist((node.x,node.y,node.z),p)>max_distance else node

 def shortest_path(self,start:str,goal:str)->list[Node]:
  if start not in self.nodes or goal not in self.nodes: raise KeyError("unknown waypoint")
  q=[(0.0,start)]; distances={start:0.0}; previous={}
  while q:
   d,u=heapq.heappop(q)
   if d!=distances[u]: continue
   if u==goal: break
   for v in self.edges.get(u,set()):
    if v not in self.nodes: continue
    w=hypot(self.nodes[u].x-self.nodes[v].x,self.nodes[u].y-self.nodes[v].y)
    nd=d+w
    if nd<distances.get(v,float("inf")):
     distances[v]=nd;previous[v]=u;heapq.heappush(q,(nd,v))
  if goal not in distances: return []
  out=[];u=goal
  while True:
   out.append(self.nodes[u])
   if u==start: break
   u=previous[u]
  return list(reversed(out))

 def path_from_position(self,position,goal:str,max_snap_distance:float|None=None)->list[Node]:
  start=self.nearest_node(position,max_snap_distance)
  if start is None: return []
  return self.shortest_path(start.id,goal)

 def to_dict(self):
  return {"nodes":[asdict(n) for n in self.nodes.values()],
          "edges":[[a,b] for a,edges in self.edges.items() for b in sorted(edges) if a<b]}

 @classmethod
 def from_dict(cls,data):
  graph=cls()
  for n in data.get("nodes",[]):
   graph.add(Node(str(n["id"]),float(n["x"]),float(n["y"]),float(n.get("z",0))))
  for a,b in data.get("edges",[]): graph.connect(str(a),str(b))
  return graph

class RouteStore:
 def __init__(self,store): self.store=store
 def load(self): return self.store.load({"maps":{}})
 def maps(self): return sorted((self.load().get("maps") or {}).keys())
 def get(self,map_name): return RouteGraph.from_dict(self.load().get("maps",{}).get(map_name,{}))
 def save(self,map_name,graph):
  data=self.load();data.setdefault("maps",{})[map_name]=graph.to_dict();self.store.save(data)
