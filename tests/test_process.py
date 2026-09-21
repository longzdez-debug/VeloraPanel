from velora.process import ProcessIdentity, ProcessSupervisor

def test_empty_supervisor():
    assert ProcessSupervisor().owned == {}


def test_claim_missing_process_is_safe():
    assert ProcessSupervisor().claim(999999999, "C:/missing/cs2.exe") is None


def test_alive_handles_process_race():
    supervisor = ProcessSupervisor()
    supervisor.owned[999999999] = ProcessIdentity(999999999, 0.0, "C:/missing/cs2.exe")
    assert supervisor.alive(999999999) is False


def test_find_and_claim_skips_owned_and_old_processes(monkeypatch, tmp_path):
    import velora.process as process_module
    exe = str(tmp_path / "cs2.exe")

    class Proc:
        def __init__(self, pid, created):
            self.pid = pid
            self.info = {"pid": pid, "exe": exe, "create_time": created}

    supervisor = ProcessSupervisor()
    supervisor.owned[1] = ProcessIdentity(1, 100.0, exe)
    monkeypatch.setattr(process_module.psutil, "process_iter", lambda fields: [Proc(1, 101.0), Proc(2, 99.0), Proc(3, 102.0)])
    claimed = []

    def fake_claim(pid, expected, manage=True):
        claimed.append((pid, manage))
        return ProcessIdentity(pid, 102.0, expected)

    supervisor.claim = fake_claim
    result = supervisor.find_and_claim(exe, not_before=100.0)
    assert result.pid == 3
    assert claimed == [(3, True)]


def test_find_existing_marks_process_unmanaged(monkeypatch, tmp_path):
    import velora.process as process_module
    exe = str(tmp_path / "cs2.exe")

    class Proc:
        pid = 42
        info = {"pid": 42, "exe": exe, "create_time": 123.0}

    supervisor = ProcessSupervisor()
    monkeypatch.setattr(process_module.psutil, "process_iter", lambda fields: [Proc()])
    monkeypatch.setattr(
        process_module.psutil,
        "Process",
        lambda pid: type("P", (), {
            "pid": pid,
            "exe": lambda self: exe,
            "create_time": lambda self: 123.0,
            "cmdline": lambda self: [exe],
        })(),
    )
    result = supervisor.find_existing(exe)
    assert result.pid == 42
    assert supervisor.is_managed(42) is False
    assert supervisor.terminate(42) is False
    assert 42 not in supervisor.owned


def test_terminate_is_safe_when_process_exits_between_check_and_terminate(monkeypatch):
    import velora.process as process_module

    supervisor = ProcessSupervisor()
    supervisor.owned[42] = ProcessIdentity(42, 1.0, "C:/cs2.exe")

    class Gone:
        def terminate(self):
            raise process_module.psutil.NoSuchProcess(42)

    monkeypatch.setattr(supervisor, "is_owned", lambda pid: True)
    monkeypatch.setattr(supervisor, "alive", lambda pid: False)
    monkeypatch.setattr(process_module.psutil, "Process", lambda pid: Gone())

    assert supervisor.terminate(42) is True
    assert 42 not in supervisor.owned
