from __future__ import annotations

from dataclasses import dataclass
from threading import Condition, Lock
from time import monotonic
from typing import Protocol


@dataclass(frozen=True)
class FrameMetadata:
    frame_id: int
    timestamp: float
    width: int
    height: int
    monitor: str = ""
    window: str = ""


@dataclass(frozen=True)
class Frame:
    metadata: FrameMetadata
    pixels: bytes
    channels: int = 4
    pixel_format: str = "BGRA8"


class IScreenCapture(Protocol):
    def capture(self) -> Frame: ...
    def close(self) -> None: ...


class BoundedFrameBuffer:
    """Latest-frame buffer with bounded memory and explicit overwrite semantics."""

    def __init__(self, capacity: int = 2):
        self.capacity = max(1, int(capacity))
        self._items: list[Frame] = []
        self._condition = Condition(Lock())

    def put(self, frame: Frame) -> None:
        with self._condition:
            if len(self._items) >= self.capacity:
                self._items.pop(0)
            self._items.append(frame)
            self._condition.notify()

    def get(self, timeout: float | None = None) -> Frame | None:
        deadline = None if timeout is None else monotonic() + max(0.0, timeout)
        with self._condition:
            while not self._items:
                if deadline is None:
                    self._condition.wait()
                    continue
                remaining = deadline - monotonic()
                if remaining <= 0:
                    return None
                self._condition.wait(remaining)
            return self._items.pop(0)


class WindowsGdiCapture:
    """Real Windows desktop capture using GDI; never reads CS2 process memory."""

    def __init__(self, left=0, top=0, width=0, height=0, window="desktop"):
        self.left, self.top, self.width, self.height = map(int, (left, top, width, height))
        self.window = window
        self._frame_id = 0
        self._closed = False

    def capture(self) -> Frame:
        if self._closed:
            raise RuntimeError("capture is closed")
        import ctypes
        from ctypes import wintypes
        if not hasattr(ctypes, "windll"):
            raise RuntimeError("Windows GDI capture requires Windows")

        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32
        screen_dc = user32.GetDC(0)
        if not screen_dc:
            raise OSError("GetDC failed")
        try:
            width = self.width or user32.GetSystemMetrics(0)
            height = self.height or user32.GetSystemMetrics(1)
            mem_dc = gdi32.CreateCompatibleDC(screen_dc)
            if not mem_dc:
                raise OSError("CreateCompatibleDC failed")
            bitmap = gdi32.CreateCompatibleBitmap(screen_dc, width, height)
            if not bitmap:
                gdi32.DeleteDC(mem_dc)
                raise OSError("CreateCompatibleBitmap failed")
            old = gdi32.SelectObject(mem_dc, bitmap)
            try:
                if not gdi32.BitBlt(mem_dc, 0, 0, width, height, screen_dc, self.left, self.top, 0x00CC0020):
                    raise OSError("BitBlt failed")

                class BITMAPINFOHEADER(ctypes.Structure):
                    _fields_ = [
                        ("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG),
                        ("biHeight", wintypes.LONG), ("biPlanes", wintypes.WORD),
                        ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                        ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                        ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
                        ("biClrImportant", wintypes.DWORD),
                    ]

                header = BITMAPINFOHEADER(40, width, -height, 1, 32, 0, width * height * 4, 0, 0, 0, 0)
                size = width * height * 4
                buffer = (ctypes.c_ubyte * size)()
                gdi32.GetDIBits(mem_dc, bitmap, 0, height, buffer, ctypes.byref(header), 0)
                self._frame_id += 1
                return Frame(
                    FrameMetadata(self._frame_id, monotonic(), width, height, "primary", self.window),
                    bytes(buffer),
                )
            finally:
                gdi32.SelectObject(mem_dc, old)
                gdi32.DeleteObject(bitmap)
                gdi32.DeleteDC(mem_dc)
        finally:
            user32.ReleaseDC(0, screen_dc)

    def close(self):
        self._closed = True
