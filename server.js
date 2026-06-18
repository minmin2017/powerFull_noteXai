// Powerfull Note — web server
// Serves the mind-map UI, holds the single source of truth (mindmap.json),
// exposes a REST API, and broadcasts live updates over WebSocket.
// The MCP server (mcp-server.js) talks to this process over HTTP so there is
// exactly one writer to the data file.

import express from "express";
import { WebSocketServer } from "ws";
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";
import os from "node:os";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.PORT) || 4321;
const BOOT_ID = "boot_" + Date.now().toString(36); // changes every server (re)start
const DATA_DIR = path.join(__dirname, "data");
const PROJECTS_DIR = path.join(DATA_DIR, "projects");
const INDEX_FILE = path.join(DATA_DIR, "projects.json");
const LEGACY_FILE = path.join(DATA_DIR, "mindmap.json"); // pre-multi-project single file
const ASSETS_DIR = path.join(DATA_DIR, "assets"); // pasted/dropped/fetched images

function uid(prefix = "n") {
  return prefix + "_" + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
}

// ---------------------------------------------------------------------------
// Store — multiple projects, one active at a time.
//   data/projects.json        → { activeId, projects: [{id, title}] }
//   data/projects/<id>.json    → one mind map (meta, nodes, drawings, chat, …)
// `state` always holds the ACTIVE project's content; `projects`/`activeId`
// hold the index. Switching projects flushes the current one and loads another.
// ---------------------------------------------------------------------------
function emptyState(title = "My Mind Map") {
  return {
    meta: { title, updatedAt: Date.now() },
    nodes: [],
    drawings: [],
    images: [], // pasted/dropped/fetched images: {id, src, x, y, w, h, rotation}
    boxes: [], // boxes: handwriting {kind:"note",strokes:[...]} OR gallery {kind:"image",items:[{src,url,caption}]}
    boxLinks: [], // connections between boxes: {id, from, to}
    chat: [], // chat messages, each tagged with a `section` id
    chatSections: [{ id: "main", name: "แชทหลัก" }], // chat tabs/threads
    activeSection: "main", // which section new messages land in + is shown
    voice: { latest: null, history: [] },
    inbox: [], // typed/spoken messages queued for Claude Code to drain
    imageInbox: [], // image refs the user sent for Claude to LOOK at: {id, src, note, ts}
  };
}

let projects = []; // [{ id, title }]
let activeId = null;
let state = emptyState();

// Ephemeral UI state: the world-area the user is currently looking at (reported
// by the browser on pan/zoom). Lets new nodes/images land where the user can see
// them, and lets Claude read it via get_mindmap. Not persisted, not broadcast.
let lastViewport = null;

function ensureDirs() {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
  if (!fs.existsSync(PROJECTS_DIR)) fs.mkdirSync(PROJECTS_DIR, { recursive: true });
  if (!fs.existsSync(ASSETS_DIR)) fs.mkdirSync(ASSETS_DIR, { recursive: true });
}

const projectFile = (id) => path.join(PROJECTS_DIR, id + ".json");

function loadProjectData(id) {
  try {
    const raw = JSON.parse(fs.readFileSync(projectFile(id), "utf8"));
    return { ...emptyState(), ...raw };
  } catch {
    return emptyState();
  }
}

function writeProjectData(id, data) {
  ensureDirs();
  fs.writeFileSync(projectFile(id), JSON.stringify(data, null, 2));
}

function saveIndex() {
  ensureDirs();
  fs.writeFileSync(INDEX_FILE, JSON.stringify({ activeId, projects }, null, 2));
}

function bootstrap() {
  ensureDirs();
  if (fs.existsSync(INDEX_FILE)) {
    try {
      const idx = JSON.parse(fs.readFileSync(INDEX_FILE, "utf8"));
      projects = Array.isArray(idx.projects) ? idx.projects : [];
      activeId = idx.activeId || projects[0]?.id || null;
    } catch (err) {
      console.error("[store] bad index, rebuilding:", err.message);
    }
  }
  // First run (or no projects yet): seed one, migrating the legacy file if present.
  if (!projects.length || !activeId) {
    const id = uid("p");
    let data = emptyState();
    if (fs.existsSync(LEGACY_FILE)) {
      try {
        data = { ...emptyState(), ...JSON.parse(fs.readFileSync(LEGACY_FILE, "utf8")) };
      } catch (err) {
        console.error("[store] failed to migrate legacy file:", err.message);
      }
    }
    projects = [{ id, title: data.meta?.title || "My Mind Map" }];
    activeId = id;
    writeProjectData(id, data);
    saveIndex();
  }
  state = loadProjectData(activeId);
}
bootstrap();

let saveTimer = null;
function persist() {
  state.meta.updatedAt = Date.now();
  // keep the index title in sync with the active project's title
  const entry = projects.find((p) => p.id === activeId);
  if (entry && entry.title !== state.meta.title) {
    entry.title = state.meta.title;
    saveIndex();
  }
  if (saveTimer) return;
  saveTimer = setTimeout(() => {
    saveTimer = null;
    try {
      writeProjectData(activeId, state);
    } catch (err) {
      console.error("[store] save failed:", err.message);
    }
  }, 150);
}

function flushNow() {
  if (saveTimer) {
    clearTimeout(saveTimer);
    saveTimer = null;
  }
  try {
    writeProjectData(activeId, state);
  } catch (err) {
    console.error("[store] flush failed:", err.message);
  }
}

// ---------------------------------------------------------------------------
// Project management
// ---------------------------------------------------------------------------
function createProject(title) {
  const id = uid("p");
  const data = emptyState(title && title.trim() ? title.trim() : "Untitled");
  writeProjectData(id, data);
  projects.push({ id, title: data.meta.title });
  saveIndex();
  return { id, title: data.meta.title };
}

function activateProject(id) {
  if (id === activeId) return true;
  if (!projects.some((p) => p.id === id)) return false;
  flushNow(); // persist the project we're leaving
  activeId = id;
  state = loadProjectData(id);
  lastViewport = null; // viewport is per-project; the browser re-reports on switch
  saveIndex();
  return true;
}

