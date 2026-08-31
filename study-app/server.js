// Video Study App — separate-port companion to PowerNote for watching
// AI-generated teaching videos with editable, timestamp-synced explanation
// text. Talks to the main PowerNote server (port 4321) over HTTP for chat
// and TTS; never touches PowerNote's own data files.
import express from "express";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const STUDY_PORT = Number(process.env.STUDY_PORT) || 4322;
const NOTE_BASE = process.env.NOTE_SERVER_URL || "http://127.0.0.1:4321";
const DATA_DIR = path.join(__dirname, "data");

function uid(prefix = "study") {
  return prefix + "_" + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
}

function readVideo(id) {
  if (!/^study_[a-z0-9]+$/i.test(id)) return null;
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

// Remux (never re-encode — just repackage) the source video into an mp4
// with the "moov" metadata atom moved to the front. A plain file copy of a
// manim/ffmpeg-concat output leaves moov trailing after the mdat block,
// which plays fine in a native player (which can seek anywhere in a local
// file) but leaves a browser <video> tag stuck at readyState 0 forever,
// since it can't get duration/seek info without either the moov atom up
// front or downloading the whole file first. Found by registering the real
// 3.5-minute Agile Robot video and watching it hang in Chrome.
function remuxFaststart(srcPath, destPath) {
  return new Promise((resolve, reject) => {
    const ff = spawn("ffmpeg", ["-y", "-v", "error", "-i", srcPath, "-c", "copy", "-movflags", "+faststart", destPath]);
    let stderr = "";
    ff.stderr.on("data", (d) => { stderr += d; });
    ff.on("close", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`ffmpeg remux failed (code ${code}): ${stderr.trim()}`));
    });
    ff.on("error", reject);
  });
}

// Splits a "สอนทีละหน้า" note's markdown into ordered text chunks, one per
// page marker, matching either heading style Claude has used so far:
//   "## 📄 หน้า 6 — ..."   (Electrical Power System chapters)
//   "**หน้า 6-7** — **Title**:"  (Power Electronics / Fluid Power Control notes)
// Falls back to treating the whole note as one chunk if no markers found.
function splitNoteIntoPageChunks(noteText) {
  const lines = noteText.split(/\r?\n/);
  const markerRe = /^(##\s*.*?หน้า\s*\d|\*\*หน้า[^*]*\*\*)/;
  const starts = [];
  lines.forEach((line, i) => {
    if (markerRe.test(line.trim())) starts.push(i);
  });
  if (starts.length === 0) return [noteText.trim()].filter(Boolean);
  const chunks = [];
  for (let k = 0; k < starts.length; k++) {
    const from = starts[k];
    const to = k + 1 < starts.length ? starts[k + 1] : lines.length;
    chunks.push(lines.slice(from, to).join("\n"));
  }
  return chunks;
}

// Strips markdown/Obsidian syntax that isn't meant to be read as prose:
// wiki embeds (images/video/pdf), fenced code blocks (mermaid etc.), and
// callout admonition markers (keeps the callout's own text).
function cleanChunkText(raw) {
  return raw
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/!\[\[[^\]]*\]\]/g, " ")
    .replace(/!\[[^\]]*\]\([^)]*\)/g, " ")
    .replace(/^\s*>\s*\[![\w-]+\]\s*/gm, "")
    .replace(/^\s*>\s?/gm, "")
    .replace(/[ \t]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

// Turns a note's page chunks into {start,end,text} segments spanning the
// full clip duration, each segment's share proportional to its cleaned
// text length (a denser page gets more on-screen time than a one-liner).
// Heuristic v1: real narration timing (if these clips ever get voiceover)
// or manual per-scene review will beat this — it's meant to save Claude
// from hand-deriving timestamps for silent/no-audio clips, not to replace
// visual verification for anything that matters (e.g. an exam-prep video
// someone will study frame-by-frame).
function buildSegmentsFromNote(noteText, durationS) {
  const chunks = splitNoteIntoPageChunks(noteText).map(cleanChunkText).filter((t) => t.length > 0);
  if (chunks.length === 0) return [{ start: 0, end: durationS, text: "(no content parsed from note)" }];
  const weights = chunks.map((t) => Math.max(t.length, 40));
  const totalWeight = weights.reduce((a, b) => a + b, 0);
  const segments = [];
  let cursor = 0;
  chunks.forEach((text, i) => {
    const isLast = i === chunks.length - 1;
    const share = isLast ? durationS - cursor : (weights[i] / totalWeight) * durationS;
    const start = cursor;
    const end = isLast ? durationS : Math.min(durationS, cursor + share);
    segments.push({ start: Number(start.toFixed(2)), end: Number(end.toFixed(2)), text });
    cursor = end;
  });
  return segments;
}

function ffprobeDuration(filePath) {
  return new Promise((resolve, reject) => {
    const ff = spawn("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", filePath]);
    let out = "", err = "";
    ff.stdout.on("data", (d) => { out += d; });
    ff.stderr.on("data", (d) => { err += d; });
    ff.on("close", (code) => {
      const val = parseFloat(out.trim());
      if (code === 0 && Number.isFinite(val)) resolve(val);
      else reject(new Error(`ffprobe failed (code ${code}): ${err.trim()}`));
    });
    ff.on("error", reject);
  });
}

