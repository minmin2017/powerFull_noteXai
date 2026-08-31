import subprocess
import time
import sys
import os
import json
import urllib.request
import win32gui
import win32con
import win32clipboard
import win32process
import pyautogui

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Set up logging to file
log_file = os.path.join(WORKSPACE, "startup_bot.log")
def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}\n"
    print(msg)
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass

# Clear old log
if os.path.exists(log_file):
    try:
        os.remove(log_file)
    except Exception:
        pass

def set_clipboard_text(text):
    for _ in range(5):
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            return True
        except Exception:
            time.sleep(0.1)
    return False

def is_gemini_alive():
    try:
        req = urllib.request.Request("http://127.0.0.1:4321/api/state", headers={"User-Agent": "StartupBot"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode())
            seen_ts = data.get("agentSeen", {}).get("gemini", 0)
            now_ms = time.time() * 1000
            # If seen within the last 10 seconds, Gemini is alive and listening!
            if (now_ms - seen_ts) < 10000:
                return True
    except Exception:
        pass
    return False

def find_antigravity_window():
    hwnd_list = []
    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            class_name = win32gui.GetClassName(hwnd)
            if class_name == "Chrome_WidgetWin_1":
                title = win32gui.GetWindowText(hwnd)
                t_low = title.lower()
                if "antigravity" in t_low or "powerfull_note" in t_low or "powernote" in t_low:
                    hwnd_list.append((hwnd, title))
        return True
    win32gui.EnumWindows(callback, None)
    return hwnd_list

def focus_window(hwnd):
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shell.SendKeys('%') # Tap Alt key to unlock foreground window
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        return True
    except Exception as e:
        log(f"Focus warning: {e}")
        return False

def inject_prompt(hwnd, prompt):
    log(f"Focusing window (HWND: {hwnd})...")
    focus_window(hwnd)
    time.sleep(1)

    log("Setting prompt to clipboard...")
    set_clipboard_text(prompt)
    time.sleep(0.3)

    log("Focusing chat panel (Ctrl+Alt+C)...")
    pyautogui.hotkey('ctrl', 'alt', 'c')
    time.sleep(0.6)

    log("Pasting prompt (Ctrl+V)...")
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.4)

    log("Submitting prompt (Enter)...")
    pyautogui.press('enter')

def main():
    log("Startup bot started.")

    # 1. Quick check: Is Gemini already running and listening?
    if is_gemini_alive():
        log("Gemini is already active and listening. Nothing to do!")
        sys.exit(0)

    exe_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "antigravity", "Antigravity.exe")
    workspace = WORKSPACE

    # 2. Check if Antigravity is open or needs launching
    hwnds = find_antigravity_window()
    if not hwnds:
        log("Launching Antigravity IDE...")
        if os.path.exists(exe_path):
            subprocess.Popen([exe_path, workspace])
        else:
            log(f"Error: Executable not found at {exe_path}")
            sys.exit(1)

    # 3. Dynamic wait for Antigravity window (up to 60s)
    log("Waiting for Antigravity window to appear...")
    hwnd = None
    window_title = ""
    for i in range(60):
        hwnds = find_antigravity_window()
        if hwnds:
            hwnd, window_title = hwnds[0]
            log(f"Found Antigravity window: '{window_title}' (HWND: {hwnd}) after {i}s.")
            break
        time.sleep(1)

    if not hwnd:
        log("Error: Antigravity window not found after 60 seconds.")
        sys.exit(1)

    # Prepare command
    gemini_md = os.path.join(WORKSPACE, "GEMINI.md").replace("\\", "/")
    prompt = f"read {gemini_md} and listen to powernote"

    # 4. Retry loop with heartbeat verification (up to 5 attempts)
    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        log(f"Attempt {attempt}/{max_attempts}: Injecting prompt...")
        # Give a small initial settling pause on first boot attempt
        if attempt == 1:
            time.sleep(5)

        inject_prompt(hwnd, prompt)

        # Wait and verify if Gemini heartbeat wakes up (check up to 15s)
        log("Verifying Gemini heartbeat...")
        verified = False
        for _ in range(15):
            time.sleep(1)
            if is_gemini_alive():
                verified = True
                break

        if verified:
            log("🎉 SUCCESS! Gemini heartbeat detected and verified active.")
            sys.exit(0)
        else:
            log(f"Attempt {attempt} did not activate Gemini heartbeat yet. Retrying in 3s...")
            time.sleep(3)

    log("Warning: Completed all attempts without heartbeat confirmation. IDE may still be loading.")

if __name__ == '__main__':
    main()
