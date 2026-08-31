# Powerfull Note — project instructions

แอป mind-map โลคอล + MCP bridge ของ Min (http://localhost:4321)

## 🧹 MCP `run-filtered` — รันคำสั่งแบบกรอง progress bar ทิ้ง (ประหยัด token)

สร้างวันที่ 2026-09-01 เพราะ log ที่มี progress bar (tqdm ตอนเรนเดอร์ Manim local,
`git clone`/`pip install`/`apt-get` ตอน setup Kaggle, `gh run download`) เป็นตัวกิน
token อันดับ 1 ที่วัดได้จริงในหลาย session — MCP server อยู่ที่ `mcp-run-filtered.js`
ลงทะเบียนใน `.mcp.json` แล้ว (เครื่องมือชื่อ `run_filtered`)

**ใช้เมื่อไหร่:** แทนที่ Bash tool ปกติ ทุกครั้งที่คาดว่าคำสั่งจะมี progress bar เยอะ
(install/clone/render/download ที่ใช้เวลา) และสนใจแค่ผลสุดท้าย (สำเร็จ/error/ตัวเลข)
ไม่สนใจ % ระหว่างทาง — มันจะตัดบรรทัดที่มี `\r`/รูปแบบเปอร์เซ็นต์ซ้ำๆ ทิ้งก่อนส่งกลับมา
ให้ Claude เลย ไม่ใช่กรองทีหลังแบบ grep/tail ที่ยังต้องรับ raw output เต็มๆ ก่อน

**ยืนยันแล้วว่าทำงานจริง** (ทดสอบ 2026-09-01: กรอง progress-bar ปลอมออกได้ถูกต้อง
เหลือแค่บรรทัดผลลัพธ์จริง) — ไม่ได้แทนที่ระบบแจ้งเตือน background task ที่มีอยู่แล้ว
(อันนั้นตอบแค่ "เสร็จหรือยัง" ก็เพียงพออยู่แล้ว) ตัวนี้ช่วยเฉพาะตอนต้องอ่าน**เนื้อหา**ของ log จริงๆ

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

## 🔎 กฎการรับงานใหม่ — ค้นก่อน เทียบก่อน ห้ามตอบ "ทำไม่ได้" ลอยๆ

เมื่อ Min **ขอฟีเจอร์ / อยากสร้างอะไรบางอย่าง โดยไม่ได้บอกวิธีทำมาด้วย** ให้ทำตามลำดับนี้ทุกครั้ง:

1. **ไปค้นหาหลายวิธีมาก่อน** อย่าเพิ่งลงมือด้วยวิธีแรกที่นึกออก
2. **เทียบข้อดี–ข้อเสียของแต่ละวิธี** แล้วเสนอให้ Min เห็นภาพรวมพร้อมกัน (ตาราง/ข้อ ๆ) — เห็นหลายทางวางเรียงกันแล้วตัดสินใจง่ายกว่าเห็นทางเดียว
3. **ถ้าคิดว่า "ทำไม่ได้" ห้ามตอบทันที** → ค้นเน็ตก่อนว่ามีคนเคยทำสำเร็จไหม
4. **ถ้าค้นแล้วไม่มีใครทำ ยังห้ามยอมแพ้** → คิดต่อว่า "ถ้าเล่นตุกติก / สร้างระบบเสริมขึ้นมาคั่น จะทำได้ไหม"

**เคสตัวอย่างที่เป็นที่มาของกฎนี้ (Chrome Web Speech):** ผมเคยสรุปว่า *ใช้ไม่ได้ถ้าไม่เปิดหน้าต่าง Chrome* แล้วจบแค่นั้น
แต่ Min ดันทุรังต่อ → พอไปค้นจริงพบว่ามีคนแก้ด้วยการ **เขียน Chrome extension เสริม** ซึ่งทำงานได้โดยไม่ต้องแย่งโฟกัสหน้าจอเลย
= คำว่า "ทำไม่ได้" ของผมตอนนั้น **ผิด** เพราะยังไม่ได้ค้น ไม่ใช่เพราะมันเป็นไปไม่ได้จริง

**เพิ่มเติม — วัดจริงก่อนเชื่อ:** ถ้าข้อเสนอเป็นเรื่องความเร็ว/ประสิทธิภาพ ให้ **เบนช์มาร์กจริงบนเครื่องนี้** แล้วรายงานตัวเลข
อย่าลอกความเชื่อทั่วไปมาตอบ (เคสจริง: "ใช้ GPU เรนเดอร์เร็วกว่า" — วัดแล้ว**ช้ากว่า** ส่วนที่ GPU ช่วยจริงคือตอนบีบไฟล์
ดูสกิล `manim-teaching-video` §12–13) และถ้าผลไม่ตรงกับที่ Min คาดไว้ **ให้รายงานตามจริง** พร้อมตัวเลข ไม่ใช่ทำตามคำสั่งแบบเงียบๆ

## กฎสำคัญ
- **tidy_layout**: ระบุ `rootId` เสมอ = จัดเฉพาะกิ่งที่แก้ ไม่เขย่าทั้งกระดาน
  จัดทั้งโปรเจกต์ (ไม่ใส่ rootId) **เฉพาะตอน Min สั่งจัดทั้งกระดานเท่านั้น**
- **รีเซ็ต/restart server / รีเฟรชหน้าแอป**: **ห้ามทำเอง เว้นแต่ Min สั่งตรงๆ เท่านั้น** — มี 2 กลไกที่ทำให้หน้าแอป Min โดน `location.reload()` แบบไม่ทันตั้งตัว:
  1. แก้ `server.js` ขณะ `node --watch server.js` รันอยู่ → auto-restart process (bootId เปลี่ยน → client reload)
  2. แก้ไฟล์ใน `public/` (style.css, app.js, index.html, modules/*.js) → `fs.watch` ฝั่ง server ยิง `sendReload()` → **ทุกแท็บที่เปิดอยู่ reload ทันที** (นี่คือกลไกที่เคยตัดจังหวะ Min ตอนกำลังพูดไมค์อยู่พอดี ไม่ใช่ process restart)
  ก่อนแก้ไฟล์ที่เข้าข่ายทั้งสองแบบ ให้ **บอก Min ก่อน** ว่าจะทำให้หน้าแอป reload แล้วรอโอเค (โดยเฉพาะถ้า Min กำลังพิมพ์/พูดไมค์อยู่)
  (บทเรียน 2026-08-29: แก้ style.css ตอน Min กำลังพูดไมค์ค้างอยู่พอดี หน้าเขา reload ตัดจังหวะกลางคัน)
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
