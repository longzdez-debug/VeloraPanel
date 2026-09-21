def test_walkbot_options_are_grouped_and_immutable():
    from velora.options import WalkBotOptions
    options = WalkBotOptions()
    assert options.vision.frame_buffer_capacity >= 1
    assert options.recovery.max_recoveries >= 0
    try:
        options.navigation.arrive_radius = 10
    except Exception:
        pass
    else:
        raise AssertionError("options must be immutable")
