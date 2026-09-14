# SESSION HANDOFF MASTER — Delta Academy Video Project

เขียนโดย Claude 2026-09-15 ก่อนจบ session — **อ่านไฟล์นี้ไฟล์เดียวก็พอสำหรับเริ่มงานต่อ**
ไฟล์อื่นที่อ้างถึงด้านล่างมีรายละเอียดลึกกว่าถ้าต้องการ แต่ไฟล์นี้คือสรุปรวมทุกอย่างที่ต้องรู้

---

## 1. บริบทโปรเจกต์

| อะไร | คือ |
|---|---|
| **เจ้าของ** | Min — นักศึกษา KMITL กำลังแข่งขัน Delta Academy |
| **เป้าหมาย** | ทำวิดีโอให้กรรมการ**เข้าใจกลไก**ของ Zero-Downtime Changeover Cell (เปลี่ยนขนาดขวด **250ml → 500ml** โดยไม่ต้องรื้อไลน์ ใช้เวลา ≤5 นาที จากเดิมช่างขันน็อต 45 นาที) |
| **ขอบเขตของ Min** | อธิบายกลไกเท่านั้น **ห้ามใส่ ROI/ต้นทุน/ตัวเลขเงินเด็ดขาด** (เพื่อนร่วมทีมคนอื่นรับผิดชอบส่วนนั้น) |
| **ทีมทำงาน** | Min (ผู้ตัดสินใจ) + **Claude** (วางแผน/ตรวจสอบ/ประสานงาน) + **Gemini** (ลงมือทำ Unity+ตัดต่อ token สูง) + **Codex** (ตรวจสอบ/QA คู่ขนาน) — ทั้ง 3 agent ทำงานในโปรเจกต์ Unity เดียวกัน **พร้อมกันได้** ผ่าน MCP/inbox คนละช่องทาง |

---

## 2. มี 3 คลิป + 1 diagram — สถานะล่าสุด

| # | ชื่อ | เป้าความยาว | % คืบหน้า | เหลืออะไร |
|---|---|---|---|---|
| — | **Flow Diagram** (ภาพนิ่ง เปิดคลิป C พาร์ท 1 หรือใช้แนะนำ B) | ภาพนิ่ง | 🔶 **95%** | ⚠️ **มีบั๊กต้องแก้ก่อนใช้จริง — ดู §4 ข้อ 5** |
| **C** | Hardware Intro (แนะนำ PLC/HMI/VFD/Servo) | ~50-65s | 🔶 **85%** | แก้กล้อง HMI ที่ t=34s แล้ว (โดน pillar ตู้บัง) รอเรนเดอร์ 50s ใน Unity จริง + ต่อ diagram 15s |
| **A** | Line Overview (พาชมทั้งไลน์) | 90.57s | 🔶 **75%** | มีเวอร์ชันที่ผ่านมาแล้ว (`A_LineOverview_FINAL_v2.mp4`) แต่ Gemini กำลังรีเซ็ตใหม่ทั้งชุดหลังอัปเดตโมเดล 3D (Capping Station ใหม่) — ต้องเรนเดอร์ Travel(10.5s)+Zones(80s) ใหม่ + ประกอบ subtitle |
| **B** | Changeover (กลไกเปลี่ยนรุ่น) | ~90-123s | 🔶 **65%** | มีเวอร์ชันที่ผ่านมาแล้ว (`B_Changeover_FINAL_v4.mp4`, 45s) แต่ Gemini กำลังขยายเป็นเวอร์ชันใหญ่กว่า (89s 3D + digital twin dashboard 14s ท้ายคลิป) |

