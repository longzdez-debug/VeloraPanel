from velora.process import ProcessSupervisor

def test_process_supervisor_starts_empty():
 assert ProcessSupervisor().owned=={}
