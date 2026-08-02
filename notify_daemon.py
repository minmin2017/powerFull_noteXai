"""Custom desktop toast notifications for Powerfull Note (Claude/Gemini replies).

Polls the app's /api/state for new chat messages and shows a full-content
always-on-top overlay window in the corner of the screen so Min can read the
whole answer (including rendered $...$/$$...$$ LaTeX equations, via
matplotlib) without switching to the Chrome tab. Auto-dismisses after
DISPLAY_SECONDS, but hovering the mouse over a card pauses/resets that timer
so it won't vanish mid-read.

Requires: pip install requests pywin32 matplotlib pillow   (tkinter ships with Python on Windows)

Run: python notify_daemon.py   (or via notify-listen.cmd)
"""
import io
import os
import re
import threading
import time
import tkinter as tk
import tkinter.font as tkfont

import requests
import win32gui
import win32process
import win32api
import win32con
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageTk

SERVER = "http://localhost:4321"
POLL_INTERVAL = 1.5
SEEN_FILE = os.path.join(os.path.dirname(__file__), ".notify_daemon_seen_ts.txt")
BANNER_W = 560
BANNER_MARGIN = 16
MIN_BANNER_W = 300
MAX_BANNER_W = 1100
MAX_BODY_LINES = 24  # beyond this the Text widget scrolls instead of growing forever
DISPLAY_SECONDS = 6
BROWSER_WINDOW_TITLE_HINT = "Powerfull Note"
MATH_PATTERN = re.compile(r"\$\$(.+?)\$\$|\$(.+?)\$", re.S)

root = None
last_ts = 0
active_toasts = []  # stack toasts vertically so several don't overlap


def load_last_ts():
    global last_ts
    try:
        with open(SEEN_FILE, "r") as f:
            last_ts = int(f.read().strip() or 0)
    except Exception:
        last_ts = 0


def save_last_ts(ts):
    try:
        with open(SEEN_FILE, "w") as f:
            f.write(str(ts))
    except Exception:
        pass


