# ใบสั่งงาน — แอปติววิดิโอแยกต่างหาก (Video Study App)

> **สถานะ:** Min อนุมัติดีไซน์แล้ว (2026-08-28, ผ่านแชทแอป powernote — MCP bridge ล่มระหว่างคุย เลยสรุปฝั่ง terminal แทน)
> **ผู้เขียน:** Claude (brainstorming session 2026-08-28)
> **ขอบเขต:** แอปใหม่แยกพอร์ต สำหรับดูวิดิโอสอนพร้อมข้อความอธิบายที่แก้ไขได้ + สั่งสร้างวิดิโอใหม่ผ่านแชท
> **ไม่อยู่ในขอบเขต:** การนำเข้าวิดิโอจากภายนอก (YouTube ที่ไม่ได้ generate เอง), มือถือ PowerNote แบบ chat-only, บั๊กปุ่มพูดมือถือ, บั๊ก popup toast — ทั้งหมดนี้เป็นงานแยกที่คุยไว้ระหว่าง session เดียวกันแต่ยังไม่ผ่านกระบวนการ brainstorming เป็นของตัวเอง

---

## 1. ที่มา — สิ่งที่ Min ต้องการ

Min อยากได้แอปสำหรับ "ติว" (เรียนรู้ผ่านวิดิโอ) ที่:
- ปุ่มใน PowerNote กดแล้ว **เปิดโปรแกรมแยกต่างหากจริงๆ** ไม่เกี่ยวกับบอร์ด mind-map
- ในแอปนั้นมีแชทคุยกับ Claude โดยตรง สั่งให้สร้างวิดิโอสอนเรื่องใหม่ได้
- วิดิโอเล่นฝั่งซ้าย ข้อความอธิบายฝั่งขวาผูกกับเวลาในวิดิโอ กด "warp" แล้ววิดิโอกระโดดไปวินาทีนั้น
- ข้อความฝั่งขวา **แก้ไขได้เอง** และ **แก้ผ่านแชทได้ด้วย** (ถาม Claude เพิ่ม → Claude อัปเดตข้อความให้)
- แต่ละข้อความมีปุ่มอ่านออกเสียงภาษาไทยที่ฟังเป็นธรรมชาติ (ฟรี)
- **เป้าหมายทางธุรกิจ:** Min ตั้งใจให้แอปนี้ดูมืออาชีพ เพราะอยากเอาไปเสนอขาย/ให้คนอื่นใช้ด้วย ไม่ใช่แค่เครื่องมือส่วนตัว

**หมายเหตุความซื่อสัตย์เรื่อง scope:** สเปกนี้ยังเป็น single-user local app (รันบนเครื่อง Min เอง ไม่มี auth/multi-tenant) — ถ้าจะขายจริงต้องมีงานเพิ่มเติมเรื่อง packaging/auth/hosting ซึ่ง**ไม่อยู่ในสเปกนี้** แค่บันทึกไว้เป็นเป้าหมายระยะยาวที่ต้องคำนึงตอนออกแบบ UI ให้ดูเป็นมืออาชีพไว้ก่อน

## 2. สิ่งที่มีอยู่แล้วในโปรเจกต์ (นำมาใช้ซ้ำ ไม่สร้างใหม่)

ตรวจโค้ดจริงก่อนออกแบบ พบว่ามีโครงสร้างพร้อมใช้เกินคาด:

| มีอยู่แล้ว | ไฟล์ | ใช้ทำอะไรในสเปกนี้ |
|---|---|---|
| TTS ไทยธรรมชาติ ฟรี ไม่จำกัดโควตา (`edge-tts`, เสียง `th-TH-PremwadeeNeural`/`NiwatNeural`) | `server.js:1030-1096` (`/api/tts`) | ปุ่ม 🔊 อ่านออกเสียงต่อ segment — **ใช้ endpoint เดิมตรงๆ ไม่ต้องผูก Google Cloud/Azure เพิ่ม** |
| ระบบห้องแชท (chat-sections) + inbox ที่ Claude Code หลายหน้าต่างฟังพร้อมกันได้ | `server.js` (`/api/chat`, `/api/chat-sections`, `/api/inbox`) + `claude-listen.cmd` | กล่องแชทในแอปใหม่ — เปิดห้องใหม่ชื่อ `study`, ใช้แพทเทิร์นเดียวกับที่ Min เปิดหลาย Claude ขนานกันอยู่แล้วทุกวันนี้ |
| MCP bridge (`mcp-server.js`, `server.registerTool(...)` แพทเทิร์นเดิม) | `mcp-server.js` | เพิ่ม tool ใหม่ 3 ตัว (ดูข้อ 5) |
| Pipeline สร้างวิดิโอสอนเต็มรูปแบบ (manim-teaching-video skill, GitHub Actions cloud render) | ใช้แล้วในคลิป Agile Robot วันนี้ | Claude ใช้ pipeline เดิมทุกอย่างตอนสร้างวิดิโอใหม่ผ่านแชทของแอปนี้ |
| `video-digest/video_digest.py` (whisper transcript + scene-detect ท้องถิ่น, ฟรี) | root โปรเจกต์ | **ไม่ใช้ในสเปกนี้** (ดูข้อ 3 เหตุผล) — เก็บไว้เผื่อสเปกอนาคตเรื่องนำเข้าวิดิโอนอก |

