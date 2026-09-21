from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class VisionOptions:
    capture_fps: float = 30.0
    light_cv_fps: float = 15.0
    heavy_cv_fps: float = 5.0
    frame_buffer_capacity: int = 2

@dataclass(frozen=True)
class NavigationOptions:
    arrive_radius: float = 28.0
    max_snap_distance: float = 250.0
    replan_min_interval: float = 1.0

@dataclass(frozen=True)
class MovementOptions:
    dead_zone: float = 8.0
    steer_angle: float = 20.0
    turn_dead_zone: float = 8.0

@dataclass(frozen=True)
class RecoveryOptions:
    stuck_seconds: float = 3.0
    max_recoveries: int = 3
    micro_timeout: float = 0.35
    steering_timeout: float = 0.75
    replan_timeout: float = 2.0
    route_switch_timeout: float = 4.0
    relocalize_timeout: float = 5.0
    reset_timeout: float = 8.0

@dataclass(frozen=True)
class LocalizationOptions:
    gsi_confidence: float = 0.95
    vision_confidence: float = 0.65
    max_position_age: float = 3.0

@dataclass(frozen=True)
class WalkBotOptions:
    vision: VisionOptions = VisionOptions()
    navigation: NavigationOptions = NavigationOptions()
    movement: MovementOptions = MovementOptions()
    recovery: RecoveryOptions = RecoveryOptions()
    localization: LocalizationOptions = LocalizationOptions()
