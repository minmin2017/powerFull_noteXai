import subprocess
import time
import sys
import os
import win32gui
import win32con
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

def find_antigravity_window():
    hwnd_list = []
    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            class_name = win32gui.GetClassName(hwnd)
            # Chrome_WidgetWin_1 is the class name for Electron/VS Code/Antigravity GUI windows.
            # This prevents matching "ConsoleWindowClass" (cmd.exe).
            if class_name == "Chrome_WidgetWin_1":
                title = win32gui.GetWindowText(hwnd)
                t_low = title.lower()
                if "antigravity" in t_low or "powerfull_note" in t_low:
                    hwnd_list.append((hwnd, title))
        return True
    win32gui.EnumWindows(callback, None)
    return hwnd_list

def main():
    exe_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "antigravity", "Antigravity.exe")
    workspace = WORKSPACE

    log("Launching Antigravity IDE...")
    if os.path.exists(exe_path):
        subprocess.Popen([exe_path, workspace])
    else:
        log(f"Error: Executable not found at {exe_path}")
        sys.exit(1)
        
    # Wait for the window to appear (up to 30 seconds)
    log("Waiting for Antigravity window to open...")
    hwnd = None
    window_title = ""
    for i in range(30):
        hwnds = find_antigravity_window()
        if hwnds:
            hwnd, window_title = hwnds[0]
            log(f"Found Antigravity window: '{window_title}' (HWND: {hwnd}) after {i} seconds.")
            break
        time.sleep(1)
        
    if not hwnd:
        log("Error: Antigravity window not found after 30 seconds.")
        sys.exit(1)
        
    log("Waiting 20 seconds for full IDE initialization...")
    time.sleep(20)
    
    # Try to focus the window
    log("Focusing window...")
    try:
        # Unlock SetForegroundWindow using Windows Shell Alt-key trick
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shell.SendKeys('%') # Tap Alt key to release lock
        
        # SW_RESTORE restores the window even if it is currently minimized!
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        log("ShowWindow and SetForegroundWindow called successfully.")
    except Exception as e:
        log(f"Focus warning: {e}")
        
    time.sleep(2)
    
    # Simulate focusing the chat panel
    log("Sending hotkeys to focus chat panel...")
    # Send Ctrl+Alt+C
    pyautogui.hotkey('ctrl', 'alt', 'c')
    time.sleep(1)
    
    # Type the greeting message and send
    log("Typing and sending message...")
    gemini_md = os.path.join(WORKSPACE, "GEMINI.md").replace("\\", "/")
    pyautogui.typewrite(f"read {gemini_md} and listen to powernote", interval=0.03)
    time.sleep(1)
    pyautogui.press('enter')
    log("Startup sequence complete!")

if __name__ == '__main__':
    main()
