from velora.orchestrator import FarmOrchestrator
from velora.farm import FarmManager
from velora.resource import ResourceManager,ResourceBudget
from velora.account_pool import AccountPool

def test_orchestrator_snapshot_roundtrip():
    class A:
        def __init__(self,i): self.id=i;self.enabled=True
    class S: pass
    s=S();s.farm=FarmManager(AccountPool([A("a")]),ResourceManager(ResourceBudget(1,1)));s.get_account=lambda i:None;s.lobbies=type("L",(),{"lobbies":{}})();s.stats=type("T",(),{})()
    o=FarmOrchestrator(s);o.runtime["b1"]=o.runtime.get("b1") or __import__("velora.orchestrator",fromlist=["BatchRuntime"]).BatchRuntime("b1",{"a"},2,10,"error","x")
    x=FarmOrchestrator(s);x.load_snapshot(o.snapshot());assert x.runtime["b1"].ready=={"a"};assert x.runtime["b1"].retries==2
