@echo off
setlocal
where py >nul 2>&1
if errorlevel 1 (echo Python launcher not found.&pause&exit /b 1)
if not exist .venv\Scripts\python.exe py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
if errorlevel 1 (echo Install failed.&pause&exit /b 1)
.venv\Scripts\python.exe -m pytest
if errorlevel 1 (echo Tests failed.&pause&exit /b 1)
.venv\Scripts\python.exe -m velora
