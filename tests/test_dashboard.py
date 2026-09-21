

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


def test_dashboard_russian_localization_covers_ui_and_dynamic_surfaces():
    from velora.dashboard import HTML

    assert "Панель управления" in HTML
    assert "Редактор маршрутов" in HTML
    assert "АВАРИЙНАЯ ОСТАНОВКА" in HTML
    assert "function localizeDom()" in HTML
    assert "placeholder','title','aria-label'" in HTML
    assert "No diagnostic data." in HTML
    assert "No accounts." in HTML
    assert "No batches." in HTML


def test_dashboard_control_center_has_live_refresh_and_account_selection():
    from velora.dashboard import HTML

    assert "id=lastUpdate" in HTML
    assert "function selectedAccounts()" in HTML
    assert "function selectVisible()" in HTML
    assert "setInterval(load,2000)" in HTML


def test_dashboard_account_kill_targets_process_stop():
    from velora.dashboard import Dashboard
    import inspect

    source = inspect.getsource(Dashboard.start)
    assert 'outer.s.stop_account(a.id)' in source


def test_dashboard_event_timeline_surface_and_api_are_present():
    from velora.dashboard import HTML

    assert 'api/events?limit=100' in HTML
    assert 'function renderEvents' in HTML
    assert 'EVENT TIMELINE' in HTML
    assert 'setInterval(loadEvents,2500)' in HTML


def test_dashboard_event_buffer_is_bounded_and_structured():
    from velora.dashboard import Dashboard
    from types import SimpleNamespace

    supervisor = SimpleNamespace(config=SimpleNamespace(data_dir='.'),)
    dashboard = Dashboard(supervisor)
    for i in range(600):
        dashboard._event('test', f'event-{i}')
    assert len(dashboard._events) == 500
    assert dashboard._events[-1]['message'] == 'event-599'
    assert dashboard._events[0]['id'] == 101


def test_dashboard_exposes_walkbot_gsi_and_route_validation_surfaces():
    from velora.dashboard import HTML
    import inspect
    from velora.dashboard import Dashboard

    assert "walkbot_telemetry" in inspect.getsource(Dashboard.start)
    source = inspect.getsource(Dashboard.start)
    assert "outer.s.gsi.snapshot()" in source
    assert "outer.s.gsi.health()" in source
    assert HTML.count("<section id=walkbot") == 1
    assert "id=walkTelemetry" in HTML
    assert "api/routes/" in HTML and "function validateRoute" in HTML
    assert "routeValidation" in HTML
    assert "RECOVERY ACTIVE" in HTML
    assert "SERVER" in HTML and "PACKETS" in HTML


def test_dashboard_batch_view_visualizes_member_states_and_errors():
    from velora.dashboard import HTML

    assert "const members=(x.account_ids||[])" in HTML
    assert "stateClass(a.state)" in HTML
    assert "x.errors||[]" in HTML


def test_dashboard_kill_switch_recovery_is_explicit_and_visible():
    from velora.dashboard import HTML

    assert 'api/kill-switch/clear' in HTML
    assert 'id=clearKillBtn' in HTML
    assert 'id=panelClearKillBtn' in HTML
    assert 'RESUME AUTOMATION' in HTML
    assert "$('clearKillBtn').style.display=ks?'inline-block':'none'" in HTML
    assert "$('panelClearKillBtn').style.display=ks?'inline-block':'none'" in HTML


def test_dashboard_clear_kill_requires_confirmation():
    from velora.dashboard import HTML

    assert "function clearKill(){confirmAction('Resume Automation'" in HTML
