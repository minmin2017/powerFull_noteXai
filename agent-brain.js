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
  const data = await callApp('/api/inbox?drain=true');
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
