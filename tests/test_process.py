from velora.process import ProcessSupervisor

def test_empty_supervisor():
    assert ProcessSupervisor().owned == {}

def test_claim_missing_process_is_safe():
    assert ProcessSupervisor().claim(999999999, "C:/missing/cs2.exe") is None
