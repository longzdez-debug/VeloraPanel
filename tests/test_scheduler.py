from velora.scheduler import Job, Scheduler

def test_scheduler_priority_and_capacity():
    s = Scheduler(max_concurrent=1)
    s.add(Job("low", "a", priority=1))
    s.add(Job("high", "b", priority=5))
    assert s.next().id == "high"

def test_scheduler_retry_backoff_is_bounded():
    s = Scheduler()
    j = Job("x", "a", max_retries=2)
    s.add(j)
    s.mark_done("x", success=False)
    assert j.retries == 1
    assert j.next_run > 0
    s.mark_active("x")
    assert s.next() is None

def test_scheduler_cooldown():
    s = Scheduler()
    j = Job("x", "a", cooldown=10)
    s.add(j)
    s.mark_done("x", success=True)
    assert s.next() is None
