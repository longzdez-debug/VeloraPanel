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


def test_route_store_serializes_concurrent_saves_without_losing_maps(tmp_path):
    from velora.routes import RouteStore
    from velora.storage import JsonStore
    import threading

    store = RouteStore(JsonStore(str(tmp_path / "routes.json")))
    barrier = threading.Barrier(2)

    def save(name):
        graph = RouteGraph()
        graph.add(Node("start", 0, 0))
        barrier.wait()
        store.save(name, graph)

    threads = [threading.Thread(target=save, args=(f"map{i}",)) for i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert store.maps() == ["map0", "map1"]
