from velora.replay import ReplaySession


def test_replay_load_can_enforce_event_bound(tmp_path):
    path = tmp_path / "replay.json"
    session = ReplaySession("demo", max_events=10)
    for i in range(5):
        session.record("tick", float(i), {"i": i})
    session.save(path)

    loaded = ReplaySession.load(path, max_events=2)
    assert [event.payload["i"] for event in loaded.events] == [3, 4]
    assert loaded.max_events == 2


def test_replay_from_dict_preserves_default_all_events():
    session = ReplaySession.from_dict({
        "session_id": "demo",
        "events": [{"timestamp": 1, "kind": "gsi", "payload": {}}],
    })
    assert session.session_id == "demo"
    assert len(session.events) == 1
