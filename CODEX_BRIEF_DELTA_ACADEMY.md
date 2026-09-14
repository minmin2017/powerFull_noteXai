# CODEX BRIEF — Delta Academy Video Project
> **อ่านไฟล์นี้ให้จบก่อนเริ่มทำงานใดๆ**
> มีบริบท, path, งานเสร็จ, งานค้าง, กับดัก, และกฎการทำงานครบทั้งหมด — ไม่ต้องอ่านไฟล์อื่นเพิ่ม

> [!CAUTION]
> **⚠️ พบว่า Codex ทำงานคู่ขนานอยู่แล้วจริง (2026-09-14 ~18:15) — อ่านก่อนแตะอะไรต่อ**
>
> ระหว่างที่ Claude กำลังแก้บั๊กเสา พบว่า **Codex เปิด Unity Editor เดียวกันทำงานคู่ขนานอยู่จริง**
> (ไม่ใช่แค่ทำงานผ่าน git worktree แยก) หลักฐาน:
> - `git log --oneline -5` เจอ commit `bfb7415 feat: Add Hardware Intro scripts, update Cabinet
>   and Guide Rails (Phase 2)` วางซ้อนอยู่ระหว่าง commit ของ Claude สองอัน
> - พบไฟล์ `Assets/Scripts/HardwareIntroManualRecorder.cs` **ที่ enabled อยู่บน GameObject "Cell"
>   จริงในฉากที่เปิดอยู่** — สคริปต์นี้ตั้งใจ force-quit Play Mode หลัง 360 เฟรม (12s) ซึ่งไป
>   **ขัดจังหวะ render 45s ของ B_Changeover ที่ Claude กำลังทำอยู่พอดี** (ไฟล์ออกมาสั้นแค่ 11.97s
>   แทนที่จะเป็น 45.03s) — Claude ปิด component นี้แล้วเพื่อทำงานต่อได้ **ถ้า Codex กำลังใช้
>   component นี้อยู่ อาจต้องเปิดกลับหรือ refactor ให้ไม่ไปแตะ GameObject ที่ agent อื่นใช้ render ด้วย**
> - พบไฟล์วิดีโอที่ Claude ไม่เคยสร้าง ใน `Recordings\` (ตอนนี้ path นี้ถูก gitignore แล้ว ไม่โผล่ใน
>   `git status` ธรรมดา ต้องใช้ `git status --ignored` ถึงจะเห็น): `C_HardwareIntro_FINAL.mp4`,
>   `C_HardwareIntro_RAW.mp4` (0 byte, เสีย), `C_HardwareIntro_RAW_v3.mp4`, `Recipe_UI_Overlay.mp4`,
>   `B_Changeover_VIBE5_PRO_90s.mp4`, `B_Changeover_HYPERFRAME_90s.mp4`,
>   `B_Changeover_PHASE2_FULL.mp4`, `B_Changeover_FINAL_PHASE2.mp4` — ตรงกับงาน 9.1 (hardware
>   intro), 9.3 (recipe UI), และ 5.1/B1 (ยืดคลิป B เป็น 90s) **ที่ Min เพิ่งขอในบทที่ 9 ทุกอย่าง
>   แปลว่า Codex อ่าน/รับโจทย์พวกนี้และเริ่มลงมือทำไปมากแล้วจริง ก่อนไฟล์บรีฟนี้จะเขียนเสร็จด้วยซ้ำ**
>
> **ตรวจ `C_HardwareIntro_FINAL.mp4` แล้วพบบั๊กจริง:** สกัดเฟรมที่ t=5s เจอกล่องสี่เหลี่ยม cyan
> ขนาดใหญ่มีตัวอักษร "T" ค้างอยู่ทับเต็มจอ (Missing/Fallback Glyph — font atlas TextMeshPro
> น่าจะเสีย) ทับ label "HMI DOP-100WS / One-Touch Changeover & CIP Verification" ที่เขียนถูกต้อง
> — Claude เจอว่า `Assets/TextMesh Pro/Resources/Fonts & Materials/LiberationSans SDF -
> Fallback.asset` ถูกแก้ไข (น่าจะเกี่ยวกับบั๊กนี้) **แต่ตั้งใจไม่ commit ทับให้** (ปล่อยเป็น working
> tree change รอ Codex แก้เอง) เพราะไม่รู้ว่า Codex แก้ไปถึงไหนแล้ว กลัว commit ทับจะทำให้เสียงาน
>
> **คำแนะนำ:** ถ้า Min ให้ Codex อ่านไฟล์นี้ต่อ **ให้ Codex เช็คสถานะงานตัวเองก่อน** (ดู
> `Recordings\` ทั้งหมด + `git log` + component บน `Cell`) แทนที่จะเริ่มใหม่จากศูนย์ตามบทที่ 9
> ด้านล่าง เพราะเนื้อหาส่วนใหญ่ในบทที่ 9 อาจซ้ำกับที่ทำไปแล้ว — บทที่ 9 เขียนไว้ตอนที่ Claude ยังไม่รู้
> ว่า Codex ทำไปถึงไหน ให้ใช้เป็น "requirement เต็ม" อ้างอิง ไม่ใช่ "task list เริ่มจากศูนย์"

---

## 1. บริบทโปรเจกต์

| คน / ทีม | บทบาท |
|---|---|
| **Min** | เจ้าของโปรเจกต์ นักศึกษา KMITL กำลังแข่งขัน |
| **Codex / Gemini** | AI agents ที่ช่วยทำงาน Unity + ffmpeg |
| **เพื่อนร่วมทีม (คนอื่น)** | รับผิดชอบส่วน ROI / ต้นทุน / ตัวเลขเงิน — **ไม่ใช่ Min** |

### เป้าหมายคลิป
ทำให้กรรมการ **เข้าใจกลไก** ของ **Zero-Downtime Changeover Cell**
(เปลี่ยนสูตรขวด 250 ml → 500 ml โดยไม่ต้องรื้อไลน์หรือ slow-motion)

> [!CAUTION]
> **ขอบเขตของ Min = กลไกเท่านั้น**
> ห้ามใส่ ROI / ต้นทุน / ประหยัดกี่บาท ลงในคลิปนี้เด็ดขาด — เป็นงานของเพื่อนคนอื่น

---

## 2. Path ไฟล์ทั้งหมด

### 2.1 Unity Project (Git Repo 1)

```
D:\unity_project\delta_academy\                 ← git repo หลัก
  Assets\
    Scripts\
      ChangeoverSequencer.cs                    ← state machine S1→S10, recipe 250/500 ml
      CameraDirector.cs                         ← สลับกล้องตาม state (ใช้กับคลิป B)
      TimedShotSwitcher.cs                      ← สลับกล้องตามเวลา (ใช้กับคลิป A)
      TravelingCamera.cs                        ← กล้องเดินทางเปิดคลิป A
      MotionHighlightController.cs              ← pulsing cyan glow บนราง/หัวฉีดขณะขยับ
    Editor\
      ZoneLabelsBuilder.cs                      ← world-space label อุปกรณ์รายโซน
      AClipZoneCamerasBuilder.cs                ← สร้าง 4 กล้องล็อกมุมสำหรับคลิป A
      FillingZonePropsBuilder.cs                ← Tank/Pump/FlowMeter/AntiDripValve
      InfeedZoneBuilder.cs                      ← Unscrambler/StarWheel/Sensor/Stopper
      CappingZoneBuilder.cs                     ← Cap Feeder/Capping Head
      EndOfLineBuilder.cs                       ← Checkweigher/Reject/Labeler/Outfeed
    Scenes\
      SampleScene.unity                         ← scene เดียวที่ใช้งานจริง

  Recordings\                                   ← ห้ามลบหรือทับไฟล์ต้นฉบับ!
