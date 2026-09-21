from velora.decision import DecisionEngine
from velora.movement_controller import MovementController
from velora.movement_intent import MovementIntent
from velora.world import WorldModel


class SpyInput:
    def __init__(self):
        self.calls = []

    def move(self, forward, back, left, right):
        self.calls.append((forward, back, left, right))

    def release_all(self):
        self.calls.append(("release",))


def test_movement_controller_is_the_input_boundary():
    spy = SpyInput()
    controller = MovementController(spy)
    output = controller.apply(MovementIntent(forward=1.0))
    assert output.forward is True
    assert spy.calls == [(True, False, False, False)]


def test_decision_engine_has_no_input_dependency():
    world = WorldModel()
    decision = DecisionEngine().decide(world.snapshot())
    assert decision.action == "relocalize"


def test_decision_engine_relocalizes_when_position_is_stale():
    from velora.decision import DecisionEngine
    from velora.navigation import NavigationGoal
    from velora.world import ObservationValue, WorldModel
    world = WorldModel()
    world.update_localization(
        position=ObservationValue((1.0, 2.0, 3.0), 0.0, "gsi", 0.95, True),
        status="localized",
    )
    decision = DecisionEngine().decide(world.snapshot(), NavigationGoal("waypoint", target_area="a"), max_localization_age=0.1)
    assert decision.action == "relocalize"
    assert decision.reason == "localization_stale"
