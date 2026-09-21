from velora.routes import Node,RouteGraph
def test_shortest_path():
 g=RouteGraph()
 for n in [Node("a",0,0),Node("b",1,0),Node("c",2,0),Node("d",0,5)]:g.add(n)
 g.connect("a","b");g.connect("b","c");g.connect("a","d")
 assert [n.id for n in g.shortest_path("a","c")]==["a","b","c"]
