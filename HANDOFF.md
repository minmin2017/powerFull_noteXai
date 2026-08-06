# HANDOFF — สถานะงานล่าสุด

> ไฟล์นี้คือ "สมองสำรอง" ข้าม session — เขียนไว้กัน context เต็มแล้วงานหาย
> **session ถัดไป: อ่านไฟล์นี้ก่อนเริ่มงาน** แล้วอัปเดตทับเรื่อยๆ (ไม่ต้องสร้างไฟล์ใหม่ตามวันที่)

**อัปเดตล่าสุด:** 2026-08-06 — session 86% (Usage Guard เตือน)

## ✅ เสร็จแล้วรอบนี้ (เข้า Obsidian vault `Main_note/Exam_Prep/` ครบทุกอัน)

### Electrical Power System (โฟลเดอร์ใหม่ทั้งชุด)
- `Electrical Power System MOC.md` + ลิงก์จากตารางสอบแล้ว (เดิมเป็นตัวหนังสือเปล่า วิชาเดียวที่ไม่มีลิงก์)
- `... — Topic Walkthrough (บทที่ 1-5).md` — สรุปเป็นหัวข้อ 126 หน้า + คลิป EP01-EP06 ฝังในเนื้อหา
- `... — Homework Walkthrough (บทที่ 1-4).md` — เฉลย + ภาพลายมือ Min 9 หน้า (`hw-ch1-1..5`, `hw-ch2-1..2`, `hw-ch3-1..2`)

### Mechanics of Machinery (ใหม่ล่าสุด)
- `Lecture 1 + HW1-2 — Mechanism Fundamentals and Degrees of Freedom.md` + คลิป M01-M04 + ลิงก์ใน MOC แล้ว
- **ตรวจการเคลื่อนที่ของกลไกสี่ชิ้นเชิงตัวเลขแล้ว** (Min กังวลเรื่องนี้): Grashof ผ่าน (4.30 ≤ 5.20, ข้อเหวี่ยงสั้นสุด → หมุนครบรอบได้จริง), ความยาวก้านคงที่ error 1e-15, ไม่มีตำแหน่งที่เอื้อมไม่ถึง, ก้าวใหญ่สุดระหว่างเฟรม 0.0039 (ไม่มีการดีด/สลับ branch), คันโยกแกว่ง 52.2° ไม่ครบรอบ = พฤติกรรม rocker ถูกต้อง

### แก้ปัญหาหน้าติวแลค
- แปลง PNG→JPEG ที่โน้ตอ้างถึงจริง 60 ไฟล์: **42.3 MB → 12.8 MB (−70%)** แก้ embed ในโน้ต 8 ไฟล์อัตโนมัติ ลิงก์ไม่พังสักอัน

### ⏳ ต้องทำต่อ
1. **บีบวิดีโอยังไม่จบ** — เหลือ ~39 ไฟล์ ใช้ `scratchpad/shrink.ps1` (PowerShell, CRF 28 ลดได้ ~77% ตาไม่เห็นต่าง — เช็คเฟรมแล้ว)
   - ⚠️ **bash ใน session นี้ PATH พัง** (`find`/`curl`/`ffmpeg` not found) → ใช้ PowerShell แทน
   - เจอไฟล์ `*.__re.mp4` ค้าง = ffmpeg โดน kill กลางคัน ลบทิ้งได้เลย
2. **Power Electronics PC01-09** ยังเป็นสไลด์สูตรแบบเก่า — Min เคยบ่น "เห็นแต่สูตร อยากได้กราฟ" ถ้ารื้อใช้แพทเทิร์นเดียวกับ EP/WK
3. **Mechanics บทอื่น** — `ClassNoteMachinery63.pdf` (137 หน้า) ดึงมาแค่บทที่ 4-5
4. **บทที่ 4 ปี3.xopp** (Elec Power) ยังไม่ได้ถอดเฉลยลายมือ

### 🔧 บทเรียน Manim (อย่าพลาดซ้ำ)
1. **ห้ามใช้ `self.xxx` เป็นฟังก์ชันวาดกราฟ** (`ax.plot(self.f, ...)`) — ParametricFunction จะอ้างถึง Scene ที่มี thread lock → **ค้างนิ่ง 12 นาทีโดยไม่มี error** แล้วตายด้วย `cannot pickle '_thread.lock'` → ประกาศเป็นฟังก์ชันระดับโมดูลเสมอ
2. ป้ายแกน x ห้ามวางที่ `c2p(v, 0)` ถ้าเส้นโค้งตัดผ่าน y=0
3. ห้ามใส่ภาษาไทยใน `MathTex` — ใช้ `Text()` แยก
4. walrus `:=` ใช้ใน keyword argument ไม่ได้
5. `[LAYOUT]` จับ text ทับ graphic ได้ แต่**จับข้อผิดพลาดเชิงข้อเท็จจริงไม่ได้** — ต้องดึงเฟรมดูจริง (เคยเจอคลิปโชว์น้ำมันยุบ 16% ซึ่งมั่ว ของจริง ~1.2%)

