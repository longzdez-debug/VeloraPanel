from velora.scheduler import Job,Scheduler
def test_priority_and_concurrency():
 s=Scheduler(max_concurrent=1);s.add(Job("a","a",1));s.add(Job("b","b",5))
 assert s.next().account_id=="b";s.mark_active("b");assert s.next() is None
