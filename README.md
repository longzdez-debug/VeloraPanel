# VELORA PANEL

Windows-first CS2 orchestration panel built around explicit FSMs, GSI, account supervision and an integrated WalkBot.

## Quick start
- Python 3.12+
- Windows 10/11
- Run `run.bat` or `run.ps1`
- Open `http://127.0.0.1:8765`
- Copy `config/gamestate_integration_velora.cfg` into the CS2 cfg folder and set the same GSI token in `VELORA_GSI_TOKEN`.

WalkBot input is enabled by default and remains safety-gated to the owned/attached CS2 process being foreground. Set `VELORA_INPUT_ENABLED=false` to force a no-input/headless mode. Keyboard movement uses W/A/S/D and steering is driven from the GSI forward vector. The panel never stores Steam passwords or session secrets.

## Controls
- Dashboard: account start/stop, WalkBot kill, global emergency stop and kill-switch clear.
- Route editor: create waypoints, connect/delete nodes and persist maps.
- Diagnostics: runtime, Steam/CS2 discovery, data directory and configured endpoints.
- WalkBot: GSI timeout, dead-player release, process-death release, bounded recovery, keyboard movement and steering.

## Test
`.venv\\Scripts\\python.exe -m pytest`

The repository also has a Windows GitHub Actions workflow that runs compile checks, Ruff, the full pytest suite and an EXE build on pushes to main.