```

**ไฟล์ต้นฉบับที่ใช้งานได้ (timestamp ถูก):**

| ไฟล์ | ความยาว | เนื้อหา |
|---|---|---|
| `A_LineOverview_DRAFT_25690914_020259.mp4` | 10.533s | Traveling establishing shot |
| `A_LineOverview_ZONES_25690914_132308.mp4` | 80.033s | 5 zone shots (เวอร์ชันสุดท้ายที่ถูก) |
| `B_Changeover_MULTICAM_25690914_132124.mp4` | 45.033s | Multicam ตัดกล้องตาม state |

> [!WARNING]
> **ไฟล์เหล่านี้ มีบั๊ก ห้ามใช้:**
> - `A_LineOverview_ZONES_25690914_063523.mp4` — บั๊กขวดทะลุเสา
> - `B_Changeover_DRAFT_25690914_013714.mp4` — เปื้อน Unity Editor gizmo เต็มจอ
> - `B_Changeover_MULTICAM_25690914_064203.mp4` — เวอร์ชันเก่า

**ไฟล์ผลลัพธ์ FINAL (พร้อมส่งจริง — ใช้ตัวที่มี ⭐ เท่านั้น ตัวอื่นเป็นเวอร์ชันก่อนแก้บั๊กเสา/nozzle height):**

| ไฟล์ | Path เต็ม | ยาว | สถานะ |
|---|---|---|---|
| `A_LineOverview_FINAL.mp4` | `Recordings\A_LineOverview_FINAL.mp4` | 90.57s | ❌ เก่า มีบั๊กเสายังไม่แก้จริง |
| `B_Changeover_FINAL_v2.mp4` / `_v3.mp4` | `Recordings\...` | 45.03s | ❌ เก่า มีบั๊กเสา+nozzle height ผิด (1123mm) |
| **`A_LineOverview_FINAL_v2.mp4`** | `Recordings\A_LineOverview_FINAL_v2.mp4` | 90.57s | ⭐ **ล่าสุด** — แก้เสาจริงแล้ว (ดู §3 ข้อ 1 รอบสอง) |
| **`B_Changeover_FINAL_v4.mp4`** | `Recordings\B_Changeover_FINAL_v4.mp4` | 45.03s | ⭐ **ล่าสุด** — แก้เสาจริง + glow ไม่เบลด + nozzle height ถูกต้อง (228mm) |

> ⚠️ **แต่ดูหัวข้อ caution บนสุดของไฟล์นี้ก่อน** — Codex อาจมีเวอร์ชันที่ใหม่กว่านี้อีกจากงานคู่ขนาน
> (เช่น `B_Changeover_VIBE5_PRO_90s.mp4`, `B_Changeover_PHASE2_FULL.mp4`) เช็ค timestamp ไฟล์จริง
> ใน `Recordings\` ก่อนใช้ตัวไหนเป็นทางการ อย่าเชื่อตารางนี้ 100% ถ้าเวลาผ่านมานานแล้ว

### 2.2 powerNote (Git Repo 2 — ระบบ agent)

```
C:\Users\wicha\Desktop\powerfull_note\
  GEMINI.md                    ← กฎ Gemini / Event-Driven listener
  CODEX.md                     ← กฎ Codex / MCP bridge
  HANDOFF.md                   ← สมองสำรองข้าม session (อ่านเพิ่มได้)
  DELTA_EDIT_PLAN.md           ← แผนตัดต่อเต็ม (timeline + ffmpeg commands)
  antigravity-wait.py          ← Gemini event-driven listener
  mcp-server.js                ← MCP server (stdio → HTTP:4321)
  scratch\
    send_delta_academy_notification.py   ← รอ Gmail re-auth ก่อนใช้
