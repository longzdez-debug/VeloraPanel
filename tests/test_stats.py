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


def test_unknown_match_result_does_not_become_loss():
    store = StatsStore()
    store.record_match("a", xp_delta=125, win=None)
    stats = store.get("a")
    assert stats.matches == 1
    assert stats.xp == 125
    assert stats.wins == 0
    assert stats.losses == 0


def test_explicit_match_result_updates_win_loss():
    store = StatsStore()
    store.record_match("a", xp_delta=50, win=True)
    store.record_match("a", xp_delta=25, win=False)
    stats = store.get("a")
    assert stats.xp == 75
    assert stats.wins == 1
    assert stats.losses == 1


def test_match_score_and_duration_roundtrip():
    store = StatsStore()
    store.record_match("a", xp_delta=100, win=True, score=16, opponent_score=12, duration=123.5)
    snapshot = store.snapshot()
    restored = StatsStore()
    restored.load_snapshot(snapshot)
    stats = restored.get("a")
    assert stats.last_score == 16
    assert stats.last_opponent_score == 12
    assert stats.last_match_duration == 123.5
