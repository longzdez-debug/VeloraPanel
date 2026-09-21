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
