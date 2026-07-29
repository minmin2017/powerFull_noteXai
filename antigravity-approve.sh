#!/bin/bash
# antigravity-approve.sh — watches for the Antigravity "requesting your
# permission" desktop notification and auto-approves it: focuses the real
# Antigravity window (found by owning process, not by title — its title is
# whatever file/tab is open, so it changes constantly), sends "1" + Enter,
# then minimizes it back out of the way.
#
# Run in a terminal (foreground, Ctrl+C to stop) or backgrounded with `&`.
# Logs one line per action so it's easy to see what it's doing.

set -u

find_antigravity_window() {
  # The main Electron process has no --type=... flag (children/zygotes do).
  # It also owns a couple of tiny 10x10 / 200x200 helper windows, so pick
  # the LARGEST visible window it owns — that's the real IDE window.
  local pid best_id="" best_area=0
  for p in /proc/[0-9]*; do
    pid="${p#/proc/}"
    if [ -r "$p/cmdline" ] && [ "$(tr -d '\0' < "$p/cmdline" 2>/dev/null)" = "/home/minmin/Desktop/Antigravity-x64/antigravity" ]; then
      for id in $(xdotool search --onlyvisible --pid "$pid" 2>/dev/null); do
        geo=$(xdotool getwindowgeometry --shell "$id" 2>/dev/null)
        w=$(echo "$geo" | grep '^WIDTH=' | cut -d= -f2)
        h=$(echo "$geo" | grep '^HEIGHT=' | cut -d= -f2)
        area=$(( ${w:-0} * ${h:-0} ))
        if [ "$area" -gt "$best_area" ]; then
          best_area=$area
          best_id=$id
        fi
      done
    fi
  done
  echo "$best_id"
}

approve() {
  local title="$1" body="$2"
  echo "[$(date +%H:%M:%S)] permission prompt seen: $title -- $body"
  local win
  win=$(find_antigravity_window)
  if [ -z "$win" ]; then
    echo "[$(date +%H:%M:%S)] could not find the Antigravity window — skipping (nothing sent)"
    return
  fi
  local active_win
  active_win=$(xdotool getactivewindow 2>/dev/null)

  if [ "$active_win" = "$win" ]; then
    echo "[$(date +%H:%M:%S)] Antigravity is already active — approving without switching/minimizing"
    xdotool key 1
    sleep 0.3
    xdotool key Return
  else
    echo "[$(date +%H:%M:%S)] Antigravity is in background — activating, approving, and minimizing"
    xdotool windowactivate "$win"
    sleep 0.5
    xdotool key 1
    sleep 0.3
    xdotool key Return
    sleep 0.3
    xdotool windowminimize "$win"
  fi
  echo "[$(date +%H:%M:%S)] approved window $win"
}

echo "[$(date +%H:%M:%S)] watching for Antigravity permission prompts (Ctrl+C to stop)..."

dbus-monitor --session "interface='org.freedesktop.Notifications',member='Notify'" 2>/dev/null | python3 -u -c '
import sys, re

def flush(strings):
    if len(strings) >= 4:
        title = strings[2]
        body = strings[3] if len(strings) > 3 else ""
        blob = title + " " + body
        if re.search(r"requesting your permission|permission.*(needed|required)|needs your permission", blob, re.I):
            print(f"{title}\t{body}", flush=True)

strings = []
in_call = False
for line in sys.stdin:
    if line.startswith(("method call", "method return", "signal", "error")):
        if in_call:
            flush(strings)
        in_call = line.startswith("method call") and "Notify" in line
        strings = []
        continue
    if in_call:
        m = re.match(r"\s*string \"(.*)\"\s*$", line.rstrip("\n"))
        if m:
            strings.append(m.group(1))
' | while IFS=$'\t' read -r title body; do
  approve "$title" "$body"
done
