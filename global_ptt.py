"""Global push-to-talk for Powerfull Note.

Hold Alt+P anywhere on the system to talk to the "main" chat section.

Three modes. The active one is picked in the app's UI ("ปุ่มลัด PTT") and lands
in data/ptt_config.json, which this script re-reads on every press; PTT_MODE
below is only the fallback when that file is missing.
  "webspeech" — briefly steals foreground focus to the Powerfull Note browser
                window so the page can use the fast, in-browser Web Speech API,
                then restores focus to whatever window you were using. Fast,
                but momentarily interrupts whatever has focus (games, other
                apps) and needs that browser tab open somewhere.
  "record"    — records straight from the mic via ffmpeg, no window/tab
                needed at all, transcribes via local Whisper. Slower, but
                fully invisible — never touches window focus.
  "extension" — the Chrome extension in tools/chrome-extension picks the press
                up over the websocket and transcribes in an offscreen document,
                so nothing here touches focus or the mic.

Requires: pip install keyboard requests pywin32
Requires: ffmpeg on PATH (only used by "record" mode).

Run: python global_ptt.py   (or via ptt-listen.cmd)
"""
import json
import os
import subprocess
import tempfile
import threading
import time
import tkinter as tk

import keyboard
import requests
import win32api
import win32con
import win32gui
import win32process

# 127.0.0.1, never "localhost": getaddrinfo returns ::1 first on this machine and
# the Node server only listens on IPv4, so every "localhost" request sat through a
# ~2s failed IPv6 connect before falling back. That is 2s per call, and a single
# key press makes three or four of them.
SERVER = "http://127.0.0.1:4321"
SECTION = "main"
LANG = "th"
MIC_DEVICE = "Microphone (Realtek(R) Audio)"  # from: ffmpeg -list_devices true -f dshow -i dummy
BROWSER_WINDOW_TITLE_HINT = "Powerfull Note"  # substring of the page <title>
_HERE = os.path.dirname(os.path.abspath(__file__))
PTT_CONFIG_FILE = os.path.join(_HERE, "data", "ptt_config.json")
PTT_EXT_PING_FILE = os.path.join(_HERE, "data", "ptt_extension_ping")
PTT_EXT_PING_MAX_AGE = 90  # seconds; the extension pings every 30s
VALID_MODES = ("webspeech", "record", "extension")
PTT_MODE = "webspeech"  # fallback when data/ptt_config.json is missing

state_lock = threading.Lock()
is_active = False

# --- Screen border overlay (Windows, click-through) ------------------------
# One fullscreen borderless window per agent colour, built ONCE at startup and
# afterwards only shown/hidden through raw Win32 calls. Two reasons it is not a
# fresh tk.Tk() per keypress:
#   * Tk is not thread-safe. Spawning a root + mainloop from the keyboard hook
#     thread on every press leaked one mainloop per press, and a press released
#     before the thread finished starting up leaked the window permanently — a
#     fullscreen topmost window stuck on screen is exactly what made everything
#     feel laggy.
#   * ShowWindow/SetWindowPos are safe to call across threads, so the hotkey
#     thread can flash the border without touching Tk at all.
OVERLAY_COLORS = {"claude": "#ff6f00", "gemini": "#a020f0"}
BORDER_THICKNESS = 12

overlay_hwnds = {}  # agent -> toplevel HWND


def _is_overlay(hwnd):
    return bool(hwnd) and hwnd in overlay_hwnds.values()