function deleteProject(id) {
  if (!projects.some((p) => p.id === id)) return false;
  if (projects.length <= 1) return false; // always keep at least one project
  projects = projects.filter((p) => p.id !== id);
  try {
    fs.unlinkSync(projectFile(id));
  } catch {}
  if (activeId === id) {
    activeId = projects[0].id;
    state = loadProjectData(activeId);
    lastViewport = null;
  }
  saveIndex();
  return true;
}

// ---------------------------------------------------------------------------
// Mutations (used by REST handlers; each one broadcasts + persists)
// ---------------------------------------------------------------------------
function childrenOf(id) {
  return state.nodes.filter((n) => n.parentId === id);
}

function autoPosition({ parentId }) {
  if (parentId) {
    const parent = state.nodes.find((n) => n.id === parentId);
    if (parent) {
      const sibs = childrenOf(parentId);
      const x = (parent.x ?? 0) + 240;
      // Stack the new child just below the lowest existing sibling so it never
      // overlaps one that was moved by hand — and nobody else has to shift.
      if (sibs.length) {
        const lowest = Math.max(...sibs.map((s) => s.y ?? 0));
        return { x, y: lowest + 96 };
      }
      return { x, y: parent.y ?? 0 };
    }
  }
  const roots = state.nodes.filter((n) => !n.parentId);
  // Drop new top-level topics where the user is currently looking (current
  // viewport), lightly fanned so several adds in a row don't stack exactly.
  if (lastViewport && Number.isFinite(lastViewport.cx)) {
    const k = roots.length % 6;
    return {
      x: Math.round(lastViewport.cx - 90 + k * 18),
      y: Math.round(lastViewport.cy - 24 + k * 48),
    };
  }
  return { x: 120, y: 120 + roots.length * 140 };
}

const PALETTE = ["#6366f1", "#ec4899", "#14b8a6", "#f59e0b", "#8b5cf6", "#ef4444", "#0ea5e9", "#22c55e"];

function createNode({ text, parentId = null, x, y, color }) {
  if (parentId && !state.nodes.some((n) => n.id === parentId)) parentId = null;
  if (x === undefined || y === undefined) {
    const pos = autoPosition({ parentId });
    x = x ?? pos.x;
    y = y ?? pos.y;
  }
  const depth = parentId
    ? 1 + (state.nodes.find((n) => n.id === parentId)?._depth ?? 0)
    : 0;
  const node = {
    id: uid("n"),
    text: text ?? "หัวข้อใหม่",
    parentId,
    x,
    y,
    color: color || PALETTE[state.nodes.length % PALETTE.length],
    collapsed: false,
    _depth: depth,
    createdAt: Date.now(),
  };
  state.nodes.push(node);
  changed();
  return node;
}

// True if `ancestorId` sits above `nodeId` in the parent chain (cycle-safe walk).
function isAncestorOf(ancestorId, nodeId) {
  let cur = state.nodes.find((n) => n.id === nodeId);
  const seen = new Set();
  while (cur && cur.parentId && !seen.has(cur.id)) {
    seen.add(cur.id);
    if (cur.parentId === ancestorId) return true;
    cur = state.nodes.find((n) => n.id === cur.parentId);
  }
  return false;
}

function updateNode(id, patch) {
  const node = state.nodes.find((n) => n.id === id);
  if (!node) return null;
  // Reject a reparent onto the node itself or one of its descendants — a parent
  // cycle would freeze computeHidden (client) and overflow tidyLayout (server).
  if (patch.parentId !== undefined && patch.parentId !== null &&
      (patch.parentId === id || isAncestorOf(id, patch.parentId))) {
    patch = { ...patch };
    delete patch.parentId;
  }
  for (const k of ["text", "x", "y", "color", "collapsed", "parentId", "tags"]) {
    if (patch[k] !== undefined) node[k] = patch[k];
  }
  changed();
  return node;
}

function deleteNode(id) {
  // delete node and its whole subtree
  const toDelete = new Set([id]);
  let grew = true;
  while (grew) {
    grew = false;
    for (const n of state.nodes) {
      if (n.parentId && toDelete.has(n.parentId) && !toDelete.has(n.id)) {
        toDelete.add(n.id);
        grew = true;
      }
    }
  }
  const before = state.nodes.length;
  state.nodes = state.nodes.filter((n) => !toDelete.has(n.id));
  changed();
  return before - state.nodes.length;
}

// Tidy tree layout: lay every node out left-to-right per branch so siblings
// never overlap. x = depth column; y = packed rows (leaves get their own row,
// parents center on their children). Roots stack vertically with a gap.
function tidyLayout({ colW = 260, rowH = 92, gap = 1, x0, y0, rootId } = {}) {
  const kidsOf = (id) => state.nodes.filter((n) => (n.parentId || null) === id);

  // Scoped tidy: arrange ONLY the given node's subtree, pinned where that node
  // currently sits. Every other branch and all images stay exactly put — so
  // adding/arranging one topic never reshuffles the whole project.
  if (rootId) {
    const root = state.nodes.find((n) => n.id === rootId);
    if (!root) return 0;
    const baseX = root.x ?? 0, baseY = root.y ?? 0;
    const subtree = [];
    let row = 0;
    const placeOne = (node, depth) => {
      subtree.push(node);
      node.x = baseX + depth * colW;
      const children = kidsOf(node.id);
      if (!children.length) { node.y = baseY + row * rowH; row += 1; return; }
      for (const c of children) placeOne(c, depth + 1);
      node.y = (children[0].y + children[children.length - 1].y) / 2;
    };
    placeOne(root, 0);
    // pin the root to its original y (children centering may have shifted it)
    const dy = baseY - root.y;
    if (dy) for (const n of subtree) n.y += dy;
    changed();
    return subtree.length;
  }

  // When no explicit origin is given, lay the tidy tree out near the top-left of
  // what the user is currently viewing, so the result stays on screen instead of
  // snapping back to a fixed origin they may have panned away from.
  if (x0 === undefined || y0 === undefined) {
    if (lastViewport && Number.isFinite(lastViewport.minX)) {
      x0 = x0 ?? Math.round(lastViewport.minX + 60);
      y0 = y0 ?? Math.round(lastViewport.minY + 60);
    } else {
      x0 = x0 ?? 120;
      y0 = y0 ?? 120;
    }
  }
  const kids = (id) =>
    state.nodes.filter((n) => (n.parentId || null) === id);
  let row = 0;
  const place = (node, depth) => {
    node.x = x0 + depth * colW;
    const children = kids(node.id);
    if (!children.length) {
      node.y = y0 + row * rowH;
      row += 1;
      return;
    }
    for (const c of children) place(c, depth + 1);
    node.y = (children[0].y + children[children.length - 1].y) / 2;
  };
  const roots = state.nodes.filter(
    (n) => !n.parentId || !state.nodes.some((p) => p.id === n.parentId)
  );
  for (const r of roots) {
    place(r, 0);
    row += gap; // blank row between top-level branches
  }

  // Images aren't part of the node tree, so spread them into their own
  // non-overlapping row below the lowest node — add_image alone can't avoid
  // stacking everything at the same default (200,200) spot.
  if (state.images.length) {
    const maxNodeY = state.nodes.length
      ? Math.max(...state.nodes.map((n) => n.y || 0))
      : y0;
    let imgX = x0;
    const imgY = maxNodeY + rowH * 2;
    const imgGap = 40;
    for (const img of state.images) {
      img.x = imgX;
      img.y = imgY;
      imgX += (img.w || 240) + imgGap;
    }
  }

  changed();
  return state.nodes.length;
}

