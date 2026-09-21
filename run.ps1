$ErrorActionPreference="Stop"
if (!(Get-Command py -ErrorAction SilentlyContinue)) { throw "Python launcher not found" }
if (!(Test-Path ".venv\Scripts\python.exe")) { py -3 -m venv .venv }
& ".venv\Scripts\python.exe" -m pip install -e ".[dev]"
& ".venv\Scripts\python.exe" -m pytest
& ".venv\Scripts\python.exe" -m velora