### 📂 โค้ด Manim
- `mecho_life/fluid power control/week1_properties_energy.py`
- `mecho_life/electrical power system/eps_ch1_5.py`
- `mecho_life/machinary/new_2569/mech_fundamentals.py`
- เรนเดอร์: `Desktop\manium\.venv_community\Scripts\python.exe -m manim -ql --fps 25 <file> <Scene>`


### ✅ Push ขึ้น GitHub แล้ว
- Repo: `github.com/minmin2017/tew_mechoLife_hellthatyou_chose` (public, shared สำหรับสลับกันติวกับเพื่อน)
- Push แล้ว 2 ครั้ง: commit `27bfc1e` (โน้ต+A/H วิดีโอ) และ `da02ed0` (C วิดีโอ)
- โครงสร้าง: โฟลเดอร์ `Mechanics of Machinery/` แยกจาก `Fluid Power Control/` ที่มีอยู่เดิมที่ root
- **สำคัญ:** ไม่ push `Attachments/` (PDF ตำราต้นฉบับ) หรือ `pages_*/` (ภาพตัดจากตำรา) เพราะเป็นเนื้อหาลิขสิทธิ์ — push แค่โน้ต .md/.html + `anim/*.mp4`

### ✅ เพิ่ม "วิธีคิดทีละขั้น" ใน Template
- `Exam_Prep/Templates/Topic Template.md` มี section "🧭 วิธีคิดทีละขั้น" แล้ว — โจทย์ตัวอย่างทุกวิชาต่อไปนี้ต้องเขียนเป็นขั้นตอนเลข (เข้าใจโจทย์→เลือกสูตร→แทนค่า→ตรวจคำตอบ)

✅ `usage-guard.js` ยืนยันแล้วว่าใช้งานได้จริงทั้ง 2 จังหวะ (85%+ เตือน / รีเซ็ตแล้วปลุก) — ผูกกับ `start.cmd` แล้วด้วย ไม่ต้องรันมืออีก

---

## 🔴 ทำก่อนอื่นทุก session

1. **Arm inbox listener** (ไม่ persist ข้าม session):
```bash
curl -s -G http://localhost:4321/api/inbox \
  --data-urlencode "section=main" --data-urlencode "drain=true" --data-urlencode "agent=claude"
```
   แล้ว arm Monitor ให้ poll คำสั่งนี้ทุก ~3 วิ (ห้ามลืม `agent=claude` ไม่งั้น server ตอบ "who are you?")
2. ตอบ Min ผ่าน MCP `say_to_user` พร้อม `section: "main"` — **ตอบเป็นภาษาไทยเสมอ**

---

## ✅ เสร็จแล้ว (session นี้)

### โน้ต Obsidian — `Desktop/Main_note/Exam_Prep/Mechanics of Machinery/`
| ไฟล์ | สถานะ |
|---|---|
| `Lecture Walkthrough — Acceleration Analysis of Mechanisms.md` | ✅ ครบ 24 หน้า + ภาคผนวกเทียบตำรา + แฟลชการ์ด + ฝังวิดีโอ 22 คลิปแล้ว |
| `Homework 4 Walkthrough — Velocity Vector Analysis.md` | ✅ 2 ข้อครบ + แฟลชการ์ด — **ยังไม่มีวิดีโอฝัง** |
| `Mechanics of Machinery MOC.md` | ✅ |
| `Mechanics of Machinery Flashcard Review.md` | ✅ |
| `Exam Prep Home.md` | ✅ เพิ่มลิงก์วิชาใหม่แล้ว |

**คำตอบการบ้าน 4** (ตรวจแล้ว เลขลงตัวสวย = เรขาคณิตอ่านถูก):
- ข้อ 1: `v_B = 6 cm/s ไปทางซ้าย`, **`ω_AB = 0`** (ไม่ใช่ error — ปลายก้าน 2 ข้างวิ่งขนาน = pure translation)
- ข้อ 2: `v_C = 4.5 m/s ไปทางขวา`, **`ω_DC = 9 rad/s ตามเข็ม`** (ความเร็วไถล 3.90 m/s)
- ⚠️ ข้อ 2 มุม 60° วัดจาก**แนวดิ่ง** ไม่ใช่แนวนอน / α ที่ให้มาทั้ง 2 ข้อไม่ต้องใช้