function addDrawing(stroke) {
  const d = {
    id: uid("d"),
    color: stroke.color || "#111827",
    width: stroke.width || 3,
    points: Array.isArray(stroke.points) ? stroke.points : [],
    createdAt: Date.now(),
  };
  state.drawings.push(d);
  changed();
  return d;
}

function deleteDrawing(id) {
  const before = state.drawings.length;
  state.drawings = state.drawings.filter((d) => d.id !== id);
  changed();
  return before - state.drawings.length;
}

// ----- Images ----------------------------------------------------------------
const MIME_EXT = {
  "image/png": "png",
  "image/jpeg": "jpg",
  "image/jpg": "jpg",
  "image/gif": "gif",
  "image/webp": "webp",
  "image/svg+xml": "svg",
  "image/bmp": "bmp",
};

// Save raw bytes to the assets dir and return the public URL path.
function saveAsset(buffer, mime) {
  ensureDirs();
  const ext = MIME_EXT[(mime || "").toLowerCase()] || "png";
  const file = uid("img") + "." + ext;
  fs.writeFileSync(path.join(ASSETS_DIR, file), buffer);
  return "/assets/" + file;
}

// Place an image object into the active map (src is a public /assets URL).
function placeImage({ src, x, y, w, h, rotation }) {
  w = w ?? 240;
  h = h ?? 180;
  // No explicit position → center the image on the user's current viewport so a
  // pasted/fetched picture lands where they're looking (paste from the browser
  // already passes explicit coords; this covers Claude's add_image).
  if ((x === undefined || y === undefined) && lastViewport && Number.isFinite(lastViewport.cx)) {
    x = x ?? Math.round(lastViewport.cx - w / 2);
    y = y ?? Math.round(lastViewport.cy - h / 2);
  }
  const img = {
    id: uid("im"),
    src,
    x: x ?? 200,
    y: y ?? 200,
    w,
    h,
    rotation: rotation ?? 0,
    createdAt: Date.now(),
  };
  state.images.push(img);
  changed();
  return img;
}

// Accept a data URL ("data:image/png;base64,....") from paste/drag-drop.
function addImageFromDataUrl({ dataUrl, x, y, w, h }) {
  const m = /^data:([^;,]+)?(;base64)?,(.*)$/s.exec(dataUrl || "");
  if (!m) return null;
  const mime = m[1] || "image/png";
  const isB64 = !!m[2];
  const buffer = Buffer.from(decodeURIComponent(m[3]), isB64 ? "base64" : "utf8");
  const src = saveAsset(buffer, mime);
  return placeImage({ src, x, y, w, h });
}

// Download an image from a URL (used by Claude's add_image MCP tool).
async function addImageFromUrl({ url, x, y, w, h }) {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error("fetch failed: " + resp.status);
  const mime = resp.headers.get("content-type") || "image/png";
  if (!mime.startsWith("image/")) throw new Error("not an image: " + mime);
  const buffer = Buffer.from(await resp.arrayBuffer());
  const src = saveAsset(buffer, mime);
  return placeImage({ src, x, y, w, h });
}

function updateImage(id, patch) {
  const img = state.images.find((i) => i.id === id);
  if (!img) return null;
  for (const k of ["x", "y", "w", "h", "rotation"]) {
    if (patch[k] !== undefined) img[k] = patch[k];
  }
  changed();
  return img;
}

function deleteImage(id) {
  const img = state.images.find((i) => i.id === id);
  const before = state.images.length;
  state.images = state.images.filter((i) => i.id !== id);
  // best-effort remove the underlying file
  if (img && typeof img.src === "string" && img.src.startsWith("/assets/")) {
    try {
      fs.unlinkSync(path.join(ASSETS_DIR, path.basename(img.src)));
    } catch {}
  }
  changed();
  return before - state.images.length;
}

function addChat({ role = "claude", text, section }) {
  let sec = state.activeSection || "main";
  if (section) sec = resolveSectionKey(section) || sec;
  const msg = { id: uid("c"), role, text: String(text ?? ""), ts: Date.now(), section: sec };
  state.chat.push(msg);
  if (state.chat.length > 500) state.chat = state.chat.slice(-500);
  changed();
  return msg;
}

