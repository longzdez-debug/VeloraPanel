from dataclasses import dataclass
import os

def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

@dataclass(frozen=True)
class Config:
    gsi_host: str = "127.0.0.1"
    gsi_port: int = 27100
    gsi_token: str = ""
    tick_hz: float = 20
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 8765
    data_dir: str = "data"
    input_enabled: bool = False
    input_require_foreground: bool = True
    process_start_timeout: float = 30.0
    watchdog_enabled: bool = True
    watchdog_max_restarts: int = 3
    watchdog_backoff: float = 5.0

    @classmethod
    def from_env(cls):
        return cls(
            os.getenv("VELORA_GSI_HOST", "127.0.0.1"),
            int(os.getenv("VELORA_GSI_PORT", "27100")),
            os.getenv("VELORA_GSI_TOKEN", ""),
            float(os.getenv("VELORA_TICK_HZ", "20")),
            os.getenv("VELORA_DASHBOARD_HOST", "127.0.0.1"),
            int(os.getenv("VELORA_DASHBOARD_PORT", "8765")),
            os.getenv("VELORA_DATA_DIR", "data"),
            _bool("VELORA_INPUT_ENABLED", False),
            _bool("VELORA_INPUT_REQUIRE_FOREGROUND", True),
            float(os.getenv("VELORA_PROCESS_START_TIMEOUT", "30")),
            _bool("VELORA_WATCHDOG_ENABLED", True),
            int(os.getenv("VELORA_WATCHDOG_MAX_RESTARTS", "3")),
            float(os.getenv("VELORA_WATCHDOG_BACKOFF", "5")),
        )
