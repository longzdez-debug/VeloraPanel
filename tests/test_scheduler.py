from velora.scheduler import Scheduler,Job
def test_priority(): s=Scheduler();s.add(Job('a','a',1));s.add(Job('b','b',2));assert s.next().id=='b'
