from velora.routes import Node,RouteGraph

def test_route_graph():
 g=RouteGraph();g.add(Node("a",0,0));g.add(Node("b",1,0));g.connect("a","b")
 assert g.validate()==[]

def test_nearest_and_path_from_position():
 g=RouteGraph()
 for n in [Node("a",0,0),Node("b",100,0),Node("c",200,0)]:g.add(n)
 g.connect("a","b");g.connect("b","c")
 assert g.nearest_node((82,3,0)).id=="b"
 assert [n.id for n in g.path_from_position((95,0,0),"c")]==["b","c"]
 assert g.path_from_position((5000,0,0),"c",100)==[]
