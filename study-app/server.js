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

export { app, STUDY_PORT, NOTE_BASE, DATA_DIR, uid, readVideo, writeVideo, readVideoIndex };

// Every later task inserts its new routes ABOVE this line (before this
// listen call), never below it — this must stay the last statement in the
// file so the process actually stays alive and accepts connections.
app.listen(STUDY_PORT, "127.0.0.1", () => {
  console.log(`[study-app] listening on http://127.0.0.1:${STUDY_PORT}`);
});
