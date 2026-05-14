"""
WhatsApp Poll Bot — Config Loader  (app_v2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reads settings from config.json in this directory.
Exposes the same module-level names as the original config.py so
bot.py can do `import config` without any changes.

config.json is written by the Flask UI (app.py) whenever the user
saves settings from the browser.
"""

import json
from pathlib import Path

_CONFIG_FILE = Path(__file__).parent / "config.json"

_DEFAULTS: dict = {
    "TARGET_GROUP":        "",
    "POLL_CHECK_INTERVAL": 30,
    "VOTE_OPTION_INDEX":   0,
    "HEADLESS":            False,
    "QR_TIMEOUT_SECONDS":  120,
}


def _load() -> dict:
    if _CONFIG_FILE.exists():
        try:
            return {**_DEFAULTS, **json.loads(_CONFIG_FILE.read_text())}
        except Exception:
            pass
    return _DEFAULTS.copy()


_data = _load()

# ── Public API (same names as original config.py) ───────────────────────────
TARGET_GROUP:        str  = _data["TARGET_GROUP"]
POLL_CHECK_INTERVAL: int  = _data["POLL_CHECK_INTERVAL"]
VOTE_OPTION_INDEX:   int  = _data["VOTE_OPTION_INDEX"]
HEADLESS:            bool = _data["HEADLESS"]
QR_TIMEOUT_SECONDS:  int  = _data["QR_TIMEOUT_SECONDS"]

# Session directory is always relative to this file, not the cwd.
SESSION_DIR: str = str(Path(__file__).parent / "whatsapp_session")
