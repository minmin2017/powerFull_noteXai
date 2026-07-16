#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo ""
echo "  Powerfull Note - starting (auto-restart on code changes)..."
echo "  เปิดเบราว์เซอร์ที่ http://localhost:4321 (Chrome/Firefox)"
echo ""

# install dependencies if missing
if [ ! -d "node_modules" ]; then
  echo "  Installing dependencies..."
  npm install
fi

# open browser after a short delay (server needs a moment to bind)
(sleep 1 && xdg-open "http://localhost:4321" 2>/dev/null || true) &

node --watch server.js