// ----- Chat sections (multiple chat threads/tabs) -----
function ensureSections() {
  if (!Array.isArray(state.chatSections) || !state.chatSections.length)
    state.chatSections = [{ id: "main", name: "แชทหลัก" }];
  if (!state.chatSections.some((s) => s.id === state.activeSection))
    state.activeSection = state.chatSections[0].id;
}
function addSection(name) {
  ensureSections();
  const sec = { id: uid("sec"), name: String(name || "แชทใหม่").slice(0, 40) };
  state.chatSections.push(sec);
  state.activeSection = sec.id;
  changed();
  return sec;
}
function activateSection(id) {
  ensureSections();
  if (!state.chatSections.some((s) => s.id === id)) return false;
  state.activeSection = id;
  changed();
  return true;
}
function renameSection(id, name) {
  ensureSections();
  const sec = state.chatSections.find((s) => s.id === id);
  if (!sec) return null;
  sec.name = String(name || sec.name).slice(0, 40);
  changed();
  return sec;
}
function deleteSection(id) {
  ensureSections();
  if (state.chatSections.length <= 1) return false; // keep at least one
  if (!state.chatSections.some((s) => s.id === id)) return false;
  state.chatSections = state.chatSections.filter((s) => s.id !== id);
  state.chat = state.chat.filter((m) => (m.section || "main") !== id); // drop its messages
  if (state.activeSection === id) state.activeSection = state.chatSections[0].id;
  changed();
  return true;
}

function setVoice(text) {
  const entry = { text: String(text ?? ""), ts: Date.now(), consumed: false };
  state.voice.latest = entry;
  state.voice.history.push(entry);
  if (state.voice.history.length > 100) state.voice.history = state.voice.history.slice(-100);
  changed();
  return entry;
}

function consumeVoice() {
  const v = state.voice.latest;
  if (v) v.consumed = true;
  changed();
  return v;
}

// Resolve a chat-section "key" (its id OR its display name) to the canonical id.
// Lets launchers/tools address a section by a human-friendly name.
function resolveSectionKey(key) {
  if (!key) return null;
  ensureSections();
  const k = String(key).trim();
  let s = state.chatSections.find((x) => x.id === k);
  if (s) return s.id;
  s = state.chatSections.find((x) => (x.name || "").toLowerCase() === k.toLowerCase());
  return s ? s.id : null;
}

// Inbox: a queue of messages the user typed/spoke for Claude Code to pick up.
// Each entry is tagged with the chat section it belongs to so multiple Claude
// Code instances (one per section) can each drain only their own messages.
function addInbox(text, section) {
  const sec = (section && resolveSectionKey(section)) || state.activeSection || "main";
  const entry = { id: uid("in"), text: String(text ?? ""), ts: Date.now(), section: sec };
  state.inbox.push(entry);
  if (state.inbox.length > 200) state.inbox = state.inbox.slice(-200);
  changed();
  return entry;
}

function drainInbox() {
  const items = state.inbox.slice();
  if (items.length) { state.inbox = []; changed(); }
  return items;
}

// Image inbox: images the user explicitly sent for Claude to LOOK at.
// We resolve the src to an existing image's asset, or accept a raw /assets path.
function addImageInbox({ id, src, note }) {
  let url = src;
  if (!url && id) {
    const img = state.images.find((i) => i.id === id);
    if (img) url = img.src;
  }
  if (!url) return null;
  const entry = { id: uid("uimg"), src: url, note: String(note ?? ""), ts: Date.now() };
  state.imageInbox.push(entry);
  if (state.imageInbox.length > 50) state.imageInbox = state.imageInbox.slice(-50);
  changed();
  return entry;
}

function drainImageInbox() {
  const items = state.imageInbox.slice();
  if (items.length) { state.imageInbox = []; changed(); }
  return items;
}

// ---------------------------------------------------------------------------
// WebSocket broadcast
// ---------------------------------------------------------------------------
const app = express();
app.use(express.json({ limit: "30mb" })); // pasted images arrive as base64 data URLs
const server = http.createServer(app);
const wss = new WebSocketServer({ server, path: "/ws" });

function broadcast() {
  const payload = JSON.stringify({ type: "state", state, projects, activeId, history: historyCounts(), bootId: BOOT_ID });
  for (const client of wss.clients) {
    if (client.readyState === 1) client.send(payload);
  }
}

// Send an arbitrary message (e.g. calendar pushes) to every connected client.
function broadcastRaw(payload) {
  const s = JSON.stringify(payload);
  for (const client of wss.clients) {
    if (client.readyState === 1) client.send(s);
  }
}

// Live reload: when frontend files change, tell every open page to refresh.
function sendReload() {
  const payload = JSON.stringify({ type: "reload" });
  for (const client of wss.clients) {
    if (client.readyState === 1) client.send(payload);
  }
}
let reloadTimer = null;
try {
  fs.watch(path.join(__dirname, "public"), { recursive: true }, () => {
    clearTimeout(reloadTimer);
    reloadTimer = setTimeout(sendReload, 200);
  });
} catch (err) {
  console.warn("[watch] live-reload disabled:", err.message);
}

// ---------------------------------------------------------------------------
// Undo / redo history (per project). Snapshots only the mind-map content
// (meta, nodes, drawings, images) — chat/voice/inbox are left untouched.
// ---------------------------------------------------------------------------
const HISTORY_CAP = 100;
const histories = new Map(); // projectId -> { past:[], future:[], last }
let applyingHistory = false;

