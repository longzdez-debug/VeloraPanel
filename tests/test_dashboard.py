

def test_dashboard_bool_parser_is_not_truthiness_based():
    from velora.dashboard import _as_bool

    assert _as_bool("false", "enabled") is False
    assert _as_bool("0", "enabled") is False
    assert _as_bool("true", "enabled") is True
    assert _as_bool(False, "enabled") is False
