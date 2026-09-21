$ErrorActionPreference="Stop"
if (!(Test-Path ".venv\Scripts\python.exe")) { py -3.12 -m venv .venv }
& ".venv\Scripts\python.exe" -m pip install -e ".[dev]"
& ".venv\Scripts\python.exe" -m velora
