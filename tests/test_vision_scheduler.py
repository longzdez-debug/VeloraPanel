from velora.vision_scheduler import VisionScheduler


def test_scheduler_bounds_light_and_heavy_work():
    s=VisionScheduler(light_hz=10,heavy_hz=2)
    assert s.should_run_light(1.0)
    assert not s.should_run_light(1.05)
    assert s.should_run_light(1.11)
    assert s.should_run_heavy(1.0)
    assert not s.should_run_heavy(1.2)
    assert s.should_run_heavy(1.51)
