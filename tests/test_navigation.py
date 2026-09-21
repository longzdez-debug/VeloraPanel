from velora.domain import Vector3
from velora.navigation import Waypoint,WaypointGraph,Navigator
def test_shortest_path():
    g=WaypointGraph([Waypoint("a",Vector3(0,0,0)),Waypoint("b",Vector3(10,0,0)),Waypoint("c",Vector3(20,0,0))],{"a":["b"],"b":["c"],"c":[]})
    assert g.shortest_path("a","c")==["a","b","c"]
def test_navigation_intent():
    n=Navigator(WaypointGraph([Waypoint("a",Vector3(0,0,0)),Waypoint("b",Vector3(100,0,0))],{"a":["b"],"b":[]}))
    assert n.plan(Vector3(0,0,0),Vector3(100,0,0));assert n.intent(Vector3(0,0,0),0).forward
