"""Global push-to-talk for Powerfull Note.

Hold Alt+P anywhere on the system to talk to the "main" chat section.

Two modes (set PTT_MODE below):
  "webspeech" — briefly steals foreground focus to the Powerfull Note browser
                window so the page can use the fast, in-browser Web Speech API,
                then restores focus to whatever window you were using. Fast,
                but momentarily interrupts whatever has focus (games, other
                apps) and needs that browser tab open somewhere.
  "record"    — records straight from the mic via ffmpeg, no window/tab
                needed at all, transcribes via local Whisper. Slower, but
                fully invisible — never touches window focus.

Requires: pip install keyboard requests pywin32
Requires: ffmpeg on PATH (only used by "record" mode).

Run: python global_ptt.py   (or via ptt-listen.cmd)
"""
import os
import subprocess
import tempfile
import threading
import time

import keyboard
import requests
import win32api
import win32con
import win32gui
import win32process

SERVER = "http://localhost:4321"
SECTION = "main"
LANG = "th"
MIC_DEVICE = "Microphone (Realtek(R) Audio)"  # from: ffmpeg -list_devices true -f dshow -i dummy
BROWSER_WINDOW_TITLE_HINT = "Powerfull Note"  # substring of the page <title>
PTT_MODE = "webspeech"  # "webspeech" or "record"

state_lock = threading.Lock()
is_active = False

# --- "record" mode state (local ffmpeg + Whisper) ---
recording_proc = None
audio_path = None

# --- "webspeech" mode state (focus-steal) ---
prev_hwnd = None
browser_hwnd = None


def set_server_ptt_state(active: bool, mode: str):
    try:
        requests.post(f"{SERVER}/api/ptt", json={"active": active, "mode": mode}, timeout=3)
    except Exception:
        pass  # server may be down — glow just won't show


def set_agent_listener(agent: str):
    try:
        requests.post(f"{SERVER}/api/agent-listener", json={"section": SECTION, "agentListener": agent}, timeout=3)
    except Exception:
        pass


def toggle_tts_mute():
    try:
        requests.post(f"{SERVER}/api/tts/toggle", timeout=3)
        print("[PTT] TTS mute toggled")
    except Exception as e:
        print(f"[PTT] TTS toggle failed: {e}")


# ---------------------------------------------------------------------------
# "record" mode — local ffmpeg capture + server-side Whisper
# ---------------------------------------------------------------------------
def start_recording():
    global recording_proc, audio_path
    audio_path = os.path.join(tempfile.gettempdir(), f"ptt_{int(time.time() * 1000)}.wav")
    try:
        recording_proc = subprocess.Popen(
            ["ffmpeg", "-y", "-f", "dshow", "-i", f"audio={MIC_DEVICE}", "-ac", "1", "-ar", "16000", audio_path],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"[PTT] ffmpeg failed to start: {e}")
        return
    print("[PTT] recording…")
    set_server_ptt_state(True, "record")


def stop_recording_and_send():
    global recording_proc, audio_path
    proc, path = recording_proc, audio_path
    recording_proc, audio_path = None, None
    set_server_ptt_state(False, "record")
    if proc is None:
        return
    try:
        proc.communicate(input=b"q", timeout=5)
    except Exception:
        try:
            proc.terminate()
        except Exception:
            pass
    print("[PTT] transcribing…")
    threading.Thread(target=transcribe_and_send, args=(path,), daemon=True).start()


def transcribe_and_send(path):
    try:
        if not os.path.exists(path) or os.path.getsize(path) < 1000:
            print("[PTT] recording too short, skipped")
            return
        with open(path, "rb") as f:
            data = f.read()
        r = requests.post(
            f"{SERVER}/api/transcribe-local?lang={LANG}",
            data=data, headers={"Content-Type": "audio/wav"}, stream=True, timeout=60,
        )
        r.raise_for_status()
        parts = [line.strip() for line in r.iter_lines(decode_unicode=True) if line and line.strip()]
        text = " ".join(parts).strip()
        if not text:
            print("[PTT] empty transcript")
            return
        requests.post(f"{SERVER}/api/chat", json={"role": "user", "text": text, "section": SECTION}, timeout=5)
        requests.post(f"{SERVER}/api/inbox", json={"text": text, "section": SECTION}, timeout=5)
        requests.post(f"{SERVER}/api/voice", json={"text": text}, timeout=5)
        print(f"[PTT] sent: {text}")
    except Exception as e:
        print(f"[PTT] error: {e}")
    finally:
        try:
            os.remove(path)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# "webspeech" mode — steal foreground focus to the browser tab, let its own
