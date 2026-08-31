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
import subprocess
import tempfile
import threading
import time
import tkinter as tk
import tkinter.font as tkfont
import webbrowser

import requests
import win32gui
import win32process
import win32api
import win32con
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageTk, ImageSequence

# 127.0.0.1, not "localhost" — see global_ptt.py: localhost resolves to ::1 first
# here and the server is IPv4-only, so every poll burned ~2s on a dead IPv6
# connect. With a 1.5s poll interval that meant this daemon was never idle.
SERVER = "http://127.0.0.1:4321"
POLL_INTERVAL = 1.5
SEEN_FILE = os.path.join(os.path.dirname(__file__), ".notify_daemon_seen_ts.txt")
BANNER_W = 560
BANNER_MARGIN = 16
MIN_BANNER_W = 300
MAX_BANNER_W = 1100
MAX_BODY_LINES = 24  # beyond this the Text widget scrolls instead of growing forever
# Floor for the body height. Sizing purely to the wrapped line count made a
# one-line reply ("โอเคครับ") render as a sliver barely taller than its own
# header — technically correct, but too small to read at a glance from across
# the desk, which is the whole point of the toast. Short replies now get a
# card with some room around them; long ones are unaffected.
MIN_BODY_LINES = 4
DISPLAY_SECONDS = 6
BROWSER_WINDOW_TITLE_HINT = "Powerfull Note"
# Attached media (say_to_user media hint) thumbnail cap — small preview inside
# the toast, not a fullscreen player. Click opens the real file in the browser.
MEDIA_MAX_W = 320
MEDIA_MAX_H = 200
# Gemini/Claude เขียนสมการได้ 4 แบบ: $$..$$, $..$, \[..\], \(..\)
# กลุ่มคู่ (1,3) = display (บรรทัดของตัวเอง), กลุ่มคี่ (2,4) = inline
MATH_PATTERN = re.compile(
    r"\$\$(.+?)\$\$|\$(.+?)\$|\\\[(.+?)\\\]|\\\((.+?)\\\)", re.S
)
THAI_RE = re.compile(r"[฀-๿]")

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


def animate_toast(win, start_x, target_x, start_alpha, target_alpha,
                   steps=18, delay=14, ease_out=True, on_done=None):
    """Slide win's x from start_x -> target_x while cross-fading alpha, one
    `after`-scheduled tick at a time. y is re-read from the window every tick
    (not captured once) so a concurrent reflow_toasts() call from another
    toast opening/closing can still shift this one vertically mid-animation.
    ease_out (decelerate into place) reads right for an arrival; ease_out=False
    (accelerate away) reads right for a dismissal."""
    state = {"i": 0}

    def tick():
        if not win.winfo_exists():
            return
        state["i"] += 1
        t = min(1.0, state["i"] / steps)
        e = (1 - (1 - t) ** 3) if ease_out else t ** 3
        x = int(start_x + (target_x - start_x) * e)
        a = start_alpha + (target_alpha - start_alpha) * e
        try:
            y = win.winfo_y()
            win.geometry(f"{win.winfo_width()}x{win.winfo_height()}+{x}+{y}")
            win.attributes("-alpha", a)
        except Exception:
            pass
        if t < 1.0:
            win.after(delay, tick)
        elif on_done:
            on_done()

    tick()


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


def latex_to_plain(expr):
    """LaTeX -> ข้อความอ่านง่าย ใช้เมื่อมีภาษาไทยปนอยู่ในสมการ

    matplotlib mathtext วาดอักษรไทยไม่ได้เลย (ฟอนต์ DejaVu ไม่มี glyph ไทย)
    ผลคือได้สี่เหลี่ยม/วงกลมเรียงกันยาว เช่น '⊂⊃⊂⊃⊂⊃ = P x V_D'
    เจอไทยเมื่อไหร่จึงเลิกวาดเป็นรูป แล้วแปลงเป็นข้อความธรรมดาแทน"""
    s = expr
    s = re.sub(r"\\(?:text|mathrm|mathbf|textbf)\s*\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}", r"(\1)/(\2)", s)
    for cmd, sym in (
        (r"\times", "×"), (r"\cdot", "·"), (r"\approx", "≈"), (r"\neq", "≠"),
        (r"\leq", "≤"), (r"\geq", "≥"), (r"\pi", "π"), (r"\eta", "η"),
        (r"\omega", "ω"), (r"\rho", "ρ"), (r"\mu", "μ"), (r"\Delta", "Δ"),
        (r"\phi", "φ"), (r"\theta", "θ"), (r"\gamma", "γ"), (r"\beta", "β"),
    ):
        s = s.replace(cmd, sym)
    s = re.sub(r"\\[a-zA-Z]+", "", s)          # คำสั่งที่เหลือ ตัดทิ้ง
    s = s.replace("{", "").replace("}", "").replace("\\", "")
    return re.sub(r"[ \t]+", " ", s).strip()