> ⚠️ **สำคัญ:** มีไฟล์ "FINAL" หลายเวอร์ชันซ้อนกันใน `Recordings\` จากการทำงานหลาย agent คู่ขนาน
> **ก่อนใช้ไฟล์ไหนจริง ให้เช็ค timestamp ล่าสุดใน `Recordings\DELIVERABLES_V2\` ก่อนเสมอ** (Gemini
> ใช้โฟลเดอร์นี้เป็นที่รวมไฟล์ล่าสุด) และดูวันที่ในชื่อไฟล์ประกอบ

---

## 3. ⛔ บั๊กที่เจอแล้ว + แก้แล้วจริง (ยืนยันด้วยเฟรมจริง ไม่ใช่แค่ ffprobe)

รายการนี้คือ "อย่าทำผิดซ้ำ" — ทุกข้อเจอจริง มีหลักฐาน ไม่ใช่ทฤษฎี:

1. **ขวดทะลุเสา (2 รอบ)** — รอบแรกแค่ขยับกล้องหนี (ไม่ใช่แก้จริง) รอบสองเจอว่า `Gantry_VerticalColumn` ทับกับ `GuideRail_Left/Right` ในพิกัด 3D จริง (`Renderer.bounds.Intersects()=true`) แก้โดยรัน `Build Full Line` ซ้ำเพื่อ apply โค้ดที่แก้ไว้แล้วแต่ไม่เคย apply เข้า scene
2. **Nozzle Height เพี้ยน** — `CurrentNozzleHeightMm` คืนค่า world Y ตรงๆ (1123mm) แทนที่จะลบ `BeltSurfaceY` ก่อน (ค่าจริงควร 165-240mm) แก้แล้ว ยืนยันได้ 228mm ตรงสเปก
3. **Glow effect เบลดข้ามคลิป** — `MotionHighlightController` (หรือ sequencer แบบเดียวกัน) ต้องปิดระหว่างเรนเดอร์คลิปอื่น ไม่งั้นมันจะ trigger ตาม state ที่วิ่งอยู่เบื้องหลังไม่ว่าจะอัดคลิปไหน
4. **กล่อง "T" ทับจอ** — เข้าใจผิดว่าเป็น texture โหลดไม่ขึ้น จริงๆ คือ **Unity Editor Gizmo icon ของ TextMeshPro** ถูก `ScreenCapture` capture ติดไปด้วย (บั๊กเดียวกับที่เจอตอนทำคลิป A/B ตอนแรกของทั้ง session) แก้โดยปิด `GameView.showGizmos`
5. **⚠️ ยังไม่แก้ — ขนาดขวดผิดใน Flow Diagram:** รูป `Overall_Changeover_Flow_4K.png`/`_1080p.png` ที่ Gemini ทำ ระบุ **"300 / 600 / 1500 ml"** ซึ่ง**ผิด** — ขนาดจริงทั้งโปรเจกต์คือ **250 / 500 / 1000 ml** (ตรงกับ `ChangeoverSequencer.Recipes[]`, ตรงกับ spec sheet ของ Delta, ตรงกับ label ที่เรนเดอร์ในคลิป B ไปแล้ว) **ต้องแก้ก่อนใช้จริง**
6. **HardwareIntroManualRecorder ค้าง enabled บน GameObject "Cell"** — component ทดสอบของ agent หนึ่งไปบังคับ force-quit Play Mode หลัง 360 เฟรม ตัดคลิปของอีก agent ที่กำลังเรนเดอร์อยู่ให้สั้นผิดปกติ — **บทเรียน: ห้ามทิ้ง component ทดสอบ enabled ค้างบน GameObject ที่ agent อื่นใช้ render**
7. **RenderAutoQueue.cs (Gemini เจอ+แก้เอง)** — เรียกชื่อ method ผิด (CS0117), ตัด Play Mode ก่อน encoder เขียนไฟล์เสร็จ (0-byte bug), `CameraInputSettings` ใช้กับ URP ไม่ได้ต้องใช้ `RenderTextureInputSettings`

---

## 4. ⛔ กฎเหล็ก 8 ข้อ (สรุปจาก PLAN.md — ห้ามลืม)

1. รูป `D:\Downloads\image.png`–`image4.png` = เอกสารสเปก ใช้เขียนป้าย/สคริปต์เท่านั้น **ห้ามแปะลงวิดีโอ ห้ามทำเป็นวัตถุ 3D**
2. `ffprobe` ผ่าน ≠ เนื้อหาถูก — **ต้องสกัดเฟรมดูด้วยตาทุกครั้ง**
3. **Save scene ทุกครั้งหลังรัน builder** ก่อนเข้า Play Mode ไม่งั้นงานหายเงียบๆ (Unity revert scene กลับสถานะก่อน Play ถ้ายังไม่เคย save)
4. Overlay ที่ต้องติดในคลิปต้องเป็น **world-space TextMeshPro เท่านั้น** — Screen Space Overlay canvas ไม่ถูก Recorder จับภาพ
5. MonoBehaviour ที่ทำ glow/highlight ต้อง**ปิดตอนเรนเดอร์คลิปอื่น** ไม่งั้นเบลดข้ามคลิป
6. **ห้ามทิ้ง component ทดสอบ enabled ค้างบน GameObject "Cell"**
7. **ชื่อรุ่นต้องตรงเป๊ะ**: AS320T-B (PLC) / DOP-100WS หรือ 103WQ (HMI) / MS300 (VFD) / ASD-A3 (Servo)
8. **ขนาดขวดต้องเป็น 250/500/1000 ml เท่านั้น** (เพิ่งเจอบั๊กข้อนี้ — ดู §3.5)

---

## 5. Path ไฟล์ทั้งหมด

### 5.1 Unity Project (git repo แยกจาก powerfull_note)
```
D:\unity_project\delta_academy\              Unity 6000.6.0f1, URP
  Assets\Scripts\
    ChangeoverSequencer.cs                   state machine S1-S10, Recipes[] (250/500/1000ml)
    CameraDirector.cs                        สลับกล้องตาม state (คลิป B)
    TimedShotSwitcher.cs                     สลับกล้องตามเวลา (คลิป A)
    EquipmentIntroSequencer.cs               6-shot storyboard + glow (คลิป C, Gemini เขียน)
    MotionHighlightController.cs             pulsing glow + mm readout บนราง/หัวฉีด
  Assets\Editor\
    RecorderSmokeTest.cs                     ตัวควบคุม Recorder หลักของทุกคลิป
    RenderAutoQueue.cs                       headless render queue (ใหม่, Gemini เขียน, มี fix ล่าสุด)
    AClipZoneCamerasBuilder.cs               สร้างกล้อง 5 โซนคลิป A
    ZoneLabelsBuilder.cs                     world-space label อุปกรณ์รายโซน
    TelemetryOverlayAttacher.cs              แนบ MotionHighlightController
  Assets\Scenes\SampleScene.unity            scene หลัก
  Assets\ReferenceImages\                    รูปสินค้าจริง Delta ครบ 5 รุ่นแล้ว (_front.jpg)
  Recordings\                                ⚠️ มีไฟล์เก่าปนเยอะ เช็ค timestamp เสมอ
  Recordings\DELIVERABLES_V2\                โฟลเดอร์รวมไฟล์ล่าสุดที่ Gemini ใช้
  Recordings\FINAL_DELIVERABLES\             ปลายทางไฟล์ส่งจริงตามที่ Min ขอ
  Recordings\render_command.json             ช่องทาง headless สั่งเรนเดอร์ (เขียน JSON แล้วรอ render_response.json)
