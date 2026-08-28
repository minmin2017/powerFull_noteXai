# Video Study App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone, separate-port "study app" where Min chats with Claude to commission AI-generated teaching videos, watches them with timestamp-synced explanation text he (or Claude) can edit, warps the video to any segment, and hears any segment read aloud in natural free Thai TTS.

**Architecture:** A new lightweight Express server (`study-app/server.js`, own port) is spawned as a child process by the existing `server.js` (same pattern as its `tts_worker.py` spawn). It serves its own frontend and stores each video's data (`video.mp4` + `explain.json`) under `study-app/data/<id>/`, completely separate from PowerNote's own state. It has no chat logic of its own — it proxies typed chat messages into the *existing* chat-section/inbox mechanism in `server.js` (a new section called "study"), and reuses the *existing* `/api/tts` endpoint for read-aloud. A Claude Code window Min opens with `claude-listen.cmd study` listens to that section, authors+renders new videos with the manim-teaching-video skill, and registers the finished video with the study-app server via `POST /videos`.

**Tech Stack:** Node.js (ESM, `"type": "module"`), Express 4 (already a dependency — no new npm packages needed), vanilla JS/HTML/CSS frontend (matches the rest of the project — no framework), MCP SDK (`@modelcontextprotocol/sdk`, already a dependency) for the 3 new tools.

**Spec:** `docs/superpowers/specs/2026-08-28-video-study-app-design.md`

## Global Constraints

