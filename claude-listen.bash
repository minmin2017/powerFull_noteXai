#!/usr/bin/env bash
# Usage:
#   ./claude-listen.bash              -> listen to main chat section (default)
#   ./claude-listen.bash "chat2"      -> bind to another section (multi-instance)
cd "$(dirname "$0")"

SECTION_INPUT="${1:-main}"

# start note server if not running
if ! curl -s -m 3 -o /dev/null "http://localhost:4321/api/state"; then
  echo "Note server not running - starting it..."
  bash "$(dirname "$0")/start.bash" &
  sleep 3
fi

# Resolve section name → real ID (server accepts name or id, but we want the canonical id
# so Claude gets it right from the start with no ambiguity)
CHAT_SECTION=$(curl -s "http://localhost:4321/api/state" | python3 -c "
import sys, json
d = json.load(sys.stdin)
k = '''$SECTION_INPUT'''.strip().lower()
for s in d.get('chatSections', []):
    if s['id'] == '''$SECTION_INPUT''' or (s.get('name','') or '').lower() == k:
        print(s['id'])
        sys.exit(0)
print('''$SECTION_INPUT''')
" 2>/dev/null || echo "$SECTION_INPUT")

echo "Opening Claude Code - listening to section: $SECTION_INPUT → id: $CHAT_SECTION"
CHAT_SECTION="$CHAT_SECTION" claude --dangerously-skip-permissions \
  "Read CLAUDE.md. You are bound to chat section id '$CHAT_SECTION' (real canonical ID, already resolved — do NOT look up a different ID). Arm a persistent background Monitor that polls ONLY this section: curl -s -G http://localhost:4321/api/inbox --data-urlencode section=$CHAT_SECTION --data-urlencode drain=true  every ~3s, and act on each message. Reply ONLY via the say_to_user MCP tool with section='$CHAT_SECTION'. Reply in Thai. Do not drain the shared inbox and do not touch other sections."
