# Powerfull Note 🧠✏️

> **สำหรับ AI/agent ที่มาอ่านไฟล์นี้เป็นครั้งแรก:** Powerfull Note คือแอป **mind-map แบบโลคอล** (Node + Express + vanilla JS, ไม่มี framework, ไม่มี build step) ที่ทำหน้าที่เป็น **"ตัวกลาง (bridge) ระหว่างมนุษย์กับ AI agent"** — ผู้ใช้เขียน/พูด/วาดลงกระดาน แล้ว Claude Code (หรือ Gemini) เข้ามาอ่าน แก้ไข และตอบกลับผ่าน **MCP server ในตัว** ทุกอย่างรันบนเครื่อง ไม่มี cloud backend
>
> เข้าใจโปรเจกต์เร็วสุด: อ่านหัวข้อ [สถาปัตยกรรม](#สถาปัตยกรรม) → [ฟีเจอร์ทั้งหมด](#ฟีเจอร์ทั้งหมด) → [MCP](#mcp--เชื่อม-claude-code-เข้ากับแอป)
> ถ้าต้องการ "ใครเรียกใคร" ในโค้ด → query `graphify-out/graph.json` แทนการไล่อ่านไฟล์ (ดู [Graphify](#graphify--knowledge-graph-ของโค้ด))

---

## สารบัญ

- [ภาพรวม 30 วินาที](#ภาพรวม-30-วินาที)
- [เริ่มใช้งาน](#เริ่มใช้งาน)
- [สถาปัตยกรรม](#สถาปัตยกรรม)
- [ฟีเจอร์ทั้งหมด](#ฟีเจอร์ทั้งหมด)
  - [1. กระดาน mind-map](#1-กระดาน-mind-map)
  - [2. กล่อง 4 ชนิด](#2-กล่อง-4-ชนิด-box)
  - [3. พาเนลแชท AI + หลาย section](#3-พาเนลแชท-ai--หลาย-section)
  - [4. ระบบเสียง — พูดคุยกับ AI](#4-ระบบเสียง--พูดคุยกับ-ai-ด้วยเสียง)
  - [5. Desktop Notification + สูตรคณิตศาสตร์](#5-desktop-notification--เรนเดอร์สูตรคณิตศาสตร์-ใช้ติวได้)
  - [6. ย่อยวิดีโอด้วย AI](#6-ย่อยวิดีโอด้วย-ai-video-comprehension)
  - [7. Export / GitHub / Obsidian](#7-export--github--obsidian)
  - [8. อื่นๆ](#8-อื่นๆ)
- [MCP — เชื่อม Claude Code เข้ากับแอป](#mcp--เชื่อม-claude-code-เข้ากับแอป)
- [MCP server ตัวอื่นบนเครื่องนี้](#mcp-server-ตัวอื่นบนเครื่องนี้)
- [HTTP API](#http-api)
- [Environment variables](#environment-variables)
- [Graphify](#graphify--knowledge-graph-ของโค้ด)
- [โครงสร้างไฟล์](#โครงสร้างไฟล์)

---

## ภาพรวม 30 วินาที

| ด้าน | รายละเอียด |
|---|---|
| **คืออะไร** | แอป mind-map โลคอล + สะพานเชื่อม AI agent |
| **รันที่** | `http://localhost:4321` (Chrome/Edge — จำเป็นสำหรับ Web Speech API) |
| **Stack** | Node.js + Express + `ws` (WebSocket) + vanilla JS/Canvas — **ไม่มี build step** |
| **AI เชื่อมยังไง** | MCP server (`mcp-server.js`) — Claude Code เรียก tool ได้ 25 ตัว |
| **ข้อมูลเก็บที่** | `data/` (JSON, git-ignored) |
| **จุดขาย** | **พูดไทย → AI ตอบ → อ่านออกเสียงกลับเป็นภาษาไทย** → เห็นผลบนกระดานสด ๆ + แจ้งเตือนเด้งนอกเบราว์เซอร์พร้อมสูตรคณิตศาสตร์ |
| **ภาษาไทยเต็มระบบ** | ฟังไทย (Web Speech `th-TH` / Whisper) · **พูดไทยกลับด้วยเสียงธรรมชาติ** (edge-tts `th-TH-PremwadeeNeural`) · OCR ลายมือไทย · UI ไทย |

---

## เริ่มใช้งานใน 1 นาที (สำหรับคนที่เพิ่งได้ไฟล์มา)

1. ดับเบิลคลิก **`setup.cmd`** — ลงของให้อัตโนมัติ ขาดอะไรมันจะบอก
2. ดับเบิลคลิก **`start-lite.cmd`** — เปิดแอป
3. เบราว์เซอร์จะเปิด http://127.0.0.1:4321 ให้เอง

เท่านี้ใช้ได้เลย — เขียน วาด อัดเสียง ทำ mind-map ได้ครบ

> อยากได้ AI ตอบในแอปด้วย (Claude Code / Gemini) ต้องตั้งเพิ่ม — ดู [เริ่มใช้งาน](#เริ่มใช้งาน) ข้างล่าง

---

## เริ่มใช้งาน

### 1) ติดตั้ง

```powershell
cd path\to\powerfull_note
npm install
pip install -r requirements.txt   # สำหรับเสียง + notification
```

### 2) เปิดแอป

ดับเบิลคลิก **`start.cmd`** — คลิกเดียวได้ครบทั้งระบบ (รวมติดตั้ง `npm install` / `pip install -r requirements.txt` ให้อัตโนมัติถ้ายังไม่ได้ติดตั้ง):

1. `node --watch server.js` (auto-restart เมื่อแก้โค้ด)
2. `ptt-listen.cmd` → `global_ptt.py` — global push-to-talk (Alt+P / Alt+O)
3. `notify-listen.cmd` → `notify_daemon.py` — desktop notification มุมขวาบน
4. **`claude-listen.cmd main` — เปิด Claude Code ผูกกับ section `main` และ arm listener ให้เองอัตโนมัติ** → พูดใส่ไมค์ได้ทันทีโดยไม่ต้องเปิดเทอร์มินัลเอง
5. เปิดเบราว์เซอร์ที่ `http://localhost:4321` (ครั้งแรกกดอนุญาตไมโครโฟน)

> ไม่อยากให้เปิด Claude อัตโนมัติ: `start.cmd --no-claude`
> (`claude-listen.cmd` จะรอ server ของหน้าต่างนี้ bind ให้เสร็จก่อนสูงสุด 15 วิ ไม่แย่งกันสตาร์ท server ซ้ำ)

> **เปิดอัตโนมัติตอนบูต Windows:** รัน `install-autostart.cmd` ครั้งเดียว (ยกเลิก: `uninstall-autostart.cmd`)

### 3) ต่อ Claude Code (ถ้าไม่ได้ใช้ auto-launch จากข้อ 2)

```powershell
cd path\to\powerfull_note
claude
```

`.mcp.json` ในโฟลเดอร์จะถูกโหลดอัตโนมัติ — Claude Code จะขออนุญาตเปิด MCP server ชื่อ `powerfull-note` (ตรวจด้วย `/mcp`)

**ทางลัด:** `claude-listen.cmd [ชื่อ section]` = เช็ค/สตาร์ท server + เปิด Claude แบบ skip-permissions + arm listener ให้เสร็จในคลิกเดียว

---

## สถาปัตยกรรม

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser (Chrome/Edge)  ·  public/                              │
│  ┌───────────────┐  ┌──────────────────────────────────────┐    │
│  │ พาเนลแชทซ้าย │  │ Canvas mind-map (app.js 3,300 บรรทัด) │    │
│  │  chat.js      │  │  โหนด · เส้นวาด · กล่อง · เส้นโยง    │    │
│  │  voice.js     │  │                                      │    │
│  │  calendar.js  │  │  api() = ประตูเดียวที่คุยกับ server  │    │
│  └───────────────┘  └──────────────────────────────────────┘    │
└────────────┬──────────────────────────────────▲─────────────────┘
             │ HTTP (REST)                      │ WebSocket (push สด)
┌────────────▼──────────────────────────────────┴─────────────────┐
│  server.js  ·  Express :4321  ·  แหล่งความจริงเดียว (state)      │
│   • REST ~70 endpoints   • WS broadcast ทุกครั้งที่ state เปลี่ยน │
│   • เก็บลง data/*.json   • undo/redo history                     │
│   • spawn worker: tts_worker.py (edge-tts), faster-whisper       │
└──────▲───────────────────────▲──────────────────────▲───────────┘
       │ HTTP                  │ HTTP poll            │ HTTP poll
┌──────┴────────┐   ┌──────────┴──────────┐  ┌────────┴──────────┐
│ mcp-server.js │   │   global_ptt.py     │  │  notify_daemon.py │
│  (stdio MCP)  │   │  Alt+P / Alt+O      │  │  tkinter toast    │
│      ▲        │   │  global hotkey      │  │  + LaTeX renderer │
│      │ stdio  │   └─────────────────────┘  └───────────────────┘
│ ┌────┴─────┐                                                     
│ │  Claude  │  ← อ่าน/เขียนกระดานผ่าน tool 25 ตัว                 
│ │   Code   │  ← ตอบผู้ใช้ผ่าน say_to_user                        
│ └──────────┘                                                     
└───────────────┘
```

**หลักการสำคัญ:**
- `server.js` เป็น **single source of truth** — ทุกการเปลี่ยนแปลง (จาก UI หรือจาก AI) ผ่านที่นี่ แล้ว broadcast ผ่าน WebSocket → ทุกแท็บ/ทุก agent เห็นตรงกันทันที
- `api()` ใน `public/app.js` คือ **gateway เดียว** ระหว่าง canvas กับ server (god node ในกราฟ)
- `mcp-server.js` **ไม่มี state ของตัวเอง** — เป็นแค่ HTTP client บาง ๆ ที่แปลง MCP tool call → REST call

---

## ฟีเจอร์ทั้งหมด

### 1. กระดาน mind-map

| ทำอะไร | วิธีใช้ |
|---|---|
| เพิ่มหัวข้อ | ปุ่ม `+ หัวข้อ` หรือ **ดับเบิลคลิกที่ว่าง** |
| เพิ่มหัวข้อย่อย | ชี้ที่โหนด → กด `+` ทางขวา |
| แก้ข้อความ | ดับเบิลคลิกที่โหนด |
| ย้าย / ลบ | ลากโหนด · คลิกแล้วกด `Delete` |
| ยุบ/ขยายกิ่ง | ปุ่ม `−/+` ทางซ้ายโหนด |
| เลื่อนกระดาน | ลากที่ว่าง / Space+ลาก / คลิกขวาลาก |
| ซูม | สกรอลล์เมาส์ · `➕/➖` · `🔭 ภาพรวม` = fit ทั้งกระดาน |
| **วาดอิสระ** | `✏️ วาด` — รองรับ **แรงกดปากกา (pressure)**, เลือกสี/ขนาด, `🧽` ยางลบ, `↶` ย้อน |
| เลือกหลายชิ้น | ลากกรอบ — `🎯` สลับเป้าหมายระหว่าง *หัวข้อ* ↔ *เส้นที่วาด* |
| Undo / Redo | `Ctrl+Z` / `Ctrl+Shift+Z` (เก็บ history ฝั่ง server) |
| **หลายโปรเจกต์** | `＋ โปรเจกต์` — แต่ละโปรเจกต์มีกระดาน/แชทของตัวเอง สลับได้ทันที |
| จัดระเบียบอัตโนมัติ | MCP tool `tidy_layout` — **ระบุ `rootId` เสมอ** เพื่อจัดเฉพาะกิ่งนั้น ไม่เขย่าทั้งกระดาน |
| พาเนล Object | `📋` — รายการทุกอย่างในโปรเจกต์แบบ list |

### 2. กล่อง 4 ชนิด (box)

กล่องคือพื้นที่สี่เหลี่ยมบนกระดานที่ทำงานเฉพาะทาง — **โยงหากันได้** (กด 🔗 บนหัวกล่อง แล้วลากไปอีกกล่อง · ลบเส้นด้วย × กลางเส้น)

| ชนิด | ปุ่มสร้าง | ทำอะไรได้ |
|---|---|---|
| **📦 note (ลายมือ)** | `📦 กล่อง` | เขียนลายมือด้วยปากกา/นิ้ว → `👁 ส่งให้ Claude` ให้ AI อ่านภาพจริง หรือ `🔤 OCR` ถอดด้วย Tesseract (ไทย+อังกฤษ) |
| **🖼️ image (แกลเลอรี)** | `🖼️ กล่องรูป` | เก็บรูปหลายใบ กดเปิด URL เต็ม · AI เพิ่มรูปได้ผ่าน `add_image` |
| **🤖 aibox** | (AI สร้างเอง) | พื้นที่ทำงานของ Claude — เขียนผลลัพธ์/สรุปลงกระดานโดยตรง |
| **🎞 video** | `🎞 วิดีโอ` | รายการคลิป กด ▶ เล่นในแอป (YouTube embed หรือไฟล์โลคอลผ่าน `GET /api/media?path=`) |

**ลายมือ → Markdown อัตโนมัติ:** เมื่อกด `👁 ส่งให้ Claude` บนกล่องลายมือ Claude จะถอดข้อความ → หาเส้นโยงของกล่องนั้น → เขียนไฟล์ `notes/<title>.md` พร้อม frontmatter และ `[[wikilink]]` ไปยังกล่องเพื่อนบ้าน → **กราฟใน Obsidian ตรงกับกระดานอัตโนมัติ**

### 3. พาเนลแชท AI + หลาย section

- พาเนลซ้ายคือ **ช่องคุยกับ AI** — พิมพ์หรือพูดเข้าไป Claude Code อ่านผ่าน MCP แล้วตอบกลับผ่าน `say_to_user`
- **แท็บหลาย section** (`＋` ด้านบนพาเนล) — ดับเบิลคลิกเปลี่ยนชื่อได้
  → **รัน Claude หลายตัวขนานกัน** ตัวละ section: `claude-listen.cmd "หลัก"` + `claude-listen.cmd "งานวิจัย"`
  แต่ละ instance ผูกกับ `CHAT_SECTION` ของตัวเอง **ห้ามยุ่ง section อื่น**
- **สลับ agent ต่อ section** — ปุ่ม Gemini เปลี่ยน `agentListener` ของ section เป็น `"gemini"`
  server มี filter ในตัว: ส่ง `?agent=claude` ใน poll URL แล้ว server จะคืน `items:[]` เอง เมื่อ section อยู่โหมด Gemini → ไม่ตีกัน
- `🗑` ล้างแชท section นี้ (ประหยัด token) · `🔊` เปิด/ปิดให้อ่านออกเสียงคำตอบ Claude
- **In-app banner** — popup แบบ Messenger เด้งในหน้าเว็บเมื่อแท็บนี้ถูกโฟกัสอยู่ (⚙️ ตั้งค่า → "แจ้งเตือนข้อความ")
- **มอบงานให้ Gemini** — MCP tool `delegate_to_gemini` ส่งงานหนัก/งานยาวไปให้ Gemini ทำแล้วรอผลกลับ

### 4. ระบบเสียง — พูดคุยกับ AI ด้วยเสียง

หัวใจของโปรเจกต์: **กดปุ่มเดียวแล้วพูดไทยได้เลย** ไม่ต้องพิมพ์ (เกิดเพราะ `/voice` ของ Claude Code ไม่รองรับภาษาไทย)

#### 🎤 Speech-to-Text — 3 ทางเลือก

| วิธี | เรียกยังไง | จุดเด่น |
|---|---|---|
| **Web Speech API** | ปุ่มไมค์ / กด `P` | เร็วที่สุด (ในเบราว์เซอร์ล้วน) รองรับ `th-TH` เต็ม |
| **Groq Whisper** (`whisper-large-v3`) | `POST /api/transcribe` | แม่นสุด ต้องมี `GROQ_API_KEY` |
| **faster-whisper โลคอล** | `POST /api/transcribe-local` | ออฟไลน์ 100% · worker โหลดโมเดลค้างไว้ (default `large-v3-turbo`) เลือกโมเดลได้ผ่าน `/api/whisper-model` |

#### ⌨️ Push-to-Talk — 3 แบบ

| ปุ่ม | ขอบเขต | พฤติกรรม |
|---|---|---|
| **กด `P` ค้าง** | เมื่อแท็บแอปโฟกัสอยู่ | ยิงตรงจาก keydown ของเบราว์เซอร์ — **ทันที ไม่มี round-trip** ปล่อย = ส่งเข้า AI เลย (ไม่ทำงานถ้ากำลังพิมพ์ในช่อง input) |
| **`Alt+P`** (global) | **ทั้งระบบ Windows** อยู่โปรแกรมไหนก็ได้ | `global_ptt.py` เด้งโฟกัสไปหน้าต่าง Chrome ของแอป → สลับ `agentListener` เป็น `claude` → ให้หน้าเว็บฟังเสียงเอง → **ปล่อยปุ่มแล้วคืนโฟกัสให้โปรแกรมเดิม + ย่อ Chrome กลับอัตโนมัติ** |
| **`Alt+O`** (global) | ทั้งระบบ | เหมือน Alt+P แต่สลับเป็น **Gemini** — สั่งงาน agent คนละตัวด้วยปุ่มเดียว ไม่ต้องสลับแท็บ |

> **หมายเหตุประสิทธิภาพ:** `/api/ptt` (สั่งให้ขอบจอเรืองแสง) ถูกยิงใน background thread **ก่อน** การแย่งโฟกัส และยิง **ก่อน** `/api/agent-listener` เสมอ — เพราะตัวหลัง trigger full-board broadcast ที่หนักกว่ามาก ถ้าสลับลำดับจะรู้สึกว่าไมค์ "ตื่นช้า"
>
> ⚠️ ต้องมี `global_ptt.py` **ตัวเดียว** เท่านั้น — ถ้ามีตัวค้างจาก session เก่า ทุกครั้งที่กดจะยิง request ซ้ำสองรอบ ตรวจด้วย:
> ```powershell
> Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*global_ptt*' }
> ```

#### 🔊 Text-to-Speech ภาษาไทย

- `GET /api/tts?text=...&voice=female|male` — **สตรีม MP3 ทีละ chunk** ตั้งแต่ยังสังเคราะห์ไม่เสร็จ
- ใช้ `tts_worker.py` = persistent worker ครอบ **edge-tts** (`th-TH-PremwadeeNeural`) — worker ค้างไว้ตัวเดียว ไม่ spawn process ใหม่ทุกครั้ง (นี่คือสาเหตุที่ TTS เวอร์ชันเก่ากระตุก) + auto-restart ถ้า worker ตาย
- ปุ่ม `🔊` บนพาเนลแชท = ให้อ่านคำตอบ Claude ออกเสียงอัตโนมัติ

### 5. Desktop Notification + เรนเดอร์สูตรคณิตศาสตร์ (ใช้ติวได้)

`notify_daemon.py` — **การ์ดแจ้งเตือนมุมขวาบนของจอ Windows** สร้างด้วย **tkinter** ไม่ใช่ Notification API ของเบราว์เซอร์

**ทำไมถึงสำคัญ:** ทำให้อ่าน **คำตอบเต็ม ๆ ของ AI ได้โดยไม่ต้องสลับกลับไปที่แท็บ Chrome เลย** — เหมาะกับตอนติวหนังสือ/ทำงานในโปรแกรมอื่นแล้วยิงคำถามใส่ AI ไปเรื่อย ๆ

| ความสามารถ | รายละเอียด |
|---|---|
| **เรนเดอร์สูตรคณิตศาสตร์** ⭐ | ข้อความส่วนที่เป็น `$...$` / `$$...$$` ถูกแปลงเป็น **ภาพสมการจริง** ด้วย matplotlib `Figure` + `savefig(transparent=True)` → เห็นสมการสวย ๆ บนการ์ดแจ้งเตือนได้เลย **ใช้ติวเลข/ฟิสิกส์ได้จริง** |
| ข้อความเต็ม ไม่ตัด | ยาวเกิน `MAX_BODY_LINES` แล้วสกรอลล์ในตัวการ์ดเอง |
| กว้างอัตโนมัติ | การ์ดขยายตามความกว้างของภาพสมการที่กว้างที่สุด (จำกัด 85% ของจอ) |
| ปรับขนาดเองได้ | ลากที่จับ **"◢"** มุมซ้ายล่าง — ลากแนวนอน = เปลี่ยนความกว้าง, ลากแนวตั้ง = เพิ่มจำนวนบรรทัดที่เห็น |
| หยุดนับถอยหลังตอนอ่าน | ปิดเองใน 6 วิ แต่ **เอาเมาส์ไปวางแล้วหยุดนับ** เริ่มนับใหม่เมื่อเมาส์ออก → ไม่หายกลางคัน |
| กดแล้วไปต่อ | คลิกหัวการ์ด = กระโดดไปหน้าต่าง Chrome · กด ✕ = ปิด |

รันเดี่ยว: `python notify_daemon.py` (หรือ `notify-listen.cmd`) · poll `/api/state` ทุก ~1.5 วิ หาข้อความใหม่จาก `role:"claude"` / `role:"gemini"`
รายละเอียดเชิงลึก: [`docs/voice-ptt-and-notifications.md`](docs/voice-ptt-and-notifications.md)

### 6. ย่อยวิดีโอด้วย AI (video comprehension)

- ปุ่ม `🎬` ในพาเนลแชท — ใส่ลิงก์ YouTube/URL หรืออัปโหลดไฟล์วิดีโอ
- `video-comprehension.js` แตกเฟรม + ถอดเสียง → สร้าง **digest** ให้ AI อ่านแทนการดูคลิปทั้งเรื่อง
- MCP tools: `comprehend_video` (สั่งย่อย) · `get_video_digest` (อ่านสรุป) · `get_video_frame` (ดึงเฟรมเจาะจง)
- **แนบคลิปกลับเข้ากระดาน:**
  ```bash
  curl -X POST localhost:4321/api/videos/add -d '{"path":"<abs .mp4>","title":"..."}'
  # หรือใช้ "url" สำหรับ YouTube · ไม่ระบุ boxId = ลงกล่อง video กล่องแรก
  ```

### 7. Export / GitHub / Obsidian

| ปุ่ม | ผลลัพธ์ |
|---|---|
| `⬇ MD` | ส่งออกโครงหัวข้อเป็น Markdown แบบ nested |
| `⬇ PNG` | ภาพทั้งกระดาน |
| `⬇ PDF` | PDF ความละเอียดสูง **รวมลายมือทั้งหมด** |
| `🐙 GitHub` | push กระดานปัจจุบันขึ้น repo (`POST /api/github/push`, ใช้ `GITHUB_TOKEN` / `GITHUB_REPO`) |
| `notes/` | โฟลเดอร์ Obsidian vault — ไฟล์ `.md` ที่ AI จดจากลายมือ พร้อม `[[wikilink]]` ตรงกับเส้นโยงบนกระดาน |

### 8. อื่นๆ

- **🗓️ ปฏิทิน** — พาเนลตารางเวลา ดึงจาก Google Calendar (`/api/calendar`) มีทั้งมุมมองเดือนและซูมเข้าไปดูรายวัน อัปเดตสดผ่าน WebSocket
- **📱 รองรับมือถือ/ทัชสกรีน** — วาด ลาก ซูมด้วยนิ้วได้
- **สลับโมเดล Claude** — `/api/current-model`, `/api/set-model`
- **ดู token usage** — `/api/claude-usage`
- **Agent heartbeat** — `/api/agent/heartbeat`, `/api/agent/status` บอกว่า agent ยังมีชีวิตอยู่ไหม
- **Inbox แบบ event-based** — `ws-inbox.js` ใช้ WebSocket แทนการ poll ทุก 3 วิ (ดู `docs/event-based-system.md`)

---

## MCP — เชื่อม Claude Code เข้ากับแอป

### ติดตั้ง

**วิธีที่ 1 — project scope (ใช้อยู่แล้วในโปรเจกต์นี้):** ไฟล์ `.mcp.json` อยู่ที่ root แล้ว แค่รัน `claude` ในโฟลเดอร์นี้

```json
{
  "mcpServers": {
    "powerfull-note": {
      "command": "node",
      "args": ["${CLAUDE_PROJECT_DIR:-.}/mcp-server.js"],
      "env": { "PORT": "4321" }
    }
  }
}
```

**วิธีที่ 2 — user scope (ใช้ได้ทุกโปรเจกต์):**

```bash
claude mcp add powerfull-note -s user -- node path/to/powerfull_note/mcp-server.js
claude mcp list          # ดูสถานะ
claude mcp remove powerfull-note -s user
```

> ⚠️ **ต้องเปิด `start.cmd` ค้างไว้ก่อน** MCP ถึงจะทำงาน — `mcp-server.js` เป็นแค่ HTTP client ที่ยิงไปที่ `localhost:4321`
> ⚠️ แก้ไฟล์ MCP แล้วต้อง **restart Claude Code** เสมอ (tool โหลดตอนเปิด session)

### Tool ทั้ง 25 ตัว

| กลุ่ม | Tool | หน้าที่ |
|---|---|---|
| **อ่านกระดาน** | `get_mindmap` | อ่านโครงมายด์แมปปัจจุบัน (พร้อม id ทุกโหนด) |
| | `get_full_map` | ภาพรวมทั้งกระดาน (โหนด + กล่อง + เส้นโยง) |
| | `get_canvas_screenshot` | ภาพหน้าจอกระดานจริง |
| **แก้กระดาน** | `add_topic` | เพิ่มหัวข้อ/หัวข้อย่อย (ระบุ `parentId`) |
| | `add_topics_bulk` | เพิ่มหลายหัวข้อ + ผูกแม่-ลูก ในคำสั่งเดียว |
| | `update_node` | แก้ข้อความ/สีโหนด |
| | `move_node` | ย้ายตำแหน่ง |
| | `delete_node` | ลบโหนด (พร้อมลูกทั้งหมด) |
| | `tidy_layout` | จัดวางอัตโนมัติ — **ระบุ `rootId` เสมอ** |
| **คุยกับผู้ใช้** | `say_to_user` | ส่งข้อความเข้าพาเนลแชทซ้าย (ระบุ `section` ได้) |
| | `get_voice_input` | ดึงข้อความเสียง/ข้อความล่าสุดที่ผู้ใช้พูด |
| | `get_inbox` | อ่านข้อความค้างใน inbox ของ section |
| **รูปภาพ** | `add_image` / `list_images` / `move_image` | จัดการรูปบนกระดาน |
| | `get_user_images` | **อ่านภาพลายมือที่ผู้ใช้เขียน** (ใช้กับกล่อง note) |
| **กล่อง** | `list_aiboxes` | ดูรายการ aibox ทั้งหมด |
| | `delete_box` | ลบกล่อง |
| **โปรเจกต์** | `list_projects` / `create_project` / `switch_project` | สลับ/สร้างกระดานหลายชุด |
| **วิดีโอ** | `comprehend_video` / `get_video_digest` / `get_video_frame` | ย่อยและอ่านวิดีโอ |
| **Agent อื่น** | `delegate_to_gemini` | มอบงานให้ Gemini ทำ |

**ตัวอย่างที่สั่งได้:**
> "ดูเสียงล่าสุดที่ฉันพูด แล้วแตกเป็นมายด์แมปหัวข้อย่อยให้หน่อย"
> "อ่านลายมือในกล่องนี้ แล้วจดเป็นไฟล์ md ใน notes/"
> "ย่อยคลิปนี้ให้หน่อย แล้วสรุปเป็นหัวข้อย่อยบนกระดาน"

---

## MCP server ตัวอื่นบนเครื่องนี้

นอกจาก `powerfull-note` เครื่องนี้ยังลง MCP server อื่นไว้ (user scope — ใช้ได้ทุกโปรเจกต์) รายละเอียดเต็ม: [`notes/custom-mcp-servers.md`](notes/custom-mcp-servers.md)

| MCP | ที่มา | ทำอะไร |
|---|---|---|
| **`powerfull-note`** | **เขียนเอง** (repo นี้) | มายด์แมป + เสียง + วิดีโอ + แชท (25 tools) |
| `tia-openness-full` | clone (MIT) | Siemens TIA Portal V20 ครบเครื่อง — PLC block/tag/UDT, HMI Classic+Unified, alarm, online read-only, compile (**189 tools**) |
| `tiaportal-mcp` | clone (MIT) | TIA Portal พื้นฐาน — PLC block/type export/import, compile |
| `plcsim-mcp` | **เขียนเอง** (C#, net48) | คุม PLCSIM Advanced — สร้าง vPLC, RUN/STOP, อ่าน/เขียน tag & bit (27 tools) ⚠️ ต้องมี PLCSIM **Advanced** runtime |
| `claude-in-chrome` | Anthropic | สั่งงาน Chrome — คลิก กรอกฟอร์ม อ่าน console/network |
| `unity-mcp` | ภายนอก | สร้าง/แก้ scene, prefab, material ใน Unity |

**คำสั่งจัดการ MCP:**
```bash
claude mcp add <ชื่อ> -s user -- "<path ถึง exe หรือ node script>"
claude mcp get <ชื่อ>      # ดูรายละเอียด
claude mcp list            # ดูทั้งหมด + สถานะ connected
claude mcp remove <ชื่อ> -s user
```

---

## HTTP API

~70 endpoints ใน `server.js` — กลุ่มหลัก:

| กลุ่ม | Endpoints |
|---|---|
| **State** | `GET/POST /api/state` · `/api/viewport` · `/api/clear` · `POST /api/undo` `/api/redo` |
| **โหนด** | `POST /api/nodes` · `DELETE /api/nodes/:id` · `POST /api/layout` |
| **วาด** | `POST /api/drawings` · `DELETE /api/drawings/:id` · `POST /api/drawings/erase` |
| **รูป** | `POST /api/images` · `/api/images/from-url` · `DELETE /api/images/:id` · `GET /api/media?path=` |
| **กล่อง** | `POST/DELETE /api/boxes` · `/api/box-links` · `POST /api/boxes/:id/to-claude` |
| **แชท** | `POST /api/chat` · `/api/chat/clear` · `/api/chat-sections` (+`/:id/activate`) |
| **Inbox** | `GET/POST /api/inbox` · `/api/image-inbox` · `/api/video-inbox` |
| **Agent** | `GET/POST /api/agent-listener` · `/api/agent/heartbeat` · `/api/agent/status` · `/api/launch-claude` |
| **Gemini** | `POST /api/gemini/handoff` · `/api/gemini/task` (+`/:id/claim`, `/:id/result`) |
| **เสียง** | `POST /api/voice` · `/api/transcribe` (Groq) · `/api/transcribe-local` (faster-whisper) · `GET /api/tts` · `/api/whisper-model` · `POST /api/ptt` |
| **วิดีโอ** | `POST /api/videos/add` · `/api/video-upload` · `/api/video-complete` · `GET /api/video-digest` · `/api/video-frame` |
| **อื่นๆ** | `GET/POST /api/calendar` · `/api/projects` · `POST /api/github/push` · `GET /api/claude-usage` · `/api/current-model` · `POST /api/set-model` · `/api/screenshot` · `/api/fullmap` |

**Inbox กับ agent filter** (สำคัญเวลาเขียน agent ที่มาฟัง):
```bash
curl -s -G http://localhost:4321/api/inbox \
  --data-urlencode "section=<SECTION_ID>" \
  --data-urlencode "drain=true" \
  --data-urlencode "agent=claude"        # ← ต้องมี ไม่งั้น server ตอบ "who are you?"
```
ถ้า section นั้นถูกสลับเป็นโหมด Gemini แล้ว server จะคืน `items: []` ให้ `agent=claude` โดยอัตโนมัติ

---

## Environment variables

| ตัวแปร | ค่าเริ่มต้น | ใช้ทำอะไร |
|---|---|---|
| `PORT` | `4321` | พอร์ต server (ต้องแก้ใน `.mcp.json` ด้วย) |
| `CHAT_SECTION` | — | ผูก Claude instance นี้กับ section เดียว (สำหรับรันหลายตัวขนาน) |
| `AGENT` | `claude` | บอกว่า instance นี้คือ agent ตัวไหน |
| `NOTE_SERVER_URL` | `http://localhost:$PORT` | ให้ MCP ชี้ไปเซิร์ฟเวอร์เครื่องอื่นได้ |
| `GROQ_API_KEY` | — | เปิดใช้ `/api/transcribe` (Whisper บนคลาวด์) |
| `GITHUB_TOKEN` / `GITHUB_REPO` / `GITHUB_BRANCH` | branch=`main` | ปุ่ม 🐙 GitHub |
| `TERMINAL` | อัตโนมัติ | เทอร์มินัลที่ `/api/launch-claude` จะเปิด |

---

## Graphify — knowledge graph ของโค้ด

`graphify-out/graph.json` — กราฟความสัมพันธ์ของโค้ดทั้งโปรเจกต์ (~493 nodes, 732 edges)

**กฎการใช้ (สำคัญสำหรับ AI agent):**
- ✅ **query เฉพาะจุด** — ดึง subgraph รอบ node ที่สนใจ ("ใครเรียก `api()` บ้าง", "ลบฟังก์ชันนี้กระทบอะไร") ประหยัดโทเคนได้ ~13.8x
- ❌ **ห้ามโหลดทั้งไฟล์** — graph.json อาจใหญ่กว่าโค้ดจริง (~85k tokens)
- ❌ **ไม่ช่วยเรื่องเนื้อโค้ด/style** — กราฟมีแต่โครงสร้าง ไม่มีตัวโค้ด ต้องการโค้ดจริงให้อ่านไฟล์ตรง ๆ
- **God nodes:** `$()`, `render()`, `changed()`, `eventCanvasPos()`, `api()`
- อัปเดตกราฟ: `/graphify --update` · รายงาน: `graphify-out/GRAPH_REPORT.md` · ดูภาพ: `graphify-out/graph.html`

---

## โครงสร้างไฟล์

```
powerfull_note/
├── server.js                 ★ Express + WebSocket + state ทั้งหมด (1,900 บรรทัด)
├── mcp-server.js             ★ MCP stdio server — 25 tools ให้ Claude (739 บรรทัด)
├── .mcp.json                   ตั้งค่า MCP scope โปรเจกต์
├── package.json                deps: express, ws, zod, @modelcontextprotocol/sdk
│
├── public/                   ── ฝั่งเบราว์เซอร์ (ไม่มี build step)
│   ├── index.html              โครง UI ทั้งหมด (toolbar, พาเนล, modal)
│   ├── app.js                ★ canvas engine — โหนด/วาด/กล่อง/ซูม (3,300 บรรทัด)
│   ├── style.css
│   └── modules/
│       ├── chat.js             พาเนลแชท + sections + in-app banner
│       ├── voice.js            ไมค์ + PTT (`P` / Alt+P) + TTS
│       ├── calendar.js         พาเนลปฏิทิน
│       ├── export.js           export MD / PNG / PDF
│       └── github.js           ปุ่ม push ขึ้น GitHub
│
├── global_ptt.py             ── global hotkey Alt+P (Claude) / Alt+O (Gemini)
├── notify_daemon.py          ── desktop toast + เรนเดอร์สมการ LaTeX
├── tts_worker.py             ── persistent edge-tts worker (สตรีม MP3)
├── video-comprehension.js    ── ย่อยวิดีโอเป็น digest ให้ AI อ่าน
│
├── start.cmd                 ── เปิดครบชุด: server + PTT + notification
├── claude-listen.cmd         ── ทางลัด: เปิด Claude + arm listener ให้ section
├── install-autostart.cmd     ── ตั้งให้เปิดเองตอนบูต Windows
├── ptt-listen.cmd / notify-listen.cmd
│
├── notes/                    ── Obsidian vault (AI จดลายมือลงที่นี่)
├── docs/                     ── เอกสารเชิงลึก
│   └── voice-ptt-and-notifications.md
├── graphify-out/             ── knowledge graph ของโค้ด
├── tools/                    ── MCP server อื่น (TIA Portal, PLCSIM)
├── data/                     ── state ที่ persist (git-ignored)
└── CLAUDE.md / GEMINI.md     ── คำสั่งประจำโปรเจกต์สำหรับ AI agent
```

---

## หมายเหตุ

- ข้อมูลทั้งหมดเก็บใน `data/` เป็น JSON — git-ignored, ไม่มี cloud, ไม่มี DB
- ต้องใช้ **Chrome หรือ Edge** — Web Speech API (`th-TH`) ไม่มีใน Firefox/Safari
- เรื่อง `/voice` ของ Claude Code: ตัวมันเป็นโปรแกรมปิด แก้ที่ตัวมันไม่ได้ → เลยทำระบบเสียงไทยครบวงจรไว้ในแอปนี้แทน
- อ่าน [`CLAUDE.md`](CLAUDE.md) ก่อนถ้าคุณคือ AI agent ที่จะมาทำงานกับโปรเจกต์นี้ — มีกฎเฉพาะ (เช่น `tidy_layout` ต้องระบุ `rootId`, ห้าม drain inbox ข้าม section)
