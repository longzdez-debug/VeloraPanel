def test_movement_controller_is_the_only_adapter_boundary_for_intent():
    from velora.input import NullInput
    from velora.movement_controller import MovementController
    from velora.movement_intent import MovementIntent

    adapter = NullInput()
    controller = MovementController(adapter)
    output = controller.apply(MovementIntent(forward=1, strafe=-1))
    assert output.forward and output.left
    assert adapter.last == (True, False, True, False)
    controller.apply(MovementIntent(stop=True))
    assert adapter.last == (False, False, False, False)


def test_movement_controller_forwards_turn_when_adapter_supports_it():
    from velora.movement_controller import MovementController
    from velora.movement_intent import MovementIntent

    class Adapter:
        def __init__(self):
            self.moves = []
            self.turns = []

        def move(self, forward, back, left, right):
            self.moves.append((forward, back, left, right))

        def release_all(self):
            self.moves.append(("release",))

        def turn(self, amount):
            self.turns.append(amount)

    adapter = Adapter()
    MovementController(adapter).apply(MovementIntent(forward=1, turn=0.5))
    assert adapter.turns == [0.5]
