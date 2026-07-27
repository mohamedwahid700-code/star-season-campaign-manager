@echo off
REM ============================================================
REM  Star Season Campaign Manager - Windows build script
REM
REM  Run this FROM THE PROJECT ROOT, on Windows, with Python 3.13
REM  installed. It creates a virtual environment (if missing),
REM  installs dependencies, and builds the .exe with PyInstaller.
REM
REM  Usage (double-click, or from cmd.exe):
REM      packaging\build_windows.bat
REM
REM  Output:
REM      dist\Release\Star Season Campaign Manager.exe
REM ============================================================

setlocal

cd /d "%~dp0.."

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo Building executable with PyInstaller...
pyinstaller packaging\star_season_campaign_manager.spec --noconfirm

if exist "dist\Release\Star Season Campaign Manager.exe" (
    echo.
    echo ============================================================
    echo  Build complete.
    echo  Executable: dist\Release\Star Season Campaign Manager.exe
    echo ============================================================
) else (
    echo.
    echo Build finished, but the expected .exe was not found.
    echo Check the messages above for errors.
)

pause