function snapMap() {
  return JSON.parse(
    JSON.stringify({
      meta: state.meta,
      nodes: state.nodes,
      drawings: state.drawings,
      images: state.images,
      boxes: state.boxes,
      boxLinks: state.boxLinks,
    })
  );
}
function applyMapSnap(s) {
  state.meta = s.meta;
  state.nodes = s.nodes;
  state.drawings = s.drawings;
  state.images = s.images;
  state.boxes = s.boxes || [];
  state.boxLinks = s.boxLinks || [];
}
function historyOf() {
  let h = histories.get(activeId);
  if (!h) {
    h = { past: [], future: [], last: snapMap() };
    histories.set(activeId, h);
  }
  return h;
}
function recordHistory() {
  const h = historyOf();
  const snap = snapMap();
  // Only count it as an undo step if the mind-map content actually changed.
  // Chat/inbox/voice/section mutations call changed() too but leave the map
  // identical — without this they'd flood the undo stack with no-op steps.
  if (h.last && JSON.stringify(h.last) === JSON.stringify(snap)) return;
  if (h.last) {
    h.past.push(h.last);
    if (h.past.length > HISTORY_CAP) h.past.shift();
  }
  h.future = [];
  h.last = snap;
}
function historyCounts() {
  const h = histories.get(activeId);
  return { canUndo: !!(h && h.past.length), canRedo: !!(h && h.future.length),
           past: h ? h.past.length : 0, future: h ? h.future.length : 0 };
}
function undo() {
  const h = historyOf();
  if (!h.past.length) return false;
  h.future.unshift(snapMap());
  applyMapSnap(h.past.pop());
  h.last = snapMap();
  applyingHistory = true;
  changed();
  applyingHistory = false;
  return true;
}
function redo() {
  const h = historyOf();
  if (!h.future.length) return false;
  h.past.push(snapMap());
  applyMapSnap(h.future.shift());
  h.last = snapMap();
  applyingHistory = true;
  changed();
  applyingHistory = false;
  return true;
}

let broadcastTimer = null;
function changed() {
  if (!applyingHistory) recordHistory();
  persist();
  if (broadcastTimer) return;
  broadcastTimer = setTimeout(() => {
    broadcastTimer = null;
    broadcast();
  }, 30);
}

wss.on("connection", (ws) => {
  ws.send(JSON.stringify({ type: "state", state, projects, activeId, history: historyCounts(), bootId: BOOT_ID }));
});

// ---------------------------------------------------------------------------
// REST API
// ---------------------------------------------------------------------------
app.get("/api/state", (_req, res) => res.json({ ...state, projects, activeId, viewport: lastViewport, history: historyCounts() }));

// Ephemeral: the world-area the user is currently looking at. Reported by the
// browser on pan/zoom (debounced). Does NOT broadcast or persist — it's a
// one-way hint so server-side auto-placement and Claude can use the live view.
app.post("/api/viewport", (req, res) => {
  const b = req.body || {};
  const n = (v) => (Number.isFinite(v) ? v : undefined);
  if (Number.isFinite(b.cx) && Number.isFinite(b.cy)) {
    lastViewport = {
      x: n(b.x), y: n(b.y), scale: n(b.scale) || 1,
      cx: b.cx, cy: b.cy,
      minX: n(b.minX), minY: n(b.minY), maxX: n(b.maxX), maxY: n(b.maxY),
      w: n(b.w), h: n(b.h),
      ts: Date.now(),
    };
  }
  res.json({ ok: true });
});
app.get("/api/viewport", (_req, res) => res.json(lastViewport || {}));

// Canvas screenshot — browser POSTs a JPEG dataUrl after each viewport settle
const SCREENSHOT_PATH = "D:\\powerfull_note_screenshot.jpg";
app.post("/api/screenshot", (req, res) => {
  const { dataUrl } = req.body || {};
  if (dataUrl && dataUrl.startsWith("data:image/")) {
    const base64 = dataUrl.replace(/^data:image\/\w+;base64,/, "");
    fs.writeFile(SCREENSHOT_PATH, Buffer.from(base64, "base64"), () => {});
  }
  res.json({ ok: true });
});
app.get("/api/screenshot", (_req, res) => {
  if (!fs.existsSync(SCREENSHOT_PATH)) return res.status(404).json({ error: "no screenshot yet" });
  const base64 = fs.readFileSync(SCREENSHOT_PATH).toString("base64");
  res.json({ dataUrl: "data:image/jpeg;base64," + base64 });
});

// Full-map snapshot — Claude asks via GET; we tell the browser (over WS) to fit
// the whole map and capture it, then resolve once the browser POSTs it back.
const FULLMAP_PATH = "D:\\powerfull_note_fullmap.jpg";
const fullmapWaiters = new Map(); // reqId -> {resolve, timer}
app.post("/api/fullmap", (req, res) => {
  const { reqId, dataUrl, error } = req.body || {};
  const w = fullmapWaiters.get(reqId);
  if (w) {
    fullmapWaiters.delete(reqId);
    clearTimeout(w.timer);
    if (dataUrl && dataUrl.startsWith("data:image/")) {
      const base64 = dataUrl.replace(/^data:image\/\w+;base64,/, "");
      fs.writeFile(FULLMAP_PATH, Buffer.from(base64, "base64"), () => {});
      w.resolve({ dataUrl });
    } else {
      w.resolve({ error: error || "no image" });
    }
  }
  res.json({ ok: true });
});
app.get("/api/fullmap", (_req, res) => {
  if (!wss.clients.size) return res.status(503).json({ error: "no browser connected — open http://localhost:4321 first" });
  const reqId = "fm_" + Date.now() + "_" + Math.random().toString(36).slice(2, 7);
  const p = new Promise((resolve) => {
    const timer = setTimeout(() => { fullmapWaiters.delete(reqId); resolve({ error: "timeout — browser did not respond" }); }, 12000);
    fullmapWaiters.set(reqId, { resolve, timer });
  });
  broadcastRaw({ type: "capture-fullmap", reqId });
  p.then((out) => {
    if (out.dataUrl) res.json({ dataUrl: out.dataUrl });
    else res.status(504).json({ error: out.error || "capture failed" });
  });
});

app.post("/api/undo", (_req, res) => res.json({ ok: undo(), history: historyCounts() }));
app.post("/api/redo", (_req, res) => res.json({ ok: redo(), history: historyCounts() }));

// ----- Projects --------------------------------------------------------------
app.get("/api/projects", (_req, res) => res.json({ activeId, projects }));

app.post("/api/projects", (req, res) => {
  const p = createProject((req.body || {}).title);
  res.json(p);
});

app.post("/api/projects/:id/activate", (req, res) => {
  if (!activateProject(req.params.id)) return res.status(404).json({ error: "project not found" });
  broadcast();
  res.json({ activeId, projects });
});