### วิดีโอ — `Mechanics of Machinery/anim/`
- Gemini เจนครบ 22 คลิปแต่คุณภาพต่ำ + **ทิศลูกศรผิดฟิสิกส์** (hardcode `LEFT*0.8+UP*0.8`)
- ✅ **เขียนใหม่เองครบ 22/22 คลิป (A01–A22)** ทิศเวกเตอร์คำนวณจากมุมก้านจริงทุกตัว
  (A09 38.2s, A05 30.9s, A08 26.9s เป็น 3 คลิปหลัก; ที่เหลือ 10–23s รวมยาวขึ้น ~2 เท่าจากของ Gemini)
- ✅ **วิดีโอการบ้านใหม่ H01 (20.3s), H02 (22.4s)** เสร็จ + ฝังในโน้ตการบ้านแล้ว
- ✅ **ตรวจด้วยตาแล้ว** (แคปเฟรม) — ฟอนต์ไทยถูก, ข้อความไม่ล้นจอ, ทิศเวกเตอร์ถูกฟิสิกส์
- ⚠️ **บทเรียน:** ห้ามใส่ภาษาไทยใน `MathTex` เด็ดขาด (LaTeX Error: Unicode) — ผมพลาดเอง 8 คลิปในรอบเดียว
  ต้องแยกเป็น `Text(...)` แล้ว `VGroup(...).arrange(RIGHT)` — และ **grep หาไทยใน MathTex ก่อนเรนเดอร์ทุกครั้ง**
- ⚠️ **บทเรียน 2:** พาเนลขวาที่ใช้ `next_to(..., aligned_edge=LEFT)` จะล้นขอบจอ → ใช้ `aligned_edge=RIGHT`

---

## ⏳ ค้างอยู่ / ทำต่อ

1. ~~A08 re-render~~ ✅ เสร็จแล้ว (26.9s) copy ไป `anim/` เรียบร้อย
2. ~~วิดีโอการบ้าน H01, H02~~ ✅ เสร็จ + ฝังในโน้ตแล้ว
3. ~~A02–A22 คุณภาพต่ำ~~ ✅ เขียนใหม่หมดแล้ว — **เหลือแค่ A01** (คลิปเปิดเรื่อง) ที่ยังเป็นของ Gemini
4. ตำรา `ClassNoteMachinery63.pdf` (137 หน้า) — ดึงมาแค่**บทที่ 4** ตามที่ Min สั่ง บทอื่นยังไม่แตะ
5. **ข้อสอบซ้อมอีก 4 วิชา** (Power Electronics / Electrical Power System / PLC / Fluid Power) — ยังไม่เริ่ม
   ต้นแบบดูที่ `Mechanics of Machinery/Practice Midterm — Mechanics of Machinery.html`

---

## 🔧 ความรู้เชิงเทคนิคที่เพิ่งได้ (อย่าเสียเวลาค้นใหม่)

**Manim อยู่ใน venv ไม่ได้อยู่บน PATH:**
```bash
cd /c/Users/wicha/Desktop/manium && ./.venv_community/Scripts/manim.exe -qm a09.py A09
```
(`manim`, `python -m manim`, `import manim` ล้มเหลวหมด)

- ต้องมี `Text.set_default(font="Leelawadee UI")` ทุกไฟล์ ไม่งั้นภาษาไทยเป็นกล่องสี่เหลี่ยม
- ห้ามใส่ภาษาไทยใน `MathTex` (LaTeX พัง) — ไทยใช้ `Text` คณิตใช้ `MathTex` แยกกัน
- output: `manium/media/videos/<script>/720p30/<Scene>.mp4` → copy ไป `anim/` แล้วฝังเป็น `![[A09.mp4]]`
- `Downloads` จริงอยู่ที่ **`D:\Downloads`** (ไม่ใช่ `C:\Users\wicha\Downloads` ซึ่งไม่มีอยู่)
- แปลง PDF เป็นรูป: `pdftoppm -png -r 150 in.pdf out` (มากับ MiKTeX, อยู่บน PATH แล้ว)
- ตรวจวิดีโอ: `ffmpeg -v error -ss 12 -i x.mp4 -frames:v 1 out.png` แล้วเปิดดูด้วยตา

**บทเรียนสำคัญ:** Gemini รายงานว่า "เสร็จ verified ครบ" ทั้งที่งานผิดฟิสิกส์ — **ต้องแคปเฟรมดูเองทุกครั้ง** log ที่ขึ้นว่า render ผ่านไม่ได้แปลว่างานถูก

---

## 📌 กฎที่ Min ย้ำใน session นี้

- Min บอกว่า "**ผมมีความรู้เท่ากับ 0**" → โน้ต/วิดีโอต้องปูพื้นฐานก่อนเสมอ ทำให้**เห็นภาพ** ไม่ใช่โชว์สมการเฉยๆ
- **~90% context → เขียน HANDOFF.md + re-arm listener** (ไฟล์นี้แหละ) — Min เป็นคนดู % เอง ผมดูไม่ได้ ต้องรอเขาบอกหรือเขียนเผื่อไว้ก่อน
