#!/usr/bin/env bash
# claude-wake.bash — schedule a ONE-SHOT self-wake of the Claude listener.
#
# WHY: when the Claude account session cap is hit, this session dies. There is no
# in-model way to "sleep until reset", so we hand the wake-up to a LOCAL, FREE
# systemd --user transient timer (no external/paid service). At the scheduled
# time it opens a terminal running claude-listen.bash, which re-arms the inbox
# listener and resumes work. Before scheduling, write what to continue into the
# memory note `resume-next` (MEMORY.md is auto-loaded, so the woken Claude sees it).
#
# Usage:
#   ./claude-wake.bash "3am" [section]     # wake at the next 03:00
#   ./claude-wake.bash "15:30" [section]   # wake at the next 15:30
#   ./claude-wake.bash "+90m" [section]    # wake 90 minutes from now
#   ./claude-wake.bash status              # show a pending wake
#   ./claude-wake.bash cancel              # cancel a pending wake
#
# section defaults to "main".

set -uo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
UNIT="claude-wake"
SECTION="${2:-main}"

case "${1:-}" in
  cancel)
    systemctl --user stop "${UNIT}.timer" 2>/dev/null
    systemctl --user reset-failed "${UNIT}.service" 2>/dev/null
    echo "cancelled any pending wake."
    exit 0 ;;
  status)
    systemctl --user list-timers "${UNIT}.timer" --all 2>/dev/null | sed -n '1,3p'
    exit 0 ;;
  "")
    echo "usage: claude-wake.bash \"3am\"|\"HH:MM\"|\"+90m\"|status|cancel [section]"; exit 1 ;;
esac

WHEN="$1"
# Resolve WHEN to an absolute "YYYY-MM-DD HH:MM:SS" for a one-shot OnCalendar.
if [[ "$WHEN" =~ ^\+([0-9]+)m$ ]]; then
  TS="$(date -d "+${BASH_REMATCH[1]} minutes" '+%Y-%m-%d %H:%M:%S')"
else
  TS="$(date -d "$WHEN" '+%Y-%m-%d %H:%M:%S' 2>/dev/null)"
  if [ -z "$TS" ]; then echo "cannot parse time: '$WHEN'"; exit 1; fi
  # if the parsed time is already past, roll to tomorrow
  if [ "$(date -d "$TS" +%s)" -le "$(date +%s)" ]; then
    TS="$(date -d "$WHEN tomorrow" '+%Y-%m-%d %H:%M:%S')"
  fi
fi

TERM_EMU="$(command -v gnome-terminal || command -v x-terminal-emulator || command -v xterm)"
if [ -z "$TERM_EMU" ]; then echo "no terminal emulator found"; exit 1; fi

# Command the timer runs: open a terminal that launches the listener and stays open.
WAKECMD="$(cat <<EOF
"$TERM_EMU" -- bash -lc '"$DIR/claude-listen.bash" "$SECTION"; exec bash'
EOF
)"

# One pending wake at a time.
systemctl --user stop "${UNIT}.timer" 2>/dev/null
systemctl --user reset-failed "${UNIT}.service" 2>/dev/null

systemd-run --user \
  --on-calendar="$TS" \
  --unit="$UNIT" \
  --setenv=DISPLAY="${DISPLAY:-:0}" \
  --setenv=XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}" \
  --setenv=DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-}" \
  bash -lc "$WAKECMD"

echo "self-wake scheduled for: $TS  (section: $SECTION)"
echo "reminder: update the 'resume-next' memory note so the woken session continues."
echo "cancel with: $DIR/claude-wake.bash cancel"