def _build_overlay(master, color):
    """One fullscreen window: transparent centre, coloured border, click-through."""
    win = tk.Toplevel(master)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.config(bg="white")
    win.attributes("-transparentcolor", "white")  # sets WS_EX_LAYERED + colour key

    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"{sw}x{sh}+0+0")
    canvas = tk.Canvas(win, width=sw, height=sh, bg="white", highlightthickness=0, borderwidth=0)
    canvas.pack(fill="both", expand=True)
    t = BORDER_THICKNESS
    canvas.create_rectangle(t // 2, t // 2, sw - t // 2, sh - t // 2, outline=color, width=t)
    win.update_idletasks()

    # winfo_id() is the inner "TkChild" window, NOT the toplevel — verified with
    # GetClassName. Styling the child is what made the old border invisible:
    # WS_EX_LAYERED on a window that never gets SetLayeredWindowAttributes is
    # simply never painted, so the rectangle was drawn and then swallowed.
    # -transparentcolor above already layers the real toplevel correctly; all
    # this needs to add is the click-through/no-focus behaviour.
    hwnd = win32gui.GetParent(win.winfo_id()) or win.winfo_id()
    ex = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    win32gui.SetWindowLong(
        hwnd,
        win32con.GWL_EXSTYLE,
        ex
        | win32con.WS_EX_TRANSPARENT   # mouse clicks pass straight through
        | win32con.WS_EX_NOACTIVATE    # never steals focus from the browser
        | win32con.WS_EX_TOOLWINDOW,   # stay out of Alt+Tab
    )
    win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
    return hwnd


def _overlay_thread():
    try:
        master = tk.Tk()
        master.withdraw()
        for agent, color in OVERLAY_COLORS.items():
            overlay_hwnds[agent] = _build_overlay(master, color)
        master.mainloop()
    except Exception as e:
        print(f"[PTT] screen border unavailable: {e}")


def show_border(agent):
    hwnd = overlay_hwnds.get(agent)
    if not hwnd:
        return
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_SHOWNOACTIVATE)
        win32gui.SetWindowPos(
            hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
        )
    except Exception as e:
        print(f"[PTT] show border failed: {e}")


def hide_border():
    for hwnd in overlay_hwnds.values():
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
        except Exception:
            pass

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
    if _is_overlay(fg_hwnd):
        fg_hwnd = None
    cur_thread = win32api.GetCurrentThreadId()
    fg_thread = win32process.GetWindowThreadProcessId(fg_hwnd)[0] if fg_hwnd else 0
    target_thread = win32process.GetWindowThreadProcessId(hwnd)[0] if hwnd else 0
    attached_fg = attached_target = False
    try:
        if fg_thread and fg_thread != cur_thread:
            try:
                win32process.AttachThreadInput(cur_thread, fg_thread, True)
                attached_fg = True
            except Exception: pass
        if target_thread and target_thread != cur_thread:
            try:
                win32process.AttachThreadInput(cur_thread, target_thread, True)
                attached_target = True
            except Exception: pass
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
    except Exception as e:
        print(f"[PTT] force_foreground warning: {e}")
    finally:
        if attached_fg:
            try: win32process.AttachThreadInput(cur_thread, fg_thread, False)
            except Exception: pass
        if attached_target:
            try: win32process.AttachThreadInput(cur_thread, target_thread, False)
            except Exception: pass


def start_webspeech():
    global prev_hwnd, browser_hwnd
    fg = win32gui.GetForegroundWindow()
    if _is_overlay(fg):
        fg = None
    hwnd = find_browser_window()
    if hwnd is None:
        print(f"[PTT] no window titled like '{BROWSER_WINDOW_TITLE_HINT}' found — open the app in a browser tab")
        prev_hwnd = browser_hwnd = None
        return
    # If the app is ALREADY in front, Min is working inside it: don't steal
    # focus and — the part that really hurt — don't minimize it on release.
    # prev_hwnd staying None is what marks "we never switched away".
    prev_hwnd = None if (not fg or fg == hwnd) else fg
    browser_hwnd = hwnd
    # Fire the glow notification in the background: it is an HTTP round trip
    # plus a WS broadcast, and it must not delay the local focus switch.
    threading.Thread(target=set_server_ptt_state, args=(True, "webspeech"), daemon=True).start()
    if prev_hwnd:
        try:
            force_foreground(hwnd)
        except Exception as e:
            print(f"[PTT] focus switch failed: {e}")
    print("[PTT] listening (web speech)…")


def stop_webspeech():
    global prev_hwnd, browser_hwnd
    restore, browser = prev_hwnd, browser_hwnd
    prev_hwnd = browser_hwnd = None
    # Only undo a switch we actually made. Minimizing unconditionally used to
    # minimize the app out from under Min whenever he pressed Alt+P while
    # already looking at it.
    if restore:
        try:
            force_foreground(restore)
        except Exception as e:
            print(f"[PTT] restore focus failed: {e}")
        if browser:
            try:
                win32gui.ShowWindow(browser, win32con.SW_MINIMIZE)
            except Exception as e:
                print(f"[PTT] minimize browser failed: {e}")
    threading.Thread(target=set_server_ptt_state, args=(False, "webspeech"), daemon=True).start()