def strip_markdown(s):
    """ตัดสัญลักษณ์ Markdown ออก — toast เป็น Text widget ธรรมดา
    ถ้าไม่ตัด จะเห็น '**ตัวหนา**' กับ '###' โผล่มาดิบๆ เต็มไปหมด"""
    s = re.sub(r"^\s{0,3}#{1,6}\s*", "", s, flags=re.M)        # ### หัวข้อ
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s, flags=re.S)          # **หนา**
    s = re.sub(r"__(.+?)__", r"\1", s, flags=re.S)              # __หนา__
    s = re.sub(r"`([^`]+)`", r"\1", s)                          # `code`
    s = re.sub(r"^\s*[-*+]\s+", "• ", s, flags=re.M)            # bullet
    s = re.sub(r"^\s*-{3,}\s*$", "─" * 24, s, flags=re.M)       # เส้นคั่น
    return s


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
        # กลุ่ม 1=$$..$$ 2=$..$ 3=\[..\] 4=\(..\)  — คู่ = display, คี่ = inline
        block = m.group(1) is not None or m.group(3) is not None
        expr = next((g for g in m.groups() if g is not None), "")
        if THAI_RE.search(expr):
            # มีไทยในสมการ -> วาดเป็นรูปไม่ได้ ใส่เป็นข้อความแทน
            plain = latex_to_plain(expr)
            segments.append(("text", f"\n{plain}\n" if block else plain))
        else:
            try:
                img = render_math_photo(expr, block)
                segments.append(("img", img, block))
            except Exception:
                segments.append(("text", latex_to_plain(expr)))
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


def fetch_media_bytes(url_path):
    """url_path is what /api/chat stored — either a relative /api/media?... path
    or an already-absolute http(s) URL. Returns (bytes, absolute_url)."""
    full_url = url_path if url_path.startswith("http") else SERVER + url_path
    r = requests.get(full_url, timeout=8)
    r.raise_for_status()
    return r.content, full_url


def make_video_thumb(video_bytes):
    """Grab the first frame of a downloaded video via ffmpeg. Tkinter has no
    native video widget, so the toast shows this still frame with a play badge;
    clicking it opens the real file in the browser instead of playing inline."""
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in")
        dst = os.path.join(td, "thumb.png")
        with open(src, "wb") as f:
            f.write(video_bytes)
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", src, "-vframes", "1", dst],
                check=True, capture_output=True, timeout=15,
            )
            with open(dst, "rb") as f:
                return f.read()
        except Exception:
            return None


def build_media_widget(parent, media):
    """media = {"kind": "image"|"video", "url": "..."}. Returns a widget to pack
    above the body text, or None if the media couldn't be fetched/decoded —
    callers must tolerate that and just show the text toast without it.

    The returned widget carries a `.rescale_to_width(max_w)` method so the
    toast's drag-resize grip can grow/shrink the picture along with the card,
    not just the text body."""
    try:
        raw, full_url = fetch_media_bytes(media["url"])
    except Exception:
        return None

    is_video = media.get("kind") == "video"
    durations = None
    try:
        if is_video:
            thumb = make_video_thumb(raw)
            if not thumb:
                return None
            frames = [Image.open(io.BytesIO(thumb)).convert("RGBA")]
        else:
            img = Image.open(io.BytesIO(raw))
            if getattr(img, "is_animated", False):
                frames = [f.copy().convert("RGBA") for f in ImageSequence.Iterator(img)]
                durations = [f.info.get("duration", 80) or 80 for f in ImageSequence.Iterator(img)]
            else:
                frames = [img.convert("RGBA")]
    except Exception:
        return None

    orig_w, orig_h = frames[0].size
    if not orig_w or not orig_h:
        return None

    holder = tk.Label(parent, bg="#111827", cursor="hand2", bd=0)
    state = {"photos": [], "i": 0, "size": None}

    def render_at(max_w):
        # Cap so a runaway drag can't blow up memory resampling huge frames repeatedly.
        max_w = max(40, min(max_w, MEDIA_MAX_W * 3))
        scale = min(max_w / orig_w, MEDIA_MAX_H / orig_h, 1.0)
        size = (max(1, int(orig_w * scale)), max(1, int(orig_h * scale)))
        if size == state["size"]:
            return
        state["size"] = size
        state["photos"] = [ImageTk.PhotoImage(f.resize(size, Image.LANCZOS)) for f in frames]
        holder.image_list = state["photos"]  # keep every frame alive, not just the current one
        idx = min(state["i"], len(state["photos"]) - 1)
        holder.configure(image=state["photos"][idx])
        holder.image = state["photos"][idx]  # must keep the actual PhotoImage alive, not its Tk name

    render_at(MEDIA_MAX_W)
    holder.rescale_to_width = render_at

    if is_video:
        badge = tk.Label(holder, text="▶", fg="white", bg="#000000", font=("Segoe UI", 13, "bold"), padx=7, pady=3)
        badge.place(relx=0.5, rely=0.5, anchor="c")
        badge.bind("<Button-1>", lambda _e: webbrowser.open(full_url))
    elif durations and len(frames) > 1:
        def animate():
            if not holder.winfo_exists():
                return
            state["i"] = (state["i"] + 1) % len(state["photos"])
            holder.configure(image=state["photos"][state["i"]])
            holder.after(max(40, durations[state["i"]]), animate)

        holder.after(max(40, durations[0]), animate)

    holder.bind("<Button-1>", lambda _e: webbrowser.open(full_url))
    return holder