def find_browser_window():
    matches = []

    def handler(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and BROWSER_WINDOW_TITLE_HINT in win32gui.GetWindowText(hwnd):
            matches.append(hwnd)

    win32gui.EnumWindows(handler, None)
    return matches[0] if matches else None


def force_foreground(hwnd):
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


def reflow_toasts():
    """Stack currently-visible toasts top-to-bottom so new ones don't cover old ones.
    Each toast may have its own width now (widened to fit equations), so re-derive
    its x position from its own current width rather than a shared constant."""
    y = BANNER_MARGIN
    for win in list(active_toasts):
        if not win.winfo_exists():
            active_toasts.remove(win)
            continue
        screen_w = win.winfo_screenwidth()
        w = win.winfo_width()
        x = screen_w - w - BANNER_MARGIN
        win.geometry(f"{w}x{win.winfo_height()}+{x}+{y}")
        y += win.winfo_height() + 10


def render_math_photo(expr, block, color="#e5e7eb"):
    """LaTeX-ish expression -> Tk PhotoImage with a TRANSPARENT background.
    mathtext.math_to_image() always fills an opaque white background (no way
    to disable it), which showed up as a jarring white patch on the dark
    card. Rendering through a bare Figure with fig.patch.set_alpha(0) and
    savefig(transparent=True) keeps only the glyph strokes."""
    fontsize = 15 if block else 12
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.patch.set_alpha(0.0)
    text_obj = fig.text(0, 0, f"${expr}$", fontsize=fontsize, color=color)
    fig.canvas.draw()
    bbox = text_obj.get_window_extent()
    fig.set_size_inches(bbox.width / fig.dpi + 0.15, bbox.height / fig.dpi + 0.15)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, transparent=True, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    buf.seek(0)
    return ImageTk.PhotoImage(Image.open(buf).convert("RGBA"))


def build_segments(s):
    """Split s into ('text', str) / ('img', PhotoImage, is_block) tokens, rendering
    equations up front so we know the widest equation's pixel width before we size
    the window (letting the toast grow wider for wide formulas instead of clipping)."""
    segments = []
    pos = 0
    for m in MATH_PATTERN.finditer(s):
        start, end = m.span()
        if start > pos:
            segments.append(("text", s[pos:start]))
        block = m.group(1) is not None
        expr = m.group(1) if block else m.group(2)
        try:
            img = render_math_photo(expr, block)
            segments.append(("img", img, block))
        except Exception:
            segments.append(("text", s[start:end]))
        pos = end
    if pos < len(s):
        segments.append(("text", s[pos:]))
    return segments


def insert_segments(text_widget, segments):
    for seg in segments:
        if seg[0] == "text":
            text_widget.insert(tk.END, seg[1])
        else:
            _, img, block = seg
            if block:
                text_widget.insert(tk.END, "\n")
            text_widget.image_create(tk.END, image=img)
            if block:
                text_widget.insert(tk.END, "\n")


def show_toast(role, text):
    label = "Claude ตอบกลับแล้ว 🧠" if role == "claude" else "Gemini ตอบกลับแล้ว 💎"
    color = "#818cf8" if role == "claude" else "#fbbf24"

    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    try:
        win.attributes("-alpha", 0.0)
    except Exception:
        pass
    win.configure(bg="#111827")

    segments = build_segments(text)
    image_refs = [seg[1] for seg in segments if seg[0] == "img"]
    win.image_refs = image_refs  # keep alive for this window's lifetime
    max_img_w = max((img.width() for img in image_refs), default=0)

    screen_w = win.winfo_screenwidth()
    # Dynamic width: grow past the default to fit the widest equation image,
    # capped so a single toast never eats the whole screen. Also manually
    # resizable afterwards via the grip in the bottom-left corner.
    win_w = max(BANNER_W, min(max_img_w + 60, int(screen_w * 0.85), MAX_BANNER_W))
    win.geometry(f"{win_w}x100+{screen_w - win_w - BANNER_MARGIN}+{BANNER_MARGIN}")

    head_row = tk.Frame(win, bg="#111827")
    head_row.pack(fill="x")
    head = tk.Label(
        head_row, text=label, fg=color, bg="#111827", font=("Segoe UI", 11, "bold"),
        anchor="w", padx=14,
    )
    head.pack(side="left", fill="x", expand=True, pady=(10, 2))
    close_btn = tk.Label(head_row, text="✕", fg="#9ca3af", bg="#111827", font=("Segoe UI", 10), cursor="hand2", padx=10)
    close_btn.pack(side="right")

    body = tk.Text(
        win, fg="#e5e7eb", bg="#111827", font=("Segoe UI", 10),
        wrap="word", padx=14, pady=6, bd=0, highlightthickness=0,
        height=3, cursor="arrow",
    )
    insert_segments(body, segments)
    body.configure(state="disabled")
    body.pack(fill="both", expand=True, padx=(0, 0), pady=(0, 10))

    win.update_idletasks()
    line_count = int(body.index("end-1c").split(".")[0])
    body.configure(height=min(max(line_count, 1), MAX_BODY_LINES))
    if line_count > MAX_BODY_LINES:
        scrollbar = tk.Scrollbar(body, command=body.yview)
        body.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    win.update_idletasks()
    # Everything in the window besides the resizable text body (header row,
    # padding) — used below to compute exact pixel heights when the grip
    # changes the body's line count, since Tk won't auto-shrink/grow a
    # Toplevel that already has an explicit geometry() applied.
    chrome_h = win.winfo_height() - body.winfo_height()
    active_toasts.append(win)
    reflow_toasts()

    def close(*_):
        if win in active_toasts:
            active_toasts.remove(win)
        try:
            win.destroy()
        except Exception:
            pass
        reflow_toasts()

    def bring_to_front(*_):
        try:
            hwnd = find_browser_window()
            if hwnd:
                force_foreground(hwnd)
        except Exception:
            pass

    head.bind("<Button-1>", bring_to_front)
    close_btn.bind("<Button-1>", close)

    # Manual resize grip, bottom-left corner — drag left/right to widen/narrow
    # (card is anchored to the screen's right edge, so widening grows it
    # further left) and drag up/down to reveal more/fewer lines of the body
    # text (height alone doesn't do this — the Text widget's line count has
    # to be raised too, or extra window space just shows as blank padding).
    grip = tk.Label(win, text="◢", fg="#4b5563", bg="#111827", font=("Segoe UI", 9), cursor="size_nw_se")
    grip.place(relx=0.0, rely=1.0, anchor="sw")
    resize_state = {}
    line_px = tkfont.Font(font=body["font"]).metrics("linespace")

    def resize_start(e):
        cancel_dismiss()
        resize_state["x"] = e.x_root
        resize_state["y"] = e.y_root
        resize_state["w"] = win.winfo_width()
        resize_state["lines"] = int(body.cget("height"))

    def resize_drag(e):
        if "x" not in resize_state:
            return
        dx = resize_state["x"] - e.x_root
        new_w = max(MIN_BANNER_W, min(MAX_BANNER_W, resize_state["w"] + dx))
        x = win.winfo_screenwidth() - new_w - BANNER_MARGIN

        dy = e.y_root - resize_state["y"]
        delta_lines = int(dy / line_px)
        new_lines = max(1, min(line_count, resize_state["lines"] + delta_lines))
        body.configure(height=new_lines)

        new_h = int(chrome_h + new_lines * line_px)
        win.geometry(f"{new_w}x{new_h}+{x}+{win.winfo_y()}")

    def resize_end(_e):
        resize_state.clear()
        reflow_toasts()
        arm_dismiss()

    grip.bind("<ButtonPress-1>", resize_start)
    grip.bind("<B1-Motion>", resize_drag)
    grip.bind("<ButtonRelease-1>", resize_end)

    def fade_in(alpha=0.0):
        alpha = min(1.0, alpha + 0.15)
        try:
            win.attributes("-alpha", alpha)
        except Exception:
            pass
        if alpha < 1.0:
            win.after(20, lambda: fade_in(alpha))

    fade_in()

    # Auto-dismiss after DISPLAY_SECONDS, but hovering the card resets the
    # countdown to zero so it never vanishes out from under Min mid-read; the
    # timer only starts counting again once the mouse leaves.
    dismiss_timer = [None]

    def arm_dismiss():
        cancel_dismiss()
        dismiss_timer[0] = win.after(DISPLAY_SECONDS * 1000, close)

    def cancel_dismiss():
        if dismiss_timer[0] is not None:
            win.after_cancel(dismiss_timer[0])
            dismiss_timer[0] = None

    for w in (win, head_row, head, body):
        w.bind("<Enter>", lambda _e: cancel_dismiss())
        w.bind("<Leave>", lambda _e: arm_dismiss())

    arm_dismiss()


def poll_loop():
    global last_ts
    while True:
        try:
            r = requests.get(f"{SERVER}/api/state", timeout=5)
            r.raise_for_status()
            state = r.json()
            chat = state.get("chat", [])
            new_msgs = sorted(
                (m for m in chat if m.get("role") in ("claude", "gemini") and m.get("ts", 0) > last_ts),
                key=lambda m: m.get("ts", 0),
            )
            if last_ts == 0:
                # first poll — record baseline, don't spam existing backlog
                if new_msgs:
                    last_ts = new_msgs[-1]["ts"]
                    save_last_ts(last_ts)
            else:
                for m in new_msgs:
                    last_ts = m["ts"]
                    save_last_ts(last_ts)
                    if root:
                        root.after(0, show_toast, m.get("role"), m.get("text", ""))
        except Exception:
            pass
        time.sleep(POLL_INTERVAL)


def main():
    global root
    load_last_ts()
    root = tk.Tk()
    root.withdraw()  # hidden root — Toplevels are the actual visible toasts
    threading.Thread(target=poll_loop, daemon=True).start()
    print("[notify] armed — watching Powerfull Note chat for Claude/Gemini replies")
    root.mainloop()


if __name__ == "__main__":
    main()
