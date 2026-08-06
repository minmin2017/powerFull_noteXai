// background.js — powerNote Web Speech Helper
//
// Bridges the system-wide Alt+P hotkey (global_ptt.py) to an offscreen document
// that listens without a visible window, so nothing has to steal focus.

const SERVER = "http://127.0.0.1:4321";
const WS_URL = "ws://127.0.0.1:4321/ws";
const SECTION = "main";
const KEEPALIVE = "pn-keepalive";

let socket = null;

function connect() {
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) return;

  socket = new WebSocket(WS_URL);

  socket.onopen = () => {
    console.log("[Background] connected to powerNote");
    announce();
  };

  socket.onmessage = (event) => {
    // The server broadcasts the whole project state on every change — hundreds
    // of KB. Parsing all of that here would burn CPU for nothing, so match the
    // one frame shape we care about (broadcastRaw serialises `type` first) and
    // drop everything else without ever calling JSON.parse.
    const raw = event.data;
    if (typeof raw !== "string" || !raw.startsWith('{"type":"ptt"')) return;
    let data;
    try {
      data = JSON.parse(raw);
    } catch {
      return;
    }
    if (data.active && data.mode === "extension") startListening();
    else if (!data.active) stopListening();
  };

  socket.onclose = () => {
    socket = null;
    setTimeout(connect, 3000);
  };

  socket.onerror = () => {
    try {
      if (socket) socket.close();
    } catch {}
  };
}

// Tell global_ptt.py we exist. It refuses to run in "extension" mode unless
// this ping is recent, because a missing extension makes every key press light
// up the screen border and then record nothing at all.
function announce() {
  fetch(`${SERVER}/api/ptt/extension-ping`, { method: "POST" }).catch(() => {});
}

// An MV3 service worker is torn down after ~30s idle, which would silently kill
// the socket and leave Alt+P doing nothing. A periodic alarm wakes it back up,
// and the top-level connect() on each wake re-opens the socket.
chrome.alarms.create(KEEPALIVE, { periodInMinutes: 0.5 });
chrome.alarms.onAlarm.addListener((a) => {
  if (a.name !== KEEPALIVE) return;
  connect();
  announce();
});
chrome.runtime.onStartup.addListener(connect);
chrome.runtime.onInstalled.addListener(connect);

connect();

async function ensureOffscreen() {
  if (await chrome.offscreen.hasDocument()) return;
  await chrome.offscreen.createDocument({
    url: "offscreen.html",
    reasons: ["USER_MEDIA"],
    justification: "Transcribe push-to-talk audio in the background",
  });
}

async function startListening() {
  try {
    await ensureOffscreen();
    await chrome.runtime.sendMessage({ target: "offscreen", type: "start" });
  } catch (e) {
    console.error("[Background] start failed:", e);
  }
}

async function stopListening() {
  try {
    if (!(await chrome.offscreen.hasDocument())) return;
    await chrome.runtime.sendMessage({ target: "offscreen", type: "stop" });
  } catch (e) {
    console.error("[Background] stop failed:", e);
  }
}

chrome.runtime.onMessage.addListener((message) => {
  if (message && message.target === "background" && message.type === "transcript") {
    const text = (message.text || "").trim();
    if (text) postTranscript(text);
  }
});

async function postTranscript(text) {
  const post = (path, body) =>
    fetch(`${SERVER}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  try {
    await Promise.all([
      post("/api/chat", { role: "user", text, section: SECTION }),
      post("/api/inbox", { text, section: SECTION }),
      post("/api/voice", { text }),
    ]);
    console.log("[Background] sent:", text);
  } catch (e) {
    console.error("[Background] could not reach powerNote:", e);
  }
}
