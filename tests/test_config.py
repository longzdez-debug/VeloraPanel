def test_walkbot_input_is_enabled_by_default(monkeypatch):
    from velora.config import Config

    monkeypatch.delenv("VELORA_INPUT_ENABLED", raising=False)
    assert Config.from_env().input_enabled is True


def test_walkbot_input_can_be_disabled(monkeypatch):
    from velora.config import Config

    monkeypatch.setenv("VELORA_INPUT_ENABLED", "false")
    assert Config.from_env().input_enabled is False
