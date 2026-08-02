"""Reusable TIA Portal UI-automation toolkit (no Openness license needed).

Usage (must run elevated/Administrator for click/focus commands — TIA Portal
runs elevated and Windows UIPI blocks lower-privilege processes from
interacting with it):

    python tia_tool.py handle
    python tia_tool.py shot [outfile.png]
    python tia_tool.py foreground-check
    python tia_tool.py focus
    python tia_tool.py click X Y [--double]
    python tia_tool.py keys "text to type"
"""
import sys
import time
import argparse

import win32gui
import win32process
import psutil
from PIL import ImageGrab
from pywinauto import mouse, keyboard


def find_tia_handle():
    for p in psutil.process_iter(["pid", "name"]):
        if p.info["name"] == "Siemens.Automation.Portal.exe":
            try:
                import win32ui  # noqa
            except Exception:
                pass
    result = []

    def cb(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        title = win32gui.GetWindowText(hwnd)
        if not title:
            return True
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            pname = psutil.Process(pid).name()
        except Exception:
            pname = ""
        if pname == "Siemens.Automation.Portal.exe" and "Siemens" in title:
            result.append(hwnd)
        return True

    win32gui.EnumWindows(cb, None)
    return result[0] if result else None


def cmd_handle(_args):
    h = find_tia_handle()
    if h is None:
        print("NOT_FOUND")
        sys.exit(1)
    print(h)


def cmd_shot(args):
    h = find_tia_handle()
    if h is None:
        print("NOT_FOUND")
        sys.exit(1)
    rect = win32gui.GetWindowRect(h)
    img = ImageGrab.grab(bbox=rect, all_screens=True)
    out = args.outfile or "tia_shot.png"
    img.save(out)
    print(f"rect={rect} size={img.size} saved={out}")


def foreground_is_tia():
    """True if the foreground window belongs to TIA Portal's process
    (covers modal dialogs owned by the app, which get their own HWND
    distinct from the main window handle)."""
    fg = win32gui.GetForegroundWindow()
    if not fg:
        return False, fg
    try:
        _, pid = win32process.GetWindowThreadProcessId(fg)
        pname = psutil.Process(pid).name()
    except Exception:
        return False, fg
    return pname == "Siemens.Automation.Portal.exe", fg


def cmd_foreground_check(_args):
    ok, fg = foreground_is_tia()
    print("MATCH" if ok else f"MISMATCH fg={fg}")


def cmd_focus(_args):
    h = find_tia_handle()
    if h is None:
        print("NOT_FOUND")
        sys.exit(1)
    win32gui.ShowWindow(h, 9)  # SW_RESTORE
    win32gui.SetForegroundWindow(h)
    time.sleep(0.3)
    fg = win32gui.GetForegroundWindow()
    print("OK" if fg == h else f"FAILED fg={fg} tia={h}")


def cmd_click(args):
    ok, fg = foreground_is_tia()
    if not ok and not args.force:
        print(f"REFUSED: TIA Portal (or its dialog) not foreground (fg={fg}). "
              f"Run 'focus' first or pass --force.")
        sys.exit(2)
    if args.double:
        mouse.double_click(coords=(args.x, args.y))
    else:
        mouse.click(coords=(args.x, args.y))
    print(f"clicked ({args.x},{args.y}) double={args.double}")


def cmd_drag(args):
    import win32api
    import win32con
    ok, fg = foreground_is_tia()
    if not ok and not args.force:
        print(f"REFUSED: TIA Portal (or its dialog) not foreground (fg={fg}). "
              f"Run 'focus' first or pass --force.")
        sys.exit(2)
    x1, y1, x2, y2 = args.x1, args.y1, args.x2, args.y2
    win32api.SetCursorPos((x1, y1))
    time.sleep(0.2)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.15)
    # small jiggle first to cross the WPF drag-detection threshold
    for dx, dy in [(3, 0), (6, 2), (10, 4)]:
        win32api.SetCursorPos((x1 + dx, y1 + dy))
        time.sleep(0.08)
    time.sleep(0.15)
    steps = 25
    for i in range(1, steps + 1):
        ix = x1 + (x2 - x1) * i // steps
        iy = y1 + (y2 - y1) * i // steps
        win32api.SetCursorPos((ix, iy))
        time.sleep(0.05)
    time.sleep(0.3)
    win32api.SetCursorPos((x2, y2))
    time.sleep(0.2)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    print(f"dragged ({x1},{y1}) -> ({x2},{y2})")


def cmd_keys(args):
    ok, fg = foreground_is_tia()
    if not ok and not args.force:
        print(f"REFUSED: TIA Portal (or its dialog) not foreground (fg={fg}). "
              f"Run 'focus' first or pass --force.")
        sys.exit(2)
    keyboard.send_keys(args.text)
    print("sent keys")


_VK = {"enter": 0x0D, "tab": 0x09, "esc": 0x1B, "escape": 0x1B, "f2": 0x71,
       "delete": 0x2E, "backspace": 0x08, "ctrl+a": (0x11, 0x41),
       "ctrl+c": (0x11, 0x43), "ctrl+v": (0x11, 0x56)}


def cmd_key(args):
    import win32api
    import win32con
    ok, fg = foreground_is_tia()
    if not ok and not args.force:
        print(f"REFUSED: TIA Portal (or its dialog) not foreground (fg={fg}). "
              f"Run 'focus' first or pass --force.")
        sys.exit(2)
    code = _VK.get(args.name.lower())
    if isinstance(code, tuple):
        mod, key = code
        win32api.keybd_event(mod, 0, 0, 0)
        time.sleep(0.03)
        win32api.keybd_event(key, 0, 0, 0)
        time.sleep(0.03)
        win32api.keybd_event(key, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.03)
        win32api.keybd_event(mod, 0, win32con.KEYEVENTF_KEYUP, 0)
        print(f"sent key {args.name}")
        return
    code = _VK.get(args.name.lower())
    if code is None:
        print(f"UNKNOWN_KEY: {args.name} (known: {list(_VK)})")
        sys.exit(1)
    win32api.keybd_event(code, 0, 0, 0)
    time.sleep(0.03)
    win32api.keybd_event(code, 0, win32con.KEYEVENTF_KEYUP, 0)
    print(f"sent key {args.name}")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("handle")

    sp = sub.add_parser("shot")
    sp.add_argument("outfile", nargs="?")

    sub.add_parser("foreground-check")
    sub.add_parser("focus")

    sp = sub.add_parser("click")
    sp.add_argument("x", type=int)
    sp.add_argument("y", type=int)
    sp.add_argument("--double", action="store_true")
    sp.add_argument("--force", action="store_true")

    sp = sub.add_parser("keys")
    sp.add_argument("text")
    sp.add_argument("--force", action="store_true")

    sp = sub.add_parser("key")
    sp.add_argument("name", help="enter | tab | esc | f2")
    sp.add_argument("--force", action="store_true")

    sp = sub.add_parser("drag")
    sp.add_argument("x1", type=int)
    sp.add_argument("y1", type=int)
    sp.add_argument("x2", type=int)
    sp.add_argument("y2", type=int)
    sp.add_argument("--force", action="store_true")

    args = p.parse_args()
    {
        "handle": cmd_handle,
        "shot": cmd_shot,
        "foreground-check": cmd_foreground_check,
        "focus": cmd_focus,
        "drag": cmd_drag,
        "click": cmd_click,
        "keys": cmd_keys,
        "key": cmd_key,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