## 3. การตัดสินใจสำคัญที่เปลี่ยนระหว่างคุย (และเหตุผล)

1. **ไม่มี transcription pipeline (ตัดออกจากดีไซน์แรกที่เสนอ)** — Min ทักถูก: วิดิโอที่ generate ผ่านแชทของแอปนี้ Claude เป็นคนเขียน scene เอง รู้ script/เวลาแต่ละช่วงอยู่แล้วตอน render จึงเขียน `explain.json` คู่กับวิดิโอได้ทันที ไม่ต้องถอดเสียงย้อนกลับด้วย whisper/cloud STT ใดๆ ทั้งสิ้น — ตัดทั้งแผน GitHub Actions transcribe workflow และแผนสำรอง Kaggle ออกจากสเปกนี้ทั้งหมด
2. **แอปแยกพอร์ตจริง ไม่ใช่ overlay ในบอร์ด PowerNote** — ดีไซน์แรกเสนอ overlay เต็มจอทับ canvas แต่ Min เปลี่ยนใจกลางคันขอเป็นโปรแกรม/เซิร์ฟเวอร์แยกกันจริง (คนละพอร์ต) เพราะอยากให้เป็นแอปอิสระที่เอาไปโชว์/ขายแยกได้
3. **ข้อความฝั่งขวาต้องแก้ไขได้ทั้งจาก Min เองและจาก Claude ผ่านแชท** — ไม่ใช่แค่ AI generate แล้วอ่านอย่างเดียว

## 4. สถาปัตยกรรม

```
PowerNote (port 4321)
  └─ ปุ่ม "🎓 เริ่มติววิดิโอ" → window.open("http://127.0.0.1:<STUDY_PORT>")

server.js สปอว์น Study App server เป็น child process ตอน start
  (แพทเทิร์นเดียวกับ tts_worker.py ที่มีอยู่แล้ว — ผู้ใช้ไม่ต้องเปิดเอง)

Study App server (port ใหม่ เช่น 4322)
  ├─ serve frontend คนละหน้าจาก PowerNote (public ของตัวเอง)
  ├─ เก็บข้อมูลแยกขาด: study-app/data/<videoId>/{video.mp4, explain.json}
  ├─ proxy เรียก /api/chat, /api/chat-sections ของ server.js (localhost:4321)
  │    เพื่อส่งข้อความเข้าห้องแชทชื่อ "study"
  └─ endpoint แก้ segment ข้อความ (สำหรับปุ่มแก้ไขในแอป + MCP tool)

Claude Code เพิ่มอีก 1 หน้าต่าง (Min เปิดเองด้วย claude-listen.cmd study
  — แพทเทิร์นเดียวกับที่มีอยู่แล้วสำหรับหลาย section ขนานกัน)
  ฟังห้อง "study" → รับคำสั่งสร้างวิดิโอ → รัน manim-teaching-video pipeline
  → เขียน explain.json คู่กับวิดิโอ → POST เข้า Study App server
```

**ทำไมต้องมีหน้าต่าง Claude เพิ่ม:** การสร้างวิดิโอจริงต้องเขียนโค้ด manim, สั่ง render (local/cloud), ตรวจเฟรม ฯลฯ — งานที่ต้องใช้เครื่องมือจริง (Bash, Edit, GitHub Actions) ไม่ใช่แค่คำตอบข้อความจาก API เดียว จึงต้องเป็น Claude Code session จริงเหมือนที่ใช้ทำคลิป Agile Robot วันนี้ ไม่ใช่แชทบอทเบาๆ

## 5. ส่วนประกอบที่ต้องสร้างใหม่

