// WebSocket inbox listener — replaces the curl-poll Monitor loop.
// Each new inbox message for our section is printed to stdout (one line)
// so the Claude Code Monitor wakes only when there is real work to do.
//
// Usage:  node ws-inbox.js [section]
// Env:    CHAT_SECTION (overridden by argv[2])  PORT (default 4321)

import { WebSocket } from "ws";

const PORT = Number(process.env.PORT) || 4321;
const BASE = `http://localhost:${PORT}`;
const WS_URL = `ws://localhost:${PORT}/ws`;
const SECTION = (process.argv[2] || process.env.CHAT_SECTION || "").trim();

async function drain() {
  const url = SECTION
    ? `${BASE}/api/inbox?drain=true&section=${encodeURIComponent(SECTION)}`
    : `${BASE}/api/inbox?drain=true`;
  try {
    const r = await fetch(url);
    return (await r.json()).items || [];
  } catch {
    return [];
  }
}

let lastInboxLen = 0;

function connect() {
  const ws = new WebSocket(WS_URL);

  ws.on("open", () => {
    process.stderr.write(
      `[ws-inbox] connected${SECTION ? ` (section: ${SECTION})` : " (all sections)"}\n`
    );
  });

  ws.on("message", async (data) => {
    try {
      const msg = JSON.parse(data);
      if (msg.type !== "state") return;
      const inbox = msg.state?.inbox || [];
      const mine = SECTION
        ? inbox.filter((m) => (m.section || "main") === SECTION)
        : inbox;
      if (!mine.length) { lastInboxLen = 0; return; }
      // Only drain when count grew (new items arrived), not on unrelated broadcasts.
      if (mine.length <= lastInboxLen) return;
      lastInboxLen = mine.length;
      const items = await drain();
      lastInboxLen = 0;
      for (const item of items) {
        // One line per message → one Monitor notification per message.
        console.log(item.text.replace(/\n/g, " "));
      }
    } catch {}
  });

  ws.on("close", () => {
    process.stderr.write("[ws-inbox] disconnected, reconnecting in 1.5s\n");
    setTimeout(connect, 1500);
  });

  ws.on("error", () => {});
}

connect();
