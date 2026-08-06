#!/usr/bin/env python3
"""
antigravity-wait.py  —  stable event-poller that wakes Gemini (Antigravity).

Replaces the per-conversation wait_for_powernote.py. Runs locally (no LLM /
token cost), polls powerNote every 2s, and does THREE things:

  1. Heartbeat  -> POST /api/agent/heartbeat {agent:"gemini"} every cycle so the
     app's 🤝 status dot shows Gemini ONLINE (== this poller is alive == Antigravity
     is ready to take work). When Antigravity is mid-task the poller has exited, so
     the dot may briefly go gray — that is expected.
  2. Chat/voice -> drains the active section's inbox (agent=gemini) + latest voice,
     same as the old poller.
  3. Delegated tasks -> checks /api/gemini/tasks?status=pending. These come from
     Claude's `delegate_to_gemini` MCP tool.

On ANY new input (message / voice / pending task) it prints one JSON object and
exits 0. That exit is the EVENT that wakes the Antigravity agent. See GEMINI.md
section 4 for what the agent must do on wake (esp. handling gemini_tasks:
claim -> do the work with file access + coding -> POST the result -> relaunch me).
"""
import urllib.request
import json
import time
import os
import sys
import subprocess

BASE = "http://127.0.0.1:4321"
SCRATCH_DIR = os.path.dirname(os.path.abspath(__file__))
TS_FILE = os.path.join(SCRATCH_DIR, ".last_voice_ts.txt")
APPROVE_SCRIPT = os.path.join(SCRATCH_DIR, "antigravity-approve.sh")
APPROVE_LOG = os.path.join(SCRATCH_DIR, ".antigravity-approve.log")


def ensure_approve_watcher():
    """Antigravity relaunches this file every wake cycle, so this must be
    idempotent — only start the watcher if one isn't already running,
    otherwise every relaunch would pile up another dbus-monitor chain."""
    try:
        already = subprocess.run(["pgrep", "-f", APPROVE_SCRIPT], capture_output=True).returncode == 0
        if not already:
            with open(APPROVE_LOG, "a") as log:
                subprocess.Popen(
                    ["bash", APPROVE_SCRIPT],
                    stdout=log, stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
    except Exception:
        pass


ensure_approve_watcher()


def get(path):
    return json.loads(urllib.request.urlopen(f"{BASE}{path}", timeout=10).read())


def post(path, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}{path}", data=data,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        return json.loads(urllib.request.urlopen(req, timeout=10).read())
    except Exception:
        return None


last_ts = 0
if os.path.exists(TS_FILE):
    try:
        with open(TS_FILE, "r") as f:
            last_ts = int(f.read().strip())
    except Exception:
        pass

while True:
    try:
        # 1. Heartbeat — keep the online dot green while we wait.
        post("/api/agent/heartbeat", {"agent": "gemini"})

        # 2. Pending delegated tasks from Claude (the token-saving handoff).
        tasks_res = get("/api/gemini/tasks?status=pending")
        pending = tasks_res.get("tasks", []) if isinstance(tasks_res, dict) else []

        # 3. Chat inbox (active section) + voice, same as before.
        state_res = get("/api/state")
        active_sec = state_res.get("activeSection", "main")
        inbox_res = get(f"/api/inbox?section={active_sec}&drain=true&agent=gemini")
        inbox_items = inbox_res.get("items", [])
        voice_res = get("/api/voice/latest?consume=true&agent=gemini")

        new_voice = None
        if voice_res and "ts" in voice_res and voice_res["ts"] > last_ts:
            new_voice = voice_res["text"]
            with open(TS_FILE, "w") as f:
                f.write(str(voice_res["ts"]))

        messages = [item["text"] for item in inbox_items if item.get("text")]

        # Any new input? Emit it and exit(0) to WAKE the Antigravity agent.
        if messages or new_voice or pending:
            output = {
                "messages": messages,
                "voice": new_voice,
                "section": active_sec,
                "gemini_tasks": pending,  # [{id, task:{requirement,...}}, ...] — claim + do + POST result
            }
            print(json.dumps(output, ensure_ascii=False))
            sys.exit(0)

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    time.sleep(0.4)
