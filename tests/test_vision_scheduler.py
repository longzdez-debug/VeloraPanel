from velora.vision_scheduler import VisionScheduler


def test_scheduler_bounds_light_and_heavy_work():
    s=VisionScheduler(light_hz=10,heavy_hz=2)
    assert s.should_run_light(1.0)
    assert not s.should_run_light(1.05)
    assert s.should_run_light(1.11)
    assert s.should_run_heavy(1.0)
    assert not s.should_run_heavy(1.2)
    assert s.should_run_heavy(1.51)


def test_scheduler_records_capture_and_vision():
    s = VisionScheduler(light_hz=10, heavy_hz=2)
    s.record_capture(1.0)
    s.record_vision(1.1)
    stats = s.snapshot()
    assert stats.capture_frames == 1
    assert stats.vision_frames == 1
    assert stats.last_capture_at == 1.0
    assert stats.last_vision_at == 1.1