- No transcription/whisper/cloud-STT pipeline anywhere in this feature (spec §3.1, §8) — `explain.json` is always authored directly by Claude, never derived from audio.
- Study app data lives under `study-app/data/` — never touches `data/projects/*.json` (PowerNote's own state).
- TTS must use the existing `/api/tts` endpoint on the main server (port 4321) — do not add a new TTS integration (spec §2, already free/unlimited via `edge-tts`).
- Chat must reuse the existing chat-section/inbox mechanism on the main server — do not build a second chat backend (spec §5.1).
- This project has no automated test runner (`package.json` has no `test` script, no jest/mocha/vitest dependency) — verification steps in this plan use real `curl`/`node -e`/browser checks instead of a unit-test framework, matching how `docs/superpowers/specs/2026-08-22-startup-and-onboarding-design.md` verifies its own tasks. Do not add a test framework as a side effect of this plan.
- Follow existing code style exactly: ESM imports, `const __dirname = path.dirname(fileURLToPath(import.meta.url));`, `uid(prefix)`-style id generation, `Number(process.env.X) || default` for ports.

---

### Task 1: Study app server skeleton + video storage helpers

**Files:**
- Create: `study-app/server.js`
- Create: `study-app/data/.gitkeep`
- Modify: `.gitignore` (add `study-app/data/*` except `.gitkeep`)

**Interfaces:**
- Produces: `readVideoIndex()` → `Array<{id, title, durationS, createdAt}>` (scans `study-app/data/*/explain.json`)
- Produces: `readVideo(id)` → full parsed `explain.json` object or `null` if missing
- Produces: `writeVideo(id, data)` → writes `study-app/data/<id>/explain.json` (pretty JSON, matches spec §5.4 shape)
- Produces: `STUDY_PORT` (const, `Number(process.env.STUDY_PORT) || 4322`)
- Produces: `NOTE_BASE` (const, `process.env.NOTE_SERVER_URL || "http://127.0.0.1:4321"`)

- [ ] **Step 1: Create the data directory placeholder**

```bash
mkdir -p study-app/data
touch study-app/data/.gitkeep
```

- [ ] **Step 2: Add the gitignore rule**

Append to `.gitignore`:
```
study-app/data/*
!study-app/data/.gitkeep
```

- [ ] **Step 3: Write the server skeleton**

`study-app/server.js`:
```js
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

export { app, STUDY_PORT, NOTE_BASE, DATA_DIR, uid, readVideo, writeVideo, readVideoIndex };
```

- [ ] **Step 4: Verify it loads without error**

Run: `node -e "import('./study-app/server.js').then(() => console.log('LOADS_OK'))"`
Expected: prints `LOADS_OK`, no exceptions

- [ ] **Step 5: Commit**

```bash
git add study-app/server.js study-app/data/.gitkeep .gitignore
git commit -m "study-app: server skeleton + video storage helpers"
```

---

### Task 2: `POST /videos` — register a finished video

**Files:**
- Modify: `study-app/server.js`

**Interfaces:**
- Consumes: `writeVideo`, `uid`, `DATA_DIR` from Task 1
- Produces: `POST /videos` route — request body `{title: string, videoPath: string (absolute local path), segments: [{start:number, end:number, text:string}]}`, response `{id, title, durationS, segments}`

- [ ] **Step 1: Add the route**

Insert before `export { ... }` in `study-app/server.js`:
```js
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
```

- [ ] **Step 2: Start the server temporarily and verify with a real request**

```bash
STUDY_PORT=4399 node study-app/server.js &
sleep 1
echo '{"hello":"world"}' > /tmp/dummy.mp4    # stand-in file, just needs to exist
curl -s -X POST http://127.0.0.1:4399/videos \
  -H "Content-Type: application/json" \
  -d '{"title":"ทดสอบ","videoPath":"/tmp/dummy.mp4","segments":[{"start":0,"end":5,"text":"ทดสอบข้อความ"}]}'
kill %1
```

Expected: JSON response with a `study_...` id, `title:"ทดสอบ"`, `durationS:5`; and `study-app/data/study_.../video.mp4` + `explain.json` now exist on disk (verify with `ls study-app/data/`).

- [ ] **Step 3: Clean up the test artifact and commit**

```bash
rm -rf study-app/data/study_*
git add study-app/server.js
git commit -m "study-app: POST /videos registers a rendered video + explain.json"
```

---

### Task 3: List/detail/media routes

**Files:**
- Modify: `study-app/server.js`

**Interfaces:**
- Consumes: `readVideo`, `readVideoIndex`, `DATA_DIR`
- Produces: `GET /videos` → `Array<{id,title,durationS,createdAt}>`; `GET /videos/:id` → full video object or 404; `GET /videos/:id/media` → streams the video file

- [ ] **Step 1: Add the three routes**

```js
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
```

- [ ] **Step 2: Verify against a real registered video**

```bash
STUDY_PORT=4399 node study-app/server.js &
sleep 1
echo dummy > /tmp/dummy2.mp4
ID=$(curl -s -X POST http://127.0.0.1:4399/videos -H "Content-Type: application/json" \
  -d '{"title":"t2","videoPath":"/tmp/dummy2.mp4","segments":[{"start":0,"end":3,"text":"x"}]}' | node -e "process.stdin.on('data',d=>console.log(JSON.parse(d).id))")
curl -s http://127.0.0.1:4399/videos | grep -q "$ID" && echo LIST_OK
curl -s http://127.0.0.1:4399/videos/$ID | grep -q '"title":"t2"' && echo DETAIL_OK
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:4399/videos/$ID/media
kill %1
rm -rf study-app/data/study_*
```

Expected: `LIST_OK`, `DETAIL_OK`, and `200` from the media request.

- [ ] **Step 3: Commit**

```bash
git add study-app/server.js
git commit -m "study-app: list/detail/media routes for registered videos"
```

---

### Task 4: `PATCH /videos/:id/segments/:i` — edit one segment's text

**Files:**
- Modify: `study-app/server.js`

**Interfaces:**
- Consumes: `readVideo`, `writeVideo`
- Produces: `PATCH /videos/:id/segments/:i` — body `{text: string}`, response the updated video object; 404 if video or index missing

- [ ] **Step 1: Add the route**

```js
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
```

- [ ] **Step 2: Verify edit persists to disk**

```bash
STUDY_PORT=4399 node study-app/server.js &
sleep 1
echo dummy > /tmp/dummy3.mp4
ID=$(curl -s -X POST http://127.0.0.1:4399/videos -H "Content-Type: application/json" \
  -d '{"title":"t3","videoPath":"/tmp/dummy3.mp4","segments":[{"start":0,"end":3,"text":"เดิม"}]}' | node -e "process.stdin.on('data',d=>console.log(JSON.parse(d).id))")
curl -s -X PATCH http://127.0.0.1:4399/videos/$ID/segments/0 -H "Content-Type: application/json" \
  -d '{"text":"แก้ไขแล้ว"}' | grep -q "แก้ไขแล้ว" && echo PATCH_OK
cat study-app/data/$ID/explain.json | grep -q "แก้ไขแล้ว" && echo PERSIST_OK
kill %1
rm -rf study-app/data/study_*
```

Expected: `PATCH_OK` and `PERSIST_OK` both print.

- [ ] **Step 3: Commit**

```bash
git add study-app/server.js
git commit -m "study-app: PATCH segment endpoint for editing explanation text"
```

---

### Task 5: `POST /chat` — proxy into the existing chat-section mechanism

**Files:**
- Modify: `study-app/server.js`

**Interfaces:**
- Consumes: `NOTE_BASE`
- Produces: `ensureStudySection()` → resolves/creates the "study" chat-section id on the main server, caches it in memory; `POST /chat` route — body `{text: string}`, mirrors `public/modules/voice.js:345-350`'s `submitUserInput` (calls `/api/chat`, `/api/inbox`, `/api/voice` on the main server) but with `section` fixed to the resolved "study" section id

- [ ] **Step 1: Add the section-resolution helper and route**

```js
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
```

- [ ] **Step 2: Verify against the real running main server**

This requires the main PowerNote server actually running on port 4321.

```bash
STUDY_PORT=4399 node study-app/server.js &
sleep 1
curl -s -X POST http://127.0.0.1:4399/chat -H "Content-Type: application/json" -d '{"text":"ทดสอบแชท study"}'
curl -s http://127.0.0.1:4399/chat-log | grep -q "ทดสอบแชท study" && echo CHATLOG_OK
kill %1
```

Expected: first curl returns `{"ok":true,"section":"sec_..."}`; `CHATLOG_OK` prints; and opening PowerNote's own UI shows a new "study" tab in the chat panel with the test message in it.

- [ ] **Step 3: Commit**

```bash
git add study-app/server.js
git commit -m "study-app: proxy chat into the existing study chat-section"
```

---

### Task 6: Frontend shell — video picker + layout skeleton

**Files:**
- Create: `study-app/public/index.html`
- Create: `study-app/public/style.css`
- Create: `study-app/public/app.js`
- Modify: `study-app/server.js` (serve the `public/` dir as static)

**Interfaces:**
- Consumes: `GET /videos` (Task 3)
- Produces: a working page at `http://127.0.0.1:4322/` that lists existing videos and lets Min click one to open it (sets `?v=<id>` in the URL)

- [ ] **Step 1: Serve the static frontend**

Add near the top of `study-app/server.js`, after the `express.json()` line:
```js
app.use(express.static(path.join(__dirname, "public")));
```

- [ ] **Step 2: Write the HTML skeleton**

`study-app/public/index.html`:
```html
<!doctype html>
<html lang="th">
<head>
  <meta charset="utf-8" />
  <title>แอปติววิดิโอ</title>
  <link rel="stylesheet" href="style.css" />
</head>
<body>
  <header class="topbar">
    <h1>🎓 แอปติววิดิโอ</h1>
    <button id="btn-back-to-list" class="hidden">← รายการวิดิโอ</button>
  </header>

  <section id="picker">
    <h2>เลือกวิดิโอ</h2>
    <div id="video-list"></div>
    <p class="hint">สั่งสร้างวิดิโอใหม่ได้จากกล่องแชทด้านล่างเมื่อยังไม่มีวิดิโอเลย</p>
  </section>

  <section id="player-view" class="hidden">
    <div class="left-pane">
      <video id="video" controls></video>
    </div>
    <div class="right-pane">
      <div id="segments"></div>
    </div>
  </section>

  <footer id="chat-box">
    <div id="chat-log"></div>
    <form id="chat-form">
      <input id="chat-input" type="text" placeholder="สั่งให้ Claude สร้างวิดิโอ หรือถามเพิ่มเกี่ยวกับวิดิโอนี้..." autocomplete="off" />
      <button type="submit">ส่ง</button>
    </form>
  </footer>

  <script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 3: Write minimal CSS (layout only, no polish yet — Task 11 covers visual design)**

`study-app/public/style.css`:
```css
* { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, sans-serif; display: flex; flex-direction: column; height: 100vh; }
.topbar { display: flex; align-items: center; gap: 12px; padding: 10px 16px; border-bottom: 1px solid #ddd; }
.hidden { display: none !important; }
#picker { padding: 16px; overflow-y: auto; }
#video-list .video-card { padding: 10px; border: 1px solid #ddd; border-radius: 8px; margin-bottom: 8px; cursor: pointer; }
#player-view { flex: 1; display: flex; overflow: hidden; }
.left-pane { flex: 1; display: flex; align-items: center; justify-content: center; background: #000; }
.left-pane video { max-width: 100%; max-height: 100%; }
.right-pane { width: 380px; overflow-y: auto; border-left: 1px solid #ddd; padding: 8px; }
.segment-card { border: 1px solid #ddd; border-radius: 8px; padding: 8px; margin-bottom: 8px; }
.segment-card.active { border-color: #6366f1; background: #eef; }
#chat-box { border-top: 1px solid #ddd; padding: 8px 16px; }
#chat-log { max-height: 120px; overflow-y: auto; font-size: 13px; margin-bottom: 6px; }
#chat-form { display: flex; gap: 8px; }
#chat-input { flex: 1; padding: 6px 10px; }
```

- [ ] **Step 4: Write the picker logic**

`study-app/public/app.js`:
```js
const params = new URLSearchParams(location.search);

async function loadPicker() {
  const videos = await fetch("/videos").then((r) => r.json());
  const list = document.getElementById("video-list");
  list.innerHTML = "";
  if (videos.length === 0) {
    list.innerHTML = "<p>ยังไม่มีวิดิโอ — สั่งสร้างจากแชทด้านล่างได้เลย</p>";
    return;
  }
  for (const v of videos) {
    const card = document.createElement("div");
    card.className = "video-card";
    card.textContent = v.title;
    card.addEventListener("click", () => {
      location.search = "?v=" + encodeURIComponent(v.id);
    });
    list.appendChild(card);
  }
}

const videoId = params.get("v");
if (videoId) {
  document.getElementById("picker").classList.add("hidden");
  document.getElementById("player-view").classList.remove("hidden");
  document.getElementById("btn-back-to-list").classList.remove("hidden");
} else {
  loadPicker();
}

document.getElementById("btn-back-to-list").addEventListener("click", () => {
  location.search = "";
});
```

- [ ] **Step 5: Verify in a browser**

```bash
STUDY_PORT=4399 node study-app/server.js &
```
Open `http://127.0.0.1:4399/` — expect to see "ยังไม่มีวิดิโอ..." (no videos registered yet). Then `curl` a test video in via the same command from Task 2's Step 2, reload — expect the title to appear as a clickable card, and clicking it navigates to `?v=<id>` and shows the (still-empty) player view.
```bash
kill %1
rm -rf study-app/data/study_*
```

- [ ] **Step 6: Commit**

```bash
git add study-app/server.js study-app/public/
git commit -m "study-app: frontend shell — video picker + player layout skeleton"
```

---

### Task 7: Frontend — load and render a video + its segment cards

**Files:**
- Modify: `study-app/public/app.js`

**Interfaces:**
- Consumes: `GET /videos/:id`, `GET /videos/:id/media`
- Produces: `renderSegments(video)` — populates `#segments` with one `.segment-card` per entry

- [ ] **Step 1: Add the load-and-render logic**

Append to `study-app/public/app.js` (inside the `if (videoId) { ... }` block, after the class toggles):
```js
let currentVideo = null;

async function loadVideo(id) {
  currentVideo = await fetch("/videos/" + id).then((r) => r.json());
  document.getElementById("video").src = "/videos/" + id + "/media";
  renderSegments(currentVideo);
}

function renderSegments(video) {
  const wrap = document.getElementById("segments");
  wrap.innerHTML = "";
  video.segments.forEach((seg, i) => {
    const card = document.createElement("div");
    card.className = "segment-card";
    card.dataset.index = String(i);
    card.dataset.start = String(seg.start);
    card.dataset.end = String(seg.end);

    const time = document.createElement("div");
    time.className = "seg-time";
    time.textContent = formatT(seg.start);

    const text = document.createElement("div");
    text.className = "seg-text";
    text.textContent = seg.text;

    card.appendChild(time);
    card.appendChild(text);
    wrap.appendChild(card);
  });
}

function formatT(s) {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return m + ":" + String(sec).padStart(2, "0");
}

if (videoId) loadVideo(videoId);
```

- [ ] **Step 2: Verify in a browser**

Register a real test video (Task 2's Step 2 curl, with 2-3 segments), open `http://127.0.0.1:4399/?v=<id>`. Expect: video element loads and plays the file, right pane shows one card per segment with correct times and text.

- [ ] **Step 3: Commit**

```bash
git add study-app/public/app.js
git commit -m "study-app: load a video and render its segment cards"
```

---

### Task 8: Frontend — warp button + active-segment highlight

**Files:**
- Modify: `study-app/public/app.js`
- Modify: `study-app/public/style.css` (already has `.segment-card.active` from Task 6)

**Interfaces:**
- Consumes: `currentVideo`, the `#video` element
- Produces: clicking a segment card seeks the video; the card matching the current playback time gets `.active`

- [ ] **Step 1: Add a warp button per card and the click handler**

In `renderSegments`, after building `text` and before `wrap.appendChild(card)`:
```js
    const warpBtn = document.createElement("button");
    warpBtn.className = "warp-btn";
    warpBtn.textContent = "⤴ ไปวินาทีนี้";
    warpBtn.addEventListener("click", () => {
      document.getElementById("video").currentTime = seg.start;
      document.getElementById("video").play();
    });
    card.appendChild(warpBtn);
```

- [ ] **Step 2: Add the timeupdate highlight listener**

Append after `renderSegments`/`formatT`:
```js
document.getElementById("video").addEventListener("timeupdate", (e) => {
  const t = e.target.currentTime;
  document.querySelectorAll(".segment-card").forEach((card) => {
    const start = Number(card.dataset.start);
    const end = Number(card.dataset.end);
    card.classList.toggle("active", t >= start && t < end);
  });
});
```

- [ ] **Step 3: Verify in a browser**

Open a registered video, click "⤴ ไปวินาทีนี้" on the 2nd segment — video should jump there and play. Let it play through — the card matching the current time should visibly highlight and switch as playback crosses segment boundaries.

- [ ] **Step 4: Commit**

```bash
git add study-app/public/app.js
git commit -m "study-app: warp-to-segment button + active-segment highlight"
```

---

### Task 9: Frontend — read-aloud button (existing free Thai TTS)

**Files:**
- Modify: `study-app/public/app.js`

**Interfaces:**
- Consumes: `GET http://127.0.0.1:4321/api/tts?text=...&voice=female` (existing endpoint on the main server, spec §2)
- Produces: a 🔊 button per segment card that streams and plays the TTS audio

- [ ] **Step 1: Add the button and playback logic**

In `renderSegments`, alongside the warp button:
```js
    const ttsBtn = document.createElement("button");
    ttsBtn.className = "tts-btn";
    ttsBtn.textContent = "🔊 อ่านออกเสียง";
    ttsBtn.addEventListener("click", () => {
      const url = "http://127.0.0.1:4321/api/tts?voice=female&text=" + encodeURIComponent(seg.text);
      new Audio(url).play();
    });
    card.appendChild(ttsBtn);
```

- [ ] **Step 2: Verify with real audio**

With the main PowerNote server running on 4321 and a registered test video open in the study app, click 🔊 on a segment — expect audible, natural-sounding Thai speech of that segment's exact text within ~1-2s.

- [ ] **Step 3: Commit**

```bash
git add study-app/public/app.js
git commit -m "study-app: read-aloud button using the existing free Thai TTS endpoint"
```

---

### Task 10: Frontend — editable segment text + chat panel

**Files:**
- Modify: `study-app/public/app.js`

**Interfaces:**
- Consumes: `PATCH /videos/:id/segments/:i` (Task 4), `POST /chat` + `GET /chat-log` (Task 5)
- Produces: segment text is directly editable and saves on blur; chat form posts messages and the log polls/refreshes every 3s

- [ ] **Step 1: Make segment text editable and save on blur**

In `renderSegments`, change the `text` block to:
```js
    const text = document.createElement("div");
    text.className = "seg-text";
    text.contentEditable = "true";
    text.textContent = seg.text;
    text.addEventListener("blur", async () => {
      const newText = text.textContent.trim();
      if (newText === seg.text) return;
      await fetch(`/videos/${video.id}/segments/${i}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: newText }),
      });
      seg.text = newText;
    });
```

- [ ] **Step 2: Wire the chat form**

Append to `study-app/public/app.js`:
```js
document.getElementById("chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = document.getElementById("chat-input");
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  await fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  refreshChatLog();
});

