# Powerfull Note — project instructions

แอป mind-map โลคอล + MCP bridge ของ Min (รันที่ http://localhost:4321)

## ⭐ เริ่มทุก session ให้ทำอัตโนมัติ: ฟัง inbox (event listener)
ทันทีที่เปิด Claude Code ในโฟลเดอร์นี้ ให้ **arm persistent Monitor** ที่ poll inbox เอง
โดยไม่ต้องรอให้ Min สั่ง — Min เปิดแอปมาแล้วคาดหวังว่าผมจะฟังให้เลย

ขั้นตอน:
1. เช็คว่าเซิร์ฟเวอร์รันอยู่: `curl -s -m 5 "http://localhost:4321/api/inbox?drain=true"`
   - ถ้า server down → บอก Min ให้รัน `start.cmd` ก่อน
   - ถ้ามี items ค้างอยู่ ให้ตอบกลับก่อนเริ่มฟัง
2. arm Monitor (persistent, timeout 1 ชม.) ด้วย bash loop ที่ curl `/api/inbox?drain=true`
   ทุก ~3s แล้ว print แต่ละข้อความ — shell poll ไม่กิน token, ผมตื่นเฉพาะมีข้อความจริง
3. ตอบกลับ Min ในพาเนลซ้ายผ่าน MCP `say_to_user` ว่าเริ่มฟังแล้ว

> ต้อง re-arm Monitor ใหม่ทุกครั้งที่ restart Claude Code (Monitor ไม่ persist ข้าม session)
> รายละเอียดระบบ: `docs/event-based-system.md`

## เปิดเร็ว: `claude-listen.cmd`
ดับเบิลคลิก `claude-listen.cmd` = เปิด Claude Code แบบ `--dangerously-skip-permissions`
(ไม่ต้องกดอนุญาตทุกครั้ง) + เช็ค/สตาร์ท note server ให้ + arm Monitor ฟัง inbox ทันที
- **ไม่ใส่ args = ฟังเฉพาะ "แชทหลัก" (main)** ไม่ใช่ทุกข้อความ
- ใส่ชื่อ section = ผูกตัวนั้น เช่น `claude-listen.cmd "chat2"`

**Auto-start ตอนเปิด Windows:** รัน `install-autostart.cmd` ครั้งเดียว → วาง shortcut ใน
Startup folder → ทุกครั้งที่ล็อกอิน Claude เปิดมาฟังแชทหลักเอง (ยกเลิก: `uninstall-autostart.cmd`)

## 🧵 หลาย Claude พร้อมกัน — แชทแยก section ↔ Claude คนละตัว
แต่ละ chat section (แท็บในพาเนลซ้าย) ผูกกับ Claude Code instance ได้ 1 ตัว → ทำงานขนานกันจริง

**วิธีตั้ง (สอนวิธีให้ Claude ฟังถูก chat):**
1. ในแอป สร้าง/ตั้งชื่อแท็บแชท เช่น "หลัก" กับ "งานวิจัย"
2. เปิดหน้าต่าง cmd แล้วสั่ง:
   - ตัวที่ 1:  `claude-listen.cmd "หลัก"`
   - ตัวที่ 2:  `claude-listen.cmd "งานวิจัย"`  (อีกหน้าต่าง)
3. launcher จะ `set CHAT_SECTION=<ชื่อ>` ก่อนเปิด claude → MCP server อ่าน env นี้

**กติกาที่ Claude ทุกตัวต้องทำตาม (สำคัญ):**
- ดู env `CHAT_SECTION` ของตัวเอง:
  - **ถ้ามีค่า** → arm Monitor ที่ poll *เฉพาะ section ตัวเอง*:
    `curl -s -G "http://localhost:4321/api/inbox" --data-urlencode "section=$CHAT_SECTION" --data-urlencode "drain=true"`
    และตอบด้วย `say_to_user` เท่านั้น (MCP เติม section ให้เองจาก env) — **ห้าม** drain inbox รวม,
    **ห้าม**ยุ่ง section อื่น
  - **ถ้าไม่มีค่า** → ฟังทุกข้อความตามปกติ (`/api/inbox?drain=true`) ตอบเข้า section ที่ active
- ข้อความที่ผู้ใช้พิมพ์/พูดในแท็บไหน จะถูก tag เป็น section นั้น (ตาม activeSection) →
  Claude ตัวที่ผูก section นั้นเท่านั้นที่ดึงไปได้ ไม่แย่งกัน
- โน้ต: ทุกตัวใช้ subscription เดียวกัน รันหนักพร้อมกันอาจชน rate limit; สองตัวคุยกันตรง ๆ ไม่ได้
  (ส่งต่อผ่านโน้ต/ไฟล์เอา)

## โหมด Agent (ทำงานขนานให้เร็วขึ้น)
- ถ้ามีหลายงานที่ **ไม่เกี่ยวข้องกันเลย** ให้ใช้ subagent (เครื่องมือ Agent) ทำขนานกันได้
  เพื่อให้เสร็จไวขึ้น เช่น แคปหลายเว็บ / ค้นหลายแหล่งพร้อมกัน
- แต่ถ้าแยก Agent แล้ว **ไม่ได้เร็วขึ้นจริง** (งานผูกกัน เช่นแก้ไฟล์เดียวกัน, หรือ subagent
  ต้องโหลด context ใหม่จนช้ากว่าเดิม) → **ไม่ต้องแยก** ทำเองรวดเดียว ให้ Claude ตัดสินใจเอง

## กฎสำคัญอื่น ๆ
- **หลัง add_topic / add_topics_bulk ทุกครั้ง ให้รัน `tidy_layout`** — auto-position ทำให้
  โหนดซ้อนกัน Min ไม่ชอบ (หรือ POST http://localhost:4321/api/layout ถ้า MCP tool ยังไม่โหลด)
- **รีเซ็ต Server เฉพาะหลังงานทุกขั้นเสร็จสมบูรณ์แล้วเท่านั้น** — ห้ามรีเซ็ตระหว่างทำงาน
  เพื่อลดการรบกวน ถ้าจำเป็นต้องรีเซ็ตให้รอจนขั้นสุดท้ายก่อน แล้วรีเซ็ตครั้งเดียว
- ตอบ Min เป็นภาษาไทยในพาเนลซ้ายผ่าน `say_to_user`
- เชื่อม Claude ผ่าน MCP (`.mcp.json`) ไม่ใช่ Claude API — ใช้ subscription ที่มีอยู่

## ฟีเจอร์กล่อง (boxes) — Prototype 3
- **กล่องลายมือ** (kind:"note") เขียนด้วยปากกา + OCR/ส่งให้ Claude ดู
- **กล่องรูปภาพ** (kind:"image") เก็บรูปเป็นแกลเลอรี แต่ละรูปกดเปิดลิงก์เว็บได้ (item.url)
- **โยงกล่อง**: กดปุ่ม 🔗 บนหัวกล่องแล้วลากไปอีกกล่อง = เส้นเชื่อม (ลบที่ปุ่ม × กลางเส้น)
- **แชทหลาย section**: แท็บด้านบนพาเนลซ้าย สลับ/เพิ่ม/เปลี่ยนชื่อ(ดับเบิลคลิก)/ลบได้
  ข้อความใหม่จาก say_to_user จะลงแท็บที่ active อยู่
