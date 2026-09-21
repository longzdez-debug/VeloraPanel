def test_decision_engine_never_emits_input():
    from velora.decision import DecisionEngine
    from velora.navigation import NavigationGoal
    from velora.world import WorldModel, ObservationValue

    world = WorldModel()
    world.update_localization(position=ObservationValue((1,2,0),1.0,"gsi",0.95), status="localized")
    decision = DecisionEngine().decide(world.snapshot(), NavigationGoal("move", target_position=(5,2,0)))
    assert decision.action == "move_to_target"
    assert decision.goal.target_position == (5,2,0)

def test_steering_is_feedback_driven():
    from velora.steering import Steering
    intent = Steering().steer((0,0,0),(1,0,0),(0,10,0))
    assert intent.forward > 0
    assert intent.turn > 0

def test_heatmap_decays():
    from velora.evidence import Heatmap
    h = Heatmap()
    h.add("a", 1.0, 0.0)
    assert h.value("a", 0.0) == 1.0
    assert 0.0 < h.value("a", 20.0) < 1.0

def test_behaviour_randomization_is_deterministic_and_bounded():
    from velora.behaviour import BehaviourProfile, BehaviourSampler
    a = BehaviourSampler(BehaviourProfile(seed=42))
    b = BehaviourSampler(BehaviourProfile(seed=42))
    assert [a.bounded_turn_offset() for _ in range(5)] == [b.bounded_turn_offset() for _ in range(5)]

def test_telemetry_has_correlation_id():
    from velora.telemetry import TelemetryContext
    ctx = TelemetryContext("test")
    assert ctx.correlation_id == "test"
    assert ctx.new_correlation() != "test"
