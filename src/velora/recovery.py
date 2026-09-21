from __future__ import annotations
from time import monotonic
from .domain import Vector3
class StuckDetector:
    def __init__(self,min_distance=8.0,timeout=2.5):self.min_distance=min_distance;self.timeout=timeout;self._anchor=None;self._since=monotonic()
    def update(self,p:Vector3|None)->bool:
        if p is None:return False
        now=monotonic()
        if self._anchor is None:self._anchor=p;self._since=now;return False
        if p.distance(self._anchor)>=self.min_distance:self._anchor=p;self._since=now;return False
        return now-self._since>=self.timeout
    def reset(self):self._anchor=None;self._since=monotonic()
