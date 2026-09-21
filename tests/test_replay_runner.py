from velora.replay import ReplaySession
from velora.replay_runner import ReplayRunner


def test_replay_runner_is_offline_and_bounded():
    session = ReplaySession("test", max_events=2)
    session.record("GsiUpdated", 1.0)
    session.record("MovementCommand", 2.0)
    session.record("RecoveryDecision", 3.0)
    result = ReplayRunner().run(session)
    assert result.session_id == "test"
    assert result.event_count == 2
    assert result.kinds == {"MovementCommand": 1, "RecoveryDecision": 1}
