@echo off
setlocal EnableDelayedExpansion
title WhatsApp Poll Bot

echo.
echo  ==============================================
echo   WhatsApp Poll Bot - Launcher
echo  ==============================================
echo.

:: ── Change to the folder this script lives in ──────────────────────────────
cd /d "%~dp0"

:: ── Check Python ────────────────────────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [!] Python not found on this computer.
    echo.
    echo  Attempting to install Python automatically via winget...
    echo  (This requires Windows 10/11 and may take a few minutes)
    echo.
    winget install Python.Python.3.11 -e --silent --accept-package-agreements --accept-source-agreements
    if !errorlevel! neq 0 (
        echo.
        echo  [X] Automatic install failed.
        echo.
        echo  Please install Python manually:
        echo    1. Go to https://www.python.org/downloads/
        echo    2. Download and run the installer
        echo    3. IMPORTANT: check "Add Python to PATH" during install
        echo    4. Re-run this launcher
        echo.
        pause
        exit /b 1
    )
    echo.
    echo  Python installed. Please CLOSE and RE-RUN this launcher
    echo  so the new PATH settings take effect.
    echo.
    pause
    exit /b 0
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo  Python: %%i

:: ── Create virtual environment if it doesn't exist ──────────────────────────
if not exist "venv\" (
    echo.
    echo  Setting up virtual environment (first time only)...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo  [X] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: ── Activate venv ────────────────────────────────────────────────────────────
call venv\Scripts\activate.bat

:: ── Install / upgrade requirements ──────────────────────────────────────────
echo.
echo  Installing requirements...
pip install -q --upgrade pip
pip install -q -r requirements.txt
if %errorlevel% neq 0 (
    echo  [X] Failed to install requirements.
    pause
    exit /b 1
)

:: ── Install Playwright browser (Chromium) ────────────────────────────────────
echo.
echo  Checking browser installation...
echo  (First time: downloads Chromium ~300MB — this takes a few minutes)
playwright install chromium
if %errorlevel% neq 0 (
    echo  [X] Failed to install browser.
    pause
    exit /b 1
)

:: ── Launch the app ───────────────────────────────────────────────────────────
echo.
echo  ==============================================
echo   Starting WhatsApp Poll Bot...
echo   Your browser will open automatically.
echo   Keep this window open while the bot runs.
echo   Press Ctrl+C or close this window to stop.
echo  ==============================================
echo.

python app.py

echo.
echo  Bot stopped. Press any key to close.
pause >nul
