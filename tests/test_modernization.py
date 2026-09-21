def test_world_model_records_provenance_and_freshness():
    from velora.world import ObservationValue, WorldModel
    from time import monotonic

    now = monotonic()
    value = ObservationValue((1.0, 2.0, 3.0), now, "gsi", 0.95)
    assert value.valid and value.source == "gsi" and value.confidence == 0.95
    assert value.fresh(now, 1.0)
    assert not value.fresh(now + 2.0, 1.0)

    world = WorldModel()
    world.update_player(position=value)
    assert world.snapshot().player.position.value == (1.0, 2.0, 3.0)


def test_gsi_normalizer_publishes_to_world_model():
    from velora.gsi_normalizer import GsiNormalizer
    from velora.model import GsiSnapshot
    from velora.world import WorldModel

    snap = GsiSnapshot(10.0, map_name="de_dust2", activity="playing",
                       round_phase="live", health=100,
                       position=(10.0, 20.0, 0.0), forward=(1.0, 0.0, 0.0))
    world = WorldModel()
    normalized = GsiNormalizer().publish(snap, world)
    current = world.snapshot()
    assert normalized.player.position.confidence == 0.95
    assert current.game.map_name.value == "de_dust2"
    assert current.localization.status == "localized"


def test_nav_graph_astar_supports_custom_cost():
    from velora.navigation import NavArea, NavGraph
    graph = NavGraph()
    for area in [NavArea("a",(0,0,0)), NavArea("b",(10,0,0)), NavArea("c",(20,0,0)), NavArea("d",(0,20,0))]:
        graph.add_area(area)
    graph.connect("a","b"); graph.connect("b","c"); graph.connect("a","d"); graph.connect("d","c")
    assert graph.astar("a","c") == ["a","b","c"]
    assert graph.astar("a","c", lambda edge: edge.distance + (100 if edge.target == "b" else 0)) == ["a","d","c"]


def test_frame_buffer_is_bounded_and_keeps_latest_data():
    from velora.screen import BoundedFrameBuffer, Frame, FrameMetadata
    buffer = BoundedFrameBuffer(2)
    for i in range(3):
        buffer.put(Frame(FrameMetadata(i, float(i), 1, 1), bytes([i,0,0,255])))
    assert buffer.get().metadata.frame_id == 1
    assert buffer.get().metadata.frame_id == 2
    assert buffer.get() is None


def test_cpu_vision_backend_returns_real_frame_metrics():
    from velora.screen import Frame, FrameMetadata
    from velora.vision import CpuVisionBackend
    pixels = bytes([0,0,0,255, 0,0,255,255] * 8)
    result = CpuVisionBackend(sample_step=1).process(Frame(FrameMetadata(1,1.0,4,4),pixels))
    assert result.observations and result.observations[0].kind == "frame_metrics"
    assert result.observations[0].data["mean_luma"] > 0


def test_replay_session_is_bounded():
    from velora.replay import ReplaySession
    replay = ReplaySession("test", max_events=3)
    for i in range(5):
        replay.record("event", float(i), {"i": i})
    assert len(replay.events) == 3
    assert replay.events[0].payload["i"] == 2