async function refreshChatLog() {
  try {
    const { messages } = await fetch("/chat-log").then((r) => r.json());
    const log = document.getElementById("chat-log");
    log.innerHTML = messages
      .map((m) => `<div class="chat-msg ${m.role}"><b>${m.role === "user" ? "Min" : "Claude"}:</b> ${escapeHtml(m.text)}</div>`)
      .join("");
    log.scrollTop = log.scrollHeight;
  } catch {
    // main server unreachable — leave the log as-is, chat form still queues via /chat's own error handling
  }
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

refreshChatLog();
setInterval(refreshChatLog, 3000);
```

- [ ] **Step 3: Verify editing and chat end-to-end**

Edit a segment's text in the browser, click elsewhere to blur — reload the page, confirm the edit persisted (check `study-app/data/<id>/explain.json` directly too). Type a message in the chat box, submit — confirm it appears in `#chat-log` within 3s, and confirm (via PowerNote's own UI) that the same message shows up in the "study" section there.

- [ ] **Step 4: Commit**

```bash
git add study-app/public/app.js
git commit -m "study-app: editable segment text + polling chat panel"
```

---

### Task 11: Wire it into PowerNote — auto-spawn + topbar button

**Files:**
- Modify: `C:\Users\wicha\Desktop\powerfull_note\server.js` (spawn study-app server; area right after `spawnTtsWorker();` around line 1081)
- Modify: `C:\Users\wicha\Desktop\powerfull_note\public\index.html` (add topbar button, near `btn-add-video` at line 180)
- Modify: `C:\Users\wicha\Desktop\powerfull_note\public\app.js` (wire the click handler, near the `btn-add-video` handler at line 2827)

**Interfaces:**
- Consumes: `spawn` from `node:child_process` (already imported in `server.js`), `STUDY_PORT` convention from Task 1
- Produces: the study-app server is always running whenever `server.js` is running; a topbar button opens it in a new tab

- [ ] **Step 1: Spawn the study-app server from the main server**

In `C:\Users\wicha\Desktop\powerfull_note\server.js`, immediately after the existing `spawnTtsWorker();` call (around line 1081):
```js
// Study App: separate-port companion server. Spawned here (not by the user)
// so it's always up whenever PowerNote is — same pattern as the TTS worker.
const STUDY_PORT = Number(process.env.STUDY_PORT) || 4322;
function spawnStudyApp() {
  const child = spawn("node", [path.join(__dirname, "study-app", "server.js")], {
    env: { ...process.env, STUDY_PORT: String(STUDY_PORT), NOTE_SERVER_URL: `http://127.0.0.1:${PORT}` },
    stdio: "inherit",
  });
  child.on("exit", (code) => {
    console.log(`[study-app] exited (code ${code}) — restarting in 3s`);
    setTimeout(spawnStudyApp, 3000);
  });
}
spawnStudyApp();
```

- [ ] **Step 2: Add the topbar button**

In `C:\Users\wicha\Desktop\powerfull_note\public\index.html`, after line 180 (`btn-add-video`):
```html
            <button id="btn-study-mode" class="tb-btn" title="เปิดแอปติววิดิโอ (คนละหน้าต่าง)">🎓 ติววิดิโอ</button>
