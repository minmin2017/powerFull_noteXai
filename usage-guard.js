#!/usr/bin/env node
/**
 * usage-guard.js — เฝ้าโควตา session ของ Claude แล้วสั่ง "พอแค่นี้" / "กลับมาทำต่อ" อัตโนมัติ
 *
 * ทำไมต้องเป็นสคริปต์แยก (ไม่ใช่ Monitor ใน Claude):
 *   ตอนโควตาหมด "Claude ตายไปแล้ว" — อะไรที่รันอยู่ในตัว Claude จะตายตามไปด้วย
 *   ตัวปลุกกลับมาจึงต้องอยู่ข้างนอก รันด้วย Node เปล่าๆ ไม่กิน token เลย
 *
 * กลไก 2 จังหวะ:
 *   1) session >= STOP_AT (85%)  → ยิงข้อความเข้า inbox บอก Claude ให้เขียน HANDOFF.md แล้วหยุด
 *   2) โควตารีเซ็ต (percent ตกฮวบ) → ยิงข้อความเข้า inbox บอกให้ทำต่อก่อนเสมอ แล้วเช็ค
 *      ผ่าน GET /api/agent/status?section=... ว่า Claude session เดิม (section เดียวกัน)
 *      ยัง poll/drain inbox อยู่ไหม (server stamp เวลาไว้ทุกครั้งที่ agent=claude เรียก
 *      GET /api/inbox — ทั้ง curl-poll ทุก ~3s และ ws-inbox.js heartbeat ทุก ~15s)
 *      - ยัง listen อยู่        → จบแค่ข้อความ ไม่เปิดหน้าต่างใหม่ (Min ไม่อยากให้ spawn
 *                                  agent ใหม่ทุกครั้ง — ให้ session เดิมทำต่อ คอนเท็กซ์ไม่หาย)
 *      - ไม่มีใคร listen / เช็คไม่ได้ → fallback: POST /api/launch-claude เปิด Claude ใหม่
 *
 * ใช้งาน:  node usage-guard.js [section]        (default section = main)
 * หยุด:    Ctrl+C
 */

// 127.0.0.1, not localhost: on this machine "localhost" resolves ::1 first and
// stalls ~2s against an IPv4-only server before falling back.
const BASE     = process.env.PN_BASE || "http://127.0.0.1:4321";
const SECTION  = process.argv[2] || process.env.CHAT_SECTION || "main";
const STOP_AT  = Number(process.env.STOP_AT  || 85);   // % ที่สั่งให้หยุด
const RESET_AT = Number(process.env.RESET_AT || 20);   // ต่ำกว่านี้ = ถือว่ารีเซ็ตแล้ว
const EVERY_MS = Number(process.env.EVERY_MS || 60000);
// ถือว่า session เดิม "ยัง listen อยู่" ถ้า agent=claude poll/drain inbox ของ section
// นี้มาภายในกี่ ms — ต้องกว้างกว่าจังหวะ poll ที่มีอยู่จริงทุกแบบ (curl ทุก ~3s,
// ws-inbox.js heartbeat ทุก ~15s) พอให้กัน jitter/เครื่องหน่วงชั่วคราว
const LIVE_WINDOW_MS = Number(process.env.LIVE_WINDOW_MS || 90000);

let warned = false;   // ยิงคำสั่งหยุดไปแล้วหรือยัง
let lastPct = null;

const log = (...a) => console.log(new Date().toLocaleTimeString("th-TH"), ...a);

