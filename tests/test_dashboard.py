

def test_dashboard_bool_parser_is_not_truthiness_based():
    from velora.dashboard import _as_bool

    assert _as_bool("false", "enabled") is False
    assert _as_bool("0", "enabled") is False
    assert _as_bool("true", "enabled") is True
    assert _as_bool(False, "enabled") is False


def test_dashboard_language_api_and_log_surface_are_present():
    from velora.dashboard import HTML

    assert 'api/settings/language' in HTML
    assert 'api/logs?lines=500' in HTML
    assert 'option value="ru">RU' in HTML
    assert 'option value="en">EN' in HTML
