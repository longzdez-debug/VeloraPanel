from math import isclose

from velora.aim import AimConfig, AimSolver, AimTarget


def test_select_rejects_low_confidence_and_out_of_fov_targets():
    solver = AimSolver(AimConfig(max_fov_deg=15.0, min_confidence=0.7))
    targets = [
        AimTarget("low", (10.0, 0.0, 0.0), confidence=0.4),
        AimTarget("wide", (10.0, 10.0, 0.0), confidence=1.0),
        AimTarget("good", (20.0, 2.0, 0.0), confidence=0.95),
    ]
    selected = solver.select((0.0, 0.0, 0.0), (0.0, 0.0), targets)
    assert selected is not None
    assert selected.track_id == "good"


def test_locked_target_is_stable_when_competing_targets_are_close():
    solver = AimSolver(AimConfig(max_fov_deg=20.0))
    targets = [
        AimTarget("a", (20.0, 3.0, 0.0), confidence=0.95),
        AimTarget("b", (20.0, 2.5, 0.0), confidence=0.90, locked=True),
    ]
    selected = solver.select((0.0, 0.0, 0.0), (0.0, 0.0), targets)
    assert selected is not None
    assert selected.track_id == "b"


def test_solve_predicts_motion_and_applies_smoothing():
    solver = AimSolver(AimConfig(prediction_seconds=0.1, smoothing=0.5))
    target = AimTarget("bot", (10.0, 0.0, 0.0), velocity=(0.0, 10.0, 0.0))
    solution = solver.solve((0.0, 0.0, 0.0), (0.0, 0.0), target)
    assert solution.predicted
    assert isclose(solution.aim_position[1], 1.0)
    assert 2.0 < solution.yaw_delta < 3.5
    assert isclose(solution.distance, (101.0) ** 0.5, rel_tol=1e-6)


def test_angle_wrap_is_shortest_path():
    solver = AimSolver(AimConfig(prediction_seconds=0.0, smoothing=1.0))
    target = AimTarget("wrap", (-10.0, 0.17, 0.0))
    solution = solver.solve((0.0, 0.0, 0.0), (179.0, 0.0), target)
    assert abs(solution.yaw_delta) < 2.0