```

### 5.2 powerfull_note (เอกสาร/แผนทั้งหมด)
```
C:\Users\wicha\Desktop\powerfull_note\
  SESSION_HANDOFF_MASTER.md              ← ไฟล์นี้เอง (สรุปรวมทุกอย่าง)
  PLAN.md                                แผนหลัก 3 คลิป + กฎเหล็ก 8 ข้อ + สถานะรูปสินค้า
  CODEX_BRIEF_DELTA_ACADEMY.md           บริบทเต็ม + กับดักทั้งหมด (สำหรับ Codex อ่านตอนเข้างานใหม่)
  CLIP_C_HARDWARE_INTRO_PLAN.md          storyboard คลิป C 6 ช็อต + ป้ายข้อความละเอียด
  ARCH_DIAGRAM_SPEC.md                   สเปก Flow/Architecture diagram (ไทม์ไลน์ทีละวินาที)
  DELTA_EDIT_PLAN.md                     แผนตัดต่อ ffmpeg ดั้งเดิม (คลิป A/B เวอร์ชันแรก)
  HANDOFF.md                             ประวัติงานทั้ง session ของ Claude (long-form)
  HANDOFF_DELTA_DELIVERABLES.md          handoff ล่าสุดที่ Gemini เขียน (root cause 3 บั๊ก render)
  scratch\digital_twin_dashboard.html    Digital Twin Dashboard (Claude สร้าง รอ Gemini แปลงเป็นวิดีโอ+รวม)
