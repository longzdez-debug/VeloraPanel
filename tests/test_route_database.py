from velora.route_database import RouteDatabase
from velora.routes import Node, RouteGraph, RouteStore
from velora.storage import JsonStore


def test_route_database_import_store_bridges_persistent_graph(tmp_path):
    store = RouteStore(JsonStore(str(tmp_path / "routes.json")))
    graph = RouteGraph()
    graph.add(Node("a", 0, 0, 0))
    graph.add(Node("b", 10, 0, 0))
    graph.connect("a", "b")
    store.save("de_dust2", graph)

    db = RouteDatabase()
    entry = db.import_store(store, "de_dust2", route_id="main", tags=("safe",))

    assert entry.map_name == "de_dust2"
    assert [node.id for node in entry.nodes] == ["a", "b"]
    assert db.select("de_dust2", tags=("safe",)).route_id == "main"


def test_route_database_replaces_same_route_id_without_duplicates():
    graph = RouteGraph()
    graph.add(Node("a", 0, 0, 0))
    db = RouteDatabase()
    db.import_graph("map", graph, route_id="default")
    db.import_graph("map", graph, route_id="default")
    assert len(db.candidates("map")) == 1


def test_route_database_add_replaces_same_route_id():
    db = RouteDatabase()
    graph = RouteGraph()
    graph.add(Node("a", 0, 0, 0))
    db.add(db.import_graph("map", graph, route_id="r1"))
    db.add(db.import_graph("map", graph, route_id="r1"))
    assert [r.route_id for r in db.candidates("map")] == ["r1"]