```

---

## 3. งานที่เสร็จแล้ว + กับดักสำคัญที่เจอ

### ✅ งาน A1 — Concat คลิป A (90.57s)
- ต่อ DRAFT(10.533s) + ZONES(80.033s) ด้วย `ffmpeg -f concat -safe 0 -c copy`
- ตรวจรอยต่อด้วยการสกัดเฟรม t=10.4s และ t=10.7s — สะอาด ไม่กระตุก ไม่มีเฟรมดำ

### ✅ งาน A2 — Section Title 6 อัน ลงคลิป A
ตำแหน่ง/สไตล์ทุกอัน: `x=60, y=h-110`, Arial Bold 30px, `box=1:boxcolor=black@0.55:boxborderw=14`

| ช่วง (วิ) | ข้อความ |
|---|---|
| 1.0 – 9.0 | `ZERO-DOWNTIME CHANGEOVER CELL` |
| 11.5 – 17.5 | `1 / INFEED - Unscrambler & Star Wheel` |
| 25.5 – 31.5 | `2 / FILLING - Servo Nozzle, Controlled Point` |
| 49.5 – 55.5 | `3 / CAPPING - Cap Feeder & Capping Head` |
| 59.5 – 65.5 | `4 / END OF LINE - Checkweigher, Reject, Labeler` |
| 71.5 – 77.5 | `5 / CONTROL - Delta PLC + HMI` |

ตรวจทุก title ด้วยการสกัดเฟรมจริง — ทั้ง 6 อัน PASS ทุกจุด

### ✅ งาน B2 — Callout 2 จุด ลงคลิป B
Timestamp หาด้วยการสกัดเฟรมจริงตลอด 45s — **ไม่เดา**

| ช่วง (วิ) | ข้อความ | กล้อง |
|---|---|---|
| 10.5 – 13.0 | `FILL NOZZLE - Z-axis to recipe clear height` | NozzleSideCam (S6) |
| 13.0 – 16.0 | `GUIDE RAIL - servo-positioned to recipe width` | RailTopCam (S7) |

### ✅ งานใน Unity — 4 อย่างที่ทำเสร็จแล้ว

1. **แก้บั๊กเสาบัง — 2 รอบ (รอบแรกแก้ไม่ครบ ระวังอย่าทำผิดซ้ำ)**
   - **รอบแรก (ไม่พอ):** ย้าย `CappingZoneCam` ไป `(0.55, 2.10, 1.75)` มอง `(0.00, 1.25, 1.05)`
     — นี่แค่ **ขยับกล้องหนีไม่ให้เห็น** ตัวปัญหาจริงยังอยู่ในฉาก 3D เหมือนเดิม (แก้แค่ symptom
     ในมุมกล้องเดียว ไม่ใช่แก้ root cause) — Min เจอปัญหาเดิมอีกจากมุมอื่น/คลิปอื่น พร้อมบ่นว่า
     "ขวดทะลุเสาเลย555" ยืนยันว่าโดนแค่ปิดตาไม่ให้เห็น ไม่ได้แก้จริง
   - **รอบสอง (แก้จริงแล้ว, 2026-09-14 ~18:00):** ตรวจด้วย `Renderer.bounds.Intersects()` พบว่า
     `Gantry_VerticalColumn_60x60mm` (เสาของ `FillingGantry_Stationary`, X=0.00, Z=0.75-0.81)
     **ทับกับ `GuideRail_Left/Right` และแนวเดินขวดจริงในพิกัด 3D** (ไม่ใช่แค่มุมกล้อง) — เจอว่า
     `CellBuilder.cs` **มีโค้ดแก้ไว้แล้ว** (ย้ายเสาไป X=-0.28, เปลี่ยนชื่อเป็น
     `Gantry_VerticalColumn_40x40mm`) แต่ scene ที่เซฟไว้ไม่เคยรัน `Build Full Line` ซ้ำหลังแก้โค้ด
     เลยยังใช้เรขาคณิตเก่าอยู่ — แก้โดยรัน `Tools/Delta/Build Full Line (Everything)` +
     `Add A-Clip Zone Cameras` + `Attach A-Clip Shot Switcher` + `Add Zone Equipment Labels` +
     `Attach Motion Highlights` ใหม่ทั้งหมด แล้ว save scene ทันที ยืนยันด้วย
     `bounds.Intersects()` = false และสกัดเฟรมจริงดูแล้วสะอาด
   - **บทเรียน:** เจอบั๊กแบบนี้ครั้งหน้า **ต้องเช็ค 3D bounds overlap จริงด้วย `execute_code`**
     ก่อนสรุปว่า "ขยับกล้องพอ" — การที่กล้องมองไม่เห็นปัญหาจากมุมหนึ่ง ไม่ได้แปลว่าปัญหาหายไป
     ถ้าเป็น physical collision ในพิกัดโลกจริง มันจะโผล่มาจากมุมอื่นเสมอ

2. **Label ขนาดขวด "250ml → 500ml"** — world-space label ใกล้หัวฉีด อ่านค่าสดจาก `ChangeoverSequencer` ไม่มีวันเพี้ยน

3. **Label ชื่ออุปกรณ์แต่ละโซน** (ผ่าน `ZoneLabelsBuilder.cs`) — Infeed: Unscrambler/Star Wheel/Sensor/Stopper; Filling: Product Tank/Pump/Flow Meter/Anti-Drip Valve; Capping/EndOfLine มีอยู่แล้ว

4. **Glow Highlight Effect** (`MotionHighlightController.cs`) — pulsing cyan emissive glow บนราง/หัวฉีดตอนขยับจริง (S6/S7/S9) + ตัวเลข mm สด; เมนู `Tools/Delta/Attach Motion Highlights`

---

## 4. กับดักสำคัญที่เจอระหว่างทาง (ต้องจำ)

> [!CAUTION]
> **กับดัก 1 — Scene ไม่เคยถูก Save**
> Builder menu item ทุกตัวที่รันไปตลอดคืน **ไม่เคยมีใครกด Save Scene** ของทั้งหมดอยู่ใน RAM ของ Editor เท่านั้น พอเข้า Play Mode (Recorder ต้องเข้า Play Mode) Unity revert กลับสถานะก่อน Play → ของหายเงียบๆ ทั้งหมด
>
> **กฎบังคับ:** หลังรัน builder menu item ใดๆ ต้อง `mcp__unityMCP__manage_scene action:save` ก่อนเข้า Play Mode หรือ render ทุกครั้ง

> [!CAUTION]
> **กับดัก 2 — Screen Space Overlay ไม่ติดในคลิป**
> `TelemetryOverlayController` + `LeaderLineOverlay` ที่ทำไว้แต่แรกใช้ **Screen Space - Overlay canvas** ซึ่ง Recorder (RenderTexture-based) ไม่จับภาพเลย
>
> **สำหรับทุก label/overlay ที่ต้องติดในคลิปจริง ต้องใช้ world-space TextMeshPro เท่านั้น** (แบบที่ ZoneLabelsBuilder/MotionHighlightController ใช้) — ห้ามใช้ Canvas UI แบบ Screen Space อีก

> [!NOTE]
> **กับดัก 3 — sharedMaterial vs material**
> - `renderer.material` → Unity clone material ใหม่ทันที (unique ต่ออุปกรณ์ ✅ ถ้าต้องการ glow เฉพาะชิ้น)
> - `renderer.sharedMaterial` → แก้ทุก instance ที่ใช้ material เดียวกัน ✅ ถ้าต้องการเปลี่ยนทั้งหมด

> [!NOTE]
> **กับดัก 4 — กล้อง 2 ระบบแย่งกันเงียบๆ**
> `CameraDirector` (state-based, สำหรับคลิป B) กับ `TimedShotSwitcher` (time-based, สำหรับคลิป A) อยู่ใน GameObject เดียวกัน ตอนเรนเดอร์คลิป A ต้องตั้ง `CameraDirector.autoSwitchOnState = false` ก่อน ไม่งั้น LateUpdate ของ CameraDirector จะทับคำสั่ง TimedShotSwitcher เงียบๆ — ffprobe ผ่าน แต่เนื้อภาพผิด

> [!CAUTION]
> **กับดัก 6 — MotionHighlightController เบลดข้ามคลิป (เจอ+แก้แล้ว 2026-09-14 ~18:05)**
> `ChangeoverSequencer` วิ่งวนลูปตลอดเวลาใน Play Mode **ไม่ว่าจะกำลังเรนเดอร์คลิปไหนอยู่** — ตอน
> เรนเดอร์ A_LineOverview (ใช้ `TimedShotSwitcher`) ถ้า sequencer บังเอิญวิ่งไปถึง S6/S7/S9 พอดี
> `MotionHighlightController` (ทำไว้สำหรับ B_Changeover เท่านั้น) จะ trigger glow + label mm
> เบลดเข้าไปในเฟรมของ A ด้วย (เจอจริงจากการสกัดเฟรม — เห็น "NOZZLE HEIGHT" ลอยเรืองแสงกลาง
> Filling Zone shot ทั้งที่ไม่เกี่ยวกัน) **แก้แล้ว:** เพิ่ม `s_MotionHighlight.enabled = false` ใน
> `StartZoneRecordingNow()` (ปิดทั้ง component ระหว่างเรนเดอร์ A) แล้ว restore กลับใน
> `CleanupZoneSequenceRenderTexture()` เหมือนแพทเทิร์น `autoSwitchOnState` ของ `CameraDirector`
> ทุกประการ (`Assets/Editor/RecorderSmokeTest.cs`)
>
> **บทเรียนกว้างกว่านั้น:** ทุกครั้งที่เพิ่ม MonoBehaviour ใหม่ที่ผูกกับ `ChangeoverSequencer.CurrentState`
> (เช่นงาน 9.5 เส้น before/after รางที่กำลังจะทำต่อ) **ต้องเพิ่มการปิด/เปิดมันในทั้ง 2 ฟังก์ชันเรนเดอร์
> เสมอ** (`StartZoneRecordingNow` สำหรับ A, `StartMulticamRecordingNow` สำหรับ B) ไม่งั้นจะเบลด
> ข้ามคลิปแบบเงียบๆ อีก — `ffprobe` ตรวจไม่เจอ ต้องสกัดเฟรมดูเท่านั้น

> [!NOTE]
> **กับดัก 5 — ffmpeg Windows: escape colon ใน path ฟอนต์**
> ```
> ✅ ถูก: fontfile='C\:/Windows/Fonts/arialbd.ttf'
> ❌ ผิด: fontfile='C:/Windows/Fonts/arialbd.ttf'  ← ffmpeg parse C: เป็น protocol แล้ว error งงๆ
>
> ✅ ถูก: text='FILL NOZZLE - Z-axis to ...'   ← dash ธรรมดา
> ❌ ผิด: text='FILL NOZZLE — Z-axis to ...'   ← em dash ทำ encoding error บน Windows build
> ```

---

## 5. งานที่ยังไม่เสร็จ / รอตัดสินใจ

### 5.1 Task B1 — ยืดคลิป B เป็น 90s

> [!IMPORTANT]
> **ถามก่อน อย่าทำ:** 90s เป็นข้อกำหนดจริงของการแข่ง หรือเป็นแค่ตัวเลขประมาณ?
> ถ้า 45s ใช้ได้ → ไม่ต้องยืดเลย คลิป 45s ที่กระชับดีกว่าคลิป 90s ที่ยืด

ถ้า Min ยืนยันต้องการ 90s — แผนที่แนะนำ (รวม ~90s):
1. การ์ดเปิด 6s: `RECIPE CHANGEOVER: 250ml → 500ml` / `No line teardown. No manual shimming.`
2. คลิป B ช่วงแรก 0–22s (หยุดป้อนขวด, เติมขวดค้างท่อ, เคลียร์โซน)
3. การ์ดคั่น 5s: `SAFETY INTERLOCK: nozzle retracts to home BEFORE rails move`
4. คลิป B ช่วงหลัง 22–45s (ปรับรางกว้าง, ปรับความสูงหัวฉีด, First Article Check)
5. การ์ดปิด 6s: `ONE RECIPE SELECT → SERVO-POSITIONED. REPEATABLE EVERY TIME.`

> [!CAUTION]
> ห้ามยืด B ด้วย slow motion 2x — คลิปนี้ขายเรื่อง "เปลี่ยนรุ่นได้เร็ว" การทำให้ดูช้าลงทำลายสารหลัก

### 5.2 งานนอก Unity ที่อาจยังต้องการ

- **3 ความยาว** — Min เคยขอ (~90s / 45s / 1 นาที) ยังไม่ได้ทำจริง
- **เพลงประกอบ** — ยังไม่มีการตัดสินใจ
- **ส่งอีเมลสรุปงาน** — `scratch/send_delta_academy_notification.py` พร้อมแล้ว แต่ Gmail OAuth token หมดอายุตั้งแต่ 2026-08-25 (`invalid_grant`) ต้อง Min re-auth ใหม่ก่อน

---

## 6. เครื่องมือที่ใช้ได้จริงบนเครื่อง

| เครื่องมือ | สถานะ | หมายเหตุ |
|---|---|---|
| `ffmpeg` | ✅ | v8.1.2-full_build-www.gyan.dev |
| `ffprobe` | ✅ | ใช้ตรวจ metadata เบื้องต้น แต่ไม่เพียงพอ — ต้องดูเฟรมจริงด้วยเสมอ |
| `unityMCP` | ✅ | `execute_blender_code` / `manage_scene` ฯลฯ |
| PowerNote API | ✅ | `http://127.0.0.1:4321` (ต้องรันอยู่) |
| Gmail send | ❌ | OAuth token expire 2026-08-25, ต้อง re-auth ก่อน |

