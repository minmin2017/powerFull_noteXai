#!/usr/bin/env bash
# Usage:
#   ./claude-listen.bash              -> listen to main chat section (default)
#   ./claude-listen.bash "งานวิจัย"   -> bind to another section (multi-instance)
cd "$(dirname "$0")"

CHAT_SECTION="${1:-main}"

# start note server if not running
if ! curl -s -m 3 -o /dev/null "http://localhost:4321/api/state"; then
  echo "Note server not running - starting it..."
  bash "$(dirname "$0")/start.bash" &
  sleep 3
fi

echo "Opening Claude Code - listening to chat section: $CHAT_SECTION"
CHAT_SECTION="$CHAT_SECTION" claude --dangerously-skip-permissions \
  "Read CLAUDE.md. You are bound to chat section '$CHAT_SECTION' (also in env CHAT_SECTION). Arm a persistent background Monitor that polls ONLY this section: curl -s -G http://localhost:4321/api/inbox --data-urlencode section=$CHAT_SECTION --data-urlencode drain=true  every ~3s, and act on each message. Reply ONLY via the say_to_user MCP tool (it auto-targets this section from env). Reply in Thai. Do not drain the shared inbox and do not touch other sections."
