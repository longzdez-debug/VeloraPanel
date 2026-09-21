# VELORA PANEL

Windows-first CS2 orchestration panel built around explicit FSMs, GSI, account supervision and an integrated WalkBot.

## Quick start
- Python 3.12+
- Windows 10/11
- Run `run.bat` or `run.ps1`
- Open `http://127.0.0.1:8765`

The default input adapter is safe/no-op and does not inject keyboard input. WalkBot, GSI, route graph and recovery can be developed and tested without touching the game.

## Test
`.venv\\Scripts\\python.exe -m pytest`