```

- [ ] **Step 3: Wire the click handler**

In `C:\Users\wicha\Desktop\powerfull_note\public\app.js`, after the `btn-add-video` handler (around line 2833):
```js
  $("#btn-study-mode").addEventListener("click", () => {
    window.open("http://127.0.0.1:4322/", "_blank");
  });
```

- [ ] **Step 4: Verify the full boot sequence**

```bash
node server.js &
sleep 3
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:4321/api/state    # expect 200 (main server)
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:4322/             # expect 200 (study app)
kill %1
```

Then in a browser: open PowerNote, click "🎓 ติววิดิโอ" — expect a new tab opens showing the study app's picker page.

- [ ] **Step 5: Commit**

```bash
git add server.js public/index.html public/app.js
git commit -m "powernote: auto-spawn study-app server + topbar button to open it"
```

---

### Task 12: MCP tools — start, status, edit

**Files:**
- Modify: `C:\Users\wicha\Desktop\powerfull_note\mcp-server.js`

**Interfaces:**
- Consumes: `server.registerTool`, `ok`, `fail` (existing helpers, lines 46-55), `z` from zod
- Produces: 3 new registered MCP tools callable from any Claude Code session with this project's `.mcp.json` — `start_video_study`, `get_video_study_status`, `edit_video_explanation`

- [ ] **Step 1: Add a study-app-specific `api()` helper**

Near the top of `mcp-server.js`, after the existing `api()` function (after line 44):
```js
const STUDY_BASE = process.env.STUDY_SERVER_URL || "http://127.0.0.1:4322";
async function studyApi(pathname, method = "GET", body) {
  const res = await fetch(STUDY_BASE + pathname, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`${method} ${pathname} → ${res.status} ${txt}`);
  }
  return res.json();
}
```

- [ ] **Step 2: Register `start_video_study`**

Add near the other `server.registerTool(...)` calls (any point after the helper definitions):
```js
server.registerTool(
  "start_video_study",
  {
    title: "เริ่มสร้างวิดิโอสอนใหม่สำหรับแอปติว",
    description:
      "Register that you (Claude) are about to author a new teaching video for the Video Study App. Call get_video_study_status afterward to confirm it registered. This tool does NOT render the video itself — you still author the manim scenes and render them yourself (use the manim-teaching-video skill), then call edit_video_explanation-style registration via a direct POST to the study app's /videos endpoint once the mp4 exists on disk. Use this tool first just to confirm the study app server is reachable before doing the (potentially long) render work.",
    inputSchema: {
      topic: z.string().describe("หัวข้อวิดิโอที่ Min ขอ"),
    },
  },
  async ({ topic }) => {
    try {
      const videos = await studyApi("/videos");
      return ok(
        `แอปติววิดิโอพร้อมรับวิดิโอใหม่แล้ว (ตอนนี้มี ${videos.length} เรื่องอยู่แล้ว) — ` +
        `ไปเขียน/render วิดิโอเรื่อง "${topic}" ได้เลย แล้วเรียก POST ${STUDY_BASE}/videos ` +
        `{title, videoPath, segments} ตอนเสร็จ`
      );
    } catch (e) {
      return fail(e);
    }
  }
);
```

- [ ] **Step 3: Register `get_video_study_status`**

```js
server.registerTool(
  "get_video_study_status",
  {
    title: "เช็คสถานะวิดิโอในแอปติว",
    description: "List videos currently registered in the Video Study App, or get one video's full detail (segments included) if videoId is given.",
    inputSchema: {
      videoId: z.string().optional().describe("เว้นว่าง = แสดงรายชื่อทั้งหมด, ใส่ = ดูรายละเอียดวิดิโอนั้น"),
    },
  },
  async ({ videoId }) => {
    try {
      if (videoId) {
        const v = await studyApi(`/videos/${encodeURIComponent(videoId)}`);
        const lines = v.segments.map((s, i) => `  [${i}] ${s.start}s-${s.end}s: ${s.text}`).join("\n");
        return ok(`"${v.title}" (${v.durationS}s, ${v.segments.length} segments)\n${lines}`);
      }
      const videos = await studyApi("/videos");
      if (!videos.length) return ok("ยังไม่มีวิดิโอในแอปติวเลย");
      return ok(videos.map((v) => `- [${v.id}] ${v.title} (${v.durationS}s)`).join("\n"));
    } catch (e) {
      return fail(e);
    }
  }
);
```

- [ ] **Step 4: Register `edit_video_explanation`**

```js
server.registerTool(
  "edit_video_explanation",
  {
    title: "แก้ไข/ขยายข้อความอธิบายในแอปติว",
    description: "Edit one segment's explanation text in a Video Study App video — use this when Min asks a follow-up question in the study chat and you want your fuller answer to also update the right-side text, not just appear in the chat.",
    inputSchema: {
      videoId: z.string(),
      segmentIndex: z.number().int().min(0),
      newText: z.string().describe("ข้อความใหม่ทั้งหมดของ segment นี้ (แทนที่ของเดิมทั้งหมด)"),
    },
  },
  async ({ videoId, segmentIndex, newText }) => {
    try {
      await studyApi(`/videos/${encodeURIComponent(videoId)}/segments/${segmentIndex}`, "PATCH", { text: newText });
      return ok(`แก้ไข segment [${segmentIndex}] ของวิดิโอ ${videoId} แล้ว`);
    } catch (e) {
      return fail(e);
    }
  }
);
```

- [ ] **Step 5: Verify with a real MCP tool call**

With the study-app server running (`node study-app/server.js`) and at least one video registered (reuse Task 2's Step 2 curl), start a Claude Code session in this project and call:
```
get_video_study_status
```
Expected: it lists the test video by id and title. Then call `edit_video_explanation` on it with a new text and re-call `get_video_study_status(videoId=...)` — expect the new text to show.

- [ ] **Step 6: Commit**

```bash
git add mcp-server.js
git commit -m "mcp-server: add start_video_study, get_video_study_status, edit_video_explanation tools"
```

---

## Self-Review Notes (for whoever executes this plan)

- **Spec coverage:** §4 architecture → Tasks 1,11. §5.1 server routes → Tasks 1-5. §5.2 frontend → Tasks 6-10. §5.3 MCP tools → Task 12. §5.4 data model → Task 1/2. §6 error handling → Task 5 Step 1 (502 on unreachable main server), Task 3/4 (404s). §7 testing → each task's own verify step plus a final end-to-end pass is recommended after Task 12 (create a real video via a live Claude Code session in the "study" section, not just curl stand-ins).
- **Deliberately deferred (matches spec §8):** visual polish/professional design pass (spec §5.2 notes this explicitly belongs to implementation time, not brainstorming) — recommend a follow-up pass through the project's UX/UI design skill once all 12 tasks are verified working, applied to `study-app/public/*` only. External video import, multi-user/auth, and any cloud-transcription fallback are out of scope per spec §8 and intentionally have no task here.
