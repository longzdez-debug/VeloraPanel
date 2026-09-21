import psutil


class ProcessPolicy:
    """Opt-in Windows process tuning inspired by FSM/BES watch behavior."""

    def __init__(self, priority="normal", affinity=None):
        self.priority = priority
        self.affinity = affinity
        self._original = {}

    def apply(self, process):
        if not process or not process.is_running():
            return False
        pid = process.pid
        try:
            if pid not in self._original:
                self._original[pid] = {
                    "nice": process.nice(),
                    "cpu_affinity": process.cpu_affinity(),
                }
            priority_map = {
                "idle": getattr(psutil, "IDLE_PRIORITY_CLASS", "idle"),
                "below_normal": getattr(psutil, "BELOW_NORMAL_PRIORITY_CLASS", "below_normal"),
                "above_normal": getattr(psutil, "ABOVE_NORMAL_PRIORITY_CLASS", "above_normal"),
                "normal": getattr(psutil, "NORMAL_PRIORITY_CLASS", "normal"),
            }
            if self.priority in priority_map and self.priority != "normal":
                process.nice(priority_map[self.priority])
            if self.affinity:
                process.cpu_affinity(self.affinity)
            return True
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.Error):
            return False

    def restore(self, process):
        if not process:
            return False
        original = self._original.pop(process.pid, None)
        if not original:
            return False
        try:
            process.nice(original["nice"])
            process.cpu_affinity(original["cpu_affinity"])
            return True
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.Error):
            return False