# ---------------------------------------------------------------------------
active_mode = "webspeech"
active_key = None


def fetch_active_mode():
    """Read the mode the UI last saved.

    Straight off the file the server writes, not over HTTP. Everything in here
    runs on the `keyboard` library's single hook-dispatch thread, so a blocking
    request with a 2s timeout stalled every later key event — including the
    release that ends the recording. A local read is microseconds and keeps
    working when the server is down.
    """
    mode = PTT_MODE
    try:
        with open(PTT_CONFIG_FILE, "r", encoding="utf-8") as f:
            saved = (json.load(f) or {}).get("mode")
        if saved in VALID_MODES:
            mode = saved
    except Exception:
        pass
    if mode == "extension" and not extension_alive():
        _warn_once(
            "extension",
            "[PTT] extension mode is selected but the Chrome extension isn't running "
            "— falling back to webspeech. Load tools/chrome-extension in chrome://extensions.",
        )
        return "webspeech"
    _warn_once(mode, None)
    return mode


def extension_alive():
    """True if the Chrome extension pinged the server recently.

    Extension mode hands the whole recording job to the extension, so with it
    missing a key press lights up the screen border and then silently does
    nothing at all — visually identical to the app being broken. Checking a
    file's mtime keeps this off the network and off the hot path.
    """
    try:
        return (time.time() - os.path.getmtime(PTT_EXT_PING_FILE)) < PTT_EXT_PING_MAX_AGE
    except OSError:
        return False


_warned = None


def _warn_once(key, message):
    """Print `message` only when the situation changes — this runs per keypress."""
    global _warned
    if _warned == key:
        return
    _warned = key
    if message:
        print(message)


def start(agent, key):
    global is_active, active_mode, active_key
    with state_lock:
        if is_active:
            return
        is_active = True
        active_key = key

    # 1. Border first — it is a local ShowWindow on a window that already
    #    exists, so the glow is up before anything slower begins. It is
    #    WS_EX_NOACTIVATE, so it cannot fight the focus switch below.
    show_border(agent)

    # 2. Then start listening.
    active_mode = fetch_active_mode()
    if active_mode == "webspeech":
        start_webspeech()
    elif active_mode == "extension":
        threading.Thread(target=set_server_ptt_state, args=(True, "extension"), daemon=True).start()
    else:
        start_recording()

    # 3. Heaviest call last: /api/agent-listener triggers a full-state
    #    broadcast server-side, so keep it off the critical path entirely.
    threading.Thread(target=set_agent_listener, args=(agent,), daemon=True).start()


def stop(key=None):
    global is_active, active_mode, active_key
    with state_lock:
        if not is_active:
            return
        # Releasing the *other* hotkey shouldn't end a recording — e.g. tapping
        # O while Alt+P is still held down.
        if key is not None and active_key not in (None, key):
            return
        is_active = False
        active_key = None

    hide_border()

    if active_mode == "webspeech":
        stop_webspeech()
    elif active_mode == "extension":
        threading.Thread(target=set_server_ptt_state, args=(False, "extension"), daemon=True).start()
    else:
        stop_recording_and_send()


def _alt_down():
    return (
        keyboard.is_pressed("alt")
        or keyboard.is_pressed("left alt")
        or keyboard.is_pressed("right alt")
    )


def on_p_press(_e):
    if _alt_down():
        start("claude", "p")


def on_p_release(_e):
    stop("p")


def on_o_press(_e):
    if _alt_down():
        start("gemini", "o")


def on_o_release(_e):
    stop("o")


def main():
    threading.Thread(target=_overlay_thread, daemon=True).start()
    keyboard.on_press_key("p", on_p_press, suppress=False)
    keyboard.on_release_key("p", on_p_release, suppress=False)
    keyboard.on_press_key("o", on_o_press, suppress=False)
    keyboard.on_release_key("o", on_o_release, suppress=False)
    keyboard.add_hotkey("ctrl+alt+m", toggle_tts_mute, suppress=False)
    print(f"[PTT] armed (mode={fetch_active_mode()}) — hold Alt+P to talk to Claude, Alt+O to talk to Gemini, release to send; Ctrl+Alt+M toggles TTS mute anywhere (section: main)")
    keyboard.wait()


if __name__ == "__main__":
    main()
