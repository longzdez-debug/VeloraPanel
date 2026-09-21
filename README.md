# VeloraPanel

VeloraPanel is the consolidated successor of VELORAP. The project is built around a hierarchical, event-driven FSM and explicit separation between telemetry, game-state normalization, orchestration, navigation, movement, recovery, and process supervision.

## Architecture

```
GSI -> GameState -> Supervisor FSM
                    ├─ Account FSM
                    ├─ Match FSM
                    └─ WalkBot FSM
                         ├─ Navigation
                         ├─ Pathfinding
                         ├─ Movement
                         ├─ Recovery
                         └─ Telemetry
```

The implementation is intentionally independent rather than copying source from third-party projects.

## Run

```powershell
python -m pip install -e ".[dev]"
pytest
```
