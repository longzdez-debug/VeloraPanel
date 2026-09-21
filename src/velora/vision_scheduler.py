from __future__ import annotations
from dataclasses import dataclass
from time import monotonic

@dataclass(frozen=True)
class PipelineStats:
 capture_frames:int=0
 vision_frames:int=0
 dropped_frames:int=0
 last_capture_at:float=0.0
 last_vision_at:float=0.0

class VisionScheduler:
 def __init__(self,light_hz:float=15.0,heavy_hz:float=5.0):
  self.light_interval=1.0/max(0.1,float(light_hz));self.heavy_interval=1.0/max(0.1,float(heavy_hz))
  self._last_light=0.0;self._last_heavy=0.0
  self.stats=PipelineStats()

 def should_run_light(self,now=None):
  now=monotonic() if now is None else now
  if now-self._last_light < self.light_interval:
   self.stats=PipelineStats(self.stats.capture_frames,self.stats.vision_frames,self.stats.dropped_frames+1,self.stats.last_capture_at,self.stats.last_vision_at)
   return False
  self._last_light=now;return True

 def should_run_heavy(self,now=None):
  now=monotonic() if now is None else now
  if now-self._last_heavy < self.heavy_interval:
   self.stats=PipelineStats(self.stats.capture_frames,self.stats.vision_frames,self.stats.dropped_frames+1,self.stats.last_capture_at,self.stats.last_vision_at)
   return False
  self._last_heavy=now;return True
