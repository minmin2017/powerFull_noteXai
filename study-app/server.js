// Video Study App — separate-port companion to PowerNote for watching
// AI-generated teaching videos with editable, timestamp-synced explanation
// text. Talks to the main PowerNote server (port 4321) over HTTP for chat
// and TTS; never touches PowerNote's own data files.
import express from "express";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const STUDY_PORT = Number(process.env.STUDY_PORT) || 4322;
const NOTE_BASE = process.env.NOTE_SERVER_URL || "http://127.0.0.1:4321";
const DATA_DIR = path.join(__dirname, "data");

function uid(prefix = "study") {
  return prefix + "_" + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
}

function readVideo(id) {
  const p = path.join(DATA_DIR, id, "explain.json");
  if (!fs.existsSync(p)) return null;
  try {
    return JSON.parse(fs.readFileSync(p, "utf8"));
  } catch {
    return null;
  }
}

function writeVideo(id, data) {
  const dir = path.join(DATA_DIR, id);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, "explain.json"), JSON.stringify(data, null, 2), "utf8");
}

function readVideoIndex() {
  if (!fs.existsSync(DATA_DIR)) return [];
  const out = [];
  for (const id of fs.readdirSync(DATA_DIR)) {
    const v = readVideo(id);
    if (v) out.push({ id: v.id, title: v.title, durationS: v.durationS, createdAt: v.createdAt || 0 });
  }
  out.sort((a, b) => b.createdAt - a.createdAt);
  return out;
}

const app = express();
app.use(express.json({ limit: "5mb" }));

// POST /videos {title, videoPath, segments} — Claude calls this right after
// rendering a new video: copies the local mp4 into this app's own storage
// and writes explain.json alongside it. videoPath must already exist on disk
// (this app runs on the same machine as the Claude Code session that rendered it).
app.post("/videos", (req, res) => {
  const { title, videoPath, segments } = req.body || {};
  if (!title || !String(title).trim()) return res.status(400).json({ error: "missing title" });
  if (!videoPath || !fs.existsSync(videoPath)) return res.status(400).json({ error: "videoPath does not exist" });
  if (!Array.isArray(segments) || segments.length === 0) return res.status(400).json({ error: "missing segments" });
  for (const s of segments) {
    if (typeof s.start !== "number" || typeof s.end !== "number" || typeof s.text !== "string")
      return res.status(400).json({ error: "each segment needs {start:number, end:number, text:string}" });
  }

  const id = uid("study");
  const dir = path.join(DATA_DIR, id);
  fs.mkdirSync(dir, { recursive: true });
  const destVideo = path.join(dir, "video" + path.extname(videoPath));
  fs.copyFileSync(videoPath, destVideo);

  const durationS = segments.length ? segments[segments.length - 1].end : 0;
  const data = {
    id,
    title: String(title).trim(),
    videoFile: path.basename(destVideo),
    durationS,
    createdAt: Date.now(),
    segments,
  };
  writeVideo(id, data);
  res.json(data);
});

app.get("/videos", (_req, res) => res.json(readVideoIndex()));

app.get("/videos/:id", (req, res) => {
  const v = readVideo(req.params.id);
  if (!v) return res.status(404).json({ error: "not found" });
  res.json(v);
});

app.get("/videos/:id/media", (req, res) => {
  const v = readVideo(req.params.id);
  if (!v) return res.status(404).end();
  const file = path.join(DATA_DIR, req.params.id, v.videoFile);
  if (!fs.existsSync(file)) return res.status(404).end();
  res.sendFile(file);
});

// PATCH /videos/:id/segments/:i {text} — used by both the in-app edit box
// and the edit_video_explanation MCP tool, so Claude and Min share one path.
app.patch("/videos/:id/segments/:i", (req, res) => {
  const v = readVideo(req.params.id);
  if (!v) return res.status(404).json({ error: "video not found" });
  const i = Number(req.params.i);
  if (!Number.isInteger(i) || i < 0 || i >= v.segments.length)
    return res.status(404).json({ error: "segment index out of range" });
  const { text } = req.body || {};
  if (typeof text !== "string" || !text.trim())
    return res.status(400).json({ error: "missing text" });
  v.segments[i].text = text.trim();
  writeVideo(v.id, v);
  res.json(v);
});

let studySectionId = null;

async function ensureStudySection() {
  if (studySectionId) return studySectionId;
  const state = await fetch(NOTE_BASE + "/api/state").then((r) => r.json());
  const existing = (state.chatSections || []).find((s) => (s.name || "").toLowerCase() === "study");
  if (existing) {
    studySectionId = existing.id;
    return studySectionId;
  }
  const created = await fetch(NOTE_BASE + "/api/chat-sections", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: "study" }),
  }).then((r) => r.json());
  studySectionId = created.id;
  return studySectionId;
}

// POST /chat {text} — sends a typed message into the "study" chat-section the
// exact same way the main PowerNote UI does (public/modules/voice.js
// submitUserInput), so any Claude Code window listening there (opened with
// `claude-listen.cmd study`) picks it up via the existing inbox mechanism.
app.post("/chat", async (req, res) => {
  const { text } = req.body || {};
  if (!text || !String(text).trim()) return res.status(400).json({ error: "missing text" });
  try {
    const section = await ensureStudySection();
    await fetch(NOTE_BASE + "/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role: "user", text, section }),
    });
    await fetch(NOTE_BASE + "/api/inbox", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, section }),
    });
    res.json({ ok: true, section });
  } catch (e) {
    res.status(502).json({ error: "could not reach PowerNote server (port 4321) — is it running?", detail: String(e) });
  }
});

// GET /chat-log — returns the "study" section's message history so the
// frontend chat panel can render it (polling, no WebSocket needed for MVP).
app.get("/chat-log", async (_req, res) => {
  try {
    const section = await ensureStudySection();
    const state = await fetch(NOTE_BASE + "/api/state").then((r) => r.json());
    const msgs = (state.chat || []).filter((m) => m.section === section);
    res.json({ section, messages: msgs });
  } catch (e) {
    res.status(502).json({ error: "could not reach PowerNote server", detail: String(e) });
  }
});

export { app, STUDY_PORT, NOTE_BASE, DATA_DIR, uid, readVideo, writeVideo, readVideoIndex };

// Every later task inserts its new routes ABOVE this line (before this
// listen call), never below it — this must stay the last statement in the
// file so the process actually stays alive and accepts connections.
app.listen(STUDY_PORT, "127.0.0.1", () => {
  console.log(`[study-app] listening on http://127.0.0.1:${STUDY_PORT}`);
});
