from velora.match_director import MatchDirector, MatchDirectorState


def test_match_director_full_lifecycle():
    d = MatchDirector()
    d.prepare(10)
    for _ in range(10):
        d.player_ready()
    assert d.state == MatchDirectorState.LOBBY_READY
    d.start_search()
    d.match_found(42)
    d.start_farming()
    d.finish()
    assert d.state == MatchDirectorState.FINISHED


def test_match_director_rejects_search_before_lobby():
    d = MatchDirector()
    d.prepare(4)
    try:
        d.start_search()
        assert False
    except RuntimeError:
        pass
