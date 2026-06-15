# Powerfull Note — ระบบรับข้อความแบบ Event-based (Data Sheet)

อัปเดตล่าสุด: 2026-06-15

## สรุปสั้น
ข้อความที่พิมพ์/พูดในแอปจะ **ไม่ถูก poll ซ้ำๆ** เพื่อประหยัด token —
Claude Code จะถูกปลุก (wake) เฉพาะตอนมีข้อความจริงเท่านั้น

---

## ตารางองค์ประกอบ

| องค์ประกอบ | ไฟล์ / ที่อยู่ | หน้าที่ |
|---|---|---|
| Inbox queue (ต่อโปรเจกต์) | `data/projects/<id>.json` → `inbox[]` | เก็บข้อความที่ผู้ใช้ส่ง (cap 200) |
| ปุ่มส่ง / Enter / ไมค์ | `public/app.js` `submitUserInput()` | ดันข้อความเข้า `POST /api/inbox` |
| REST รับเข้า | `server.js` `POST /api/inbox` | `addInbox(text)` |
| REST ดึงออก | `server.js` `GET /api/inbox?drain=true` | `drainInbox()` คืน items แล้วล้างคิว |
| MCP tool | `mcp-server.js` `get_inbox` | Claude ดึงข้อความผ่าน HTTP |
| ตัวปลุก (event bridge) | persistent `Monitor` (bash loop) | curl `/api/inbox` ทุก ~3s ในเครื่อง |

---

## Flow ของ event

| ขั้น | เกิดอะไรขึ้น | ใช้ token ไหม |
|---|---|---|
| 1 | ผู้ใช้พิมพ์/พูด → กด "ส่ง" | ❌ |
| 2 | `POST /api/inbox` เก็บลงคิวของโปรเจกต์ที่ active | ❌ |
| 3 | bash Monitor curl `/api/inbox?drain=true` ทุก ~3s | ❌ (รันใน shell) |
| 4 | เจอข้อความ → print `MSG "..."` → ส่ง `<task-notification>` | ❌ |
| 5 | Claude ถูกปลุก อ่านข้อความ ทำงาน (แก้ mind map ฯลฯ) | ✅ เฉพาะตอนนี้ |
| 6 | ตอบกลับในแอปผ่าน MCP `say_to_user` | ✅ |

> หัวใจ: ขั้น 1–4 ไม่กิน token เลย เพราะเป็น curl ใน shell loop —
> Claude ตื่นเฉพาะขั้น 5 ที่มีงานจริง

---

## ทำไมต้อง event-based (เหตุผลของผู้ใช้)
ก่อนหน้านี้ใช้ `ScheduleWakeup` poll ทุก 60s → Claude ตื่นทุกนาทีแม้ไม่มีข้อความ = เปลือง token
เปลี่ยนเป็น Monitor bash loop ที่ poll ในเครื่อง (ฟรี) และปลุก Claude แค่ตอนมีของจริง

## หมายเหตุการใช้งาน
- ต้อง re-arm Monitor ใหม่ทุกครั้งที่ restart Claude Code → สั่งผ่าน `/loop`
- Monitor task ปัจจุบัน: persistent, timeout 1 ชม. (ต่ออายุเองเมื่อมี event)
- ข้อจำกัด: ไม่สามารถ "push" เข้า Claude Code TUI โดยตรงได้ จึงใช้รูปแบบ inbox-pull + local monitor แทน
