def test_windows_input_turn_is_guarded_and_scaled():
    from velora.windows import WindowsInput

    class FakeUser32:
        def __init__(self):
            self.calls = []

        def SendInput(self, count, event, size):
            self.calls.append((count, event, size))
            return 1

    class Guard:
        def allowed(self):
            return True

    adapter = WindowsInput(enabled=True, guard=Guard(), mouse_turn_counts=200)
    fake = FakeUser32()
    adapter._user32 = fake
    adapter.turn(0.5)
    assert len(fake.calls) == 1
    assert fake.calls[0][0] == 1


def test_windows_input_blocks_when_guard_denies():
    from velora.windows import WindowsInput

    class FakeUser32:
        def SendInput(self, count, event, size):
            raise AssertionError("input must be blocked")

    class Guard:
        def allowed(self):
            return False

    adapter = WindowsInput(enabled=True, guard=Guard())
    adapter._user32 = FakeUser32()
    adapter.turn(1.0)
