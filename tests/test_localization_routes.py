def test_localization_fuses_confidence_weighted_sources():
    from velora.localization import LocalizationEngine, PositionEstimate
    result = LocalizationEngine().fuse([
        PositionEstimate((0,0,0), 0.9, "gsi", 1.0),
        PositionEstimate((10,0,0), 0.5, "vision", 2.0),
    ])
    assert result is not None
    assert 0 < result.position[0] < 10
    assert result.confidence > 0

def test_route_database_selects_weighted_route_and_fallback():
    from velora.route_database import RouteDatabase, RouteEntry
    from velora.walkbot import Waypoint
    db = RouteDatabase()
    primary = RouteEntry("r1","de_test",(Waypoint("a",0,0),),1.0,recovery_route="r2")
    fallback = RouteEntry("r2","de_test",(Waypoint("b",1,0),),2.0)
    db.add(primary); db.add(fallback)
    assert db.select("de_test").route_id == "r2"
    assert db.fallback(primary).route_id == "r2"