# Web Speech API do the listening, then hand focus back.
# ---------------------------------------------------------------------------
def find_browser_window():
    matches = []

    def handler(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and BROWSER_WINDOW_TITLE_HINT in win32gui.GetWindowText(hwnd):
            matches.append(hwnd)

    win32gui.EnumWindows(handler, None)
    return matches[0] if matches else None


def force_foreground(hwnd):
    """SetForegroundWindow from a background process is normally blocked by
    Windows unless we briefly attach our input queue to the current
    foreground thread's — the standard workaround for this restriction."""
    fg_hwnd = win32gui.GetForegroundWindow()
    cur_thread = win32api.GetCurrentThreadId()
    fg_thread = win32process.GetWindowThreadProcessId(fg_hwnd)[0] if fg_hwnd else 0
    target_thread = win32process.GetWindowThreadProcessId(hwnd)[0]
    attached_fg = attached_target = False
    try:
        if fg_thread and fg_thread != cur_thread:
            win32process.AttachThreadInput(cur_thread, fg_thread, True)
            attached_fg = True
        if target_thread != cur_thread:
            win32process.AttachThreadInput(cur_thread, target_thread, True)
            attached_target = True
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
    finally:
        if attached_fg:
            win32process.AttachThreadInput(cur_thread, fg_thread, False)
        if attached_target:
            win32process.AttachThreadInput(cur_thread, target_thread, False)


def start_webspeech():
    global prev_hwnd, browser_hwnd
    prev_hwnd = win32gui.GetForegroundWindow()
    hwnd = find_browser_window()
    if hwnd is None:
        print(f"[PTT] no window titled like '{BROWSER_WINDOW_TITLE_HINT}' found — open the app in a browser tab")
        prev_hwnd = None
        return
    browser_hwnd = hwnd
    # The browser only actually starts SpeechRecognition once it receives this
    # /api/ptt notification over its websocket (window.__wsOnPtt) — that's an
    # HTTP round trip + WS broadcast + JS callback, separate from (and slower
    # than) the focus-steal below. Firing it here, before force_foreground,
    # lets both happen in parallel instead of serially — previously this ran
    # AFTER focus-steal plus a fixed 0.08s sleep, so the mic only "woke up"
    # after focus-time + sleep + the full round trip, one after another.
    threading.Thread(target=set_server_ptt_state, args=(True, "webspeech"), daemon=True).start()
    try:
        force_foreground(hwnd)
    except Exception as e:
        print(f"[PTT] focus switch failed: {e}")
    print("[PTT] listening (web speech)…")


def stop_webspeech():
    global prev_hwnd, browser_hwnd
    # restore focus/minimize FIRST — these are instant local OS calls, so the
    # tab switch feels immediate. The /api/ptt notification is a network call
    # (can take tens-hundreds of ms) and was previously blocking this switch;
    # fire it in the background instead so it never delays the tab swap.
    if prev_hwnd:
        try:
            force_foreground(prev_hwnd)
        except Exception as e:
            print(f"[PTT] restore focus failed: {e}")
        prev_hwnd = None
    # minimize the browser back down so it doesn't sit on top of/behind
    # whatever the user was working in — matches the old behavior Min wants
    if browser_hwnd:
        try:
            win32gui.ShowWindow(browser_hwnd, win32con.SW_MINIMIZE)
        except Exception as e:
            print(f"[PTT] minimize browser failed: {e}")
        browser_hwnd = None
    threading.Thread(target=set_server_ptt_state, args=(False, "webspeech"), daemon=True).start()


# ---------------------------------------------------------------------------
def start(agent: str = "claude"):
    global is_active
    with state_lock:
        if is_active:
            return
        is_active = True
    if PTT_MODE == "webspeech":
        start_webspeech()
    else:
        start_recording()
    # Switch which agent this section listens to AFTER the ptt/mic-start call —
    # /api/agent-listener triggers a full-state broadcast (changed()) server-side,
    # which is much heavier than /api/ptt's lightweight broadcastRaw. Firing it
    # first used to risk blocking Node's single event loop long enough to delay
    # the /api/ptt request that makes the recording glow appear, so the glow felt
    # noticeably slower right after switching agents (e.g. Alt+O) than on repeat
    # presses of the same agent. Order no longer matters for correctness — the
    # glow doesn't care which agent is listening — so put the heavy call last.
    threading.Thread(target=set_agent_listener, args=(agent,), daemon=True).start()


def stop():
    global is_active
    with state_lock:
        if not is_active:
            return
        is_active = False
    if PTT_MODE == "webspeech":
        stop_webspeech()
    else:
        stop_recording_and_send()


def on_p_press(_e):
    if keyboard.is_pressed("alt"):
        start("claude")


def on_p_release(_e):
    stop()


def on_o_press(_e):
    if keyboard.is_pressed("alt"):
        start("gemini")


def on_o_release(_e):
    stop()


def main():
    keyboard.on_press_key("p", on_p_press, suppress=False)
    keyboard.on_release_key("p", on_p_release, suppress=False)
    keyboard.on_press_key("o", on_o_press, suppress=False)
    keyboard.on_release_key("o", on_o_release, suppress=False)
    keyboard.add_hotkey("ctrl+alt+m", toggle_tts_mute, suppress=False)
    print(f"[PTT] armed (mode={PTT_MODE}) — hold Alt+P to talk to Claude, Alt+O to talk to Gemini, release to send; Ctrl+Alt+M toggles TTS mute anywhere (section: main)")
    keyboard.wait()


if __name__ == "__main__":
    main()
