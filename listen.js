// listen.js - Smart Gemini Auto-Agent for Powerfull Note
// This script polls the inbox and autonomously performs actions based on keywords.

const PORT = process.env.PORT || 4321;
const BASE = `http://localhost:${PORT}`;

const API = {
  // scoped to a dedicated "gemini" chat section so it never drains the messages
  // Claude listens for (Claude reads its own section's inbox via MCP)
  inbox: `${BASE}/api/inbox?section=gemini&drain=true`,
  chat: `${BASE}/api/chat`,
  nodes: `${BASE}/api/nodes`,
  layout: `${BASE}/api/layout`,
  clear: `${BASE}/api/clear`
};

console.log(`\n  🚀 Smart Gemini Agent is LIVE and Auto-Processing...`);
console.log(`  Watching: ${API.inbox}\n`);

async function call(url, method = 'GET', body = null) {
  try {
    const res = await fetch(url, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined
    });
    return res.ok ? await res.json() : null;
  } catch (e) { return null; }
}

async function say(text) {
  await call(API.chat, 'POST', { role: 'gemini', text: `[Gemini Auto] ${text}` });
}

async function handleMessage(text) {
  const msg = text.trim();
  console.log(`\x1b[36m[Processing]\x1b[0m ${msg}`);

  // 1. "เพิ่มหัวข้อ [ชื่อ]"
  if (msg.startsWith('เพิ่มหัวข้อ')) {
    const title = msg.replace('เพิ่มหัวข้อ', '').trim();
    const node = await call(API.nodes, 'POST', { text: title || 'หัวข้อใหม่' });
    if (node) {
      await say(`เพิ่มหัวข้อ "${node.text}" ให้แล้วครับ! (ID: ${node.id})`);
      await call(API.layout, 'POST'); // Auto tidy
    }
    return;
  }

  // 2. "จัดระเบียบ" หรือ "จัดเลย์เอาต์"
  if (msg.includes('จัดระเบียบ') || msg.includes('จัดเลย์เอาต์') || msg.includes('tidy')) {
    const res = await call(API.layout, 'POST');
    if (res) await say(`จัดระเบียบมายด์แมปให้สวยงามแล้วครับ (${res.nodes} โหนด)`);
    return;
  }

  // 3. "ล้าง"
  if (msg === 'ล้าง' || msg === 'เคลียร์') {
    await call(API.clear, 'POST');
    await say('ล้างมายด์แมปให้เรียบร้อยแล้วครับ เริ่มต้นใหม่ได้เลย!');
    return;
  }

  // Default: Just acknowledge
  await say(`ได้รับข้อความ: "${msg}" แล้วครับ! (สำหรับคำสั่งซับซ้อน โปรดบอก Gemini ใน Terminal นะครับ)`);
}

async function poll() {
  const data = await call(API.inbox);
  if (data && data.items && data.items.length > 0) {
    for (const item of data.items) {
      await handleMessage(item.text);
    }
  }
  setTimeout(poll, 2000);
}

poll();
