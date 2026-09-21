from velora.screen import Frame, FrameMetadata
from velora.vision import CpuVisionBackend, VisionPipeline
from velora.vision_scheduler import VisionScheduler
from velora.world import WorldModel


def test_pipeline_records_capture_and_vision_for_processed_frame():
    world = WorldModel()
    scheduler = VisionScheduler(light_hz=1, heavy_hz=1)
    pipeline = VisionPipeline(CpuVisionBackend(sample_step=1), scheduler=scheduler, world=world)
    frame = Frame(FrameMetadata(1, 2.0, 2, 1), bytes([0, 0, 0, 255, 255, 255, 255, 255]))

    result = pipeline.process(frame, heavy=True)

    assert result is not None
    stats = scheduler.snapshot()
    assert stats.capture_frames == 1
    assert stats.vision_frames == 1
    assert stats.dropped_frames == 0
    assert world.snapshot().vision.frame_id == 1


def test_pipeline_counts_captured_throttled_frames():
    scheduler = VisionScheduler(light_hz=10, heavy_hz=10)
    pipeline = VisionPipeline(CpuVisionBackend(sample_step=1), scheduler=scheduler)
    frame1 = Frame(FrameMetadata(1, 1.0, 1, 1), bytes([0, 0, 0, 255]))
    frame2 = Frame(FrameMetadata(2, 1.01, 1, 1), bytes([0, 0, 0, 255]))

    assert pipeline.process(frame1, heavy=True) is not None
    assert pipeline.process(frame2, heavy=True) is None
    stats = scheduler.snapshot()
    assert stats.capture_frames == 2
    assert stats.vision_frames == 1
    assert stats.dropped_frames == 1
