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

:: ── Find Python ──────────────────────────────────────────────────────────────
:: Try 'python', then 'py' (Windows launcher), then common install locations
set PYTHON=

python --version >nul 2>&1
if %errorlevel% equ 0 ( set PYTHON=python & goto :python_found )

py --version >nul 2>&1
if %errorlevel% equ 0 ( set PYTHON=py & goto :python_found )

:: Search common install locations (handles "installed but not in PATH")
:: Accepts any Python 3.8 or newer — no forced reinstall
for %%D in (
    "%LOCALAPPDATA%\Programs\Python\Python313"
    "%LOCALAPPDATA%\Programs\Python\Python312"
    "%LOCALAPPDATA%\Programs\Python\Python311"
    "%LOCALAPPDATA%\Programs\Python\Python310"
    "%LOCALAPPDATA%\Programs\Python\Python39"
    "%LOCALAPPDATA%\Programs\Python\Python38"
    "%ProgramFiles%\Python313"
    "%ProgramFiles%\Python312"
    "%ProgramFiles%\Python311"
    "%ProgramFiles%\Python310"
    "%ProgramFiles%\Python39"
    "%ProgramFiles(x86)%\Python313"
    "%ProgramFiles(x86)%\Python312"
    "%ProgramFiles(x86)%\Python311"
    "%ProgramFiles(x86)%\Python310"
    "C:\Python313"
    "C:\Python312"
    "C:\Python311"
    "C:\Python310"
    "C:\Python39"
    "C:\Python38"
) do (
    if exist "%%~D\python.exe" (
        set PYTHON=%%~D\python.exe
        set PATH=%%~D;%%~D\Scripts;!PATH!
        goto :python_found
    )
)

:: Absolute last resort: try winget (only if nothing above found it)
echo  [!] Python not found in any standard location.
echo  Attempting a fresh install via winget...
echo.
winget install Python.Python.3.11 -e --silent --accept-package-agreements --accept-source-agreements >nul 2>&1

:: After winget, try py launcher (winget registers it)
py --version >nul 2>&1
if %errorlevel% equ 0 ( set PYTHON=py & goto :python_found )

echo.
echo  [X] Could not find or install Python automatically.
echo.
echo  Please install Python manually:
echo    1. Go to https://www.python.org/downloads/
echo    2. Click "Download Python 3.x.x"
echo    3. Run the installer
echo    4. IMPORTANT: on the first screen, check "Add Python to PATH"
echo    5. Re-run this launcher
echo.
pause
exit /b 1

:python_found
for /f "tokens=*" %%i in ('"%PYTHON%" --version 2^>^&1') do echo  Python: %%i

:: ── Create virtual environment if it doesn't exist ──────────────────────────
if not exist "venv\" (
    echo.
    echo  Setting up virtual environment (first time only)...
    "%PYTHON%" -m venv venv
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
:: (venv is active at this point so 'python' always resolves correctly)

echo.
echo  Bot stopped. Press any key to close.
pause >nul
