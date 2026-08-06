# Powerfull Note — project instructions

แอป mind-map โลคอล + MCP bridge ของ Min (http://localhost:4321)

## 🔋 โควตา session — เช็คเองได้ ไม่ต้องถาม Min

**Claude อ่าน % การใช้โควตาของตัวเองได้** ผ่าน API ของแอปนี้:
```bash
curl -s http://localhost:4321/api/claude-usage
# {"session":{"percent":70,"resets_at":...},"weekly":{"percent":29,...}}
```
เบื้องหลัง (`server.js:1724`): อ่าน OAuth token จาก `~/.claude/.credentials.json` แล้วเรียก
`https://api.anthropic.com/api/oauth/usage` → เลข**จริง**จาก Anthropic ไม่ใช่ค่าประมาณ (cache 60 วิ)

> ⚠️ `session.percent` = **โควตาแผน** (รอบ ~5 ชม.) — คนละอย่างกับ context window ที่ harness ย่อให้เอง
> ห้ามบอก Min ว่า "ผมดู % ตัวเองไม่ได้" — ดูได้ ผ่าน endpoint นี้

**ระบบอัตโนมัติ `usage-guard.js`** (รันแยกจาก Claude เพราะตอนโควตาหมด Claude ตายไปด้วย):
- **`start.cmd` เปิดให้อัตโนมัติแล้ว** (หน้าต่าง "Usage Guard") ทุกครั้งที่ Min เปิดเซิร์ฟเวอร์ ไม่ต้องรันมือ
- รันมือถ้าจำเป็น: `node usage-guard.js main` (เปิดค้างไว้ 1 หน้าต่าง ไม่กิน token)
- ⚠️ **Claude ไม่สามารถเปิดหน้าต่างนี้แทน Min ได้** — คำสั่ง `start` จาก Bash tool ของ Claude ไม่สร้าง process จริงบนเดสก์ท็อป Min (ตรวจสอบด้วย `Get-CimInstance Win32_Process -Filter "Name='node.exe'"` ก่อนอ้างว่ารันแล้วเสมอ) ถ้า guard ไม่ได้รัน ให้ขอ Min พิมพ์ `!node usage-guard.js main` เอง
- **ถึง 85%** → ยิงข้อความเข้า inbox สั่งให้ **อัปเดต `HANDOFF.md` แล้วหยุดรับงานใหม่**
- **โควตารีเซ็ต (≤20%)** → ยิง inbox + `POST /api/launch-claude` เปิด Claude ใหม่ให้ทำงานต่อ

**`HANDOFF.md`** (root โปรเจกต์) = สมองสำรองข้าม session — **อ่านไฟล์นี้ก่อนเริ่มงานทุกครั้ง**
แล้วอัปเดตทับเรื่อยๆ ระหว่างทำงาน (เขียนเผื่อไว้ก่อนฟรี แต่รอจนโควตาหมดคือสายเกินไป)

## ⭐ เริ่มทุก session — arm inbox listener อัตโนมัติ

1. เช็คเซิร์ฟเวอร์: `curl -s -m 5 "http://localhost:4321/api/inbox?drain=true"`
   - server down → บอก Min รัน `start.cmd`
   - มี items ค้าง → ตอบก่อนเริ่มฟัง
2. **ตรวจ section ID จริงก่อน arm** — CHAT_SECTION ใน env อาจเป็นชื่อ (`main`) แต่ ID จริงต่างกัน (เช่น `sec_mqwg4mp8nubua`)
   - drain ไม่ใส่ section ก่อน: `curl /api/inbox?drain=true` → ดู field `section` ในแต่ละ item
   - หรืออ่าน memory (`MEMORY.md`) — อาจบันทึก ID จริงไว้แล้ว
   - ใช้ ID จริงเสมอ ไม่ใช่ชื่อ env ตรงๆ
3. Arm Monitor (persistent) ด้วย **ws-inbox.js** (WebSocket, ไม่ poll ทุก 3s):
   - `node ws-inbox.js "<SECTION_ID_จริง>"` ใน dir `powerNote_xai`
   - แต่ละ stdout line = ข้อความใหม่ 1 ข้อความ
4. ตอบกลับผ่าน MCP `say_to_user` พร้อม `section: "<SECTION_ID_จริง>"` เสมอ

### ปุ่ม Gemini — ไม่ต้องฟัง/ตอบ
เมื่อ Min กดปุ่ม Gemini บน section ใด `agentListener` ของ section นั้นจะเปลี่ยนเป็น `"gemini"`
Server มี built-in filter: **ส่ง `agent=claude` ใน poll URL เสมอ** — server จะคืน `items:[]` อัตโนมัติเมื่อ section อยู่ในโหมด Gemini → Claude ไม่เห็น/ไม่ drain ข้อความนั้น
```
curl -s -G http://localhost:4321/api/inbox \
  --data-urlencode "section=<ID>" \
  --data-urlencode "drain=true" \
  --data-urlencode "agent=claude"
```

> **บทเรียน (session 2026-06-28):** arm ด้วย `section=main` แต่ข้อความอยู่ใน `sec_mqwg4mp8nubua` → Monitor ไม่จับ ต้อง drain รวมก่อนถึงเจอ — ป้องกันด้วยการตรวจ ID จริงทุก session

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
`graphify-out/graph.json` (493 nodes, 732 edges) — ประหยัดโทเคน ~13.8x **ต่อ query เฉพาะจุด**
- **กฎทั่วไป:** โปรเจกต์ไหนที่ Min พูดถึงถ้ามีไฟล์ `graphify-out/graph.json` → **ต้องนึกถึง/เช็คกราฟก่อน** แล้ว query เฉพาะ node/ความสัมพันธ์ที่ต้องการ ค่อยเจาะอ่านไฟล์จริงเฉพาะส่วน — ไม่ไล่อ่านไฟล์ทีละไฟล์ตั้งแต่ต้น
- **query เฉพาะจุด ห้ามโหลดทั้งก้อน** — graph.json อาจใหญ่กว่าโค้ดจริง (powerNote ~85k tok, animation graph บวมเพราะ index ไลบรารี manim เข้าไป ~9.7M tok โหลดไม่ไหว) การประหยัดมาจาก "ดึง subgraph รอบ node ที่สนใจ" ไม่ใช่ "อ่านทั้งไฟล์แทนโค้ด"
- **ช่วยจริงตอน:** ถามความสัมพันธ์ในโค้ดใหญ่ (ใครเรียกใคร / ลบอันนี้กระทบอะไร / โครงรวมก่อนแก้)
- **ไม่ช่วย:** ต้องการ "เนื้อโค้ด/style จริง" → อ่านไฟล์ตรงๆ (กราฟมีแต่โครงสร้าง ไม่มีตัวโค้ด)
- God nodes (powerNote): `$()`, `render()`, `changed()`, `eventCanvasPos()`, `api()`
- `api()` ใน app.js = single gateway ระหว่าง canvas กับ server
- อัปเดต graph: `/graphify --update`

> **บทเรียน:** session animation_1b3b ผมลืมว่าโปรเจกต์นั้นมี graphify เลยไม่ได้เช็ค — กฎข้างบนกันไม่ให้ลืมอีก: เข้าโปรเจกต์ที่มีกราฟ = เช็คก่อนเสมอ แล้วค่อยตัดสินใจว่า query ช่วยไหม

## 🖊️ ลายมือ → Markdown (Obsidian vault = `notes/`)
เมื่อ inbox มี marker `[ลายมือ] box "<title>" (id: <boxId>)` ให้ทำ **อัตโนมัติทุกครั้ง**:
1. `get_user_images` → อ่านรูปลายมือ ถอดเป็นข้อความ (คงภาษา/ถ้อยคำตามที่ Min เขียน)
2. หาเส้นโยง: `curl -s localhost:4321/api/state | jq` → `boxes` (id→title) + `boxLinks` (from/to) → รายชื่อกล่องเพื่อนบ้านของ boxId นี้
3. เขียนทับ `notes/<title>.md` (title ว่าง → ใช้ boxId เป็นชื่อไฟล์):
   - frontmatter: `boxId`, `updated` (ISO)
   - เนื้อหาที่ถอดจากลายมือ
   - ท้ายไฟล์ `## เชื่อมโยง` + `[[<title เพื่อนบ้าน>]]` ทุกกล่องที่โยงถึง (ให้กราฟ Obsidian ตรงกับกระดาน)
4. ตอบ Min ผ่าน `say_to_user` ว่าจดไฟล์ไหนแล้ว + สรุปสั้นๆ ที่อ่านได้
- Min เปิด `notes/` ด้วย Obsidian เอง — **ห้ามลบ/ย้ายไฟล์อื่นใน notes/** นอกจากไฟล์ของ box ที่กำลังอัปเดต

## ฟีเจอร์กล่อง (Prototype 3)
- **note** = ลายมือ + OCR/ส่งให้ Claude | **image** = แกลเลอรีรูป (กดเปิด URL) | **aibox** = พื้นที่งาน Claude | **video** = รายการคลิป กด ▶ เล่นในแอป (YouTube embed / ไฟล์โลคอลผ่าน `GET /api/media?path=`)
- Claude แนบคลิปให้ Min: `curl -X POST localhost:4321/api/videos/add -d '{"path":"<abs .mp4>","title":"..."}'` (หรือ `url` สำหรับ YouTube; ไม่ระบุ boxId = ลงกล่อง video กล่องแรก/สร้างใหม่) — **เจนวิดีโอเสร็จทุกครั้งให้แนบเข้ากระดานด้วย** และถ้าจดโน้ต MD ที่เกี่ยวข้อง ใส่ลิงก์ไฟล์คลิปในไฟล์ MD ด้วย
- โยงกล่อง: กด 🔗 บนหัว → ลาก | ลบ: × กลางเส้น
- **แชทหลาย section**: แท็บบนพาเนลซ้าย — ดับเบิลคลิกเปลี่ยนชื่อ
