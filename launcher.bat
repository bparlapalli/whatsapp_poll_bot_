@echo off
setlocal EnableDelayedExpansion
title WhatsApp Poll Bot
cd /d "%~dp0"

set LOG=launcher_log.txt
echo WhatsApp Poll Bot - %date% %time% > %LOG%
echo Working dir: %CD% >> %LOG%

echo.
echo  ==============================================
echo   WhatsApp Poll Bot
echo  ==============================================
echo.

:: ── If venv already exists, skip all setup and just run ──────────────────────
if exist "venv\Scripts\activate.bat" (
    echo  Existing environment found, starting bot...
    echo Existing venv found, skipping setup >> %LOG%
    call "venv\Scripts\activate.bat"
    echo Launching app.py >> %LOG%
    python app.py
    echo app.py exited >> %LOG%
    echo.
    echo  Bot stopped. Press any key to close.
    pause >nul
    exit /b 0
)

:: ── First-time setup ─────────────────────────────────────────────────────────
echo  First time setup - this will take a few minutes...
echo First time setup >> %LOG%

:: Find Python
echo Searching for Python... >> %LOG%
set PYTHON=

python --version >nul 2>&1
if !errorlevel! equ 0 ( set PYTHON=python & goto :have_python )

py --version >nul 2>&1
if !errorlevel! equ 0 ( set PYTHON=py & goto :have_python )

for %%V in (313 312 311 310 39 38) do (
    if "!PYTHON!"=="" if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
        set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
        set "PATH=%LOCALAPPDATA%\Programs\Python\Python%%V;%LOCALAPPDATA%\Programs\Python\Python%%V\Scripts;!PATH!"
    )
    if "!PYTHON!"=="" if exist "%ProgramFiles%\Python%%V\python.exe" (
        set "PYTHON=%ProgramFiles%\Python%%V\python.exe"
    )
    if "!PYTHON!"=="" if exist "C:\Python%%V\python.exe" (
        set "PYTHON=C:\Python%%V\python.exe"
    )
)

if not "!PYTHON!"=="" goto :have_python

echo  Python not found. Installing via winget...
winget install Python.Python.3.11 -e --silent --accept-package-agreements --accept-source-agreements
py --version >nul 2>&1
if !errorlevel! equ 0 ( set PYTHON=py & goto :have_python )

echo ERROR: Could not find or install Python >> %LOG%
echo.
echo  [X] Python not found. Please install it from https://python.org/downloads/
echo      Make sure to tick "Add Python to PATH" during install.
echo.
pause
exit /b 1

:have_python
echo Found Python: !PYTHON! >> %LOG%
echo  Setting up virtual environment...
"!PYTHON!" -m venv venv >> %LOG% 2>&1
if !errorlevel! neq 0 (
    echo ERROR: venv failed >> %LOG%
    echo  [X] Failed to create virtual environment. Check launcher_log.txt.
    pause
    exit /b 1
)

call "venv\Scripts\activate.bat"

echo  Installing requirements (flask, playwright)...
echo Installing requirements... >> %LOG%
pip install -q -r requirements.txt >> %LOG% 2>&1
if !errorlevel! neq 0 (
    echo ERROR: pip install failed >> %LOG%
    echo  [X] Failed to install requirements. Check launcher_log.txt.
    pause
    exit /b 1
)

echo  Installing browser (Chromium, ~300MB)...
echo Installing playwright chromium... >> %LOG%
playwright install chromium >> %LOG% 2>&1
if !errorlevel! neq 0 (
    echo ERROR: playwright install failed >> %LOG%
    echo  [X] Failed to install browser. Check launcher_log.txt.
    pause
    exit /b 1
)

echo Setup complete >> %LOG%
echo.
echo  Setup complete!

:: ── Launch ───────────────────────────────────────────────────────────────────
echo.
echo  ==============================================
echo   Starting WhatsApp Poll Bot...
echo   Your browser opens at http://localhost:5050
echo   Keep this window open while the bot runs.
echo   Press Ctrl+C or close this window to stop.
echo  ==============================================
echo.
echo Launching app.py >> %LOG%
python app.py
echo app.py exited >> %LOG%

echo.
echo  Bot stopped. Press any key to close.
pause >nul
