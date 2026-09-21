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