```

---

## 6. งานที่กำลังทำอยู่ตอนนี้ (ณ วินาทีที่เขียนไฟล์นี้)

- **Gemini** กำลังขยายคลิป B (89s 3D + digital twin) และเพิ่งเจอ+แก้ 3 บั๊ก render (compile error, 0-byte bug, URP capture bug) ใน `RenderAutoQueue.cs`
- **Codex** เพิ่งตรวจ QA คลิป C ผ่านเกือบหมด (ไม่มี T-box, ชื่อรุ่นถูก, glow ตรง, ช็อต Servo เห็นทั้ง drive+แกนจริง) มีจุดเดียวที่ style ตัวหนังสือไม่ตรงสเปก (cyan/65% แทนขาว/55%) — **Min บอกให้ข้ามไปได้** ไม่ต้องแก้
- **Unity Editor เพิ่งเจอ compile error dialog (Safe Mode)** — ยังไม่ยืนยันว่าแก้หายหรือยัง ถ้า session ใหม่เจอ MCP unity ต่อไม่ได้ ให้เช็คว่ายังค้าง dialog นี้อยู่ไหมก่อน (ต้องกด "Enter Safe Mode" ที่หน้าจอ Unity จริงเท่านั้น ไม่มี agent ไหนกดแทนได้)

---

## 7. งานที่ยังไม่เริ่ม / ต้องทำต่อ

1. **แก้ตัวเลขขวดผิดใน Flow Diagram** (300/600/1500 → 250/500/1000) — ด่วน เพราะจะเอาไปใช้จริง
2. **Architecture diagram แบบ animated** (คลิป C พาร์ท 1, ~15-18s) — สเปกพร้อมแล้วที่ `ARCH_DIAGRAM_SPEC.md` (ทยอยโผล่กล่องทีละตัว: PLC→HMI→Servo/VFD→Sensors→DIACloud, เส้นมี pulse วิ่งมีทิศทาง+ป้ายโปรโตคอล) — ส่งให้ Codex ไปแล้วตอน offline อาจต้องส่งซ้ำ
3. **รวมไฟล์สุดท้ายทั้ง 3 คลิป** เป็นชุดที่ยืนยันแล้วจริง (เช็คเฟรมทุกจุดต่อ ไม่ใช่แค่ ffprobe)
4. **ภาพถ่ายอุปกรณ์จริงแบบ inset มุมขวาบน + เส้นโยง** (ตามที่ Min ขอ ยังไม่ได้ทำ — รูปมีพร้อมแล้วที่ `Assets\ReferenceImages\`)
5. เช็คว่า Digital Twin Dashboard (`scratch\digital_twin_dashboard.html`) ถูกแปลงเป็นวิดีโอ+รวมเข้าคลิป B แล้วหรือยัง

---

## 8. คำเตือนเรื่อง Multi-agent coordination

- Gemini กับ Codex (และก่อนหน้านี้ Claude) **แก้ไฟล์ในโปรเจกต์ Unity เดียวกันพร้อมกันได้จริง** ผ่าน live Editor — เคยชนกันมาแล้ว (component ทดสอบไปขัดจังหวะ render ของอีก agent) ให้ระวังเรื่องนี้เสมอ
- ส่งงานให้ Codex ผ่าน `POST /api/inbox` ที่ `http://127.0.0.1:4321` โดยใส่ `"to":"chatgpt"` ในkörper (ต้องเขียนเป็นไฟล์ JSON แล้ว `curl -d @file.json` เพราะ path มี backslash ใส่ inline ใน bash จะพัง)
- ส่งงานให้ Gemini ผ่าน MCP tool `mcp__powerfull-note__delegate_to_gemini` (ต้องมี `antigravity-wait.py` รันอยู่ให้สถานะเขียว)
- เช็คสถานะงาน Gemini ผ่าน `curl http://127.0.0.1:4321/api/gemini/task/<id>` — status ที่แปลว่าเสร็จคือ `"done"` ไม่ใช่ `"completed"`
- **Min คุยกับ Gemini ตรงได้เองด้วย** (ไม่ผ่าน Claude) — เคยเกิด scope ขยายแบบที่ Claude ไม่รู้ตัวมาก่อน (Digital Twin Dashboard เป็นตัวอย่าง) — เช็ค `PLAN.md` เทียบกับของจริงเสมอเวลาสรุปสถานะ