---

## 7. กฎการทำงาน (5 ข้อ)

> [!IMPORTANT]
> **กฎ 1 — ตรวจด้วยเฟรมจริงเสมอ (ไม่ใช่แค่ ffprobe)**
> บั๊กทุกตัวในโปรเจกต์นี้ (ขวดทะลุเสา / ตัวหนังสือกลับด้าน / ตัวหนังสือเล็กมองไม่เห็น / gizmo ติดเต็มจอ / โซน EndOfLine หาย 12 วิ) **ไม่มีตัวไหนเลยที่ ffprobe จับได้**
>
> ทุกครั้งที่สร้าง output ใหม่:
> 1. สกัดเฟรมออกมาดูด้วยตาจริงที่จุดเปลี่ยนช็อตทุกจุด + ทุกจุดที่มีข้อความขึ้น
> 2. เช็คว่าข้อความ: อ่านออก / สะกดถูก / ไม่ล้นจอ / ขึ้น-ลงตรงเวลา
> 3. รายงานว่าตรวจเฟรมไหนบ้าง (บอกเป็นวินาที) ไม่ใช่แค่บอกว่า "เสร็จแล้ว"
> 4. **ตรวจตลอด timeline ไม่ใช่แค่ตอนต้น** — บั๊ก EndOfLine อยู่ที่ t=55s ตรวจแค่ t=5 และ t=25 จะไม่เจอเลย

