"""
bot_runner.py — Subprocess entry point for the Flask UI.

Flask spawns:  python bot_runner.py
This script imports and runs the async bot, with all output
going to stdout so Flask can pipe and stream it to the browser.
"""

import asyncio
import sys
from pathlib import Path

# Make sure imports resolve from this directory regardless of cwd
sys.path.insert(0, str(Path(__file__).parent))

from bot import run_bot

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("Bot stopped.")
        sys.exit(0)
