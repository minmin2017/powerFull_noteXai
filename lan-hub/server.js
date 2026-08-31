import express from 'express';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = 8080;
const NOTE_BASE = process.env.NOTE_SERVER_URL || 'http://127.0.0.1:4321';
const EVENTS_FILE = path.join(__dirname, 'data', 'events.json');
const ROUTINES_FILE = path.join(__dirname, 'data', 'routines.json');

let dataVersion = Date.now();
const sseClients = new Set();

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

function readJson(file) {
  if (!fs.existsSync(file)) return null;
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return null; }
}

function writeJson(file, data) {
  fs.writeFileSync(file, JSON.stringify(data, null, 2), 'utf8');
  notifyUpdate();
}

function notifyUpdate() {
  dataVersion = Date.now();
  for (const client of sseClients) {
    try {
      client.write(`data: ${JSON.stringify({ version: dataVersion })}\n\n`);
    } catch {
      sseClients.delete(client);
    }
  }
}

// Version & SSE Live Sync API
app.get('/api/version', (_req, res) => res.json({ version: dataVersion }));
app.get('/api/live-sync', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.flushHeaders();

  sseClients.add(res);
  req.on('close', () => sseClients.delete(res));
});

// Events API
app.get('/api/events', (_req, res) => res.json(readJson(EVENTS_FILE) || []));
app.post('/api/events', (req, res) => {
  const ev = req.body;
  if (!ev || !ev.title || !ev.startDate) return res.status(400).json({ error: 'missing data' });
  const list = readJson(EVENTS_FILE) || [];
  list.push(ev);
  writeJson(EVENTS_FILE, list);
  res.json({ ok: true, event: ev });
});
app.delete('/api/events/:id', (req, res) => {
  let list = readJson(EVENTS_FILE) || [];
  list = list.filter(e => e.id !== req.params.id);
  writeJson(EVENTS_FILE, list);
  res.json({ ok: true });
});

// Routines API
app.get('/api/routines', (_req, res) => res.json(readJson(ROUTINES_FILE) || {}));
app.post('/api/routines/:phase/slot', (req, res) => {
  const { phase } = req.params;
  const slot = req.body;
  const data = readJson(ROUTINES_FILE) || {};
  if (!data[phase]) return res.status(404).json({ error: 'phase not found' });
  data[phase].slots.push(slot);
  writeJson(ROUTINES_FILE, data);
  res.json({ ok: true });
});
app.delete('/api/routines/:phase/slot/:index', (req, res) => {
  const { phase, index } = req.params;
  const idx = Number(index);
  const data = readJson(ROUTINES_FILE) || {};
  if (data[phase] && Array.isArray(data[phase].slots) && idx >= 0 && idx < data[phase].slots.length) {
    data[phase].slots.splice(idx, 1);
    writeJson(ROUTINES_FILE, data);
    return res.json({ ok: true });
  }
  res.status(400).json({ error: 'invalid index' });
});

// Chat Proxy API to PowerNote Main Section
app.post('/api/send-chat', async (req, res) => {
  const { text, section } = req.body || {};
  if (!text) return res.status(400).json({ error: 'missing text' });
  const sec = section || 'main';
  try {
    await fetch(`${NOTE_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role: 'user', text, section: sec }),
    });
    await fetch(`${NOTE_BASE}/api/inbox`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, section: sec }),
    });
    res.json({ ok: true });
  } catch (e) {
    res.status(502).json({ error: 'cannot reach PowerNote', detail: String(e) });
  }
});

app.get('/api/chat-log', async (req, res) => {
  const section = req.query.section || 'main';
  try {
    const state = await fetch(`${NOTE_BASE}/api/state`).then(r => r.json());
    const chat = (state.chat || []).filter(m => (m.section || 'main') === section);
    res.json({ section, messages: chat });
  } catch (e) {
    res.status(502).json({ error: 'cannot reach PowerNote', detail: String(e) });
  }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`[LAN-APP] Server running with Live Auto-Sync at http://0.0.0.0:${PORT}`);
  console.log(`[LAN-APP] Accessible at http://192.168.1.45:${PORT}`);
});
