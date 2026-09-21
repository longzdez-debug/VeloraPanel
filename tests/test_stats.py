from velora.stats import StatsStore


def test_stats_record():
    store = StatsStore()
    store.record_match("a", xp_delta=100, win=True)
    assert store.get("a").xp == 100
    assert store.get("a").wins == 1


def test_stats_snapshot_roundtrip():
    source = StatsStore()
    source.record_match("a", xp_delta=50, win=False)
    restored = StatsStore()
    restored.load_snapshot(source.snapshot())
    stats = restored.get("a")
    assert stats.matches == 1
    assert stats.losses == 1
    assert stats.xp == 50
