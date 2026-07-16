// agent-brain.js - Deep Trace Version
import fs from 'node:fs';

function loadEnv() {
  try {
    const envFile = fs.readFileSync('.env', 'utf8');
    envFile.split('\n').forEach(line => {
      const [key, ...val] = line.split('=');
      if (key && val) process.env[key.trim()] = val.join('=').trim();
    });
  } catch (e) { console.error("FAILED TO LOAD .ENV"); }
}
loadEnv();

const API_KEY = process.env.GOOGLE_API_KEY;
const BASE = `http://localhost:4321`;

console.log(`\n  🚀 DEEP TRACE AGENT STARTING...`);
console.log(`  Target: ${BASE}`);
console.log(`  Key: ${API_KEY ? 'Present' : 'MISSING'}\n`);

async function callApp(path, method = 'GET', body = null) {
  try {
    const res = await fetch(`${BASE}${path}`, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined
    });
    return res.ok ? await res.json() : null;
  } catch (e) { 
    console.log(`[App Error] ${e.message}`);
    return null; 
  }
}

async function askGemini(prompt) {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${API_KEY}`;
  const body = {
    contents: [{ parts: [{ text: `คุณคือผู้ช่วยในแอป Mind Map. ตอบกลับเป็น JSON: { "reply": "...", "tasks": [] }. ข้อความจากผู้ใช้: "${prompt}"` }] }],
    generationConfig: { responseMimeType: "application/json" }
  };
  try {
    const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const data = await res.json();
    if (data.error) throw new Error(data.error.message);
    return JSON.parse(data.candidates[0].content.parts[0].text);
  } catch (e) {
    console.log(`[Gemini Error] ${e.message}`);
    return { reply: "Error: " + e.message, tasks: [] };
  }
}

async function loop() {
  const data = await callApp('/api/inbox?section=gemini&drain=true'); // scoped: never steal Claude's inbox
  if (data && data.items && data.items.length > 0) {
    console.log(`[EVENT] Found ${data.items.length} msgs`);
    for (const item of data.items) {
      console.log(`[USER] ${item.text}`);
      const result = await askGemini(item.text);
      console.log(`[AI] ${result.reply}`);
      await callApp('/api/chat', 'POST', { role: 'gemini', text: result.reply });
    }
  }
  setTimeout(loop, 2000);
}
loop();

// ---------------------------------------------------------------------------
// Gemini task-delegation pipeline (separate from the chat loop above).
// Claude's MCP tool `delegate_to_gemini` posts to /api/gemini/task; we claim
// pending tasks here, run them through Gemini, and post the result back.
// ---------------------------------------------------------------------------

// Heartbeat: tells the server "I'm alive" so /api/agent/status can report
// gemini.online. Runs independently of the chat loop.
async function heartbeat() {
  await callApp('/api/agent/heartbeat', 'POST', { agent: 'gemini' });
  setTimeout(heartbeat, 5000);
}
// DISABLED 2026-07-06: delegated tasks now route to Antigravity (Min's choice).
// Its poller antigravity-wait.py owns the heartbeat + task claiming, so the
// online dot reflects Antigravity readiness — not this weak 1.5-flash bridge.
// Re-enable only if you want agent-brain.js to be the fallback delegation worker.
// heartbeat();

// Free-form (non-JSON) Gemini call for delegated subtasks, framed in the
// Thinking-Men-Men structure (requirement / prohibitions / principles / context).
async function askGeminiTask({ requirement, prohibitions, principles, context }) {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${API_KEY}`;
  const prompt =
    `คุณคือฝ่ายปฏิบัติการ ทำงานตามกรอบ Thinking Men Men.\n` +
    `ความต้องการ: ${requirement || "(ไม่ระบุ)"}\n` +
    `ข้อห้าม: ${prohibitions || "(ไม่มี)"}\n` +
    `หลักการ: ${principles || "(ไม่มี)"}\n` +
    `Context: ${context || "(ไม่มี)"}\n` +
    `ทำงานให้เสร็จ แล้วตอบผลลัพธ์เป็นข้อความล้วน (ถ้าเป็นโค้ดใส่ใน code block). ถ้าข้อมูลไม่พอให้บอกว่าขาดอะไร.`;
  const body = { contents: [{ parts: [{ text: prompt }] }] };
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.error) throw new Error(data.error.message || JSON.stringify(data.error));
  const text = data?.candidates?.[0]?.content?.parts?.[0]?.text;
  if (!text) throw new Error('Gemini ไม่คืนคำตอบ (candidates ว่าง) — ' + JSON.stringify(data).slice(0, 300));
  return text;
}

async function taskLoop() {
  try {
    const data = await callApp('/api/gemini/tasks?status=pending');
    const tasks = (data && data.tasks) || [];
    for (const t of tasks) {
      console.log(`[GeminiTask] claiming ${t.id}`);
      const claimed = await callApp(`/api/gemini/task/${t.id}/claim`, 'POST');
      if (!claimed) continue; // someone else claimed it, or server error
      try {
        const result = await askGeminiTask(t.task || {});
        console.log(`[GeminiTask] ${t.id} done`);
        await callApp(`/api/gemini/task/${t.id}/result`, 'POST', { result });
      } catch (e) {
        console.log(`[GeminiTask] ${t.id} error: ${e.message}`);
        await callApp(`/api/gemini/task/${t.id}/result`, 'POST', { error: e.message });
      }
    }
  } catch (e) {
    console.log(`[GeminiTask loop error] ${e.message}`);
  }
  setTimeout(taskLoop, 2000);
}
// DISABLED 2026-07-06: Antigravity (via antigravity-wait.py) is the delegation
// worker now — it reads files + writes code (~Sonnet), unlike this 1.5-flash
// bridge. Leaving this on would race Antigravity to claim tasks and then fail
// (no GOOGLE_API_KEY). Re-enable only as a weak auto fallback.
// taskLoop();
