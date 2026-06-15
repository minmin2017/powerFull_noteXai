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

## กฎสำคัญอื่น ๆ
- **หลัง add_topic / add_topics_bulk ทุกครั้ง ให้รัน `tidy_layout`** — auto-position ทำให้
  โหนดซ้อนกัน Min ไม่ชอบ (หรือ POST http://localhost:4321/api/layout ถ้า MCP tool ยังไม่โหลด)
- ตอบ Min เป็นภาษาไทยในพาเนลซ้ายผ่าน `say_to_user`
- เชื่อม Claude ผ่าน MCP (`.mcp.json`) ไม่ใช่ Claude API — ใช้ subscription ที่มีอยู่
