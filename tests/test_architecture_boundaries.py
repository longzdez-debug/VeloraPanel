from pathlib import Path


FORBIDDEN = (
    "ReadProcessMemory",
    "WriteProcessMemory",
    "OpenProcess",
    "CreateRemoteThread",
    "LoadLibrary",
    "ManualMap",
    "manual map",
    "detour",
    "pattern scan",
    "pattern_scan",
    "entity list",
    "entity_list",
)


def test_walkbot_source_keeps_external_only_safety_boundary():
    root = Path(__file__).parents[1] / "src" / "velora"
    offenders = []
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for token in FORBIDDEN:
            if token.lower() in text:
                offenders.append(f"{path.name}: {token}")
    assert not offenders, "\n".join(offenders)


def test_decision_engine_does_not_depend_on_input_layer():
    source = (root := Path(__file__).parents[1] / "src" / "velora" / "decision.py").read_text(encoding="utf-8")
    assert "ExternalInput" not in source
    assert "MovementController" not in source
    assert ".move(" not in source
    assert ".release_all(" not in source


def test_only_movement_controller_crosses_into_external_input():
    root = Path(__file__).parents[1] / "src" / "velora"
    offenders = []
    for path in root.glob("*.py"):
        if path.name in {"movement_controller.py", "external_input.py"}:
            continue
        source = path.read_text(encoding="utf-8")
        if "ExternalInput" in source and path.name not in {"walkbot.py"}:
            offenders.append(path.name)
    assert not offenders, offenders


def test_observation_freshness_boundaries():
    from velora.world import ObservationValue
    assert ObservationValue("x", 8.0, "test", 1.0).fresh(now=9.0, max_age=3.0)
    assert not ObservationValue("x", 10.0, "test", 1.0).fresh(now=9.0, max_age=3.0)
    assert not ObservationValue(None, 1.0, "test", 1.0).fresh(now=1.0, max_age=3.0)
