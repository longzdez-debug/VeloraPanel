# VELORA PANEL

Windows-first CS2 orchestration panel built around explicit FSMs, GSI, account supervision and an integrated WalkBot.

## Quick start
- Python 3.12+
- Windows 10/11
- Run `run.bat` or `run.ps1`
- Open `http://127.0.0.1:8765`
- Copy `config/gamestate_integration_velora.cfg` into the CS2 cfg folder and set the same GSI token in `VELORA_GSI_TOKEN`.

The default input adapter is safe/no-op. Real Windows W/A/S/D input is opt-in through `VELORA_INPUT_ENABLED=true` and is additionally gated to the owned CS2 process being foreground. The panel never stores Steam passwords or session secrets.

## Controls
- Dashboard: account start/stop, WalkBot kill, global emergency stop and kill-switch clear.
- Route editor: create waypoints, connect/delete nodes and persist maps.
- Diagnostics: runtime, Steam/CS2 discovery, data directory and configured endpoints.
- WalkBot: GSI timeout, dead-player release, process-death release and bounded recovery.

## Test
`.venv\\Scripts\\python.exe -m pytest`
