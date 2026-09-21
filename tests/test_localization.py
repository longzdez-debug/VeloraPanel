from velora.localization import LocalizationEngine, PositionEstimate


def test_localization_fuses_confidence_weighted_positions():
    result = LocalizationEngine().fuse([
        PositionEstimate((0.0, 0.0, 0.0), 1.0, "gsi", 1.0),
        PositionEstimate((10.0, 0.0, 0.0), 0.5, "vision", 2.0),
    ])
    assert result is not None
    assert result.position[0] == 10.0 / 3.0
    assert result.source == "gsi+vision"
    assert result.timestamp == 2.0


def test_localization_rejects_zero_confidence_observations():
    result = LocalizationEngine().fuse([
        PositionEstimate((1.0, 2.0, 3.0), 0.0, "vision", 1.0),
    ])
    assert result is None
