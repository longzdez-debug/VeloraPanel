from velora.windows import WindowsInput
from velora.window_guard import Cs2WindowGuard

class Guard:
    def __init__(self, allowed):
        self.value = allowed
    def allowed(self):
        return self.value

def test_windows_input_is_noop_when_disabled():
    x = WindowsInput(enabled=False)
    x.move(True, False, False, False)
    assert x.last == (False, False, False, False)

def test_windows_input_releases_when_guard_denies():
    x = WindowsInput(enabled=True, guard=Guard(False))
    x.move(True, False, False, False)
    assert x.last == (False, False, False, False)

def test_guard_requires_bound_owned_process():
    class Processes:
        def is_owned(self, pid):
            return False
    g = Cs2WindowGuard(Processes())
    g.bind(123)
    assert not g.allowed()
