@echo off
setlocal EnableExtensions
cd /d "%~dp0"

title VELORA PANEL - BUILD EXE
echo.
echo ==========================================
echo        VELORA PANEL - EXE BUILDER
echo ==========================================
echo.
echo This file BUILDS an EXE.
echo Do NOT use run.bat for this.
echo.

where py >nul 2>&1
if errorlevel 1 goto :python_error

echo [1/7] Python:
py -3 -c "import sys; print(sys.version)" || goto :error

echo [2/7] Creating virtual environment...
if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv ".venv"
    if errorlevel 1 goto :error
)

echo [3/7] Installing project...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :error
".venv\Scripts\python.exe" -m pip install -e ".[dev]"
if errorlevel 1 goto :error

echo [4/7] Running tests...
powershell -NoProfile -ExecutionPolicy Bypass -Command "& { & \".venv\\Scripts\\python.exe\" -m pytest -vv -ra -o faulthandler_timeout=30 2>&1 | Tee-Object -FilePath \"pytest-build.log\"; exit $LASTEXITCODE }"
if errorlevel 1 goto :tests_error

echo [5/7] Installing PyInstaller...
".venv\Scripts\python.exe" -m pip install --upgrade pyinstaller
if errorlevel 1 goto :error

echo [6/7] Building EXE...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "VELORA_PANEL.spec" del /q "VELORA_PANEL.spec"

".venv\Scripts\python.exe" -m PyInstaller ^
  --clean ^
  --noconfirm ^
  --onefile ^
  --console ^
  --name "VELORA_PANEL" ^
  --paths "src" ^
  --collect-submodules "velora" ^
  "src\velora\__main__.py" > "build_exe.log" 2>&1

if errorlevel 1 (
    type "build_exe.log"
    goto :error
)

if not exist "dist\VELORA_PANEL.exe" (
    echo.
    echo [ERROR] PyInstaller finished but EXE was not created.
    type "build_exe.log"
    goto :error
)

echo [7/7] Build verification...
for %%F in ("dist\VELORA_PANEL.exe") do echo EXE size: %%~zF bytes

echo.
echo ==========================================
echo             BUILD SUCCESSFUL
echo ==========================================
echo.
echo EXE:
echo %CD%\dist\VELORA_PANEL.exe
echo.
echo Full PyInstaller log:
echo %CD%\build_exe.log
echo.
echo IMPORTANT: the EXE is now in the dist folder.
echo.
pause
exit /b 0

:python_error
echo.
echo [ERROR] Python Launcher "py" was not found.
echo Install Python 3.12+ and enable the Python Launcher.
echo.
pause
exit /b 1

:tests_error
echo.
echo [ERROR] Tests failed. EXE build was stopped.
echo Fix the failing tests first.
echo.
pause
exit /b 1

:error
echo.
echo ==========================================
echo               BUILD FAILED
echo ==========================================
echo.
echo Read build_exe.log if it exists.
echo.
pause
exit /b 1
