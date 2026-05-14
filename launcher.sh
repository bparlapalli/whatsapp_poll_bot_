#!/bin/bash
# WhatsApp Poll Bot — Launcher (macOS / Linux)
# Double-click in Finder or run: bash launcher.sh

set -e

# ── Change to the directory this script lives in ──────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo " =============================================="
echo "  WhatsApp Poll Bot - Launcher"
echo " =============================================="
echo ""

# ── Check Python ────────────────────────────────────────────────────────────
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" --version 2>&1)
        echo " Python: $VER"
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo " [!] Python not found."
    echo ""

    # Try Homebrew on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &>/dev/null; then
            echo " Installing Python via Homebrew..."
            brew install python3
            PYTHON="python3"
        else
            echo " Homebrew not found. Installing Homebrew first..."
            echo " (You may be asked for your Mac password)"
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            # Add Homebrew to path for Apple Silicon
            if [ -f "/opt/homebrew/bin/brew" ]; then
                eval "$(/opt/homebrew/bin/brew shellenv)"
            fi
            brew install python3
            PYTHON="python3"
        fi
    else
        echo " Please install Python 3 from https://www.python.org/downloads/"
        echo " Then run this script again."
        read -p " Press Enter to exit..."
        exit 1
    fi
fi

# ── Create virtual environment ────────────────────────────────────────────────
if [ ! -d "venv" ]; then
    echo ""
    echo " Setting up virtual environment (first time only)..."
    $PYTHON -m venv venv
fi

# ── Activate ──────────────────────────────────────────────────────────────────
source venv/bin/activate

# ── Install requirements ───────────────────────────────────────────────────────
echo ""
echo " Installing requirements..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# ── Install Playwright browser ────────────────────────────────────────────────
echo ""
echo " Checking browser installation..."
echo " (First time: downloads Chromium ~300MB)"
playwright install chromium

# ── Launch app ────────────────────────────────────────────────────────────────
echo ""
echo " =============================================="
echo "  Starting WhatsApp Poll Bot..."
echo "  Your browser will open automatically."
echo "  Keep this window open while the bot runs."
echo "  Press Ctrl+C to stop."
echo " =============================================="
echo ""

python app.py
