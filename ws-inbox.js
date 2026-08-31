// WebSocket inbox listener — replaces the curl-poll Monitor loop.
// Each new inbox message for our section is printed to stdout (one line)
// so the Claude Code Monitor wakes only when there is real work to do.
//
// Usage:  node ws-inbox.js [section]
// Env:    CHAT_SECTION (overridden by argv[2])  PORT (default 4321)

import { WebSocket } from "ws";

const PORT = Number(process.env.PORT) || 4321;
// 127.0.0.1, not localhost: on this machine "localhost" resolves ::1 first and
// stalls ~2s against an IPv4-only server before falling back.
const BASE = `http://127.0.0.1:${PORT}`;
const WS_URL = `ws://127.0.0.1:${PORT}/ws`;
const SECTION = (process.argv[2] || process.env.CHAT_SECTION || "").trim();
const AGENT = (process.env.AGENT || "claude").trim();

async function drain() {
  const url = SECTION
    ? `${BASE}/api/inbox?drain=true&section=${encodeURIComponent(SECTION)}&agent=${AGENT}`
    : `${BASE}/api/inbox?drain=true&agent=${AGENT}`;
  try {
    const r = await fetch(url);
    return (await r.json()).items || [];
  } catch {
    return [];
  }
}

let lastInboxLen = 0;
let resolvedSectionId = null; // canonical ID resolved from first state broadcast

function resolveFromState(chatSections) {
  if (!SECTION || !Array.isArray(chatSections)) return null;
  const k = SECTION.trim().toLowerCase();
  const found = chatSections.find(
    (s) => s.id === SECTION || (s.name || "").toLowerCase() === k
  );
  return found ? found.id : SECTION; // fallback: treat SECTION as raw id
}

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
      // Resolve section name → ID once from the state's chatSections list
      if (!resolvedSectionId && SECTION) {
        resolvedSectionId = resolveFromState(msg.state?.chatSections);
        if (resolvedSectionId) {
          process.stderr.write(`[ws-inbox] section "${SECTION}" → id: ${resolvedSectionId}\n`);
        }
      }
      const inbox = msg.state?.inbox || [];
      const secId = resolvedSectionId;
      const mine = secId
        ? inbox.filter((m) => (m.section || "main") === secId)
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

// Heartbeat: touch /api/inbox every 15s even when idle, purely so the server's
// agentSeen tracker (read by usage-guard.js via /api/agent/status on quota
// reset, to decide whether to wake this session instead of spawning a new
// one) sees this Monitor as alive. The drain() call above only fires when a
// message actually arrives — long quiet periods would otherwise look "dead".
setInterval(() => {
  const sec = resolvedSectionId || SECTION;
  const url = sec
    ? `${BASE}/api/inbox?section=${encodeURIComponent(sec)}&agent=${AGENT}`
    : `${BASE}/api/inbox?agent=${AGENT}`;
  fetch(url).catch(() => {});
}, 15000);
