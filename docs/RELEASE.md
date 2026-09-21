# VELORA release checklist

## Runtime
1. Python 3.12+ installed.
2. Run run.bat.
3. Tests must pass.
4. Dashboard must answer on 127.0.0.1:8765.
5. GSI must answer on 127.0.0.1:27100.

## WalkBot
WalkBot is integrated into the supervisor and FSM. The default adapter is NullInput. WindowsInput is available behind an explicit enabled flag and always releases held keys on stop.

## Production work
Real map waypoint data, route authoring, account credentials/mafiles, Steam launching, CS2 process ownership, and replay fixtures are intentionally configuration/integration layers rather than fake hardcoded data. No credentials are committed.