### 5.1 Study App server (`study-app/server.js`)
- Express เบาๆ, พอร์ตแยก (กำหนดใน `.env`, ค่าเริ่มต้นแนะนำ 4322)
- `GET /` → หน้า UI หลัก
- `POST /videos` → รับวิดิโอ + `explain.json` จาก Claude (หลัง generate เสร็จ)
- `GET /videos` → รายชื่อวิดิโอที่มีในแอป (สำหรับหน้าเลือกวิดิโอ)
- `GET /videos/:id` → รายละเอียด + segments
- `PATCH /videos/:id/segments/:i` → แก้ข้อความ segment เดียว (ใช้ทั้งจากปุ่มแก้ไขในแอป และจาก MCP tool `edit_video_explanation`)
- `POST /chat` → proxy ไป `server.js:4321/api/chat` พร้อม `section: "study"`

### 5.2 Frontend ใหม่ (`study-app/public/`)
- ซ้าย: `<video>` player ปกติ
- ขวา: การ์ดต่อ segment — เวลา, ข้อความ (contenteditable), ปุ่ม 🔊 (เรียก `server.js:4321/api/tts?text=...`), ปุ่ม ⤴ warp (`video.currentTime = t`)
- Highlight การ์ดที่ตรงกับเวลาปัจจุบันของวิดิโอ (`timeupdate` event)
- ล่าง: กล่องแชทเล็กๆ ส่งข้อความไป `POST /chat`
- **ดีไซน์ภาพ:** ต้องดูโมเดิร์น/มืออาชีพ (เป้าหมายคือ Min อยากเอาไปโชว์คนอื่น) — ขั้นตอน implementation ควรเรียกสกิลออกแบบ UI/UX ตอนลงมือทำหน้าตาจริง (ไม่ใช่ตอน brainstorm นี้)

### 5.3 MCP tools ใหม่ (เพิ่มใน `mcp-server.js` เดิม ด้วยแพทเทิร์น `server.registerTool` ที่มีอยู่แล้ว)

| tool | ทำอะไร |
|---|---|
| `start_video_study(topic)` | เริ่มกระบวนการสร้างวิดิโอใหม่ (Claude เรียกเองตอนรับคำสั่งในห้อง "study" หรือ Min สั่งจาก session อื่นก็ได้) |
| `get_video_study_status(videoId)` | เช็คสถานะการสร้าง/render วิดิโอ |
| `edit_video_explanation(videoId, segmentIndex, newText)` | แก้/ขยายข้อความ segment จากในแชท — เรียก `PATCH /videos/:id/segments/:i` ของ Study App server |

### 5.4 Data model — `explain.json` ต่อวิดิโอ
```json
{
  "id": "study_xxxxx",
  "title": "ชื่อวิดิโอ",
  "videoFile": "video.mp4",
  "durationS": 213.6,
  "segments": [
    { "start": 0, "end": 12.3, "text": "ข้อความอธิบายที่ Claude เขียน/แก้แล้ว" }
  ]
}
```

## 6. Error handling
- Study App server หาไม่เจอ (ยังไม่ spawn/crash) → ปุ่มใน PowerNote เช็คก่อนเปิด ถ้าต่อไม่ติดขึ้นข้อความบอก Min แทนเปิดหน้าเปล่า
- แชทส่งไปห้อง "study" แต่ไม่มี Claude Code หน้าต่างไหนฟังอยู่ → ข้อความค้างใน inbox เหมือนกรณีอื่นที่มีอยู่แล้วในระบบ (ไม่ error แค่ยังไม่มีคนตอบ) — UI ควรบอก Min ว่า "ยังไม่มี Claude ฟังห้องนี้ เปิด claude-listen.cmd study ก่อน"
- `PATCH` segment ที่ index ไม่มีจริง → 404 ชัดเจน

## 7. Testing
- สร้างวิดิโอทดสอบ 1 เรื่องผ่านแชทในแอปจริง (topic ง่ายๆ) → ตรวจว่า `explain.json` มาพร้อมวิดิโอ, warp กระโดดตรงวินาที, 🔊 อ่านออกเสียงได้จริง, แก้ข้อความในแอปแล้ว persist ทับไฟล์ถูกต้อง
- ทดสอบ `edit_video_explanation` โดยพิมพ์คำถามต่อในห้องแชท "study" แล้วดูว่าข้อความฝั่งขวาอัปเดตจริง

## 8. เรื่องที่ตั้งใจไม่ทำในสเปกนี้ (YAGNI)
- นำเข้าวิดิโอจากภายนอก (ต้องใช้ `video_digest.py` + whisper) — เก็บไว้เป็นสเปกแยกถ้าต้องการภายหลัง
- ระบบ multi-user/auth สำหรับขายจริง — ต้องมีสเปกแยกเมื่อถึงเวลา
- แผนสำรอง cloud transcription (Kaggle ฯลฯ) — ไม่จำเป็นแล้วหลังตัดสินใจข้อ 3.1
