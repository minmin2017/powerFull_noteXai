# Powerfull Note — project instructions

แอป mind-map โลคอล + MCP bridge ของ Min (http://localhost:4321)

## ⭐ เริ่มทุก session — arm inbox listener อัตโนมัติ

1. เช็คเซิร์ฟเวอร์: `curl -s -m 5 "http://localhost:4321/api/inbox?drain=true"`
   - server down → บอก Min รัน `start.cmd`
   - มี items ค้าง → ตอบก่อนเริ่มฟัง
2. Arm Monitor (persistent) ด้วย **ws-inbox.js** (WebSocket, ไม่ poll ทุก 3s):
   - **มี CHAT_SECTION** → `node ws-inbox.js "$CHAT_SECTION"`
   - **ไม่มี** → `node ws-inbox.js` (ฟังทุก section)
   - แต่ละ stdout line = ข้อความใหม่ 1 ข้อความ
3. ตอบกลับผ่าน MCP `say_to_user` (env CHAT_SECTION เติมให้อัตโนมัติ)

> re-arm ทุก session — Monitor ไม่ persist ข้าม session | รายละเอียด: `docs/event-based-system.md`

## เปิดเร็ว: `claude-listen.cmd [section]`
ดับเบิลคลิก = เปิด Claude แบบ skip-permissions + เช็ค/สตาร์ท server + arm Monitor
**Auto-start ตอนเปิด Windows:** `install-autostart.cmd` ครั้งเดียว (ยกเลิก: `uninstall-autostart.cmd`)

## 🧵 หลาย Claude ขนานกัน — section ↔ Claude คนละตัว
```
claude-listen.cmd "หลัก"       # หน้าต่าง cmd ที่ 1
claude-listen.cmd "งานวิจัย"   # หน้าต่าง cmd ที่ 2
```
**กติกา:** ดู env `CHAT_SECTION` — ฟัง/ตอบเฉพาะ section ตัวเอง ห้ามยุ่ง section อื่น ห้าม drain inbox รวม

## โหมด Agent (ขนาน)
งานอิสระจากกันสนิท → ใช้ subagent ทำขนาน (เช่น ค้นหลายแหล่ง / แก้ไฟล์คนละไฟล์)
งานผูกกัน/ไฟล์เดียวกัน → ทำเองรวดเดียว (subagent โหลด context ใหม่ช้ากว่า)

## กฎสำคัญ
- **tidy_layout**: ระบุ `rootId` เสมอ = จัดเฉพาะกิ่งที่แก้ ไม่เขย่าทั้งกระดาน
  จัดทั้งโปรเจกต์ (ไม่ใส่ rootId) **เฉพาะตอน Min สั่งจัดทั้งกระดานเท่านั้น**
- **รีเซ็ต server**: รอจนงานเสร็จทุกขั้น → รีเซ็ตครั้งเดียวตอนท้าย ห้ามรีเซ็ตระหว่างงาน
- ตอบ Min เป็นภาษาไทยผ่าน `say_to_user`
- เชื่อมผ่าน MCP (`.mcp.json`) ไม่ใช่ Claude API

## Graphify — knowledge graph ของ codebase
`graphify-out/graph.json` (487 nodes, 797 edges) — ประหยัดโทเคน ~13.8x ต่อ query
- **ถามเรื่อง codebase** → อ่าน graph ก่อน ไม่อ่านไฟล์ทีละไฟล์
- God nodes: `$()`, `render()`, `changed()`, `eventCanvasPos()`, `api()`
- `api()` ใน app.js = single gateway ระหว่าง canvas กับ server
- อัปเดต graph: `/graphify --update`

## ฟีเจอร์กล่อง (Prototype 3)
- **note** = ลายมือ + OCR/ส่งให้ Claude | **image** = แกลเลอรีรูป (กดเปิด URL) | **aibox** = พื้นที่งาน Claude
- โยงกล่อง: กด 🔗 บนหัว → ลาก | ลบ: × กลางเส้น
- **แชทหลาย section**: แท็บบนพาเนลซ้าย — ดับเบิลคลิกเปลี่ยนชื่อ
