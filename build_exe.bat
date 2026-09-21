@echo off
setlocal EnableExtensions

title VELORA PANEL - EXE Builder

echo.
echo ==========================================
echo        VELORA PANEL - EXE BUILDER
echo ==========================================
echo.

where py >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python Launcher ^(py^) was not found.
    echo Install Python 3.12+ and enable the Python Launcher.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Creating virtual environment...
    py -3.12 -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo [1/5] Updating pip...
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto :error

echo [2/5] Installing VELORA PANEL...
.venv\Scripts\python.exe -m pip install -e .
if errorlevel 1 goto :error

echo [3/5] Installing PyInstaller...
.venv\Scripts\python.exe -m pip install --upgrade pyinstaller
if errorlevel 1 goto :error

echo [4/5] Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist VELORA_PANEL.spec del /q VELORA_PANEL.spec

echo [5/5] Building EXE...
.venv\Scripts\python.exe -m PyInstaller ^
    --clean ^
    --noconfirm ^
    --onefile ^
    --name VELORA_PANEL ^
    --paths src ^
    --collect-all velora ^
    src\velora\__main__.py

if errorlevel 1 goto :error

if not exist "dist\VELORA_PANEL.exe" (
    echo [ERROR] EXE was not created.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo              BUILD SUCCESS
echo ==========================================
echo.
echo EXE:
echo   dist\VELORA_PANEL.exe
echo.
echo Start it with:
echo   dist\VELORA_PANEL.exe
echo.
echo Data will be stored in:
echo   data\
echo.
pause
exit /b 0

:error
echo.
echo ==========================================
echo              BUILD FAILED
echo ==========================================
echo.
echo Check the error above.
pause
exit /b 1
