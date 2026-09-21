from time import time

from velora.scheduler import Job, Scheduler


def test_scheduler_priority_and_capacity():
    scheduler = Scheduler(max_concurrent=1)
    scheduler.add(Job("low", "a", priority=1))
    scheduler.add(Job("high", "b", priority=5))
    assert scheduler.next().id == "high"


def test_scheduler_retry_backoff_is_bounded():
    scheduler = Scheduler()
    job = Job("x", "a", max_retries=2)
    scheduler.add(job)
    scheduler.mark_done("x", success=False, now=time())
    assert job.retries == 1
    assert job.next_run > 1_000_000_000
    scheduler.mark_active("x")
    assert scheduler.next() is None


def test_scheduler_cooldown():
    scheduler = Scheduler()
    job = Job("x", "a", cooldown=10)
    scheduler.add(job)
    scheduler.mark_done("x", success=True, now=time())
    assert scheduler.next(now=time()) is None


def test_scheduler_snapshot_survives_restart_clock():
    now = time()
    scheduler = Scheduler()
    scheduler.add(Job("x", "a", cooldown=20, next_run=now + 20))
    restored = Scheduler()
    restored.load_snapshot(scheduler.snapshot())
    assert restored.get("x").next_run >= now + 19


def test_legacy_monotonic_timestamp_is_reset():
    restored = Scheduler()
    restored.load_snapshot([{"id": "x", "account_id": "a", "next_run": 12345.0}])
    assert restored.get("x").next_run == 0.0
