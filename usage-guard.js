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
 *   2) โควตารีเซ็ต (percent ตกฮวบ) → POST /api/launch-claude เปิด Claude ใหม่ + บอกให้อ่าน HANDOFF.md ทำต่อ
 *
 * ใช้งาน:  node usage-guard.js [section]        (default section = main)
 * หยุด:    Ctrl+C
 */

const BASE     = process.env.PN_BASE || "http://localhost:4321";
const SECTION  = process.argv[2] || process.env.CHAT_SECTION || "main";
const STOP_AT  = Number(process.env.STOP_AT  || 85);   // % ที่สั่งให้หยุด
const RESET_AT = Number(process.env.RESET_AT || 20);   // ต่ำกว่านี้ = ถือว่ารีเซ็ตแล้ว
const EVERY_MS = Number(process.env.EVERY_MS || 60000);

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
    try {
      await jpost("/api/launch-claude", { section: SECTION });
      log("   เปิดหน้าต่าง Claude ใหม่แล้ว");
    } catch (e) {
      log("   ⚠️ เปิด Claude ไม่สำเร็จ:", e.message, "— ข้อความยังอยู่ใน inbox");
    }
  }
}

log(`usage-guard เริ่มทำงาน · section="${SECTION}" · หยุดที่ ${STOP_AT}% · ถือว่ารีเซ็ตเมื่อ ≤ ${RESET_AT}%`);
tick();
setInterval(tick, EVERY_MS);
