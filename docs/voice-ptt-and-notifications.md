# Voice PTT (Alt+P / Alt+O) + Desktop Toast Notifications

Two standalone Python daemons, launched automatically by `start.cmd` alongside the server.

## global_ptt.py — global push-to-talk

- **Alt+P** (hold, release to send) → bounces focus to the Powerfull Note Chrome
  window, switches `section=main`'s `agentListener` to `"claude"`, and lets the
  page's own Web Speech API listen. On release, focus returns to whatever
  window was active before *and* Chrome is minimized back down automatically.
- **Alt+O** → same flow, but switches `agentListener` to `"gemini"` instead —
  lets Min dictate to either agent with a single hotkey, no manual tab-switch
  needed.
- The `/api/ptt` (start/stop glow) and `/api/agent-listener` (switch mode)
  HTTP calls are fired in background threads *before* the focus-steal, not
  after — both used to run serially after the window switch, which is what
  made the mic feel slow to "wake up" after pressing the hotkey.
- `/api/ptt` is fired *before* `/api/agent-listener`, not after — the latter
  triggers a full-board `changed()` broadcast server-side (much heavier than
  `/api/ptt`'s lightweight `broadcastRaw`), so sending it first risked
  delaying the glow-triggering `/api/ptt` request behind it. This is why
  Alt+O (which always switches agent) could feel slower to show the glow
  than Alt+P (which usually doesn't change anything). Server also now skips
  the full broadcast in `/api/agent-listener` when the value isn't actually
  changing.
- Only ever run **one** `global_ptt.py` process — a stray leftover instance
  from a previous session double-fired every hotkey (two `/api/ptt` +
  `/api/agent-listener` calls per press) and was hard to notice since both
  copies behaved identically. Check with
  `Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*global_ptt*' }`
  if PTT ever feels inconsistent.
- Run standalone: `python global_ptt.py` (or `ptt-listen.cmd`).

## notify_daemon.py — custom desktop toast notifications

Polls `/api/state` (~1.5s) for new `role:"claude"`/`role:"gemini"` chat
messages and shows a card in the top-right corner of the screen — built with
tkinter, not the browser's Notification API, so Min can read full answers
(including rendered LaTeX equations, e.g. while studying) without switching
to the Chrome tab at all.

Features:
- Full message text, not truncated — scrolls internally if it doesn't fit
  `MAX_BODY_LINES`.
- Renders `$...$` / `$$...$$` segments as actual equation images (via a
  transparent-background matplotlib `Figure`, not `mathtext.math_to_image`
  directly — that call always composites onto an opaque white background,
  which is why the equation card looked "washed out" during
  development; RGBA image `savefig(transparent=True)` fixed it).
- Card width grows automatically to fit the widest equation image (capped at
  85% of screen width).
- Manually resizable: drag the "◢" grip in the bottom-left corner —
  horizontal drag changes width, vertical drag changes how many lines of the
  body are visible (adjusts the Text widget's `height` in lines directly,
  since just resizing the Tk window doesn't reveal more text on its own).
- Auto-dismisses after `DISPLAY_SECONDS` (6s), but hovering the mouse over
  the card pauses the countdown — it only starts counting again once the
  mouse leaves, so it won't vanish mid-read.
- Click the header to jump straight to the Chrome window; click ✕ to close.
- Run standalone: `python notify_daemon.py` (or `notify-listen.cmd`).

## In-app banner (superseded)

`public/modules/chat.js` also has an in-page Messenger-style popup
(`showMsgBanner`, toggle in ⚙️ ตั้งค่า > "แจ้งเตือนข้อความ (popup)") that fires
while the Power Note tab itself has focus. `notify_daemon.py` was added
afterward because Min wanted the notification to show *outside* the browser
entirely — both still run; the in-page one is a lighter fallback for when
Chrome is already focused.
