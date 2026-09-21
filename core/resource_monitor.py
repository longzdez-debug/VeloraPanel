"""Read-only health telemetry for VELORA-owned Steam/CS2 processes."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import psutil


@dataclass(frozen=True)
class ProcessHealth:
    pid: int
    name: str
    cpu_percent: float
    memory_mb: float
    running: bool


@dataclass(frozen=True)
class ResourceSnapshot:
    steam_count: int
    cs2_count: int
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    processes: tuple[ProcessHealth, ...]

    def as_dict(self) -> dict:
        data = asdict(self)
        data["processes"] = [asdict(item) for item in self.processes]
        return data


def _health(process: psutil.Process) -> ProcessHealth | None:
    try:
        if not process.is_running():
            return None
        return ProcessHealth(
            pid=process.pid,
            name=process.name(),
            cpu_percent=round(process.cpu_percent(interval=None), 1),
            memory_mb=round(process.memory_info().rss / (1024 * 1024), 1),
            running=True,
        )
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return None


def collect(account_objects) -> ResourceSnapshot:
    processes = []
    seen = set()
    for account in account_objects:
        for process in (
            getattr(account, "steamProcess", None),
            getattr(account, "CS2Process", None),
        ):
            if not process or process.pid in seen:
                continue
            seen.add(process.pid)
            health = _health(process)
            if health is not None:
                processes.append(health)

    virtual_memory = psutil.virtual_memory()
    return ResourceSnapshot(
        steam_count=sum(item.name.lower() == "steam.exe" for item in processes),
        cs2_count=sum(item.name.lower() == "cs2.exe" for item in processes),
        cpu_percent=round(psutil.cpu_percent(interval=None), 1),
        memory_percent=round(virtual_memory.percent, 1),
        memory_used_mb=round(virtual_memory.used / (1024 * 1024), 1),
        memory_total_mb=round(virtual_memory.total / (1024 * 1024), 1),
        processes=tuple(processes),
    )
