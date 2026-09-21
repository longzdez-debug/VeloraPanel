import threading
import time


class SteamSafety:
    """Conservative pacing and circuit breaking for Steam-facing operations."""

    def __init__(self):
        self._lock = threading.RLock()
        self._last_by_operation = {}
        self._blocked_until = {}

    def wait(self, operation, key, interval):
        with self._lock:
            now = time.monotonic()
            blocked = self._blocked_until.get(key, 0)
            last = self._last_by_operation.get((operation, key), 0)
            delay = max(0.0, blocked - now, interval - (now - last))
            self._last_by_operation[(operation, key)] = now + delay
        if delay:
            time.sleep(delay)

    def block(self, key, seconds):
        with self._lock:
            self._blocked_until[key] = max(
                self._blocked_until.get(key, 0), time.monotonic() + seconds
            )

    def clear(self, key):
        with self._lock:
            self._blocked_until.pop(key, None)


steam_safety = SteamSafety()
