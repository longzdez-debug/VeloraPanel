@echo off
setlocal EnableExtensions
cd /d "%~dp0"

title VELORA PANEL - EXE BUILDER
echo.
echo ==========================================
echo        VELORA PANEL - EXE BUILDER
echo ==========================================
echo.

where py >nul 2>&1
if errorlevel 1 goto :python_error

echo [1/6] Checking Python...
py -3 -c "import sys; print(sys.version)" || goto :python_error

if not exist ".venv\Scripts\python.exe" (
    echo [2/6] Creating virtual environment...
    py -3 -m venv .venv
    if errorlevel 1 goto :error
) else (
    echo [2/6] Virtual environment already exists.
)

echo [3/6] Updating pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :error

echo [4/6] Installing VELORA...
".venv\Scripts\python.exe" -m pip install -e .
if errorlevel 1 goto :error

echo [5/6] Installing PyInstaller...
".venv\Scripts\python.exe" -m pip install --upgrade pyinstaller
if errorlevel 1 goto :error

echo [6/6] Building VELORA_PANEL.exe...
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
    "src\velora\__main__.py"

if errorlevel 1 goto :error

if not exist "dist\VELORA_PANEL.exe" (
    echo [ERROR] dist\VELORA_PANEL.exe was not created.
    goto :error
)

echo.
echo ==========================================
echo          BUILD COMPLETED SUCCESSFULLY
echo ==========================================
echo.
echo File:
echo "%~dp0dist\VELORA_PANEL.exe"
echo.
echo IMPORTANT:
echo Run the EXE from the project folder so the
echo "data" folder is created next to it.
echo.
echo To test it:
echo "%~dp0dist\VELORA_PANEL.exe"
echo.
pause
exit /b 0

:python_error
echo.
echo [ERROR] Python 3.x / Python Launcher was not found.
echo Install Python 3.12+ and make sure "py" works in CMD.
echo.
pause
exit /b 1

:error
echo.
echo ==========================================
echo              BUILD FAILED
echo ==========================================
echo.
echo The error above is the actual build error.
echo.
pause
exit /b 1
