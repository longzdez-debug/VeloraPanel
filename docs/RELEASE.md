# VELORA PANEL release checklist

## Runtime
1. Windows 10/11 and Python 3.12+.
2. Install dependencies with `python -m pip install -e .`.
3. Copy `.env.example` to `.env` and set a private GSI token.
4. Run `run.bat` or `run.ps1`.
5. Open the local dashboard at `http://127.0.0.1:8765`.
6. Install `config/gamestate_integration_velora.cfg` into the CS2 cfg directory and use the same token.
7. Verify Diagnostics reports Steam/CS2 discovery and the GSI endpoint.
8. Keep `VELORA_INPUT_ENABLED=false` until the route and FSM have been verified.

## Runtime safety
- Dashboard binds to localhost by default.
- Windows input is disabled by default.
- Foreground ownership is required by default.
- Only a process matching PID, creation time, executable path and command line is treated as owned.
- GSI timeout, process death, startup-readiness timeout, WalkBot faults and emergency stop release input.
- Watchdog restarts are bounded and exponentially backed off.
- Steam passwords, mafiles and session secrets are never stored by the panel.

## Functional layers
- Account FSM: offline/start/ready/menu/queue/in-match/stop/error.
- Match tracker: live, round-over, halftime, game-over and arbitrary round numbers.
- GSI: authenticated, duplicate-suppressed snapshots with player/map/round/position/orientation data.
- Routes: persistent map-aware waypoint graphs and pathfinding.
- WalkBot: navigation, arrival, stuck detection, bounded recovery and replanning.
- Scheduler: priority, concurrency, cooldown and retry/backoff primitives.
- Dashboard: account control, kill switch, diagnostics and route editor.

## Important integration boundary
VELORA does not pretend to know a game's internal state when GSI does not provide enough context. A process being alive is not the same as CS2 being ready, and a generic `playing` activity without map/round context does not by itself authorize WalkBot navigation.

## Final verification
Before enabling real Windows input, run the automated tests and perform a manual dry run with NullInput. Then enable foreground-gated input only on a controlled account and route.
