from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Protocol
from .screen import Frame
from .vision_scheduler import VisionScheduler


@dataclass(frozen=True)
class VisionObservation:
    kind: str
    timestamp: float
    confidence: float
    data: dict


@dataclass(frozen=True)
class VisionResult:
    frame_id: int
    timestamp: float
    observations: tuple[VisionObservation, ...]


class IVisionBackend(Protocol):
    def process(self, frame: Frame) -> VisionResult: ...


class CpuVisionBackend:
    """Dependency-free baseline CV metrics over BGRA frames.

    This is intentionally a real image-analysis backend, not a synthetic detector.
    Domain-specific landmark/object detectors can consume these frames without
    coupling the rest of WalkBot to OpenCV/ONNX.
    """

    def __init__(self, sample_step: int = 8):
        self.sample_step = max(1, int(sample_step))

    def process(self, frame: Frame) -> VisionResult:
        if frame.channels != 4 or frame.pixel_format != "BGRA8":
            raise ValueError("CpuVisionBackend expects BGRA8 frames")
        pixels = frame.pixels
        width, height = frame.metadata.width, frame.metadata.height
        step = self.sample_step * 4
        luminance = []
        for offset in range(0, len(pixels) - 3, step):
            b, g, r = pixels[offset], pixels[offset + 1], pixels[offset + 2]
            luminance.append(0.114 * b + 0.587 * g + 0.299 * r)
        if not luminance:
            return VisionResult(frame.metadata.frame_id, frame.metadata.timestamp, ())
        mean = sum(luminance) / len(luminance)
        variance = sum((x - mean) ** 2 for x in luminance) / len(luminance)
        edges = sum(abs(luminance[i] - luminance[i - 1]) >= 24 for i in range(1, len(luminance)))
        edge_density = edges / max(1, len(luminance) - 1)
        observation = VisionObservation(
            "frame_metrics", frame.metadata.timestamp, 1.0,
            {"mean_luma": round(mean, 3), "luma_stddev": round(sqrt(variance), 3),
             "edge_density": round(edge_density, 5), "sample_count": len(luminance),
             "width": width, "height": height},
        )
        return VisionResult(frame.metadata.frame_id, frame.metadata.timestamp, (observation,))


class VisionPipeline:
    def __init__(self, backend: IVisionBackend, output=None, scheduler: VisionScheduler | None = None):
        self.backend = backend
        self.output = output
        self.scheduler = scheduler or VisionScheduler()

    def process(self, frame: Frame, heavy: bool = True) -> VisionResult | None:
        if heavy:
            if not self.scheduler.should_run_heavy(frame.metadata.timestamp):
                return None
        elif not self.scheduler.should_run_light(frame.metadata.timestamp):
            return None
        result = self.backend.process(frame)
        self.scheduler.stats = type(self.scheduler.stats)(
            capture_frames=self.scheduler.stats.capture_frames + 1,
            vision_frames=self.scheduler.stats.vision_frames + 1,
            dropped_frames=self.scheduler.stats.dropped_frames,
            last_capture_at=frame.metadata.timestamp,
            last_vision_at=frame.metadata.timestamp,
        )
        if self.output:
            self.output(result)
        return result