app.delete("/api/projects/:id", (req, res) => {
  const ok = deleteProject(req.params.id);
  if (!ok) return res.status(400).json({ error: "cannot delete (not found or last project)" });
  broadcast();
  res.json({ activeId, projects });
});

app.post("/api/nodes", (req, res) => res.json(createNode(req.body || {})));

app.patch("/api/nodes/:id", (req, res) => {
  const node = updateNode(req.params.id, req.body || {});
  if (!node) return res.status(404).json({ error: "node not found" });
  res.json(node);
});

app.delete("/api/nodes/:id", (req, res) => {
  const removed = deleteNode(req.params.id);
  res.json({ removed });
});

app.post("/api/layout", (req, res) => {
  const n = tidyLayout(req.body || {});
  res.json({ ok: true, nodes: n });
});

app.post("/api/drawings", (req, res) => res.json(addDrawing(req.body || {})));
app.patch("/api/drawings/:id", (req, res) => {
  const d = state.drawings.find((x) => x.id === req.params.id);
  if (!d) return res.status(404).json({ error: "drawing not found" });
  const u = req.body || {};
  if (Array.isArray(u.points)) d.points = u.points;
  if (Number.isFinite(u.width)) d.width = u.width;
  changed();
  res.json(d);
});
app.delete("/api/drawings/:id", (req, res) => res.json({ removed: deleteDrawing(req.params.id) }));

// ----- Images ----------------------------------------------------------------
app.post("/api/images", (req, res) => {
  const img = addImageFromDataUrl(req.body || {});
  if (!img) return res.status(400).json({ error: "invalid image data" });
  res.json(img);
});

