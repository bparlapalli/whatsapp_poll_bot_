"""
WhatsApp Poll Bot — Flask Web UI  (app_v2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Run:  python app.py
      → opens http://localhost:5050 in your browser automatically.

Routes
------
GET  /                  Main UI page
POST /save-config       Save group name + settings to config.json
POST /start             Launch bot subprocess
POST /stop              Terminate bot subprocess
GET  /status            JSON: { running, has_session }
GET  /logs              Server-Sent Events stream of bot log lines
POST /clear-session     Delete saved WhatsApp session (forces new QR scan)
"""

import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

from flask import Flask, Response, jsonify, redirect, render_template, request, url_for

# ── Paths ────────────────────────────────────────────────────────────────────
APP_DIR     = Path(__file__).parent
CONFIG_FILE = APP_DIR / "config.json"
SESSION_DIR = APP_DIR / "whatsapp_session"

# ── Config defaults ───────────────────────────────────────────────────────────
DEFAULTS: dict = {
    "TARGET_GROUP":        "",
    "POLL_CHECK_INTERVAL": 30,
    "VOTE_OPTION_INDEX":   0,
}

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)

# ── Bot process state ─────────────────────────────────────────────────────────
_bot_proc: subprocess.Popen | None = None
_log_q:    queue.Queue              = queue.Queue(maxsize=2000)
_bot_lock: threading.Lock           = threading.Lock()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return {**DEFAULTS, **json.loads(CONFIG_FILE.read_text())}
        except Exception:
            pass
    return DEFAULTS.copy()


def _save_config(updates: dict) -> dict:
    cfg = _load_config()
    cfg.update(updates)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
    return cfg


def _has_session() -> bool:
    """True if a WhatsApp session has already been saved (QR already scanned)."""
    if not SESSION_DIR.exists():
        return False
    # Playwright creates a 'Default' subfolder with profile data
    return any(SESSION_DIR.iterdir())


def _is_running() -> bool:
    return _bot_proc is not None and _bot_proc.poll() is None


def _drain_queue() -> None:
    while not _log_q.empty():
        try:
            _log_q.get_nowait()
        except queue.Empty:
            break


def _reader_thread(proc: subprocess.Popen) -> None:
    """Reads bot stdout line by line and pushes to the log queue."""
    for raw in iter(proc.stdout.readline, b""):
        line = raw.decode("utf-8", errors="replace").rstrip()
        if line:
            _log_q.put(line)
    _log_q.put("__STOPPED__")


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    cfg = _load_config()
    return render_template(
        "index.html",
        config=cfg,
        is_running=_is_running(),
        has_session=_has_session(),
    )


@app.route("/save-config", methods=["POST"])
def save_config_route():
    _save_config({
        "TARGET_GROUP":        request.form.get("group_name", "").strip(),
        "POLL_CHECK_INTERVAL": int(request.form.get("interval", 30)),
        "VOTE_OPTION_INDEX":   int(request.form.get("vote_option", 0)),
    })
    return redirect(url_for("index"))


@app.route("/start", methods=["POST"])
def start_bot():
    global _bot_proc
    with _bot_lock:
        if _is_running():
            return jsonify(status="already_running")

        cfg = _load_config()
        if not cfg.get("TARGET_GROUP"):
            return jsonify(status="error", message="Group name is not set. Please save your settings first.")

        needs_qr = not _has_session()
        _save_config({"HEADLESS": not needs_qr})

        _drain_queue()

        _bot_proc = subprocess.Popen(
            [sys.executable, str(APP_DIR / "bot_runner.py")],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,   # merge stderr → stdout
            cwd=str(APP_DIR),
            env={**os.environ, "PYTHONUNBUFFERED": "1"},  # no output buffering
        )
        threading.Thread(target=_reader_thread, args=(_bot_proc,), daemon=True).start()

        return jsonify(status="started", needs_qr=needs_qr)


@app.route("/stop", methods=["POST"])
def stop_bot():
    global _bot_proc
    with _bot_lock:
        if _bot_proc and _bot_proc.poll() is None:
            _bot_proc.terminate()
            try:
                _bot_proc.wait(timeout=6)
            except subprocess.TimeoutExpired:
                _bot_proc.kill()
        return jsonify(status="stopped")


@app.route("/status")
def status():
    return jsonify(running=_is_running(), has_session=_has_session())


@app.route("/logs")
def logs():
    """
    Server-Sent Events endpoint.
    Each event: data: <log line>\\n\\n
    Special tokens:  __STOPPED__  __HEARTBEAT__
    """
    def generate():
        while True:
            try:
                line = _log_q.get(timeout=20)
                yield f"data: {line}\n\n"
                if line == "__STOPPED__":
                    break
            except queue.Empty:
                yield "data: __HEARTBEAT__\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering": "no",   # disable nginx buffering if behind proxy
        },
    )


@app.route("/clear-session", methods=["POST"])
def clear_session():
    """Delete the saved WhatsApp session so the user can re-scan the QR code."""
    if _is_running():
        return jsonify(status="error", message="Stop the bot before clearing the session.")
    if SESSION_DIR.exists():
        shutil.rmtree(SESSION_DIR)
    return jsonify(status="ok")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print()
    print("  🏏  WhatsApp Poll Bot — Web UI")
    print("  ─────────────────────────────")
    print("  Opening http://localhost:5050 ...")
    print("  Keep this window open while the bot runs.")
    print("  Press Ctrl+C to shut everything down.")
    print()
    # Open browser after Flask has had a moment to start
    threading.Timer(1.5, lambda: webbrowser.open("http://localhost:5050")).start()
    app.run(host="127.0.0.1", port=5050, debug=False, threaded=True)