> [!IMPORTANT]
> **กฎ 2 — ห้ามลบหรือทับไฟล์ต้นฉบับ**
> ทุกไฟล์ที่มี timestamp ในชื่อใน `Recordings\` แตะไม่ได้ — สร้างไฟล์ผลลัพธ์ใหม่เสมอ

> [!IMPORTANT]
> **กฎ 3 — ถามก่อนเดา**
> เวลาที่วาง callout ใน ffmpeg ต้องสกัดเฟรมหาเวลาจริงก่อน
> ถ้ามีคำถามที่ต้องการ Min ตัดสินใจ (เช่น เรื่องความยาว B1) → ถาม อย่าลงมือทำก่อน

> [!NOTE]
> **กฎ 4 — Save Scene ทุกครั้งหลัง build**
> `mcp__unityMCP__manage_scene action:save` ทันทีหลังรัน builder menu item ใดๆ

> [!NOTE]
> **กฎ 5 — World-space TextMeshPro เท่านั้นสำหรับ overlay ในคลิป**
> Screen Space - Overlay canvas ไม่ถูกจับโดย Recorder ทุก label/overlay ต้องเป็น world-space TMP เสมอ

---

## 8. 🆕 อุปกรณ์ Delta จริงทั้งหมด — สเปกเต็ม (จากรูปที่ Min ส่งมา)

Min ส่งรูป 4 รูปที่ `D:\Downloads\image.png`, `image2.png`, `image3.png`, `image4.png`
(สรุป/ transcribe ไว้ครบด้านล่างแล้ว **ไม่ต้องเปิดรูปเองก็ทำงานได้**) — ใช้ชื่อรุ่น/ตัวเลขพวกนี้
**เป๊ะๆ** ทุกครั้งที่ทำ label หรือคลิปแนะนำอุปกรณ์ (งาน 9.1 ด้านล่าง) ห้ามเดาหรือเปลี่ยนชื่อรุ่นเอง

### 8.1 สถาปัตยกรรมระบบ (จาก image.png)

```
Delta DIACloud Platform  ← Changeover & CIP Verification Log
        │ Ethernet (Modbus TCP)
        ▼
PLC Delta AS320T-B  ← Recipe Controller (5 Parameters Table), High-Speed Counter for Fill Flow Meter
        │                                              │
        │ Ethernet (Modbus TCP)                        │ RS-485 (Modbus RTU)
        ▼                                              ▼
HMI Delta DOP-100WS / 103WQ                    VFD Delta MS300
- One-Touch Changeover (250/500/1000ml)        - Conveyor Speed Profile
- CIP Step Verification Checklist              - Smooth Ramp (Anti-Tipping)
        │ Pulse Train / PR Mode
        ├──────────────────────────┐
        ▼                          ▼
