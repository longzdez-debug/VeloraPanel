# Getting started

1. Install Python 3.12+ on Windows.
2. Run `run.bat` or `run.ps1`.
3. Open `http://127.0.0.1:8765`.
4. Copy `config/gamestate_integration_velora.cfg` to the CS2 cfg folder.
5. Set `VELORA_GSI_TOKEN` to the same token as the GSI config.
6. Leave `VELORA_INPUT_ENABLED=false` for initial validation.
7. Create/edit a route in the dashboard and verify GSI telemetry before enabling OS input.
8. If enabling input, keep `VELORA_INPUT_REQUIRE_FOREGROUND=true`; the adapter releases keys whenever the owned CS2 process is not the foreground application.

The panel uses a localhost dashboard by default. Do not bind the unauthenticated control API to a public/LAN interface.
