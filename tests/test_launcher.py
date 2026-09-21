from types import SimpleNamespace

from velora.launcher import Cs2Launcher
from velora.process import ProcessIdentity


def test_start_attaches_to_existing_process_without_launching(monkeypatch, tmp_path):
    exe = tmp_path / "cs2.exe"
    exe.write_text("stub")

    class Processes:
        def __init__(self):
            self.launched = False
            self.existing = ProcessIdentity(42, 1.0, str(exe))

        def find_existing(self, path):
            assert path == str(exe)
            return self.existing

        def launch(self, *args, **kwargs):
            self.launched = True
            raise AssertionError("a second process must not be launched")

    processes = Processes()
    launcher = Cs2Launcher(processes=processes)
    monkeypatch.setattr(launcher, "resolve", lambda configured="": exe)

    result = launcher.start(via_steam=True)

    assert result.attached is True
    assert result.identity.pid == 42
    assert processes.launched is False


def test_start_launches_when_no_existing_process(monkeypatch, tmp_path):
    exe = tmp_path / "cs2.exe"
    exe.write_text("stub")

    identity = ProcessIdentity(43, 2.0, str(exe))

    class Processes:
        def find_existing(self, path):
            return None

        def launch(self, *args, **kwargs):
            return identity

    launcher = Cs2Launcher(processes=Processes())
    monkeypatch.setattr(launcher, "resolve", lambda configured="": exe)

    result = launcher.start(via_steam=False)

    assert result.attached is False
    assert result.identity.pid == 43
