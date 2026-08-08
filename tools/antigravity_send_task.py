"""Send an arbitrary prompt into an already-open Antigravity IDE chat panel.

Usage: python tools/antigravity_send_task.py "your prompt here"

Assumes Antigravity is already running (does not launch it - see
antigravity_startup_bot.py for that).
"""
import sys
import time

import win32con
import win32gui
import pyautogui


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


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/antigravity_send_task.py \"prompt text\"")
        sys.exit(1)
    message = sys.argv[1]

    hwnds = find_antigravity_window()
    if not hwnds:
        print("Error: no Antigravity window found. Is it running?")
        sys.exit(1)
    hwnd, title = hwnds[0]
    print(f"Found Antigravity window: '{title}' (HWND: {hwnd})")

    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shell.SendKeys('%')
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
    except Exception as e:
        print(f"Focus warning: {e}")

    time.sleep(1)
    pyautogui.hotkey('ctrl', 'alt', 'c')
    time.sleep(1)
    pyautogui.typewrite(message, interval=0.02)
    time.sleep(0.5)
    pyautogui.press('enter')
    print("Sent.")


if __name__ == '__main__':
    main()
