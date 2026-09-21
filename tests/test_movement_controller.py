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