async function jget(path) {
  const r = await fetch(BASE + path);
  if (!r.ok) throw new Error(path + " → " + r.status);
  return r.json();
}
async function jpost(path, body) {
  const r = await fetch(BASE + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return r.json().catch(() => ({}));
}

const say = (text) => jpost("/api/inbox", { text, section: SECTION });

// true/false = server answered definitively; null = couldn't tell (server is
// an older version without /api/agent/status?section=, or unreachable).
// Callers MUST treat null as "fall back to today's behavior" (spawn a new
// window) — never as "assume alive", or a truly dead session would never get
// woken back up.
async function isClaudeListening() {
  try {
    const r = await jget(`/api/agent/status?section=${encodeURIComponent(SECTION)}&withinMs=${LIVE_WINDOW_MS}`);
    if (r && r.claude && typeof r.claude.online === "boolean") return r.claude.online;
    return null;
  } catch {
    return null;
  }
}

async function tick() {
  let u;
  try {
    u = await jget("/api/claude-usage");
  } catch (e) {
    log("⚠️  อ่านโควตาไม่ได้:", e.message);   // server ดับชั่วคราว — ข้ามรอบนี้ ไม่ตาย
    return;
  }
  if (u.error || !u.session) { log("⚠️  usage unavailable:", u.detail || ""); return; }

  const pct = u.session.percent;
  const wk  = u.weekly ? u.weekly.percent : "?";
  if (pct !== lastPct) log(`session ${pct}%  ·  weekly ${wk}%${warned ? "  [warned]" : ""}`);
  lastPct = pct;

  // ---- จังหวะที่ 1: ถึงเพดาน → สั่งหยุดอย่างเป็นระเบียบ
  if (!warned && pct >= STOP_AT) {
    warned = true;
    const resets = u.session.resets_at
      ? new Date(u.session.resets_at).toLocaleString("th-TH", { hour12: false })
      : "ไม่ทราบ";
    log(`🛑 ถึง ${pct}% แล้ว — สั่งหยุด`);
    await say(
      `🛑 [usage-guard] โควตา session ใช้ไป ${pct}% แล้ว (โควตาจะรีเซ็ต ${resets})\n\n` +
      `ให้ทำตามนี้ทันที แล้วหยุดรับงานใหม่:\n` +
      `1. อัปเดต HANDOFF.md ให้เป็นสถานะล่าสุด (งานที่ทำค้าง, path ไฟล์, ขั้นตอนถัดไป)\n` +
      `2. สรุปให้ Min สั้นๆ ผ่าน say_to_user ว่าหยุดที่ตรงไหน\n` +
      `3. อย่าเพิ่งเริ่มงานใหม่ที่ยาว — รอโควตารีเซ็ตก่อน\n\n` +
      `(ข้อความนี้ยิงอัตโนมัติจาก usage-guard.js ไม่ใช่ Min พิมพ์เอง)`
    );
  }

  // ---- จังหวะที่ 2: รีเซ็ตแล้ว → ปลุกกลับมาทำต่อ
  if (warned && pct <= RESET_AT) {
    warned = false;
    log(`✅ โควตารีเซ็ตแล้ว (${pct}%) — ปลุก Claude กลับมา`);
    await say(
      `✅ [usage-guard] โควตารีเซ็ตแล้ว — เหลือใช้อีกเยอะ (ตอนนี้ ${pct}%)\n\n` +
      `เริ่มงานต่อได้เลย:\n` +
      `1. อ่าน HANDOFF.md ในโปรเจกต์นี้ก่อน — มีสถานะงานล่าสุดครบ\n` +
      `2. arm inbox listener ของ section "${SECTION}" ใหม่\n` +
      `3. ทำงานที่ค้างอยู่ต่อจากเดิม แล้วบอก Min ว่ากลับมาแล้ว\n\n` +
      `(ข้อความนี้ยิงอัตโนมัติจาก usage-guard.js)`
    );
    // สำคัญ (คำขอ Min): ถ้า Claude session เดิม (process เดิม, section เดียวกัน)
    // ยังไม่ตาย — แค่โควตาหมดชั่วคราว — Monitor ของมันจะเห็นข้อความข้างบนเองจาก
    // การ poll/drain ตามปกติอยู่แล้ว ไม่ต้อง spawn Claude ใหม่มาแย่งคอนเท็กซ์
    // เปิดหน้าต่างใหม่เฉพาะตอนเช็คแล้วไม่มีใคร listen จริงๆ (fallback)
    const listening = await isClaudeListening();
    if (listening === true) {
      log(`   session เดิมยัง listen section "${SECTION}" อยู่ — ส่งข้อความพอ ไม่เปิดหน้าต่างใหม่`);
    } else {
      log(
        listening === null
          ? "   เช็คสถานะ session เดิมไม่ได้ (server รุ่นเก่า/ไม่ตอบ) — fallback: เปิดหน้าต่างใหม่"
          : `   ไม่มีใคร listen section "${SECTION}" อยู่ — เปิดหน้าต่างใหม่`
      );
      try {
        await jpost("/api/launch-claude", { section: SECTION });
        log("   เปิดหน้าต่าง Claude ใหม่แล้ว");
      } catch (e) {
        log("   ⚠️ เปิด Claude ไม่สำเร็จ:", e.message, "— ข้อความยังอยู่ใน inbox");
      }
    }
  }
}

log(`usage-guard เริ่มทำงาน · section="${SECTION}" · หยุดที่ ${STOP_AT}% · ถือว่ารีเซ็ตเมื่อ ≤ ${RESET_AT}%`);
tick();
setInterval(tick, EVERY_MS);