SERVO ASD-A3 – Axis X       SERVO ASD-A3 – Axis Z
Guide Rail Width Adjuster   Nozzle Height & Dive Filling
(ปรับความกว้างตามเส้น       (ยกตามระดับของเหลวเพื่อลดฟอง)
ผ่านศูนย์กลางขวด)
```

### 8.2 ตารางสเปกเต็ม (จาก image2.png)

| Delta Model | ประเภท | เหตุผลที่เลือก | หน้าที่ในระบบ |
|---|---|---|---|
| **AS320T-B** ⭐ | PLC (Central Controller) | CPU 40k steps/ms, Ethernet+RS-485 ในตัว, High-Speed Pulse Output คุม Servo 2 แกน, High-Speed Counter อ่าน Flow Meter | ศูนย์กลางควบคุมระบบ: เก็บ Recipe Table (5 พารามิเตอร์), คุม Sequence เปลี่ยนรุ่น, คำนวณปริมาณเติม, คุม Anti-Drip, Safety Interlock |
| **DOP-100WS / 103WQ** ⭐ | HMI (Touchscreen) | จอกว้างความละเอียดสูง รองรับ Recipe Function ใน DIAScreen โดยตรง, User Level, หน้า Diagnostics | หน้าจอสั่งการ+เลือกรุ่น: ปุ่ม One-Touch สลับขนาด (250/500/1000ml), แสดงพิกัดจริงแต่ละแกน, ตัวจับเวลา Changeover, หน้า Checklist ยืนยัน CIP |
| **ASD-A3 (×2)** ⭐ | AC Servo Drive + Motor | 24-bit Absolute Encoder จำตำแหน่งได้แม้ไฟดับ, PR Mode สั่งตำแหน่งสัมบูรณ์แม่นยำ ±0.01mm โดยไม่ต้องเขียน Motion ซับซ้อน | แกน X: ปรับความกว้าง Guide Rail ตามเส้นผ่านศูนย์กลางขวด ป้องกันขวดติด/ล้ม | แกน Z: ปรับระดับความสูง Nozzle + Dive Filling ยกตัวจ่ายตามระดับน้ำเพื่อลดฟอง |
| **MS300** ⭐ | AC Motor Drive (VFD) | สื่อสาร Modbus RTU, คุมความเร็วละเอียด 0.01Hz, ตั้งค่า S-Curve Accel/Decel นุ่มนวล | คุมความเร็วสายพาน (Conveyor Speed): ปรับความเร็ว+Ramp Time ตามน้ำหนักขวด ป้องกันขวดล้ม/ซิงค์กับ Cycle Time |
| **CliQ-M (24V 10A)** | Power Supply 24VDC | ประสิทธิภาพ >94%, Power Boost 150% นาน 5 วิ, ป้องกันสัญญาณรบกวนในตู้คอนโทรล | จ่ายไฟ 24VDC ให้ PLC, HMI, เซนเซอร์ (Bottle Present Sensor, Solenoid Stopper Cylinder, Anti-Drip Valve) |
| **DIACloud / DX-Series** | IIoT Platform & Cloud Router | คลาวด์มาตรฐาน Delta ไม่ต้องตั้ง Server เอง มอนิเตอร์ผ่านมือถือได้ | เก็บ Log เวลา Changeover ทุกวินาที, คำนวณ OEE, บันทึกประวัติล้าง CIP, แจ้งเตือนซ่อมบำรุงล่วงหน้า |

**⭐ = อุปกรณ์หลัก 4 ชนิดที่ใช้ในการอบรม (PLC/HMI/SERVO/VFD) ใช้ครบทุกตัวและทำงานร่วมกันจริง**
— นี่คือ 4 ชนิดที่งาน 9.1 (คลิปแนะนำอุปกรณ์) ต้องโฟกัส

### 8.3 ความสัมพันธ์ 5 พารามิเตอร์ใน Recipe กับอุปกรณ์ (จาก image3.png)

| # | พารามิเตอร์ | ควบคุมโดย | เหตุผล |
|---|---|---|---|
| 1 | **Guide Rail Width** (ความกว้างรางกั้น) | Servo ASD-A3 แกน X | ขวด 250/500/1000ml เส้นผ่านศูนย์กลางต่างกัน รางกว้างไปขวดส่ายจนหัวจ่ายเติมไม่ตรงปากขวด รางแคบไปขวดติดจนไลน์หยุด |
| 2 | **Nozzle Height** (ความสูงหัวจ่าย) | Servo ASD-A3 แกน Z | ของเหลวเกิดฟองง่ายถ้าปล่อยตกจากที่สูง (Foaming Issue) → ปรับความสูงตามขนาดขวด + ทำ Bottom-Up/Dive Filling (จุ่มลงใกล้ก้นขวดแล้วค่อยๆ ยกขึ้นตามระดับของเหลว) |
| 3 | **Conveyor Speed** (ความเร็วสายพาน) | VFD MS300 | ขวด 1000ml หนักกว่าขวด 250ml ถึง 4 เท่า ถ้าเดินสายพานเร็วเท่าเดิมตอนเบรกที่ Stopper ของเหลวจะกระฉอกหรือขวดล้ม |
| 4 | **Fill Volume** (ปริมาณบรรจุ) | PLC AS320T-B + Flow Meter | ค่าที่ต่างกันชัดเจนที่สุด PLC รับสัญญาณ High-Speed Pulse จาก Flow Meter เมื่อครบปริมาณสั่งปิดวาล์ว Anti-Drip ทันที |
| 5 | **Fill Speed Profile** (โปรไฟล์ความเร็วการสูบจ่าย) | PLC AS320T-B + Product Pump | ของเหลวหนืดต้องเริ่มจ่ายช้า → เร่งความเร็วกลางขวด → ชะลอความเร็วช่วงปิดปากขวด เพื่อป้องกันไม่ให้ผลิตภัณฑ์ล้นทะลัก |

### 8.4 ขอบเขตโครงการตามหลัก SMED (จาก image4.png — สำคัญมากสำหรับสคริปต์บรรยาย)

- **Format Changeover** (เปลี่ยนขนาดขวด ในสูตรเดิม) — **อยู่ในขอบเขตโครงการ 100%** เป็นงานที่
  เกิดขึ้นบ่อยที่สุดในโรงงาน ระบบ Delta เปลี่ยนตำแหน่ง Guide Rail, Nozzle Height, Conveyor Speed,
  Fill Volume จบใน **≤ 5 นาที** (จากเดิมช่างขันน็อต 45 นาที) — **นี่คือประเด็นที่คลิปต้องขายเรื่องนี้**
- **Product Changeover** (เปลี่ยนสูตรผลิตภัณฑ์ที่ต้องล้างท่อ CIP) — **อยู่นอกขอบเขตการควบคุมกลไก
  โดยตรง** (CIP เป็นงานเดินท่อ สารเคมี น้ำร้อน คนละสายกับ Motion Control) แต่ระบบ Zero-Downtime
  ช่วยสนับสนุนได้ 2 ทาง:
  1. Verification Checklist — HMI มีขั้นตอน verify การล้าง CIP ก่อน ไม่ยอมให้ไลน์เดินถ้ายังล้างไม่เสร็จ
  2. Parallel Setup (แปลง Internal เป็น External Setup) — ระหว่าง CIP กำลังล้างท่ออยู่ กลไก Servo
     เลื่อนปรับรางกั้น+หัวจ่ายคู่ขนานไปพร้อมกันได้เลย ประหยัดเวลารวม

**ทำไมส่วนนี้สำคัญ:** ถ้ากรรมการถามว่า "แล้ว CIP ล่ะ ทำไมไม่โชว์" คำตอบคือ **ตั้งใจไม่โชว์เพราะรู้ขอบเขต
ของตัวเอง** ไม่ใช่คิดไม่ถึง — นี่คือมุมที่ทำให้ presentation ดูเข้าใจงานจริง ไม่ใช่ทฤษฎีในห้องเรียน

---

## 9. 🆕🆕 งานใหม่จาก Min (2026-09-14 ~17:40) — ยังไม่เริ่มทำสักข้อ

Min เขียนข้อความยาวรวดเดียว (ผสมไทย/อังกฤษ) สรุปเป็น 5 ข้อ เรียงตามที่พูดถึง:

### 9.1 คลิปแนะนำอุปกรณ์แยกต่างหาก (HMI, PLC, VFD, Servo)

> "อยากให้เรามีการทําคริปแยกไปเลย ที่อธิบาย ตัวhmi plc vdf servo ว่ารุ่นอะไร ชื่ออะไร แล้วก็ตัดให้มี
> รูปมาให้ดูด้วย โดยอยากได้ model 3D ที่เหมือนจริง ใน unity แล้ว pan กล้องนำเสนอแต่ละตัว โดยเมื่อพูดถึง
> อันไหนก็ให้ part นั้นเรืองแสง กระพริบๆ"

**สิ่งที่ต้องทำ:**
1. คลิปใหม่แยกจาก A/B (คลิปที่ 3) — แนะนำอุปกรณ์หลัก 4 ชนิด: **PLC AS320T-B, HMI DOP-100WS/103WQ,
   VFD MS300, Servo ASD-A3 (×2)** — ใช้สเปก/ชื่อรุ่นจาก §8 เป๊ะๆ
2. **โมเดล 3D ต้อง "เหมือนจริง" มากกว่าที่มีตอนนี้** — ของปัจจุบันในฉากเป็น blockout ง่ายๆ
   (กล่อง/ทรงกระบอกพื้นฐาน) ไม่ได้พยายามเลียนแบบหน้าตาอุปกรณ์ Delta จริง — งานนี้ต้องการ detail
   มากกว่าเดิม (ปุ่ม, จอ, ช่องระบายอากาศ, ป้ายชื่อรุ่น ฯลฯ ตามภาพจริงของ Delta ถ้าหาอ้างอิงได้)
   **Min บอกว่า Gemini ทำไปแล้วบางส่วนแต่ยังไม่โอเค ให้ตรวจสอบ** — เช็คว่า Gemini แก้โมเดลไหนไปแล้ว
   บ้างก่อนเริ่มทำซ้ำ (ดู git log ล่าสุดของ `D:\unity_project\delta_academy`)
3. **กล้อง pan นำเสนอทีละตัว** — คล้ายแพทเทิร์น `TravelingCamera.cs`/`TimedShotSwitcher.cs` ที่มี
   อยู่แล้ว แต่คราวนี้ target คืออุปกรณ์ควบคุม ไม่ใช่โซนผลิต
4. **Highlight/กระพริบ sync กับเสียงบรรยาย** — ใช้แพทเทิร์นเดียวกับ `MotionHighlightController.cs`
   (pulsing emissive glow) แต่ trigger ด้วย timeline/index ของสคริปต์บรรยาย ไม่ใช่ ChangeoverSequencer
   state (เพราะคลิปนี้ไม่มี state machine ให้ผูก) — ต้องออกแบบระบบ trigger ใหม่ เช่น
   `EquipmentIntroSequencer.cs` ที่มี list ของ (equipment, holdDuration) คล้าย `TimedShotSwitcher`
   แต่เพิ่ม glow บนอุปกรณ์นั้นด้วยตอน active

### 9.2 บั๊กเสาบัง+ขวดทะลุ — **แก้จริงแล้วในเซสชันนี้** (ดู §3 ข้อ 1 ด้านบน)

ไม่ต้องทำอะไรเพิ่ม เว้นแต่เจอเคสใหม่อีก (ถ้าเจอ ให้เช็ค `bounds.Intersects()` ก่อนเสมอ ตามบทเรียนที่เขียนไว้)

### 9.3 UI จำลองหน้าจอ HMI ตอนเปลี่ยน Recipe

> "อยากให้นำเสนอช่วงเปลี่ยน recipe ด้วย ทำเป็น UI เสมือนแล้วกดเลือกมาแล้วก็บอกว่าเปลี่ยนแล้ว"

Min อยากเห็น **หน้าจอ HMI จำลอง** (DOP-100WS/103WQ ตาม §8.2) ที่มีปุ่ม One-Touch Changeover
ให้กด (หรือแสดงการกดจำลอง) เลือกขนาดขวด (250/500/1000ml) แล้วขึ้นข้อความยืนยัน "Recipe Changed"
หรือคล้ายกัน — นี่คือฟีเจอร์จริงของ HMI ตามสเปก ("One-Touch Changeover") **ควรอ้างอิงโครงตาม
`DeltaHMIDisplay.cs` ที่มีอยู่แล้ว** (แสดง RECIPE: 250ml → 500ml, checklist ฯลฯ) — ขยายให้มี
"หน้าจอเลือกก่อนกด" + "หน้าจอยืนยันหลังกด" แบบ sequence 2 สเต็ป ไม่ใช่แค่ static readout เหมือนตอนนี้

**⚠️ ข้อควรระวัง (จากกับดัก #2 ในไฟล์นี้):** UI นี้ต้องโผล่ในคลิปที่เรนเดอร์จริง → **ห้ามใช้ Screen
Space - Overlay Canvas** ต้องเป็น world-space (เช่น จอ HMI จริงในฉาก 3D ที่มี RenderTexture/Canvas
แบบ World Space ติดอยู่บนตัวจอ ไม่ใช่ overlay ลอยเหนือจอเกม)

### 9.4 ตู้คอนโทรล (Control Cabinet) ดูไม่สมประกอบ

> "กล่อง cabin ดูไม่สมประกอบ ดูมุมอื่นๆ ก็เห็นว่ามันแปลกมันยุ่งไปหมด ทำเป็นตู้ดีๆ หน่อย"

**ยืนยันแล้วด้วยสายตาจริง (screenshot จาก `ControlCam_Close`, 2026-09-14 ~18:00):** ตัวถังคอนโทรล
มีปัญหาจริง — panel/ประตูดูเหมือนแผ่นลอยแยกกัน ไม่ต่อเนื่องเป็นตู้เดียว, จอ HMI (สี่เหลี่ยมฟ้า) ดูเหมือน
กล่องแยกลอยติดผนังมากกว่ามอนิเตอร์ฝังบนหน้าตู้, มุมกล้องบางมุมมีถังเก็บ (tank) บังตู้บางส่วนจน
composition ดูรก — ต้องไปดูโค้ดที่ `Assets\Editor\DeltaControlPropsBuilder.cs` (ตัวสร้าง
`DeltaControlCabinet`) แล้วออกแบบใหม่ให้:
1. ผนัง/ประตูตู้เป็นกล่องเดียวที่สมส่วน (ไม่ใช่แผ่นหลายแผ่นต่อกันแบบเห็นรอยต่อ)
2. จอ HMI DOP-100WS/103WQ ฝังเรียบกับหน้าตู้จริง ไม่ลอยเป็นกล่องแยก
3. เช็คตำแหน่งไม่ให้ tank/อุปกรณ์อื่นบังตู้จากมุมกล้องหลักที่ใช้เรนเดอร์ (`ControlCam_Close`)

### 9.5 Animation รางขยาย — อยากได้เส้น before/after

> "animation รางขยาย อยากให้มีเส้นตัดบอกด้วยว่า ตอนแรกมันอยู่ตรงนี้ แล้วมันขยายออกไปตรงนี้ จะทำให้
> สายตาคนดูดูง่ายขึ้น"

ตอนนี้ `MotionHighlightController.cs` (§3 ข้อ 4) ทำ glow + ตัวเลข mm สดแล้ว แต่ Min อยากได้เพิ่ม
**เส้น/มาร์กเกอร์แสดงตำแหน่งเดิม vs ตำแหน่งใหม่แบบ side-by-side ให้เห็นระยะที่เปลี่ยนชัดๆ** เช่น:
- เส้นประ (dashed line) ที่ตำแหน่งรางเดิมค้างไว้ทั้ง段 (ghost/afterimage ของตำแหน่งเก่า) แล้วเส้นทึบ
  ที่ตำแหน่งปัจจุบันขยับตาม railGap จริง
- หรือ bracket/caliper ⟵――――⟶ วัดระยะระหว่างตำแหน่งเก่ากับใหม่ พร้อมตัวเลข delta (เช่น "+15mm")

**แนะนำ:** ทำเป็นส่วนขยายของ `MotionHighlightController.cs` — วาดเส้น/gizmo ด้วย `LineRenderer`
(world-space, สีจาง/dashed สำหรับตำแหน่งเดิม, สีสว่างสำหรับตำแหน่งปัจจุบัน) วางไว้ข้าง
`GuideRail_Left/Right` เปิดเฉพาะตอน `S7_AdjustRailWidth` เหมือน glow effect ที่ทำไปแล้ว —
อ่านค่าตำแหน่งเริ่มต้น/ปลายทางจาก `ChangeoverSequencer` (`currentRecipe.railGap` →
`targetRecipe.railGap`) ไม่ใช่ hardcode ตัวเลข

---

## Appendix — Timeline ช็อตของ B_Changeover_MULTICAM (45.03s)

| ช่วง | กล้อง | เนื้อหา |
|---|---|---|
| 0.0 – 10.5s | CellCam_Hero | S1–S5: in-flight fill & belt clear |
| 10.5 – 13.0s | NozzleSideCam | S6: Z-axis servo retracts nozzle to 1.25m home |
| 13.0 – 16.0s | RailTopCam | S7: X-axis servo widens rails 58mm → 73mm |
| 16.0 – 17.5s | ControlCam_Close | S8: HMI checklist & in-position confirm |
| 17.6 – 32.0s | NozzleSideCam | S9: First article 500ml test bottle dive-fill |
| 32.0 – 45.0s | CellCam_Hero | S10: Full 500ml continuous production |