// Shared by POST /videos and POST /videos/auto: remux the source file into
// this app's own storage and persist explain.json.
async function saveVideoRecord({ title, videoPath, segments }) {
  const id = uid("study");
  const dir = path.join(DATA_DIR, id);
  fs.mkdirSync(dir, { recursive: true });
  const destVideo = path.join(dir, "video.mp4");
  await remuxFaststart(videoPath, destVideo);
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
  return data;
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
// PowerNote's own page (origin NOTE_BASE, normally :4321) fetch()es this
// server's endpoints directly (e.g. the "🎓 ติววิดีโอ" button's reachability
// check before opening a new tab) — without this header the browser blocks
// that cross-origin fetch even though the request itself succeeds, which
// looks exactly like "server unreachable" from the caller's point of view.
app.use((req, res, next) => {
  res.header("Access-Control-Allow-Origin", NOTE_BASE);
  next();
});
app.use(express.json({ limit: "5mb" }));
app.use(express.static(path.join(__dirname, "public")));

// POST /videos {title, videoPath, segments} — Claude calls this right after
// rendering a new video: copies the local mp4 into this app's own storage
// and writes explain.json alongside it. videoPath must already exist on disk
// (this app runs on the same machine as the Claude Code session that rendered it).
app.post("/videos", async (req, res) => {
  const { title, videoPath, segments } = req.body || {};
  if (!title || !String(title).trim()) return res.status(400).json({ error: "missing title" });
  if (!videoPath || !fs.existsSync(videoPath)) return res.status(400).json({ error: "videoPath does not exist" });
  if (!Array.isArray(segments) || segments.length === 0) return res.status(400).json({ error: "missing segments" });
  for (const s of segments) {
    if (typeof s.start !== "number" || typeof s.end !== "number" || typeof s.text !== "string")
      return res.status(400).json({ error: "each segment needs {start:number, end:number, text:string}" });
  }

  try {
    const data = await saveVideoRecord({ title, videoPath, segments });
    res.json(data);
  } catch (e) {
    return res.status(500).json({ error: "video processing failed", detail: String(e.message || e) });
  }
});

// POST /videos/auto {title, videoPath, notePath|noteText} — same as POST
// /videos but derives segments itself from a "สอนทีละหน้า" note instead of
// requiring the caller (Claude) to hand-author {start,end,text} for every
// segment. Meant for the common case: a silent Manim clip whose companion
// note already has the real explanation text, just needs it time-sliced
// across the clip's duration.
//
// IMPORTANT for chapters split into several short clips (the usual pattern
// here — e.g. one chapter note, four EP-numbered clips): pass `noteText`
// with just the excerpt covering THAT clip's pages, not notePath to the
// whole chapter file — otherwise every page in the file gets force-fit into
// one clip's short duration. notePath (whole file) is for the case where
// one video covers the entire note. See buildSegmentsFromNote for the
// timing heuristic and its limits (proportional-to-text-length, not real
// narration timing — fine for a first pass, not a substitute for watching
// the clip if precise sync matters).
app.post("/videos/auto", async (req, res) => {
  const { title, videoPath, notePath, noteText: rawNoteText } = req.body || {};
  if (!title || !String(title).trim()) return res.status(400).json({ error: "missing title" });
  if (!videoPath || !fs.existsSync(videoPath)) return res.status(400).json({ error: "videoPath does not exist" });
  if (!notePath && !rawNoteText) return res.status(400).json({ error: "provide notePath or noteText" });
  if (notePath && !fs.existsSync(notePath)) return res.status(400).json({ error: "notePath does not exist" });

  let noteText, durationS;
  try {
    noteText = rawNoteText || fs.readFileSync(notePath, "utf8");
    durationS = await ffprobeDuration(videoPath);
  } catch (e) {
    return res.status(500).json({ error: "could not read note or probe video", detail: String(e.message || e) });
  }

  const segments = buildSegmentsFromNote(noteText, durationS);
  try {
    const data = await saveVideoRecord({ title, videoPath, segments });
    res.json(data);
  } catch (e) {
    return res.status(500).json({ error: "video processing failed", detail: String(e.message || e) });
  }
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

// Re-validates the cached section id against the CURRENT project's state on
// every call (chat sections live inside each PowerNote project's state, and
// /api/state only returns the active project's — so the cached id goes stale
// the moment Min switches projects). Pass `state` if the caller already
// fetched /api/state, to avoid a redundant fetch.
async function ensureStudySection(state) {
  if (!state) state = await fetch(NOTE_BASE + "/api/state").then((r) => r.json());
  if (studySectionId) {
    const stillValid = (state.chatSections || []).some((s) => s.id === studySectionId);
    if (stillValid) return studySectionId;
    studySectionId = null;
  }
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
    const state = await fetch(NOTE_BASE + "/api/state").then((r) => r.json());
    const section = await ensureStudySection(state);
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