app.post("/api/images/from-url", async (req, res) => {
  try {
    const img = await addImageFromUrl(req.body || {});
    res.json(img);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

app.patch("/api/images/:id", (req, res) => {
  const img = updateImage(req.params.id, req.body || {});
  if (!img) return res.status(404).json({ error: "image not found" });
  res.json(img);
});

app.delete("/api/images/:id", (req, res) => res.json({ removed: deleteImage(req.params.id) }));

// ---- Handwriting boxes ----
app.post("/api/boxes", (req, res) => {
  const b = req.body || {};
  const kind =
    b.kind === "image" ? "image" :
    b.kind === "portal" ? "portal" :
    b.kind === "aibox" ? "aibox" : "note";
  // aibox = an AI working-region rectangle. It scopes voice commands: the user
  // draws it, then tells Claude what to do "inside this box". Claude reads its
  // bounds via list_aiboxes and places nodes within them.
  const defaultTitle =
    kind === "image" ? "คลังรูปภาพ" :
    kind === "portal" ? "Portal" :
    kind === "aibox" ? "AI Box" : "บันทึกลายมือ";
  const box = {
    id: uid("box"),
    kind,
    x: Number.isFinite(b.x) ? b.x : 160,
    y: Number.isFinite(b.y) ? b.y : 160,
    w: Number.isFinite(b.w) ? b.w : 200,
    h: Number.isFinite(b.h) ? b.h : (kind === "aibox" ? 200 : 80),
    title: typeof b.title === "string" ? b.title : defaultTitle,
    strokes: kind === "portal" || kind === "aibox" ? [] : Array.isArray(b.strokes) ? b.strokes : [],
    items: kind === "portal" || kind === "aibox" ? [] : Array.isArray(b.items) ? b.items : [],
    targetProjectId: kind === "portal" ? (b.targetProjectId || null) : undefined,
    createdAt: Date.now(),
  };
  if (!Array.isArray(state.boxes)) state.boxes = [];
  state.boxes.push(box);
  changed();
  res.json(box);
});
app.patch("/api/boxes/:id", (req, res) => {
  const box = (state.boxes || []).find((b) => b.id === req.params.id);
  if (!box) return res.status(404).json({ error: "box not found" });
  const u = req.body || {};
  for (const k of ["x", "y", "w", "h", "title", "strokes", "items", "targetProjectId"]) {
    if (u[k] !== undefined) box[k] = u[k];
  }
  changed();
  res.json(box);
});
app.delete("/api/boxes/:id", (req, res) => {
  const before = (state.boxes || []).length;
  state.boxes = (state.boxes || []).filter((b) => b.id !== req.params.id);
  // drop any links touching this box
  state.boxLinks = (state.boxLinks || []).filter(
    (l) => l.from !== req.params.id && l.to !== req.params.id
  );
  changed();
  res.json({ removed: before !== state.boxes.length });
});

// ---- Box links (connect two boxes with a line) ----
app.post("/api/box-links", (req, res) => {
  const { from, to } = req.body || {};
  if (!from || !to || from === to) return res.status(400).json({ error: "need distinct from/to" });
  if (!Array.isArray(state.boxLinks)) state.boxLinks = [];
  const boxes = state.boxes || [];
  const nodes = state.nodes || [];
  const validId = (id) => boxes.some((b) => b.id === id) || nodes.some((n) => n.id === id);
  if (!validId(from) || !validId(to))
    return res.status(404).json({ error: "box or node not found" });
  // ignore duplicates (either direction)
  const exists = state.boxLinks.some(
    (l) => (l.from === from && l.to === to) || (l.from === to && l.to === from)
  );
  if (exists) return res.json({ ok: true, duplicate: true });
  const link = { id: uid("bl"), from, to };
  state.boxLinks.push(link);
  changed();
  res.json(link);
});
app.delete("/api/box-links/:id", (req, res) => {
  const before = (state.boxLinks || []).length;
  state.boxLinks = (state.boxLinks || []).filter((l) => l.id !== req.params.id);
  changed();
  res.json({ removed: before !== (state.boxLinks || []).length });
});
// Rasterized handwriting → save as asset, queue for Claude to LOOK at, and
// drop an inbox marker so the listening Monitor wakes Claude.
app.post("/api/boxes/:id/to-claude", (req, res) => {
  const { dataUrl, note } = req.body || {};
  const m = /^data:([^;,]+)?(;base64)?,(.*)$/s.exec(dataUrl || "");
  if (!m) return res.status(400).json({ error: "invalid image data" });
  const mime = m[1] || "image/png";
  const buffer = Buffer.from(decodeURIComponent(m[3]), m[2] ? "base64" : "utf8");
  const src = saveAsset(buffer, mime);
  const entry = addImageInbox({ src, note: note || "ลายมือจาก Box" });
  addInbox(`[ลายมือ] ผู้ใช้ส่งบันทึกลายมือมาให้ดู — เรียก get_user_images เพื่ออ่าน`);
  res.json({ ok: true, entry });
});

app.post("/api/chat", (req, res) => res.json(addChat(req.body || {})));

// Chat sections (tabs)
app.post("/api/chat-sections", (req, res) => res.json(addSection((req.body || {}).name)));
app.post("/api/chat-sections/:id/activate", (req, res) => {
  if (!activateSection(req.params.id)) return res.status(404).json({ error: "section not found" });
  res.json({ activeSection: state.activeSection, chatSections: state.chatSections });
});
app.patch("/api/chat-sections/:id", (req, res) => {
  const sec = renameSection(req.params.id, (req.body || {}).name);
  if (!sec) return res.status(404).json({ error: "section not found" });
  res.json(sec);
});
app.delete("/api/chat-sections/:id", (req, res) => {
  if (!deleteSection(req.params.id)) return res.status(400).json({ error: "cannot delete (not found or last)" });
  res.json({ activeSection: state.activeSection, chatSections: state.chatSections });
});

app.post("/api/launch-claude", (req, res) => {
  const { section } = req.body || {};
  if (!section) return res.status(400).json({ error: "section name required" });
  const cmd = path.join(__dirname, "claude-listen.cmd");
  try {
    spawn("cmd.exe", ["/c", "start", `Claude — ${section}`, "cmd", "/k", cmd, section], {
      detached: true,
      stdio: "ignore",
      cwd: __dirname,
      windowsHide: false,
    }).unref();
    res.json({ ok: true, section });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post("/api/voice", (req, res) => res.json(setVoice((req.body || {}).text)));

// Groq Whisper transcription — accepts raw audio bytes, returns { text }
app.post("/api/transcribe", express.raw({ type: "*/*", limit: "25mb" }), async (req, res) => {
  const apiKey = process.env.GROQ_API_KEY;
  if (!apiKey) return res.status(500).json({ error: "GROQ_API_KEY ไม่ได้ตั้งค่า — ใส่ใน env ก่อนรัน server" });
  const lang = req.query.lang || "th";
  try {
    const formData = new FormData();
    const blob = new Blob([req.body], { type: req.headers["content-type"] || "audio/webm" });
    formData.append("file", blob, "audio.webm");
    formData.append("model", "whisper-large-v3");
    formData.append("language", lang);
    const r = await fetch("https://api.groq.com/openai/v1/audio/transcriptions", {
      method: "POST",
      headers: { Authorization: `Bearer ${apiKey}` },
      body: formData,
    });
    const data = await r.json();
    if (!r.ok) return res.status(r.status).json({ error: data.error?.message || "Groq API error" });
    res.json({ text: data.text || "" });
  } catch (e) {
    res.status(500).json({ error: String(e) });
  }
});
// ---------------------------------------------------------------------------
// Persistent faster-whisper worker — loads model once, reuses for all jobs
// ---------------------------------------------------------------------------
let whisperWorker = null;
let whisperReady = false;
let whisperModel = "large-v3-turbo"; // default
const whisperQueue = [];
let whisperCurrentJob = null;
let whisperLineBuf = "";

function whisperHandleLine(line) {
  if (line === "LOADING") { console.log(`[Whisper] loading ${whisperModel}…`); return; }
  if (line === "READY")   { whisperReady = true; console.log(`[Whisper] ${whisperModel} ready ✓`); whisperProcessNext(); return; }
  if (!whisperCurrentJob) return;
  const { res, tmpFile } = whisperCurrentJob;
  if (line === "DONE" || line.startsWith("ERROR:")) {
    if (line.startsWith("ERROR:")) console.error("[Whisper]", line);
    res.end();
    try { fs.unlinkSync(tmpFile); } catch {}
    whisperCurrentJob = null;
    whisperProcessNext();
    return;
  }
  if (line) res.write(line + "\n");
}

function whisperProcessNext() {
  if (!whisperReady || whisperCurrentJob || whisperQueue.length === 0) return;
  whisperCurrentJob = whisperQueue.shift();
  const { tmpFile, lang } = whisperCurrentJob;
  console.log(`[Whisper] job: lang=${lang} queue=${whisperQueue.length}`);
  whisperWorker.stdin.write(`${tmpFile}|${lang}\n`);
}

function spawnWhisperWorker(model) {
  if (model) whisperModel = model;
  if (whisperWorker) {
    // end any in-progress job so its HTTP response closes cleanly
    if (whisperCurrentJob) { whisperCurrentJob.res.end(); whisperCurrentJob = null; }
    whisperReady = false;
    try { whisperWorker.kill(); } catch {}
  }
  console.log(`[Whisper] spawning worker (${whisperModel})…`);
  whisperWorker = spawn("python", [path.join(__dirname, "whisper_worker.py"), whisperModel]);
  whisperReady = false;
  whisperLineBuf = "";
  whisperWorker.stdout.on("data", (d) => {
    whisperLineBuf += d.toString();
    const lines = whisperLineBuf.split("\n");
    whisperLineBuf = lines.pop();
    lines.forEach(l => whisperHandleLine(l.trim()));
  });
  whisperWorker.stderr.on("data", d => console.error("[Whisper stderr]", d.toString().trim()));
  whisperWorker.on("close", (code) => {
    if (code === null) return; // killed intentionally (model switch)
    console.log(`[Whisper] worker exited: ${code} — restarting in 3s`);
    whisperWorker = null; whisperReady = false;
    if (whisperCurrentJob) { whisperCurrentJob.res.end(); whisperCurrentJob = null; }
    setTimeout(() => spawnWhisperWorker(), 3000);
  });
}
spawnWhisperWorker();

const VALID_WHISPER_MODELS = ["large-v3", "large-v3-turbo", "medium", "small"];
app.get("/api/whisper-model", (_req, res) => res.json({ model: whisperModel }));
app.post("/api/whisper-model", (req, res) => {
  const { model } = req.body || {};
  if (!VALID_WHISPER_MODELS.includes(model)) return res.status(400).json({ error: "invalid model" });
  if (model === whisperModel) return res.json({ ok: true, model });
  spawnWhisperWorker(model);
  res.json({ ok: true, model });
});

// Local faster-whisper endpoint — streams segments, model stays loaded between calls
app.post("/api/transcribe-local", express.raw({ type: "*/*", limit: "100mb" }), (req, res) => {
  const lang = req.query.lang || "th";
  const body = req.body;
  if (!body || !Buffer.isBuffer(body) || body.length === 0)
    return res.status(400).json({ error: "ไม่ได้รับข้อมูลเสียง (body ว่าง)" });
  const tmpFile = path.join(os.tmpdir(), `pn_audio_${Date.now()}.webm`);
  try { fs.writeFileSync(tmpFile, body); } catch (e) { return res.status(500).json({ error: String(e) }); }
  console.log(`[STT] queued: ${body.length} bytes, lang=${lang}`);
  res.setHeader("Content-Type", "text/plain; charset=utf-8");
  res.setHeader("Transfer-Encoding", "chunked");
  res.setHeader("X-Accel-Buffering", "no");
  const job = { tmpFile, lang, res };
  whisperQueue.push(job);
  whisperProcessNext();
  res.on("close", () => {
    const qi = whisperQueue.indexOf(job);
    if (qi !== -1) { whisperQueue.splice(qi, 1); try { fs.unlinkSync(tmpFile); } catch {} }
  });
});

app.get("/api/voice/latest", (req, res) => {
  const consume = req.query.consume === "true" || req.query.consume === "1";
  const v = state.voice.latest;
  if (consume) consumeVoice();
  res.json(v || null);
});

// Inbox: queue a message for Claude Code, or drain the queue.
// Optional ?section=<id|name> scopes the drain to one chat section so multiple
// Claude Code instances don't steal each other's messages.
app.post("/api/inbox", (req, res) => {
  const b = req.body || {};
  res.json(addInbox(b.text, b.section));
});
app.get("/api/inbox", (req, res) => {
  const drain = req.query.drain === "true" || req.query.drain === "1";
  const secKey = req.query.section;
  let secId = null;
  if (secKey !== undefined && secKey !== "") {
    secId = resolveSectionKey(secKey);
    if (!secId) return res.json({ items: [] }); // unknown section → nothing, never drain all
  }
  const match = (m) => secId === null || (m.section || "main") === secId;
  const items = state.inbox.filter(match);
  if (drain && items.length) {
    // only mutate/broadcast when something was actually drained — otherwise every
    // ~3s poll triggered a full state broadcast + history snapshot + file write
    state.inbox = secId === null ? [] : state.inbox.filter((m) => !match(m));
    changed();
  }
  res.json({ items });
});

// Image inbox: queue an image for Claude to look at, or drain the queue.
app.post("/api/image-inbox", (req, res) => {
  const entry = addImageInbox(req.body || {});
  if (!entry) return res.status(400).json({ error: "no image src/id" });
  res.json(entry);
});
app.get("/api/image-inbox", (req, res) => {
  const drain = req.query.drain === "true" || req.query.drain === "1";
  const items = state.imageInbox.slice();
  if (drain) drainImageInbox();
  res.json({ items });
});

// ----- Calendar cache (Claude fetches via MCP and stores here) ---------------
let calendarCache = { events: [], fetchedAt: null };
app.get("/api/calendar", (_req, res) => res.json(calendarCache));
app.post("/api/calendar", (req, res) => {
  const { events } = req.body || {};
  calendarCache = { events: Array.isArray(events) ? events : [], fetchedAt: Date.now() };
  broadcastRaw({ type: "calendar", ...calendarCache });
  res.json({ ok: true, count: calendarCache.events.length });
});

app.patch("/api/meta", (req, res) => {
  if (req.body && typeof req.body.title === "string") state.meta.title = req.body.title;
  changed();
  res.json(state.meta);
});

app.post("/api/clear", (_req, res) => {
  state = emptyState(state.meta?.title || "My Mind Map");
  changed();
  res.json({ ok: true });
});

// Switch Claude Code model by writing ~/.claude/settings.json.
// Takes effect on the NEXT Claude Code session (requires restart).
const CLAUDE_SETTINGS = path.join(
  process.env.USERPROFILE || process.env.HOME || "",
  ".claude",
  "settings.json"
);
const VALID_MODELS = ["opus", "sonnet", "haiku"];
app.get("/api/current-model", (_req, res) => {
  try {
    const cfg = fs.existsSync(CLAUDE_SETTINGS)
      ? JSON.parse(fs.readFileSync(CLAUDE_SETTINGS, "utf8"))
      : {};
    res.json({ model: cfg.model || "sonnet" });
  } catch {
    res.json({ model: "sonnet" });
  }
});
app.post("/api/set-model", (req, res) => {
  const { model } = req.body || {};
  if (!VALID_MODELS.includes(model))
    return res.status(400).json({ error: "invalid model" });
  try {
    let cfg = {};
    if (fs.existsSync(CLAUDE_SETTINGS))
      cfg = JSON.parse(fs.readFileSync(CLAUDE_SETTINGS, "utf8"));
    cfg.model = model;
    fs.writeFileSync(CLAUDE_SETTINGS, JSON.stringify(cfg, null, 2), "utf8");
    res.json({ ok: true, model });
  } catch (e) {
    res.status(500).json({ error: String(e) });
  }
});

// Serve uploaded image assets, then the static frontend.
app.use("/assets", express.static(ASSETS_DIR));
app.use(express.static(path.join(__dirname, "public")));

server.listen(PORT, () => {
  console.log(`\n  Powerfull Note running:`);
  console.log(`    →  http://localhost:${PORT}\n`);
  console.log(`  Open it in Chrome or Edge (needed for Thai voice).`);
});