def show_toast(role, text, media=None):
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

    segments = build_segments(strip_markdown(text))
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

    if media and media.get("url"):
        media_widget = build_media_widget(win, media)
        if media_widget:
            win.media_widget = media_widget  # keep a strong ref alongside the Toplevel
            media_widget.pack(padx=14, pady=(0, 6))

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
    shown_lines = min(max(line_count, MIN_BODY_LINES), MAX_BODY_LINES)
    body.configure(height=shown_lines)
    if line_count > MAX_BODY_LINES:
        scrollbar = tk.Scrollbar(body, command=body.yview)
        body.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    win.update_idletasks()
    # Auto-size the window to the full reply right away instead of leaving
    # it locked at the placeholder 100px from the geometry() call above —
    # winfo_reqheight() reports what pack actually wants for the header row
    # + however many text rows body.configure(height=...) just set, so the
    # whole message is visible without Min needing to drag the grip first.
    req_h = win.winfo_reqheight()
    auto_x = win.winfo_screenwidth() - win_w - BANNER_MARGIN
    win.geometry(f"{win_w}x{req_h}+{auto_x}+{BANNER_MARGIN}")
    win.update_idletasks()
    active_toasts.append(win)
    reflow_toasts()
    win.update_idletasks()

    # Entrance: snap off-screen past the right edge at the resting y reflow_toasts
    # just computed, then slide+fade in from there — reads as "arriving from the
    # right, settling in toward the left" since the card is right-edge-anchored.
    rest_x, rest_y = win.winfo_x(), win.winfo_y()
    screen_w = win.winfo_screenwidth()
    win.geometry(f"{win_w}x{req_h}+{screen_w}+{rest_y}")

    def close(*_):
        if getattr(win, "_closing", False):
            return
        win._closing = True
        if win in active_toasts:
            active_toasts.remove(win)
        reflow_toasts()  # remaining toasts shift into this one's slot right away

        def _destroy():
            try:
                win.destroy()
            except Exception:
                pass

        # Exit: slide+fade back out past the right edge, accelerating away.
        animate_toast(win, win.winfo_x(), win.winfo_screenwidth(), 1.0, 0.0,
                      steps=14, delay=14, ease_out=False, on_done=_destroy)

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
        # Cap against what's actually on screen (shown_lines), not the raw
        # line_count: for a short reply the card is now taller than its text,
        # and clamping to line_count would make the grip snap it back down.
        new_lines = max(1, min(max(line_count, shown_lines), resize_state["lines"] + delta_lines))
        body.configure(height=new_lines)

        media_widget = getattr(win, "media_widget", None)
        if media_widget is not None and hasattr(media_widget, "rescale_to_width"):
            media_widget.rescale_to_width(new_w - 28)  # minus the row's own left+right padding

        # Re-derive the window height from actual widget sizes instead of the
        # fixed chrome_h math — the picture's height now changes with new_w too.
        win.update_idletasks()
        new_h = win.winfo_reqheight()
        win.geometry(f"{new_w}x{new_h}+{x}+{win.winfo_y()}")

    def resize_end(_e):
        resize_state.clear()
        reflow_toasts()
        arm_dismiss()

    grip.bind("<ButtonPress-1>", resize_start)
    grip.bind("<B1-Motion>", resize_drag)
    grip.bind("<ButtonRelease-1>", resize_end)

    animate_toast(win, screen_w, rest_x, 0.0, 1.0, steps=18, delay=14, ease_out=True)

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

    hover_widgets = [win, head_row, head, body]
    if getattr(win, "media_widget", None) is not None:
        hover_widgets.append(win.media_widget)
    for w in hover_widgets:
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
                        root.after(0, show_toast, m.get("role"), m.get("text", ""), m.get("media"))
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
