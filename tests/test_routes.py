from velora.routes import Node,RouteGraph
def test_route_graph(): g=RouteGraph();g.add(Node('a',0,0));g.add(Node('b',1,0));g.connect('a','b');assert g.validate()==[]
