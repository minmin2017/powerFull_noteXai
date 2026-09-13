# HANDOFF — สมองสำรองข้าม session

## ⚠️ หมายเหตุด่วน (2026-09-14 ~03:50) — ws-inbox listener ตายจาก OOM ระบบ ไม่ใช่บั๊กโค้ด

ระบบแรมเต็มจริง (เหลือ ~1.18GB จาก 16GB ตอนเช็คล่าสุด, ลดลงเรื่อยๆ) ทำให้ `ws-inbox.js`
ถูก Windows ฆ่าทิ้งซ้ำ 2 รอบติดกันทันทีที่เปิดใหม่ — **เช็คแล้วไม่ใช่ process ค้าง/รั่วจากงาน
Delta Academy คืนนี้** ต้นเหตุคือ `whisper_worker.py large-v3-turbo` (~1.95GB) ที่เพิ่งเริ่มรัน
~03:50 — เป็น service ถอดเสียงของแอปเอง (ฟีเจอร์ voice/PTT) ไม่ใช่ของที่ผมสร้าง **ไม่ได้ไปฆ่าทิ้ง
เพราะไม่รู้ว่า Min ต้องใช้อยู่ไหม** ถ้า session หน้าเปิดมาแล้ว inbox ไม่ตอบสนอง ให้เช็คแรมก่อน
(`Get-CimInstance Win32_OperatingSystem`) แล้วค่อยรีสตาร์ท `ws-inbox.js main` ใหม่

---

## 🆕🆕 อัปเดต (2026-09-14 กลางดึก) — Parallel agent (agy) + Recorder พิสูจน์ใช้ได้จริง

**บริบท:** เหลือเวลา 1-3 วันก่อนนำเสนอ (Min ยืนยัน) — เปลี่ยนโหมดจาก "Claude คุม Gemini ทีละงาน"
มาเป็น **"แตก agent ขนานจริง 5 ตัว แต่ละตัวเรียก `agy` headless เอง"** ผ่าน git worktree แยกกัน
(กัน conflict กับ Unity Editor ที่เปิดค้างอยู่จริง — เรียนรู้จากเหตุการณ์ค้าง 10 นาทีคืนก่อน)

**แผนเต็มของรอบนี้:** `C:\Users\wicha\.claude\plans\deep-knitting-pudding.md`

### บั๊กสำคัญที่แก้ก่อนอื่น
`ChangeoverSequencer.cs` ตั้งค่าเริ่มต้นสาธิต **500ml→1000ml** ทั้งที่โจทย์จริง/ช็อตลิสต์ต้องการ
**250ml→500ml** — แปลว่า Play Mode ที่ Codex ตรวจก่อนหน้าทั้งหมด verify ผิดคู่ recipe มาตลอด
แก้แล้ว (`initialRecipeIndex=0, targetRecipeIndex=1`) commit `53c8603`

### งานที่ agent ทำสำเร็จ (5 ตัวขนาน ผ่าน agy ใน worktree แยก แล้ว merge เข้า main ทุกตัว)
| Agent | งาน | ผลลัพธ์ |
|---|---|---|
| 1 | กล้อง RailTopCam/NozzleSideCam + `CameraDirector.cs` สลับตามสถานะ + telemetry (`CurrentRailGapMm`/`CurrentNozzleHeightMm`) + checklist HMI เพิ่ม 2 แถว | ✅ merge, build ผ่าน, "Attach Camera Director" เข้า Build Full Cell แล้ว |
| 2 | `LeaderLineOverlay.cs` — ระบบป้าย+เส้นโยง screen-space ใช้ซ้ำได้ พร้อม test scaffold | ✅ merge (เจอ error `enableWordWrapping` obsolete → Claude แก้เอง 1 บรรทัด) |
| 3 | `FillingZonePropsBuilder.cs` — Tank/Pump/FlowMeter/AntiDripValve/PipeRun ต่อเข้า nozzle จริง | ✅ merge (ล่มเงียบ 2 รอบก่อนสำเร็จ — ดูบทเรียนด้านล่าง) |
| 4 | `InfeedZoneBuilder.cs` — Unscrambler/สายพาน/StarWheel/Sensor/Stopper | ✅ merge สำเร็จรอบแรก |
| 5 | `CappingZoneBuilder.cs` + `EndOfLineBuilder.cs` — blockout ประหยัดสุด | ✅ merge สำเร็จรอบแรก |

### บั๊กที่ Claude เจอ+แก้เองหลัง merge (ไม่ใช่ agent)
1. **TMP API obsolete** (`enableWordWrapping`→`textWrappingMode`) — แก้ 1 บรรทัด
2. **ถังชนตู้คอนโทรลจริง** (3D bounding box ทับกัน) — เจอเพราะ Claude เช็ค bounds ด้วยโค้ดจริง
   ไม่ใช่แค่ดูภาพ (ภาพมุมกว้างตอนแรกดูไม่ออกว่าทับกัน) แก้ด้วยการขยับ Z -1.8m (แค่แกนเดียวพอ
   เพราะ AABB แยกกันแค่แกนเดียวก็พอไม่ชน) **บทเรียนสำคัญ:** การ set `child.transform.position`
   (world) หลัง parent มีค่า offset จะ "ลบล้าง" offset ของ parent อัตโนมัติ (Unity คำนวณ
   localPosition ใหม่ให้ตรงกับ world ที่สั่ง) ต้องใส่ offset เป็น **post-processing step หลังสุด**
   ไม่ใช่ตั้งก่อนสร้าง children
3. **ลำดับ build พัง** — เผลอเรียก "Build Full Cell" (ตัวทำลายล้างที่ wipe ทุก root) หลังจากที่
   Infeed/Capping/EndOfLine ถูกสร้างไปแล้ว ทำให้หายหมด ต้องสร้างใหม่ทั้ง 3 → **แก้ระบบด้วยการเพิ่ม
   เมนู `Tools/Delta/Build Full Line (Everything)`** ที่ chain ทุกอย่างตามลำดับที่ถูกต้องในคลิกเดียว

### 🔴 บทเรียน: agy job ล่มเงียบแบบ log ว่างเปล่า (เจอ 2 ครั้งจริงคืนนี้)
Agent3 (Filling zone) กับ agent รีวิว "industry fudamentals" ล่มโดย exit code 0 แต่ log แทบว่างเปล่า
ทั้งที่ preflight probe (`agy -p "Reply OK"`) ผ่านปกติในไดเรกทอรีเดียวกัน — ไม่ใช่ auth/worktree พัง
**ทางแก้ที่ได้ผล:** เปลี่ยนจาก shell `&` + manual redirect เป็น **harness-tracked background**
(`run_in_background: true` ของ Bash tool) — ให้ผลลัพธ์เต็มจริงทันทีที่เสร็จ ไม่มีปัญหาซ้ำ
→ **ใช้ harness background เสมอสำหรับ agy job ยาว อย่าใช้ shell `&` + redirect เอง**

### Recorder pipeline — พิสูจน์ใช้งานได้จริงแล้ว (จุดเสี่ยงสูงสุดที่ไม่เคยทดสอบมาก่อน)
`Assets/Editor/RecorderSmokeTest.cs` — **ค้นพบสำคัญ:** `RecorderController.PrepareRecording()`
**ต้องอยู่ใน Play Mode เท่านั้น** (throw exception ถ้าเรียกตอน Edit Mode) — แก้ script ให้เข้า
Play Mode อัตโนมัติก่อน (ผ่าน `EditorApplication.playModeStateChanged` callback) แล้วค่อยเริ่มอัด
**ยืนยันด้วย ffprobe จริง:** ได้ไฟล์ H.264 640×360 **30fps ตรงเป๊ะ** 2.03 วินาที (ขอ 60 เฟรม@30fps)
— pipeline ใช้งานได้จริงบน GTX 1650 เครื่องนี้ พร้อมขยายเป็นเรนเดอร์จริง 1920×1080

### Git worktree pattern ที่ใช้ได้ผลดีมากคืนนี้
`D:\unity_project\delta_academy` เป็น git repo ของตัวเอง (`github.com/minmin2017/delta_academy`)
สร้าง worktree แยก 5 อัน (`D:\unity_project_worktrees\agent{1-5}-*`) คนละ branch จาก main —
agent เขียนไฟล์ใหม่ในนั้นโดยไม่แตะ Unity Editor ที่เปิดอยู่จริงเลย (กันปัญหา external-file-change
ขณะ Editor เปิดที่เคยทำให้ค้าง 10 นาที) Claude เป็นคน `git merge` เข้า main ทีละตัว + `refresh_unity`
+ ตรวจจริงก่อนไปตัวถัดไปเสมอ — **ลบ worktree หลัง merge เสร็จด้วย** (`git worktree remove --force`)

### โปรเจกต์อ้างอิงสำหรับ polish (แสง/โมเดล) — Min ชี้มาเอง — **สรุปแล้ว: ไม่มีอะไรให้ยืม**
`D:\unity_project\industry fudamentals` — ตรวจแล้วเป็น**เทมเพลตทางการของ Unity เอง**
("Industry Fundamentals" learning template, namespace `Unity.Templates.IndustryFundamentals`)
ไม่ใช่โปรเจกต์ custom ที่มีเทคนิคพิเศษ:
- `LightRig.cs` ที่ชื่อดูน่าสนใจ จริงๆ แค่เปิด/ปิดสปอตไลท์ตอนเลือกหุ่นยนต์ ไม่ใช่ระบบจัดแสงฉาก
- `CinemachineSwitcher.cs` ใช้ `Priority` (0/100) สลับกล้อง — **ตรงกับที่ `CameraDirector.cs`
  ของเราทำด้วย `depth` อยู่แล้ว** เทคนิคเดียวกันเป๊ะ ยืนยันว่าไม่ต้องย้ายไป Cinemachine จริง
- Agent รีวิว agy ล่มเงียบ 2 รอบ (log ว่างเปล่า แม้ preflight probe ผ่านปกติ) — เปิดไฟล์ดูเอง
  โดยตรงแทน ประหยัดกว่า **บทเรียน:** งานที่ agy ล่มเงียบซ้ำๆ ให้เปลี่ยนมาทำเองถ้าเป็นงานเล็ก
  แทนที่จะไล่ retry ไม่จำกัด

---

## 🆕🆕🆕 อัปเดต (2026-09-14 01:37 — ก่อนหยุดคืนนี้ โควตาใกล้ 85%)

**Min ให้ทำต่อจนโควตา 85% แล้วไปนอน** — งานที่ทำเพิ่มก่อนหยุด:

### เสร็จแล้ว (agent 6-7 ผ่าน agy ใน worktree ใหม่ + merge แล้ว)
| Agent | งาน | ผล |
|---|---|---|
| 6 | `TelemetryOverlayController.cs` + `TelemetryOverlayAttacher.cs` — ต่อ `LeaderLineOverlay`
  เข้ากับ telemetry จริง (rail gap mm ตอน S7, nozzle height mm ตอน S6-S9) | ✅ ล่มเงียบ 1 รอบ
  ก่อนสำเร็จ (ใช้ harness background แก้ได้) merge แล้ว, เมนู `Attach Telemetry Overlay` ทำงานจริง |
| 7 | `TravelingCamera.cs` + `TravelingCameraBuilder.cs` — กล้องเดินทางเปิดคลิป A ใช้
  `ChangeoverSequencer.SCurve()` ซ้ำ พิกัดจริงจากไฟล์ builder ทุกตัว (ไม่เดา) | ✅ merge แล้ว
  **แต่กรอบภาพเริ่มต้นตัดหัวตู้คอนโทรล/ถังขาด** — Claude เจอเองจากการเช็คแบบ "คิดในมุมคนดู"
  ตามที่ Min สั่ง แก้แล้ว (ถอยกล้องออก+ยกสูงขึ้น จาก (2.2,1.8,-4.8)→(3.0,2.6,-6.5)) |

### 🔴🔴 บั๊กร้ายแรงที่พบ+แก้แล้ว: gizmo ของ Editor ถูกอัดติดวิดีโอจริง!

**"ตรวจคลิปแล้วคิดในมุมคนดู" ตามที่ Min สั่งไว้ — เจอปัญหาใหญ่ทันที:** เปิดเฟรมจากวิดีโอที่เรนเดอร์
เสร็จ (ffprobe ผ่านแล้วด้วยซ้ำ!) ด้วย ffmpeg แล้วพบว่า**เต็มไปด้วยไอคอน gizmo ของ Unity Editor**
(ตัวอักษร "T" ยักษ์ของ TextMeshPro, ไอคอนกล้อง, ไอคอน reflection probe) ทับเต็มจอ — **ทั้งคลิป A
และ B ที่เรนเดอร์รอบแรกใช้ไม่ได้เลยทั้งคู่** ทั้งที่ ffprobe บอกว่าไฟล์ถูกต้องสมบูรณ์ (codec/ความยาว/
fps ตรงหมด) **นี่คือเหตุผลที่ต้องดูเนื้อภาพจริงเสมอ ไม่ใช่แค่เช็ค metadata**

**สาเหตุ:** `MovieRecorderSettings.ImageInputSettings = GameViewInputSettings` เรนเดอร์จากสิ่งที่
Game View ของ Editor เห็นจริง ซึ่งรวม gizmo overlay ไปด้วยถ้า toggle "Gizmos" ของ Game View
เปิดอยู่ (ค่าเริ่มต้นมักเปิด) — ลองแก้ด้วย reflection ปิด `GameView.showGizmos` ก่อนแล้ว**ไม่ได้ผล
จริง** (log บอกว่า set ค่าสำเร็จ แต่ภาพยังเปื้อนเหมือนเดิม — อาจเพราะ Recorder จับจาก GameView
คนละ instance หรือ path การเรนเดอร์ต่างกัน)

**ทางแก้ที่ได้ผลจริง (ยืนยันด้วยการดึงเฟรมจริงหลายจุดในไทม์ไลน์):** เปลี่ยนจาก
`GameViewInputSettings` → **`CameraInputSettings`** (`ImageSource.MainCamera` + แท็กกล้องเป้าหมาย
เป็น `"MainCamera"`) — เรนเดอร์ตรงจากกล้องเลย ไม่ผ่าน Game View เลยไม่มี gizmo ติดมา
**ข้อแลกเปลี่ยนที่ยอมรับได้:** URP ไม่รองรับ `CaptureUI` บน input แบบนี้ → overlay Canvas
(`LeaderLineOverlay`/`TelemetryOverlayController`) **จะไม่ติดในวิดีโอ** — แต่นี่สอดคล้องกับ
การตัดสินใจเดิมของโปรเจกต์อยู่แล้วว่า overlay ควรทำตอนตัดต่อ 2D ไม่ใช่ฝังในเรนเดอร์ 3D

**ข้อจำกัดที่ยังไม่แก้ (งานต่อ):** `TaggedCamera`/`MainCamera` เลือกกล้องแบบ static (ตัวแรกที่เจอ)
**ไม่ตามการสลับกล้องสดของ CameraDirector** — คลิป B ตอนนี้เรนเดอร์จาก CellCam_Hero มุมเดียวตลอด
45 วิ ไม่มีการตัดไปมุม RailTopCam/NozzleSideCam อัตโนมัติ ต้องทำ per-frame camera-driven render
จริงในรอบหน้าถ้าต้องการภาพหลายมุมในไฟล์เดียว (ตอนนี้ยังพอใช้เป็น raw footage สำหรับตัดต่อได้)

**เมนูที่ใช้งานได้จริงตอนนี้:**
- `Tools/Delta/Render B_Changeover Draft (45s, 720p)` — ✅ เรนเดอร์แล้ว ตรวจสะอาดจริงด้วยการดึง
  เฟรม 4 จุดตลอด 45 วิ ไฟล์: `Recordings/B_Changeover_DRAFT_25690914_015834.mp4`
- `Tools/Delta/Add Traveling Establishing Camera` + `Render A_LineOverview Draft (Traveling Cam)`
  — ✅ เรนเดอร์แล้ว ตรวจสะอาดจริง ไฟล์: `Recordings/A_LineOverview_DRAFT_25690914_020259.mp4`
- `Tools/Delta/Restore Camera States After A-Draft` — คืนสถานะกล้องหลังเรนเดอร์คลิป A

**ทั้ง 2 ไฟล์ commit `c19669e` push ขึ้น GitHub แล้ว + แนบเข้ากระดาน mind-map แล้ว**
(ลบไฟล์เก่าที่เปื้อน gizmo ออกจาก repo แล้วด้วย ไม่ต้องไปดูไฟล์ `*_013714`/`*_014932`/
`*_015204`/`*_014443` อีก — ถูกลบทิ้งแล้ว)

**บทเรียนอื่นที่แก้ไปด้วย:** ตัวอักษร ✓ และ ▶ ใน `DeltaHMIDisplay.cs` ไม่มีใน LiberationSans SDF
font fallback (ขึ้น warning ทุกเฟรม, แสดงเป็นกล่องเปล่าแทน) — เปลี่ยนเป็น `[X]`/`[>]` แบบ ASCII

### ⚠️ คำขอของ Min ที่ยังไม่ได้ทำ (ของค้างชัดเจนสำหรับ session หน้า)
1. **"ตัดคลิป 3 แบบ" (แบบเดิม~90s / รวบรัด 45s / 1 นาที)** — **ยังทำไม่ได้จริงคืนนี้** เพราะยังไม่มี
   raw footage ที่สมบูรณ์ให้ตัด (เพิ่งเรนเดอร์ draft 45s ตัวแรกเสร็จตอนหยุด) การ "ตัดต่อ" ของจริง
   (เลือกช่วง/ใส่คำบรรยาย/จังหวะตัด) เป็นงานนอก Unity ต้องทำต่างหากหลังมีฟุตเทจครบ
2. **"ทำฉากหลังให้สมจริงแบบโปรเจกต์ตัวอย่าง"** — ตรวจแล้วโปรเจกต์อ้างอิงไม่มีอะไรพิเศษให้ยืม (ดูหัวข้อ
   บนนี้) **ยังไม่ได้ลงมือทำ polish จริง** เพราะโควตาหมดก่อน — งานที่ควรทำต่อ: ปรับ HDRI/skybox
   หรือรายละเอียดผิววัสดุเพิ่มถ้า Min อยากได้บรรยากาศดีขึ้นกว่าเดิม (ปัจจุบันใช้ Trilight ambient
   ไม่มี skybox ตามที่ verify แล้วว่าดีที่สุดสำหรับฉากในร่ม)

### ✅✅ อัปเดต (2026-09-14 ~06:00) — per-frame multi-camera render สำเร็จแล้วจริง!

**ข้อจำกัดที่ค้างไว้เมื่อคืน (ข้อ 2 เดิม) แก้เสร็จแล้ว** — ไม่ต้องเขียน custom Recorder input เต็มรูปแบบ
ตามที่คาดไว้ วิธีที่ง่ายกว่าและได้ผลจริง:
1. เพิ่ม `CameraDirector.SetSharedRenderTexture(RenderTexture rt)` — set `targetTexture` ของกล้อง
   ที่ CameraDirector คุมทุกตัวให้ชี้ไป RenderTexture เดียวกัน (ตัวไหน enabled อยู่ก็ render ลงนั้น)
2. Recorder ใช้ `RenderTextureInputSettings` จับภาพจาก RT นั้นตรงๆ — ได้ผลลัพธ์ตัดสลับกล้องจริง
   ตามสถานะ **ในไฟล์เดียว** และ**ไม่มี gizmo ติด**ด้วย (เหตุผลเดียวกับ CameraInputSettings —
   จับจาก render target ตรง ไม่ผ่าน Game View)
3. เมนูใหม่: `Tools/Delta/Render B_Changeover MULTICAM (45s, 720p)` +
   `Tools/Delta/Cleanup Multicam RenderTexture`

**ยืนยันด้วยการดึงเฟรมจริงข้าม timeline:** t=2s/t=20s = CellCam_Hero, **t=12s = ตัดไป RailTopCam
มุมบนสำเร็จจริง** (เห็นรางสองเส้นจากมุมตั้งฉาก คนละมุมกับ Hero ชัดเจน) — พิสูจน์ว่าระบบตัดกล้อง
ตามสถานะทำงานจริงในไฟล์ที่เรนเดอร์ออกมา

**บทเรียนใหม่ที่เจอระหว่างทำ:**
- **ระวังสับสน `EditorApplication.isPlaying` กับ `RecorderController.IsRecording()`** — รอบแรกที่
  ทำ multicam ไฟล์เสีย (`moov atom not found`) เพราะเช็คแค่ `isPlaying` (ยัง True ตลอดที่อยู่ใน
  Play Mode) แล้วสั่ง stop ทั้งที่การเรนเดอร์จริงยังไม่เสร็จ (encoder ยังไม่ finalize container)
  **ต้องเช็ค `IsRecording()` ให้เป็น false ก่อนเสมอ** ถึงจะ exit Play Mode ได้อย่างปลอดภัย
- `RenderTextureInputSettings.OutputWidth/OutputHeight` setter forward ตรงไปตั้งค่า
  `renderTexture.width/height` ซึ่ง Unity ห้ามทำกับ RT ที่ `.Create()` ไปแล้ว (ขึ้น warning)
  — ไม่ต้อง set สองค่านี้เลยถ้าสร้าง RT ที่ขนาดถูกต้องไว้แล้วตั้งแต่แรก

**ไฟล์ที่ใช้งานได้จริงตอนนี้ (แนบกระดานหมดแล้ว):**
- **`B_Changeover MULTICAM 45s v2 (HMI+RailTop+NozzleSide cuts)`** ⭐ **ใช้ตัวนี้เป็นหลัก** — ตัดกล้อง
  จริงตามสถานะ 3 มุม ยืนยันแล้ว: t=0.5s `ControlCam_Close` (S1 HMI), t=3s `CellCam_Hero` (S2+),
  t=12s `RailTopCam` (S7) — เพิ่ม S1/S8→ControlCam_Close จากเวอร์ชันแรกที่มีแค่ Hero/RailTop/NozzleSide
- `B_Changeover DRAFT 45s (clean, verified)` — สำรอง มุมเดียว (CellCam_Hero) เผื่อ multicam มีปัญหา
- `A_LineOverview DRAFT 10.5s (clean, verified)` — กล้องเดินทางเปิดคลิป A มุมเดียว (ยังไม่ทำ multicam
  ให้คลิป A เพราะ A ใช้ TravelingCamera ตัวเดียว ไม่มีการสลับกล้องอยู่แล้ว ไม่จำเป็น)

**เมนูสำหรับ multicam render:** `Tools/Delta/Render B_Changeover MULTICAM (45s, 720p)` แล้วตามด้วย
`Tools/Delta/Cleanup Multicam RenderTexture` เสมอหลังเรนเดอร์เสร็จ (คืนกล้องกลับปกติ)
**⚠️ ต้องเช็ค `IsRecording()` เป็น false ก่อน `manage_editor stop` ทุกครั้ง** ไม่งั้นไฟล์เสีย
(`moov atom not found`) — ดูบทเรียนด้านบน

### ✅✅✅ อัปเดต (2026-09-14 ~06:27) — คลิป A ได้ zone-callout cameras ครบแล้ว

**เพิ่ม 4 กล้องล็อกมุมใหม่** (`AClipZoneCamerasBuilder.cs`, agent8 ผ่าน agy) ตามช็อตลิสต์เดิมเป๊ะ:
`InfeedZoneCam` (14s) → `FillingZoneCam` (24s) → `CappingZoneCam` (10s) → `EndOfLineCam` (12s) →
`ControlCam_Close` (20s, ใช้ตัวเดิมซ้ำ ไม่สร้างใหม่) รวม 80 วิ ต่อจากกล้องเดินทางเปิดคลิป (10s)
= **90 วิเต็มตามช็อตลิสต์ต้นฉบับพอดี**

**เจอ+แก้ปัญหาจริง:** `CappingZoneCam` ตำแหน่งแรกที่ agent ให้มา (คำนวณจากพิกัดจริงถูกต้องแล้ว)
ดันมีตู้คอนโทรลบังอยู่ในมุมมอง — **สาเหตุคือตู้คอนโทรลกินพื้นที่ Z ทับซ้อนกับโซน capping จริงๆ**
(ตู้ยาวถึง Z=1.33, capping เริ่มที่ Z=1.05) ทดสอบสด 5 มุมก่อนเจอทางแก้: มุมสูงมองลงเกือบตั้งฉาก
แยกฉากหน้า-หลังด้วยความสูงแทนการมองข้าม ได้ผลจริง (ยืนยันด้วยภาพจากกล้องจริง)

**เมนูใหม่ครบชุดสำหรับคลิป A:**
`Add A-Clip Zone Cameras` → `Attach A-Clip Shot Switcher` → `Render A_LineOverview ZONES (80s, 720p)`
+ `Cleanup Zone Sequence RenderTexture` (ใช้เทคนิค shared-RenderTexture เดียวกับ B multicam)

### 🔴 บั๊กสำคัญที่เจอ+แก้: กล้อง 2 ระบบแย่งกันคุม (CameraDirector vs TimedShotSwitcher)

**เรนเดอร์รอบแรกได้ไฟล์ที่ดูเหมือนถูกต้องทุกอย่าง (80.03s, h264, ขนาดปกติ) แต่ดึงเฟรมตรวจแล้วพบว่า
t=55s กับ t=68s โชว์ `ControlCam_Close` ทั้งคู่ ทั้งที่ช่วง 48-60s ต้องเป็น `EndOfLineCam`**
— โซน EndOfLine หายไปทั้งช่วง 12 วินาที

**สาเหตุจริง:** `CameraDirector` (ระบบสลับกล้องของคลิป B ตามสถานะ) กับ `TimedShotSwitcher`
(ระบบสลับกล้องของคลิป A ตามเวลา) **อยู่บน GameObject `Cell` เดียวกันและทำงานพร้อมกัน**
เพราะ `ChangeoverSequencer` วนลูปอยู่ตลอดไม่ว่าจะเรนเดอร์คลิปไหน → พอ state วนกลับมา S1/S8
(ซึ่งผมเพิ่ง map ไป `ControlCam_Close` เอง!) `CameraDirector.LateUpdate()` จะบังคับเปิด
`ControlCam_Close` ทุกเฟรม **และ LateUpdate ทำงานหลัง Update เสมอ → ทับคำสั่งของ
TimedShotSwitcher ถาวรตั้งแต่จุดนั้นไปจนจบ**

**ทางแก้:** ตั้ง `CameraDirector.autoSwitchOnState = false` ตลอดช่วงเรนเดอร์คลิป A แล้วคืนค่า
ในเมนู cleanup (ใช้ toggle ที่มีอยู่แล้วในคลาส ไม่ต้องลบ component)

**✅ ยืนยันหลังแก้ด้วยการดึงเฟรมครบทุกโซน:** t=5 Infeed · t=25 Filling · t=42 Capping ·
**t=53 EndOfLine (จุดที่เคยพัง — ตอนนี้เห็น checkweigher/reject/labeler/outfeed ถูกต้อง)** ·
t=70 ControlCam_Close → ไฟล์: `Recordings/A_LineOverview_ZONES_25690914_063523.mp4`
(commit `6194a92`, push แล้ว, แนบกระดานแล้ว)

> **บทเรียนต่อยอด:** ระบบสลับกล้องหลายตัวในซีนเดียวกันจะแย่งกันเงียบๆ โดยไม่มี error ใดๆ —
> ffprobe ผ่าน, ไฟล์เปิดได้, ความยาวถูกต้องเป๊ะ แต่เนื้อภาพผิด **ต้องดึงเฟรมตรวจทุกช่วงเวลาสำคัญ
> เสมอ ไม่ใช่แค่ต้นคลิป** (ถ้าตรวจแค่ t=5 กับ t=25 จะไม่มีทางเจอบั๊กนี้เลย)

### ขั้นตอนถัดไปที่แนะนำ (เรียงตามลำดับ)
1. **ตรวจ `A_LineOverview_ZONES_*.mp4`** ด้วย ffprobe + ดึงเฟรมทุกโซน (ประมาณ t=12,30,55,70,85)
   ก่อนเชื่อว่าใช้ได้ — ยังไม่ทันตรวจตอนเขียน handoff นี้ (โควตาดีอยู่ 33% แต่เรนเดอร์ 80s ใช้เวลาจริง)
2. **เปิดดูวิดีโอทั้งหมดด้วยตาตัวเองก่อน** — ผมตรวจด้วยการดึงเฟรมเป็นจุดๆ เท่านั้น ไม่ใช่ดูทั้งคลิป
3. เอา footage ไปตัดต่อจริง (นอก Unity) เป็น 3 ความยาวที่ Min ขอ (เดิม~90s/45s/1min) — ตอนนี้มี
   วัตถุดิบครบทั้ง 2 คลิปตามช็อตลิสต์เต็มแล้ว (B มีตัดกล้อง 3 มุม, A มีกล้องล็อกครบ 5 โซน)
4. Polish pass (ถ้ามีเวลา): ตัวเลข recipe จริงจาก Min, รายละเอียดผิววัสดุ/บรรยากาศเพิ่ม, overlay
   ข้อมูล data-flow diagram แบบ 2D ตอนตัดต่อ (ตามที่ตัดสินใจไว้แล้วว่า overlay อยู่นอก Unity)

### 🎓 บทเรียนสำคัญที่สุดของคืนนี้ (ใช้ได้กับทุกงานเรนเดอร์ต่อจากนี้)
**อย่าเชื่อว่าเรนเดอร์ "ผ่าน" แค่เพราะ ffprobe บอกว่าไฟล์ถูกต้อง (codec/ความยาว/fps ตรง)**
ไฟล์ที่ "ถูกต้องทางเทคนิค" กับ "ภาพจริงใช้ได้" เป็นคนละเรื่องกัน — **ต้องดึงเฟรมจริงด้วย ffmpeg
แล้วดูด้วยตา (Read tool) ทุกครั้งก่อนเชื่อว่าเรนเดอร์เสร็จสมบูรณ์** ทั้งคลิป A และ B รอบแรกผ่าน
ffprobe สมบูรณ์แบบทั้งคู่ แต่เปื้อน gizmo เต็มจอ — ถ้าไม่ดึงเฟรมมาดูจะไม่มีทางรู้เลย

---

## 🆕 อัปเดต (2026-09-13 เย็น) — Delta Academy: วิดีโอ Zero-Downtime Changeover Cell (Unity)

**แผนเต็มอยู่ที่ `C:\Users\wicha\.claude\plans\warm-growing-hennessy.md` — อ่านก่อนทำต่อ**

### งานคืออะไร
Min แข่ง **Delta Academy KMITL** โปรเจกต์ **Zero-Downtime Changeover Cell** — ระบบ recipe-driven
ปรับเครื่องบรรจุสบู่เหลว/แชมพูอัตโนมัติเมื่อเปลี่ยนขนาดขวด (250/500/1000 ml) **45 นาที → ≤5 นาที**
ต้องส่ง **2 คลิป ~90 วิ** เรนเดอร์จาก Unity: `A_LineOverview` + `B_Changeover`

**Min รับผิดชอบเฉพาะส่วน "ทำให้กรรมการเข้าใจกลไก" — ROI เพื่อนอีกคนพูด ห้ามใส่เรื่องเงินในคลิป**

### แหล่งข้อมูล (อ่านครบแล้ว อยู่ที่ `D:\Downloads\`)
`Filling-Line-Hardware-Control-Points.md` (ฮาร์ดแวร์ + 5 พารามิเตอร์) · `image.png` (network topology) ·
`image2.png` (สเปกรุ่น Delta) · `image3.png` (เหตุผลวิศวกรรม) · `image4.png` (ขอบเขต SMED) ·
`Delta_Academy_KMITL_Intro_Competition-Guidline.pdf` (เกณฑ์อยู่หน้า 37)

### ตัดสินใจแล้ว (อย่ารื้อ)
| เรื่อง | สรุป | เหตุผล |
|---|---|---|
| Render pipeline | **URP** ไม่ใช่ HDRP | GTX 1650 ไม่รองรับ DXR → HDRP ray/path tracing ใช้ไม่ได้ = จุดขายหลักหายไป; Codex เห็นตรงกัน |
| Unity | **6000.6.0f1** | 6.4.5 ติดบั๊ก ShaderGraph CS0246 |
| Project | `D:\unity_project\delta_academy` | Min สร้างเอง จาก urp-blank |
| วิธีสร้างฉาก | **Editor script `[MenuItem]`** ไม่ใช่สั่ง MCP ทีละชิ้น | ต้องวางของ 40+ ชิ้นระดับมิล — script เป๊ะกว่า build ซ้ำได้ อยู่ใน git |
| กราฟิก | ทำใน Unity ชั้นเดียว (TextMeshPro) | Min เลือก — แลกกับแก้คำผิดต้องเรนใหม่ |
| รูปแบบส่ง | 2 คลิปแยก ~90 วิ | กดเล่นแยกตอนพูดได้ |

### สถานะ (อัปเดต 2026-09-13 ค่ำ — look-dev เสร็จแล้ว)

**unityMCP ใช้งานได้เต็มรูปแบบ** — Claude รัน Unity เองได้ทั้งหมด ไม่ต้องให้ Min กดเมนู:
`execute_menu_item` (รัน builder) · `read_console` (เช็ค error) · `manage_camera screenshot` (ตรวจภาพ) ·
`execute_code` (รัน C# สดในเอดิเตอร์ — ใช้ debug/tune ได้เร็วมาก) · `refresh_unity` (สั่ง import+compile)

> ⚠️ **ต้อง `refresh_unity` ทุกครั้งหลัง Gemini เขียนไฟล์ใหม่** ไม่งั้น Unity ไม่ import → เมนูไม่โผล่ →
> `execute_menu_item` fail ว่า "might be invalid" (เสียเวลาไปหนึ่งรอบเพราะเรื่องนี้)

**ไฟล์ที่มีแล้วใน `D:\unity_project\delta_academy\Assets\Editor\`:**

| ไฟล์ | เมนู | สถานะ |
|---|---|---|
| `LightingTestBuilder.cs` | `Tools/Delta/Build Lighting Test` | ✅ ผ่านแล้ว — เก็บเป็น look-dev reference **ห้ามแก้** |
| `DeltaMaterials.cs` | — | ✅ material กลางที่ผ่านการตรวจแล้ว |
| `CellBuilder.cs` | `Tools/Delta/Build Cell` | ✅ เซลล์จริง ผ่านการตรวจ 8 รอบ |

**ค่าที่ยืนยันด้วยตาแล้ว (อย่าไปรื้อ — กว่าจะได้มา 8 รอบ):**
- ambient Trilight sky `(0.30,0.31,0.34)` eq `(0.21,0.215,0.235)` gnd `(0.10,0.10,0.11)`, skybox = null
- Key **Directional** 3.4 สีกลาง `(1.00,0.98,0.95)` euler `(50,325,0)` เงา Soft strength 0.9
- Fill **Directional** 0.85 `(0.85,0.90,1.00)` euler `(35,145,0)` · Rim **Directional** 1.30 `(0.88,0.93,1.00)` euler `(8,205,0)`
- BrushedStainless `(0.55,0.56,0.58)` metallic **1.0** smooth 0.60 · PaintedSteel `(0.38,0.39,0.41)` metallic 0.15 smooth 0.30
- ผนัง+เพดาน+พื้น `≈(0.17,0.17,0.18)` · ห้อง 20×20×9 ม. + เพดาน · พื้น 80×80 ม.
- โคมเพดาน 6 ดวง: panel emissive `×6.0` ที่ y=8.60 + point light intensity **55** range 18 ที่ y=8.40

**แกนที่อนิเมทได้ (ใช้ชื่อนี้ตอนทำ changeover):**
- `GuideRailAssembly_X` — ลูกคือ `GuideRail_Left_30mm` / `GuideRail_Right_30mm` (แกน X = ASD-A3 ปรับความกว้างราง)
- `NozzleAssembly_Z` — ลูกคือ nozzle/valve/carriage ทั้งชุด (แกน Z ของเครื่อง = ขยับใน Y ของ Unity = ความสูงหัวเติม)
- กล้อง: `CellCam_Hero` depth 100 · `CellCam_Wide` depth 99

### 🧠 บทเรียนจริงจากรอบนี้ (อย่าพลาดซ้ำ)
1. **metallic = 1.0 เอาสีทั้งหมดมาจาก reflection** — พอปิดห้องด้วยผนังมืด สเตนเลสดำสนิททันที
   ต้องมี**โคมไฟจริงในห้อง**ให้มันสะท้อน ไม่ใช่แค่เพิ่มไฟส่อง
2. **spot light ไร้ผลที่ระยะเครื่องจักร** — falloff กำลังสองทำให้ fill/rim แบบ spot แทบไม่ให้อะไร
   เปลี่ยนเป็น Directional แล้วดีขึ้นทันที (สาเหตุใหญ่ที่ภาพเคยแบน)
3. **อย่าลดความสว่างหลายทางพร้อมกัน** — สั่งลด albedo 0.70→0.38 + key 2.0→1.5 + เติมผนังมืด + ambient มืด
   พร้อมกัน = เหลือ 41% ภาพดำสนิท **เป็นความผิดของบรีฟ Claude เอง ไม่ใช่ Gemini**
4. **ทดลองสดด้วย `execute_code` ก่อนสั่ง Gemini เขียนลงไฟล์** — หาค่าที่ถูกแบบฟรีและเร็ว
   แล้วค่อยส่งตัวเลขที่ยืนยันแล้วไป persist ประหยัดรอบไปมากกว่าครึ่ง
5. **Gemini เคยอ้างเท็จ 2 ครั้ง** — "compile ผ่าน 0 error" (ทั้งที่ Unity ยังไม่ import ไฟล์)
   และ "ขอบพื้นไม่มีทางเห็น" (เห็นชัดทั้งสองกล้อง) → **สั่งตรงๆ ว่าห้ามอ้างว่าตรวจแล้ว
   ให้บอกว่า "ยังไม่ได้ตรวจ"** พอสั่งแล้วทำตามดีมาก และคุณภาพงานที่เหลือดีจริง
6. **Legibility > photorealism** สำหรับคลิปนี้ — กรรมการต้องเห็นกลไก โรงงานมืดสวยๆ ทำงานสวนเป้าหมาย

## 🆕 อัปเดต (2026-09-13 ดึก) — ตู้คอนโทรล + ประตูเปิด + กล้อง close-up แก้เสร็จ

**Min มอบอำนาจตัดสินใจให้ Codex ชั่วคราว → Codex offline → Claude กลับมาคุมงานเต็มตัว**

### สิ่งที่ Codex ทำสำเร็จก่อนออฟไลน์ (ของจริง ไม่ใช่แค่รายงาน)
เจอบั๊กจริงใน `ChangeoverSequencer.cs` 5 จุด (ขวดขยับซ้อนเฟรม, ขวดทดสอบตำแหน่งกระโดด,
ระดับน้ำลดตอน loop, recipe ค้างค่าเก่า, interlock เสี่ยง null) → ให้ Gemini แก้ครบ compile ผ่าน
0 error → **ทดสอบ Play Mode จริงที่ 4× ยืนยันว่า interlock ทำงานถูก** (Z ถอย home ก่อน X ค่อยขยับ)

### 🔴 เหตุการณ์ร้ายแรง: Unity ค้าง 10 นาที
**สาเหตุ:** Gemini แก้ไฟล์ `.unity` (scene YAML) ตรงๆ บนดิสก์ ขณะ Unity เปิดฉากเดียวกันค้างในหน่วยความจำ
→ Unity เด้ง modal dialog "scene changed on disk, reload?" **บล็อกทุกอย่างรวม MCP bridge**
→ ดูเหมือนโปรแกรมค้าง (log หยุดขยับ, ping ไม่ตอบ) ทั้งที่จริงแค่รอคนกดยืนยัน
**บทเรียนสำคัญที่สุดของ session นี้:** **ห้าม AI แก้ไฟล์ `.unity` ตรงๆ เด็ดขาดขณะ Editor เปิดอยู่**
ให้แก้ผ่าน C# builder script เท่านั้น — สั่ง Gemini แล้วว่าห้ามทำอีก มันย้อนไฟล์กลับ 100% แล้ว

### บั๊กที่ตามมา + วิธีจับที่ได้ผลจริง
1. **`BatchDrawCommand` error ท่วม console** — สาเหตุจาก scene desync ที่ค้างจากเหตุการณ์บนสุด
   ผสมกับ TextMeshPro/emissive material ที่ไม่ได้ตั้ง `ShadowCastingMode.Off` → Gemini แก้แล้วหาย
2. **กล้อง `ControlCam_Close` พังต่อเนื่อง 3 รอบติด** — ทุกรอบ Gemini "รายงาน" ตัวเลขที่ตั้งไว้
   แต่**ตัวเลขจริงในฉากไม่ตรงกับที่รายงานเลย** (พิสูจน์ได้ด้วยการดึงพิกัดจริงมาวัดเทียบทุกครั้ง)
   **ทางแก้ที่ได้ผล:** สั่งตรงๆ ว่า **"อ่านย้อนไฟล์ที่เพิ่งเขียน แล้วยกบรรทัดจริงมายืนยัน แทนเดาจากความจำ"**
   — รอบถัดมาตัวเลขตรงกับที่วัดจริง 100% ทันที (เหมือนบทเรียนเรื่อง "ห้ามอ้างว่าตรวจแล้ว" ที่เจอรอบก่อน)
3. **ต้นเหตุกล้องจริงๆ คือบานพับประตูไม่ได้หมุน** (ค้างที่ -10° ไม่ใช่ 80-90° ที่รายงานไว้ 2 รอบ)
   หาเจอด้วยการวัดพิกัดจริงเทียบกับที่รายงาน ไม่ใช่เดาจากภาพ

### 🧠 เทคนิคที่ประหยัดรอบมากที่สุดของ session นี้
**หาค่ากล้อง/ตำแหน่งด้วยตัวเองสดๆ ก่อน แล้วค่อยส่งตัวเลขที่ยืนยันแล้วให้ Gemini persist**
(เหมือนที่เคยได้ผลกับแสงมาก่อน) — ใช้ `manage_camera` action `screenshot` พร้อม `view_position`/
`view_target` ทดสอบมุมกล้องได้โดยไม่ต้องแก้ไฟล์เลย (แค่ตั้งค่าจำลอง ไม่กระทบ object จริง)
ทดสอบ 4 มุมใน ~2 นาที เทียบกับอีก 3 รอบ Gemini เดาที่ผ่านมาซึ่งกินเวลาเป็น 10+ นาทีต่อรอบ

### ผลลัพธ์สุดท้าย — ยืนยันด้วยภาพจากการ rebuild สะอาด
`Assets/Screenshots/v15_persisted_verified.png` — ประตูตู้เปิด 130° เห็นอุปกรณ์ 3 ชิ้นชัดเจน
(ไฟสถานะเขียว/แดงตามจริง) + จอ HMI เห็นได้จากมุมข้าง กล้อง: pos=(0.15,1.85,1.35)
มอง target=(-1.05,1.10,0.35) ผ่าน `Quaternion.LookRotation` FOV=40 — เขียนลงไฟล์ถาวรแล้ว

**สถานะบั๊ก: 0 จุดที่ทราบและยังไม่แก้** งานที่เหลือทั้งหมดคือฟีเจอร์ใหม่ ไม่ใช่การไล่แก้บั๊ก

### 🆕 รูปอ้างอิงอุปกรณ์ — เปลี่ยนแผนเป็น post-production overlay (2026-09-13→14 ดึกมาก)

**ลองผิดทางก่อน แล้ว Min แก้ไข:** รอบแรกทำเป็นการ์ดรูป **3D ลอยในฉาก Unity** ข้างป้ายชื่อแต่ละ
อุปกรณ์ (6 ใบ) — ทำงานได้จริง ยืนยันด้วยภาพแล้ว แต่ **Min แก้ทาง**: ต้องการเป็น **2D UI overlay
ตอนตัดต่อวิดีโอ** (เหมือนการ์ดสเปกลอยมุมจอ) ไม่ใช่วัตถุ 3 มิติผูกกับมุมกล้อง (เพราะเปราะบางกับมุม
กล้องเหมือนที่เพิ่งปวดหัวกับกล้องตู้คอนโทรลมา) → **สั่งถอดการ์ด 3D ออกแล้ว ยืนยันฉากกลับมาสะอาด
เหมือนเดิมทุกอย่าง** (`Assets/Screenshots/v17_cards_removed.png` ตรงกับ v15 เป๊ะ)

**สิ่งที่ยังอยู่ใช้ได้ต่อ:** รูปจริง 5 ไฟล์ที่ import เข้า Unity แล้วที่ `Assets/ReferenceImages/*.jpg`
**ไม่ได้ลบ** — เตรียมไว้ใช้เป็นภาพ overlay ตอนตัดต่อจริงได้เลย ไม่ต้องหา/import ใหม่

**งานนี้ย้ายไปอยู่หมวด "ตัดต่อ/post-production"** ไม่ใช่ "สร้างฉาก Unity" แล้ว — รอถึงขั้นตอนตัดต่อ
คลิป A/B ค่อยหยิบรูปจาก `Assets/ReferenceImages/` มาทำ overlay 2D ตอนนั้น

### ⏭️ ขั้นถัดไป
- ยังไม่ได้ทำ: อนิเมชัน changeover จริง (ขยับ 2 แกน), ขวด 3 ขนาด, HMI/PLC/servo props, Recorder เรนเดอร์
- ยังไม่ได้คำตอบจาก Min: ตัวเลข recipe table จริง, เหลือกี่วันก่อนนำเสนอ, โทนแสงนี้โอเคไหม

### 🔴 Codex review — shot list เดิมผิด อย่าลืม
> "จุดที่กรรมการจะจับได้ที่สุดคือ **line clearance + interlock** และ **first-article validation** ไม่ใช่เรื่องล้างท่อ"

ลำดับที่ถูก: หยุดป้อนขวด → จบการเติมที่ค้าง → ปิดวาล์ว+หยุดปั๊ม → เคลียร์ขวดพ้นโซนชน → หยุดสายพาน →
**ถอย Z กลับ home ก่อน** → ค่อยให้ X ขยับ → ยืนยัน in-position/drive-ready → ขวดทดสอบใบแรก → เดินเต็ม

5 คำอธิบายที่ต้องรัดกุมขึ้นก่อนพูด (ดูตารางเต็มในไฟล์แผน) เช่น **S-curve ทำให้มอเตอร์นุ่ม แต่ไม่ได้ทำให้การชน stopper นุ่ม**
และ **ความหนืดเป็นสมบัติของผลิตภัณฑ์ ไม่ใช่ของขนาดขวด**

### การแบ่งงาน (Min กำหนด)
Claude = วางแผน/คุมงาน/QA · **Gemini (`delegate_to_gemini`) = ผู้ลงมือหลัก** (token เยอะ) ·
**Codex sol max (`to:"chatgpt"`) = ที่ปรึกษาเท่านั้น** — บรีฟเป็นอังกฤษเสมอ กัน mojibake


## 🆕 อัปเดต (2026-09-13 10:24) — ปลดล็อก GPU Hardware Acceleration (NVENC) ให้ Manim ทั้งระบบ
- **ผู้สั่งการ:** Min ("copy then modify that libraly to use gpu")
- **ผลลัพธ์:** ปรับแต่งแกนไลบรารี Manim Community (`scene_file_writer.py`) ให้ใช้ **NVIDIA NVENC (`h264_nvenc`)** บนการ์ดจอ GeForce GTX 1650 แทน CPU software encoding (`libx264`)
- **ไฟล์ที่แก้ไขและสำรอง:**
  1. `C:\Users\wicha\AppData\Local\Programs\Python\Python312\Lib\site-packages\manim\scene\scene_file_writer.py` (ไฟล์หลักที่รันคำสั่ง `manim`)
  2. `C:\Users\wicha\Desktop\manium\manim-community\manim\scene\scene_file_writer.py` (Local source clone)
  - ทั้งสองไฟล์มีแบ็กอัป `.bak` ดั้งเดิมเก็บไว้อย่างปลอดภัย
- **ฟีเจอร์เด่น:**
  1. **Auto-Detect GPU:** ตรวจจับ GPU อัตโนมัติ หากมี NVENC จะเปิดใช้ทันที พร้อมแสดง log: `INFO Using GPU hardware encoder: NVIDIA NVENC (h264_nvenc)`
  2. **Zero Overhead Remux:** การรวมไฟล์ partial movies เข้าด้วยกันทำผ่าน stream copy (lossless remux) แบบฉับพลัน
  3. **Auto CPU Fallback:** หาก GPU ไม่พร้อม หรือรันบนเครื่องที่ไม่มี NVIDIA จะ fallback กลับไปใช้ CPU `libx264` แบบไร้รอยต่อโดยงานไม่ล่ม
  4. **Manual Toggle:** สามารถสั่งปิด GPU ชั่วคราวได้ด้วย `$env:MANIM_USE_GPU='0'` (PowerShell) หรือ `set MANIM_USE_GPU=0` (CMD)
- **การทดสอบจริง:** ผ่าน 100% ทั้งการเรนเดอร์ปกติด้วย NVENC และการทดสอบ fallback เมื่อปิด GPU

## 🆕 อัปเดต (2026-09-13 09:43) — กฎเหล็ก Min (§41): Instant Snapshot & Fast OpenGL QA ก่อน Push ขึ้น GitHub ทุกครั้ง
- **เพิ่มกฎ §41 ลงใน `manim-teaching-video/SKILL.md` ครบ 4 AI:**
  - `~/.claude/skills/manim-teaching-video/SKILL.md`
  - `~/.codex/skills/manim-teaching-video/SKILL.md`
  - `~/.gemini/antigravity/skills/manim-teaching-video/SKILL.md`
  - `Desktop/powerfull_note/.agents/skills/manim-teaching-video/SKILL.md`
- **เนื้อหากฎ & เทคนิค:** 
  - ห้าม push โค้ดขึ้น GitHub หรือส่งขึ้น Cloud เด็ดขาดถ้ายังไม่ได้รัน Instant Snapshot ตรวจภาพจริงใน Local ก่อน วนลูปแก้จนกว่าจะพอใจ 100% แล้วจึงค่อย commit & push
  - คำสั่ง Snapshot: `manim -s -ql <file.py> <Scene>`
  - Fast GPU OpenGL Snapshot: `manim -s -ql --renderer=opengl <file.py> <Scene>` หรือใช้สคริปต์ `tools/manim-qa/fast_opengl_snapshot.py`
  - ดูแอนิเมชันสด 60fps บนหน้าจอ: `manim -p --renderer=opengl <file.py> <Scene>`
- **เครื่องมือใหม่:** `tools/manim-qa/fast_opengl_snapshot.py` รองรับการเรนเดอร์ภาพด้วย OpenGL บน NVIDIA GTX 1650
- **กำจัด Zombie Process:** ฆ่า `find.exe` (PID 30388) ที่ค้างรันสแกนทั้งดิสก์ คืน CPU 25% ให้ระบบเรียบร้อย

## 🆕 อัปเดต (2026-09-13 08:50) — Gemini อัปเกรดระบบ 5 ด้าน + อัปเดต Habit 1 Skill ครบทั้งระบบ

**1. สกิล `habit-1-be-proactive` ได้รับการอัปเกรดตามคำสั่ง Min และซิงค์ครบทุก AI:**
- เพิ่ม 3 กฎเหล็กใน `SKILL.md`:
  (1) **เป็นคนริเริ่มก่อนเสมอ (Initiative First):** ไม่รอให้สั่ง
  (2) **เลือกตอบสนองที่ดีเพื่อให้ครั้งหน้าเราเก่งขึ้น (Growth Response):** เปลี่ยนบั๊ก/อุปสรรคเป็นบทเรียนถาวร
  (3) **คิดถึง Session ต่อไปเสมอ (Compound Value):** สร้างเครื่องมือและเอกสารให้ Session ถัดไปเริ่มงานง่ายขึ้น
- ซิงค์ไฟล์ไปที่:
  - `~/.claude/skills/habit-1-be-proactive/SKILL.md` (Claude ใช้ได้ทันที)
  - `~/.codex/skills/habit-1-be-proactive/SKILL.md` (Codex ใช้ได้ทันที)
  - `~/.gemini/antigravity/skills/habit-1-be-proactive/SKILL.md`
  - `Desktop/powerfull_note/.agents/skills/habit-1-be-proactive/SKILL.md`

**2. สร้าง MCP Server ใหม่: `fusion-mcp` (Autodesk Fusion 360):**
- **Add-In:** ติดตั้งที่ `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\FusionMcpServer` (เชื่อมด้วย Junction มาจาก `tools/fusion-mcp/addin/`) รันบนพอร์ต 9877
- **Bridge:** `tools/fusion-mcp/fusion_mcp_bridge.py` มี 7 เครื่องมือ CAD/CAM (`get_fusion_status`, `get_active_design_info`, `list_parameters`, `set_parameter`, `create_box`, `export_cad`, `execute_fusion_script`)
- **ลงทะเบียนแล้ว:** ใน `.mcp.json` เรียบร้อย Claude และ Gemini เรียกใช้ได้ทันที

**3. สร้างระบบ Autonomous Manim Visual QA Loop:**
- สคริปต์: `tools/manim-qa/auto_manim_qa.py`
- สกัด 4-8 คีย์เฟรมอัตโนมัติด้วย ffmpeg ตรวจสอบ Layout และส่งสรุปผลตรงเข้า Inbox ของ Claude (`to: "claude"`) ทันทีที่เรนเดอร์เสร็จ

**4. แก้ปัญหาภาษาไทย Mojibake (`?????`) ข้าม AI:**
- แก้ `chatgpt-listener.js` ให้รัน childEnv ด้วย `PYTHONIOENCODING=utf-8`, `PYTHONUTF8=1` และส่ง stdin ด้วย `utf8`
- แก้ `antigravity-wait.py` ให้ครอบ `sys.stdout` ด้วย UTF-8 TextIOWrapper

**5. ย้ายโปรเจกต์ Manium คืนพื้นที่ SSD ไดรฟ์ C: ไป D:**
- ย้าย 5 โฟลเดอร์: `manium-agv-f1`, `manium-booster-landing`, `manium-car-foundation-test`, `manium-double-slit`, `manium-pe3-page14` ไปที่ `D:\Desktop\` และสร้าง Junction `mklink /J` กลับมาที่เดิม 100%
- สร้าง `C:\Users\wicha\Desktop\disable_hiberfil_admin.bat` ให้ Min คลิกขวาปิด hiberfil เพื่อคืนพื้นที่อีก 6.18 GB ได้ทันที

**6. สร้าง Interactive Mechanism Simulator บน powerNote:**
- ไฟล์: `public/sim-mechanism.html` เข้าดูได้ที่ `http://localhost:4321/sim-mechanism.html`

---

## 🆕 อัปเดต (2026-09-06 22:56, เซสชันใหม่หลัง restart) — G05B รอบ 2 เสร็จ + ระบบ cache render ใหม่

**G05B_SimilarTriangles แก้เพิ่มอีกรอบ เสร็จ+deploy แล้ว (commit `0826254` บน master):**
Min กลับมาดูคลิปแล้วขอเพิ่ม (1) เปลี่ยนสมการขั้น 4c จาก "180°−(α+90°)=90°−α" (3 พจน์ในวงเล็บ)
เป็น "มุมฉากกินไป 90° เหลืออีก 90° แบ่ง 2 ปีก" (ไม่มีวงเล็บ อยู่ในกรอบ complementary เดิม) —
ยืนยันจาก agy pedagogical review จริง (ไม่ใช่แค่เช็คบั๊กภาพ) ว่าปัญหาเดิมคือขั้น 3 สอน
complementary (บวกกัน 90°) แต่ขั้น 4 สลับไป supplementary (180°) แบบไม่เตือน (2) เพิ่มครึ่งวงกลม
สัดส่วน (ไอเดีย Min) ที่ "โผล่ออกมาจากจุด Q" ผ่าน TransformFromCopy ไม่ใช่วาดแยกลอยๆ (ตามคำแนะนำ
agy กันปัญหา split-attention) — เจอบั๊กจริง 1 จุดระหว่างทาง (ยอดครึ่งวงกลมชนป้าย "Q" ของ
สามเหลี่ยมที่ดึงออกมา) แก้แล้ว ตรวจซ้ำผ่าน agy+ซูมเฟรมเองสะอาดหมด **deploy ทับแล้ว** ที่
`Exam_Prep\Mechanics of Machinery\anim\G05B_SimilarTriangles.mp4` เสร็จสมบูรณ์
(รายละเอียด pattern อยู่ที่สกิล manim-teaching-video §31-34)

**ระบบใหม่: render cache ข้ามรอบบนคลาวด์ (commit `7ef4d45` บน master, `render_manim.yml`):**
Min ถามเรื่องความเร็วเรนเดอร์ ทุกรอบก่อนหน้านี้เรนเดอร์ทั้งซีนใหม่หมดทุกครั้งแม้แก้แค่นิดเดียว
เพราะ GitHub Actions เปิดเครื่องเปล่าใหม่ทุกรอบ ไม่มี cache ของ manim เอง (ที่มีอยู่แล้วและ
ทำงานจริงตอน render local) เหลืออยู่ข้ามรอบ — แก้ด้วย `actions/cache/restore`+`save` เก็บโฟลเดอร์
`media/` ไว้ (key ตาม scene_file+quality+fps+run_id, restore-keys เป็น prefix) ตอนนี้ **รอบต่อไป
ที่แก้ซีนเดิมบางส่วนควรจะเร็วขึ้นมาก** (manim จะข้าม animation ที่ hash ไม่เปลี่ยนเอง) — รอบ
G05B ล่าสุดเป็นรอบแรกที่มี cache step เลยยังไม่ได้ประโยชน์ (ไม่มี cache เก่าให้ใช้) แต่ได้เซฟ
cache ไว้ให้รอบหน้าแล้ว — **ยังไม่เคยวัดผลจริงว่าเร็วขึ้นเท่าไหร่ รอดูรอบถัดไปที่แก้ G05B หรือ
ซีนอื่นซ้ำ**

**บทเรียนใหม่เรื่อง agy:** เจอ false positive จริงครั้งแรก (อ้าง defect ที่พิกัดพิกเซลเกินขอบ
ภาพจริงไปเลย — เช็คแล้วภาพสะอาด) บันทึกไว้ใน memory `feedback-frame-verification-stays-with-claude`
แล้วว่าพิกัดเกินขอบภาพ = สัญญาณให้ไม่เชื่อ claim นั้นได้เลย ต้องซูมเช็คทุกครั้งเหมือนเดิม

## 🔴 อัปเดต (2026-09-06 19:26) — โควตา 85% — หยุดรับงานใหม่ ไม่มีงานค้างกลางคัน

**สถานะตอนหยุด: ไม่มีอะไรค้างครึ่งๆ กลางๆ** — งานหลักของรอบนี้ (G05B fix, ดูหัวข้อถัดไป) เสร็จ
สมบูรณ์และ deploy แล้วก่อนหน้านี้ ไม่มี subagent รันอยู่เบื้องหลังต้องสั่งหยุด

**งานล่าสุดที่เพิ่งทำ (เสร็จแล้ว ไม่ต้องทำต่อ):** Min ขอ "แจ้งเตือนเหมือน tkinter มุมขวาบนว่าใช้
skill ไหน แยก function จาก say_to_user" — เลือกทางเลือกที่ 2 (Claude Code hook, ไม่แตะแอป/ไม่มี
ความเสี่ยง reload) ทำเสร็จแล้ว:
- `~/.claude/hooks/skill_popup.py` — tkinter popup มุมขวาบน ขอบม่วง หายเองใน 3.5 วิ
- `~/.claude/hooks/skill_notify_hook.py` — PreToolUse hook script อ่าน stdin JSON เอา
  `tool_input.skill` มายิง popup แบบ detached process (ไม่บล็อกการเรียก skill จริง)
- ตั้งใน `~/.claude/settings.json` → `hooks.PreToolUse` matcher `"Skill"` (global ใช้ได้ทุกโปรเจกต์)
- ทดสอบ end-to-end แล้ว (จำลอง payload จริงผ่าน hook script โดยตรง) ทำงานถูกต้อง
- **ข้อจำกัดที่บอก Min แล้ว: hook นี้จะยังไม่ทำงานในเซสชันที่เปิดอยู่ตอนตั้งค่า** (โหลด config
  ตอนเริ่ม session เท่านั้น) — ต้องเปิดเซสชันใหม่ถึงจะเริ่มยิง popup อัตโนมัติทุกครั้งที่เรียก
  skill จริง — **ยังไม่ได้รับการยืนยันจาก Min ว่าเห็น popup จริงหรือเปล่า** (ขอให้ยืนยันไปแล้ว
  2 รอบ ยังไม่มีคำตอบตอนหยุด) — ถ้า session ใหม่แล้วยัง popup ไม่ขึ้น ให้เช็คว่า pythonw.exe path
  ยัง match `C:\Users\wicha\AppData\Local\Programs\Python\Python312\pythonw.exe` อยู่ไหมก่อน

**คำถามที่ยังค้าง ไม่มีคำตอบ:** จะ push โน้ต W06 Spur Gears + คลิปทั้งชุด (`G05A/B/G06`) ขึ้น repo
ที่แชร์กัน `minmin2017/tew_mechoLife_hellthatyou_chose` ไหม (ถามไปแล้ว รอ Min ตอบ)

**ต่อรอบหน้า:** รอโควตารีเซ็ต (22:09:59) ก่อนเริ่มงานยาวใหม่ ถ้า Min ตอบคำถามค้างระหว่างนี้ ตอบ
สั้นๆ ได้ แต่ไม่ต้องเริ่มงาน render/dispatch ใหม่จนกว่าโควตาจะรีเซ็ต

## 🆕 อัปเดต (2026-09-06 ค่ำ) — G05B เพิ่ม animation อธิบาย 90°−α แล้ว deploy ทับแล้ว

Min ติดตรงขั้น 4 ของ `G05B_SimilarTriangles` (ทำไม v_Q2⊥AQ ถึงกลายเป็นมุม 90°−α) ระหว่างติวจริง
— เพิ่ม animation สาธิตที่จุด Q จริงบนไดอะแกรม (แบ่งเส้นตรง R-Q-P 180° เป็น α+90°+เหลือ 90°−α
ทีละชิ้น) ใน `D:\Desktop\manium\gear_law_similar.py` (`G05B_SimilarTriangles`, commit `8589c67`
บน `master`) ยืนยันเลขจริงก่อนแก้ (α=62.7°, มุม QA-QE=90.0° เป๊ะ) — รอบแรกใช้สี WARN ซ้ำกับ arc
ของ α ทำให้ agy (Antigravity) อ่านมุมผิดเป็น ~63° จริง (ไม่ใช่ agy มโน — ซูมยืนยันแล้วว่าสีชนกัน
ทำให้ตาไหลเป็นเส้นเดียว) แก้เป็นสีเขียว `C_DEMO="#66BB6A"` แยกจาก α/ผลลัพธ์ (ยัง WARN) + ขยับ
ป้าย 90°-α ให้พ้นเส้น QP แล้ว — ตรวจซ้ำผ่านทั้ง agy และซูมเฟรมเอง (t=36-65) สะอาดหมด **deploy
ทับแล้ว** ที่ `Exam_Prep\Mechanics of Machinery\anim\G05B_SimilarTriangles.mp4` — เสร็จ ไม่ต้อง
แตะซีนนี้อีกเว้นแต่ Min แจ้งปัญหาใหม่ (ดู [[manim-teaching-video]] skill §31-32 สำหรับ pattern
ที่ใช้ทำ + เพิ่ม memory `feedback-frame-verification-stays-with-claude` เรื่อง agy ต้องบอกชัดๆ
ว่าห้ามเขียนสคริปต์ ให้ดูภาพตรงๆ ไม่งั้นมันจะไปเขียนสคริปต์เช็ค dimension แล้วค้าง)

Min ยังถามด้วยว่าจะ push โน้ต W06 Spur Gears + คลิปทั้งชุดขึ้น repo ที่แชร์กัน
(`minmin2017/tew_mechoLife_hellthatyou_chose`) ไหม — ยังไม่ได้คำตอบ ถามค้างไว้

## 🆕 อัปเดต (2026-09-06) — G05A/B/G06 เสร็จสมบูรณ์แล้ว, กำลังตรวจ oil-flow ของ Fluid W07

**G05A/B/G06 rebuild: เสร็จ 100% แล้ว** (merge เข้า master, push แล้ว, deploy แล้ว, spot-check เอง
ผ่าน) — ไม่ต้องแตะอีก

**งานใหม่ (กำลังทำ):** Min ดูซีรีส์ Fluid W07 Hydraulic Circuit (HC01-14) แล้วบอกว่าการไหลของ
น้ำมันในท่อ "ไหลแปลกๆ" เกือบทุกคลิป ขอให้ปรึกษา Gemini — dispatch subagent
`af8f6a46c3cf189d9` ("Review oil-flow animation across HC01-13 clips") ไปตรวจ:
- ไฟล์โค้ด `D:\Desktop\manium\hydraulic_circuits.py`, helper `flow_dots()`/`pipe()`/`elbow_pts()`
- ตรวจว่า point list ของ `flow_dots(...)` ตรงกับ point list ของ `pipe(...)` ที่มันควรวิ่งทับไหม
  (สงสัยว่า mismatch ทำให้จุดน้ำมันลอยออกจากเส้นท่อ หรือตัดมุมเป็นเส้นทแยงแทนที่จะเลี้ยวฉาก)
- **วินิจฉัยเสร็จแล้ว** — สาเหตุ: `flow_dots(...)` ส่วนใหญ่ใช้จุดต้น-ปลาย 2 จุดตรงๆ แทนที่จะผ่าน
  `elbow_pts(...)` แบบเดียวกับที่ `pipe()` ใช้วาดท่อจริง เลยทำให้จุดน้ำมันตัดทแยงลอยออกจากท่อ
  พบใน HC05,HC06,HC07(แย่สุด),HC08,HC09(ผิด100%),HC10,HC12,HC13(+พิกัดพิมพ์ผิด) — HC04/HC11 ปกติ

**Dispatch subagent แก้แล้ว: `a183fdd6bb08a42b2`** ("Fix flow_dots elbow mismatch in HC05-13") —
บรีฟจุดแก้ทีละคลิปละเอียดแล้ว ให้ทำ: แก้โค้ด → เรนเดอร์ 8 คลิปที่มีปัญหา → ตรวจเฟรมต่อเนื่องเอง
→ deploy ทับ `Exam_Prep\Fluid Power Control\anim\` → commit/push/merge — **ยังไม่มี notification
ว่าเสร็จ** เช็ค `ListAgents` ก่อนถ้าเปิด session ใหม่มาเจอ

## 🔴 อัปเดต (2026-09-05 ~17:35) — โควตา 85% รอบ 4 — กำลังรีบิลด์ G05A/G05B/G06 (หน้า 5-6) อยู่

**บริบท:** Min ให้ไฟล์ CAD trace จริง (`D:\Downloads\ai_tew.dxf`) ของหน้า 5-6 วิชา Mechanics of
Machinery (Velocity Ratio / Pitch Point) มายืนยันว่าคลิปเดิม `G05A_PointsAndLines`,
`G05B_SimilarTriangles`, `G06_PitchPoint` (ใน `D:\Desktop\manium\gear_law_similar.py`) **ผิด**
— ตรวจสอบเฟรมจริงจากคลิปเก่าแล้วยืนยันว่าจริง: จุด P บนเส้น A-B ในคลิปเก่าอยู่แค่ ~24% จาก A
(ควรอยู่ ~55% ใกล้ B มากกว่า ตามตารางพิกัดที่ยืนยันแล้ว) สเปกเต็มอยู่ที่
`C:\Users\wicha\Desktop\Main_note\Claude_Specs\Spur Gear Pages 5-6 — Velocity Ratio Geometry Spec.md`
(มีตารางพิกัด A/B/R/Q/P/S/E/F ที่ยืนยันครบแล้ว — **ห้ามถามซ้ำ ใช้ตารางนี้เป็นความจริง**)

**บั๊กนี้จำกัดอยู่แค่ 3 คลิปนี้เท่านั้น** — ตรวจแล้วว่า 33 คลิปที่เหลือ (G01-G03, G07-G38) ใช้
สเปกคนละชุด (มุมกด 20° มาตรฐาน, ผ่าน Gemini review+fix ไปแล้ว commit `e8ba607`) ไม่เกี่ยวกัน
ไม่ต้องไล่แก้ทั้งหมด

**สถานะ (อัปเดต 17:40):** subagent เดิม `a0fe78064929d0d69` **ตายจริงจาก rate limit** (429 ตอน
17:20) ไม่ได้อยู่ใน ListAgents แล้ว — เช็ค git log พบว่ามันทำไปไกลมาก (7 commit หลัง rebuild
แรก รวม Gemini review + fix แล้ว) แต่ commit ล่าสุด `b9cc9bf` ("Fix RecursionError in
small_angle()") **ยังไม่เคยเรนเดอร์ยืนยันเลย** — ตายไปทันทีหลัง commit

**Dispatch subagent ใหม่แล้ว: `a95806161634e19ed`** ("Verify and finish G05A/B/G06 rebuild") —
บรีฟให้ทำต่อจาก `b9cc9bf` (ไม่ใช่เริ่มใหม่): เรนเดอร์ยืนยัน fix → เช็ค [LAYOUT] → ตรวจเฟรม
(Claude+Gemini) เน้นตำแหน่ง P ต้อง ~55% จาก A → deploy ทับ 3 ไฟล์ → merge branch
`gear-geometry-rebuild-w06` เข้า main → push — **ยังไม่มี notification ว่าเสร็จ**

**ขั้นตอนต่อ (session ใหม่หรือหลังโควตารีเซ็ต):**
1. `ListAgents` เช็คว่า `a0fe78064929d0d69` ยังอยู่ไหม (running/completed) — ถ้าอยู่ `SendMessage`
   ต่อ ไม่ dispatch ใหม่
2. ถ้า "completed" แต่ result text บอกว่ายัง "รอ/monitoring" อยู่ → **ยังไม่เสร็จจริง** สั่งให้
   resume แล้วบล็อกจนจบจริง (ดู memory `feedback-subagent-ends-turn-while-polling`)
3. งานที่เหลือให้ทำ: แก้ layout ให้ผ่านครบ 3 scene → เรนเดอร์เต็ม → ตรวจเฟรม (Claude+Gemini
   ทั้งคู่) → **เช็คตำแหน่ง P บนเส้น A-B ต้องอยู่ ~55% จาก A (ใกล้ B) ไม่ใช่ใกล้ A** → deploy ทับ
   `Exam_Prep\Mechanics of Machinery\anim\{G05A_PointsAndLines,G05B_SimilarTriangles,G06_PitchPoint}.mp4`
   → commit/push → merge branch `gear-geometry-rebuild-w06` เข้า main ถ้ายังไม่ merge
4. รายงาน Min ว่าเสร็จแล้ว พร้อมสรุปว่าแก้อะไรไปบ้าง

**งานอื่นที่ทำเสร็จระหว่างรอบนี้:** ส่งอีเมลเฟรมนิ่ง (ไม่ใช่วิดิโอเต็ม เพราะ base64 inline แพง
เกินไป) ของ `G06_PitchPoint` (คลิปเก่า) ไปที่ wichayapatmeen@gmail.com แล้ว — บอก Min ในอีเมล
แล้วว่ากำลังรีบิลด์คลิปใหม่อยู่ ไม่ต้องส่งซ้ำ

---

## 🔴 อัปเดต (2026-09-05 ~00:46) — โควตา 86% รอบ 2 แล้ว, subagent 2 ตัวยังรันอยู่ตอนหยุด

**สถานะตอนหยุด:**
- **Fluid W07 subagent** (`ad69050dbcee6d4e5` — ใช้ `ListAgents`/`SendMessage` ต่อได้ด้วยชื่อนี้): เพิ่ง resume ไป 1 รอบเพราะมันจบ turn เองตอนรอ render (run `33904924660`) ค้างอยู่ ยังไม่รู้ผลว่าเรนเดอร์ผ่านไหม — **สั่งไปแล้วให้ poll เองจนจบจริงๆ ไม่ใช่แค่เช็คแล้วจบ turn**
- **Mechanics Spur Gears subagent** (`a2e6eba118052af68`): ตอนหยุดยัง "running" อยู่ ไม่มี notification เสร็จเลย ไม่รู้สถานะ — เช็ค `ListAgents` ก่อนว่ายัง running จริงไหม

**ขั้นตอนตอนเปิด session ใหม่ (หลังโควตารีเซ็ต 06:09:59):**
1. `ListAgents` เช็คว่า 2 subagent นี้ยังอยู่ไหม (ชื่อ `ad69050dbcee6d4e5` กับ `a2e6eba118052af68`)
2. ถ้ายังอยู่ (completed หรือ running) → `SendMessage` ไปถามสถานะ/สั่งต่อ ไม่ต้อง dispatch ใหม่
3. ถ้าหายไป (ตายไปพร้อม session เดิมจริงๆ) → เช็ค `cd Desktop/manium && git log --oneline -10` + เช็ค anim/ ทั้ง 2 วิชาว่ามีคลิปใหม่ HC04+/G04+ มาหรือยัง แล้วตัดสินใจว่าจะ resume ต่อจากตรงไหนหรือ dispatch ใหม่
4. **บทเรียนจากรอบนี้: subagent ที่ต้องรอ cloud render นานๆ มักจบ turn เองตอนรอ (ไม่ error แต่ "completed" ทั้งที่งานยังไม่เสร็จ) — ต้องกำชับให้ poll แบบ blocking จริงๆ (shell loop + sleep) ไม่ใช่แค่ "เช็คสถานะแล้วจบ" ทุกครั้งที่ dispatch/resume งานที่มี cloud render ยาวๆ**

---

## ✅ อัปเดต (2026-09-05 ~00:10) — โควตารีเซ็ตแล้ว, subagent เดิม 2 ตัวตายเพราะ rate limit, dispatch ต่อใหม่แล้ว

**พบว่า subagent รอบแรก 2 ตัวตายจริงตอนโควตาหมด** (error 429 "session limit") แต่ทำความคืบหน้าจริงไปเยอะก่อนตาย:
- **Fluid W07:** เขียนโค้ดครบทั้ง 11 scene (HC04-HC14) ใน `hydraulic_circuits.py` + commit แล้ว มีของค้าง uncommitted อยู่ (fix HC06 loop + ลบ shift= ออกจาก caption ทั้งไฟล์) — **ผมเช็คแล้วว่าโค้ดสมบูรณ์ compile ผ่าน เลย commit+push ให้เองแล้ว** (`f8155d8`) — แต่**ยังไม่มีคลิปไหนเรนเดอร์เลยสักตัว** (anim/ ยังมีแค่ HC01-03 เดิม)
- **Mechanics Spur Gears:** เขียนได้ 15 scene (G01-G03, G07-G18) จาก ~30 ที่ต้องมี — **เจอช่องโหว่จริง: G04-G06 (หน้า 5-6 ซึ่งเป็นหน้าอนุมานหลักของบท ⭐⭐⭐) ยังไม่ได้เขียน** ต้องเติมก่อนถึงจะไปต่อหน้า 19+ ได้อย่างสมเหตุสมผล — **ก็ยังไม่มีคลิปไหนเรนเดอร์เลยเช่นกัน**

**Dispatch subagent ต่อใหม่แล้ว 2 ตัว (หลังโควตารีเซ็ต) — งานที่สั่งไปคือ "render+verify+deploy" เป็นหลัก (โค้ด Fluid เขียนเสร็จแล้ว) และ "เติมช่องโหว่ G04-06 แล้วต่อ + render+verify+deploy" (Mechanics)** — เช็คสถานะด้วย `ListAgents` ถ้าเปิด session ใหม่มาเจอข้อความนี้แล้วยังไม่มี notification ว่าเสร็จ

**สถานะ: งานของ session นี้เองเสร็จหมดแล้ว แต่มี 2 subagent (dispatch ผ่าน Agent tool) ที่ยังรันอยู่เบื้องหลังตอนโควตาหมด — session ใหม่ต้องเช็คก่อนว่ายังรันอยู่ไหม**

### ✅ งานที่เสร็จสมบูรณ์แล้ว session นี้ (ไม่ต้องแตะอีก)
1. **วิดีโอคิวบิก 3×3×3** (`Desktop/manium/rubiks_cube.py`, class `RubiksCube3D`) — เรนเดอร์ 1080p, ตรวจ 2 รอบ (Claude เอง + Gemini อิสระ) ผ่านสะอาด, แนบบอร์ดแล้ว
2. **เบนช์มาร์ก import โมเดล 3D ผ่าน Polyhedron** — ทดสอบลูกบาศก์/รถสังเคราะห์/โมเดลจริง 2 ตัว (sedan 2032 หน้า, ปลา 1799 หน้า) สรุปว่า import ได้จริงแต่ช้ากว่า native ~20-300 เท่า ไม่คุ้มใช้จริง — บันทึกลง `manim-teaching-video` skill §26 แล้ว (`Desktop/manium/import_benchmark*.py`, `model_a.obj`, `model_b.obj`)
3. **เบนช์มาร์ก CPU vs OpenGL บน Kaggle + Colab** — OpenGL ใช้ไม่ได้ทั้ง 2 แพลตฟอร์ม (ไม่มี hardware OpenGL จริง + โค้ด manim เองก็ crash) สร้าง skill ใหม่ `kaggle-manim-render` บันทึกครบ (`Desktop/powerfull_note/kaggle_manim_render_bench/`, `Desktop/manium/manim_cpu_vs_opengl_bench_COLAB.ipynb`)
4. **เทสความเร็ว render local** — เจอว่าเครื่อง Min ช้ากว่า cloud ฟรีทั้งคู่จริงๆ (background service กิน CPU) + เจอบั๊กจริง 2 อย่าง (รัน manim 2 ตัวพร้อมกันทำให้ช้าลงมาก, cancel/timeout ไม่ได้ฆ่า process จริง) — บันทึกลง `manim-teaching-video` skill §28 + memory `feedback-taskstop-timeout-leaves-orphans` แล้ว
5. **สกิลปรับปรุงระบบ** — เพิ่ม "หลักการปรับปรุงตัวเองต่อเนื่อง" ลงสกิลส่วนตัวของ Min ครบ 10 ไฟล์ + เชื่อม `Desktop/Main_note/Manim_Reference/` เข้า skill + เพิ่ม §27 smooth-transition + แก้ policy Gemini-เป็นผู้ตรวจหลัก (ดู memory `feedback-frame-verification-stays-with-claude` ฉบับล่าสุด)
6. **วิดีโอ Deep Learning ตัวแรก** — "Neural Network คืออะไร" (`Desktop/manium/neural_network_intro.py`) เสร็จ ตรวจแล้ว แนบบอร์ดแล้ว โน้ตอยู่ที่ `Desktop/Main_note/Deep_Learning/Deep Learning Series.md` (มีแผนตอนต่อไปในโน้ต: backprop, CNN, MNIST — ยังไม่ได้เริ่ม รอ Min สั่ง)

### 🔴 ยังรันค้างอยู่เบื้องหลังตอนโควตาหมด — เช็คก่อนทำอะไรใหม่
Dispatch ผ่าน Agent tool (`subagent_type: general-purpose`) แบบขนาน 2 ตัว ตอน ~16:20 (2026-09-04):

**1. "Fluid W07 Hydraulic Circuit clips"** — ทำ `Desktop/Main_note/Exam_Prep/Fluid Power Control/W07 บทเรียน — Hydraulic Circuit Design.md` ที่เหลือ 11 หน้า (หน้า 1,2,3,5,6,7,8,9,10,14,15 — หน้า 4,11-12,13 ทำไปแล้วเป็น HC01-03) ตั้งชื่อ HC04-HC14 ต่อ สร้างไฟล์ `Desktop/manium/hydraulic_circuits.py`

**2. "Mechanics W06 Spur Gears clips"** — ทำ `Desktop/Main_note/Mechanics of Machinery/📘 W06 บทเรียนละเอียด — เฟืองตรง (Spur Gears)...md` ทั้ง 39 หน้า (ยังไม่เคยทำทีละหน้าเลย) ตั้งชื่อ G01+ สร้างไฟล์ `Desktop/manium/spur_gears.py` — สั่งไว้ว่าทำไม่ครบ 39 ในรอบเดียวก็ได้ ให้รายงานตามจริง

**ขั้นตอนที่ต้องทำตอนเปิด session ใหม่:**
1. เช็คว่า subagent ทั้ง 2 ยังรันอยู่ไหมด้วย `ListAgents` — ถ้ายังอยู่ ใช้ `SendMessage` ต่อได้เลย (ระบุชื่องานที่ตรงกับด้านบน ไม่ต้องเดา ID)
2. ถ้าหายไปแล้ว (agent ตายไปพร้อม session เดิม) เช็คว่าทำไปถึงไหนแล้วจริงๆ: `cd Desktop/manium && git log --oneline -20` ดู commit ใหม่ + เช็คไฟล์ `hydraulic_circuits.py`/`spur_gears.py` มีอยู่ไหม + เช็ค anim/ folder ทั้ง 2 วิชาว่ามีคลิปใหม่มาหรือยัง (`HC04+`, `G01+`)
3. ถ้าทำไปครึ่งทาง ให้ dispatch subagent ใหม่ต่อจากจุดที่ค้าง (บอกให้เช็คงานเดิมก่อนแล้วทำต่อ ไม่ใช่เริ่มใหม่) — บรีฟเดิมอยู่ในข้อความ Agent call ของ session นี้ (ดูใน context เดิมถ้า resume ได้ หรือใช้โครงเดียวกับที่อธิบายไว้ข้างบน)
4. **โควตาเพิ่งรีเซ็ต — งานยังเหลือเยอะ (2 ก้อนใหญ่) เริ่มงานใหม่ได้แต่ระวังอย่าเปิดงานที่ 3 ซ้อนจนกระจายเกินไป**

### 📌 หมายเหตุอื่น
- section ที่ผูกอยู่: **`main`**
- ห้ามลืม: **run-both/Gemini-primary policy** ใหม่ — ให้ Gemini ตรวจเฟรมเป็นหลักเพื่อประหยัดโทเคน ไม่ต้องตรวจซ้ำเองทุกครั้ง (เก็บไว้เฉพาะแพ็กเกจสำคัญจริงๆ)

---

## 🔴 อัปเดต (2026-09-05 ~12:05) — โควตา 89% รอบ 3 — Fluid+Mechanics เสร็จหมดแล้ว เหลือแค่ fix เล็กน้อย + ไฟล์ค้าง

**✅ Fluid W07 (Hydraulic Circuit Design): เสร็จสมบูรณ์ 100%** — ครบ 14 คลิป (HC01-14) เรนเดอร์+ตรวจ (Gemini + ซูมเช็คเอง)+แนบบอร์ด+ลงติวๆ+ฝังโน้ต+push ครบหมด ไม่มีอะไรค้าง

**✅ Mechanics of Machinery W06 Spur Gears: เสร็จ 100% ทั้ง 39 หน้า (36 คลิป G01-G38)** — deploy ครบหมดแล้ว (project บอร์ดใหม่ "W06 Spur Gears (Mechanics of Machinery)") — **แต่เจอ 5 จุดบกพร่องจริงจาก Gemini review รอบ 2** (ตรวจ 18 คลิปหลังที่ subagent เดิมไม่ได้ตรวจ) กำลังแก้อยู่:
1. G35 — สูตรโดนตัดขอบขวาจอ
2. G25 — สูตร Z ทับเส้นวงกลม
3. G31 — ตาราง column German เลื่อนหลุด
4. G23 — มุม pressure angle กลับด้าน (340° แทน 20°) + เส้นทับป้าย P
5. G20 — เส้น line of action สั้นไปไม่ถึง E2 + ป้าย A ทับป้าย E1

**✅ แก้ครบทั้ง 5 จุดแล้ว จริงจบสมบูรณ์** (`a81c494881bdf8727` รายงานเสร็จ) — commit `e8ba607`, render+ซูมเช็คแต่ละจุดยืนยันแล้ว, deploy ทับไฟล์เดิมแล้ว **Mechanics Spur Gears ตอนนี้เสร็จ 100% ไม่มีอะไรค้างแล้ว**

รายละเอียดสาเหตุที่เจอ (กันลืม):
- G35: `eq2` centered ทับ `eq1` แบบไม่ใส่ `aligned_edge` เลยล้นขวาจอ 0.126 หน่วย — แก้ align ขอบขวาแทน
- G25: **จริงๆ code เก่าถูกแก้ไปแล้วในอีก commit ก่อนหน้า (`2e1b3e3`) แต่ mp4 ที่ deploy ไว้เก่ากว่า** (render ไม่ทันหลัง fix) — เพิ่ม margin อีกหน่อยแล้ว re-render ใหม่ให้ตรงกับ code ปัจจุบัน
- G23: `Angle()` สลับ argument order ทำให้ได้มุม 340° แทน 20° จริง + ป้าย P ทับเส้นตัวเอง
- G31: แต่ละแถวตารางจัด column อิสระกันไม่มี shared x — แถว "Module m" หลุด
- G20: เส้น line-of-action extrapolate ไม่ถึง E2 จริง (สั้นไป 0.42 หน่วย) + ป้าย A ทับโซนป้าย E1

**🔴 ค้างรอ Min ตอบ:** Min บอกว่ามีไฟล์ `download/ai_tew.dxf` ที่มีเนื้อหาถูกต้องของหน้า 5-6 (Mechanics of Machinery) ให้เอาไปแก้วิดิโอ — **หาไฟล์นี้ไม่เจอเลยในเครื่อง** (เช็คแล้ว: `C:\Users\wicha\Downloads`, `.claude\downloads`, โปรเจกต์ powerfull_note) — ถาม Min แล้วให้ยืนยัน path จริงหรือส่งไฟล์มาทางแชทแอป ยังไม่ได้คำตอบตอนโควตาหมด — **เช็คเรื่องนี้ก่อนเป็นอันดับแรกตอนกลับมา**

**Deep Learning + เบนช์มาร์กต่างๆ (คิวบิก, import 3D, Kaggle/Colab, local speed):** เสร็จหมดแล้วจาก session ก่อนหน้า ไม่มีอะไรค้าง

---

## 🔴 อัปเดตล่าสุด (2026-09-04 ~01:35) — Q1 fix เสร็จ, Q2 แพ็กเกจใหม่เสร็จ, Min ไปนอนแล้ว มีของค้างรอตอบพรุ่งนี้

**สถานะ: งานที่ทำเสร็จแล้วครบ ไม่มีอะไรพังค้าง — มี 1 คำถามใหญ่รอ Min ตอบตอนตื่น (cloud vs local transcription)**

### งานที่เสร็จแล้ว session นี้
1. **แก้ omega-arrow bug ในแพ็กเกจ Q1** (`icr_gear_slider.py`) — เปลี่ยน `CurvedArrow` เป็น `Arc` จริง
   ที่ centered บนเฟือง, บันทึกบทเรียนลง `manim-teaching-video` skill §8 แล้ว
2. **ตอบคำถาม Min เรื่อง render-round/frame-review count แบบตรงไปตรงมา** (ใช้ git log + gh run list
   เป็นหลักฐานจริง ไม่เดา) + ทดสอบ `delegate_to_gemini` ยืนยันว่าใช้ได้จริง (ดูรูปได้ด้วย แต่ latency
   ไม่นิ่ง เคยค้าง 24+ นาที) + รวมคลิป Q1 ทั้ง 9 เป็นวิดีโอเดียว (2:27→2:35 หลังแก้เพิ่ม) แนบบอร์ดแล้ว
3. **แก้ Q1 คลิป 04/07 ตามฟีดแบ็ก Min** — เพิ่มกฎ "โชว์สูตรตัวแปรก่อนค่อยแทนเลข" (บันทึกลง
   `visual-for-teach` skill ใหม่แล้ว) + อธิบาย "ทำไมใช้ r_x=4 ไม่ใช่ r_y=6.93" ให้ชัดในคลิป07 —
   render/verify/รวมคลิปใหม่/แนบบอร์ดครบ
4. **สร้างแพ็กเกจใหม่ทั้งชุด: Q2 กลไกปลอกไถลบนแขนหมุน** (`q2_sliding_collar.py`, 8 คลิป, 1:48) —
   โจทย์ที่ Min ส่งรูปมา (rod AB pinned ที่ A, collar C ไถลไปตามแขนพร้อมปักหมุดกับ CD ที่หมุด D คงที่)
   - **geometry spec**: `Desktop/Main_note/Claude_Specs/Manim — Q2 Sliding-Collar Rod-Linkage Geometry Spec.md`
   - คำตอบ v_C = 3√3 ≈ 5.196 m/s (ซ้าย), ω_DC = 6√3 ≈ 10.39 rad/s (ทวนเข็ม) — ตรวจ 2 วิธีแล้วตรงกัน
   - เจอบั๊กจริงระหว่างทาง: Thai text ใน `MathTex \text{}` พัง LaTeX บน cloud (บันทึก skill แล้ว),
     ป้าย omega_AB/alpha_AB โดนตัดขอบจอซ้าย, ลูกศรทับข้อความ 60° — **แก้หมดแล้ว ตรวจเฟรมจริงยืนยันแล้ว**
   - render ผ่าน GitHub Actions ครบ, รวมคลิป, แนบบอร์ดแล้ว (ยังไม่ได้เปิดให้ Min ดูเพราะเขาหลับไปแล้ว)
5. **เพิ่มกฎใหม่ลง `manim-teaching-video` skill**: §25 ใช้ `ReplacementTransform` แทน Fade เมื่อของใหม่
   "วิวัฒนาการ" มาจากของเก่า (ไม่ใช่ blanket rule — สลับกับของที่คนละเรื่องกันยังใช้ Fade เหมือนเดิม)
6. **บันทึก memory ใหม่**: `feedback-use-obsidian-as-external-memory.md` — Min อนุญาตให้ใช้ vault
   เป็นความจำสำรองสำหรับ content ใหญ่ๆ ไม่ใช่แค่ deliverable สุดท้าย

### 🔴 ค้างรอ Min ตอบพรุ่งนี้ (สำคัญที่สุด — ถามก่อนเริ่มงานใหม่)
**โปรเจกต์ใหม่ที่ Min ขอก่อนนอน:** วิจัยฟีเจอร์/คำสั่ง/advanced techniques ทั้งหมดของ Manim library
ผ่าน YouTube (เน้น 3Blue1Brown), ถอดคลิปด้วย `comprehend_video`, เซฟเป็นโน้ต Obsidian พร้อมรูปแนบ,
แล้วใช้ `/graphify` ทำ knowledge graph ให้ย้อนดูได้ — **Min สลับใจไปมาเรื่อง cloud vs local transcription
3 รอบติดกัน** (เอา Groq cloud → ไม่เอา ใช้ local ฟรี → อยากได้ cloud เพราะเร็วกว่า → ถามเรื่อง GitHub
Actions) **ไม่ได้ปิดท้ายชัดเจนก่อนหลับ — ต้องถามให้แน่ชัดอีกทีก่อนเริ่ม** อย่าเดาเอง

สิ่งที่ตรวจแล้ว: มี Groq Whisper endpoint (`whisper-large-v3`) เขียนไว้ใน `server.js` แล้วจริง
(บรรทัด ~1498) แต่ **ไม่มี `GROQ_API_KEY` ใน .env** — ถ้า Min เลือก cloud ต้องขอ key จาก Min ก่อน
(สมัครแทนไม่ได้ ต้องผูกบัญชี Min เอง) วิดีโอตัวแรกที่เลือกไว้: "How I animate 3Blue1Brown videos -
A Manim Demo" (54 นาที, ช่อง 3Blue1Brown เอง) — ยังไม่ได้เริ่มถอดคลิปจริงเลย

**ข้อความสุดท้ายก่อนหลับ (สำคัญ): Min เสนอ Kaggle** (มี GPU T4 ฟรี ไม่ต้องขอ API key) เป็นตัวเลือก
ที่ 3 — ฟังดูลงตัวที่สุด (เร็วเพราะมี GPU จริง + ฟรี 100%) **เริ่มจากตรงนี้ก่อนตอนตื่นมาคุยกัน** ก่อนจะ
ไปเขียน pipeline ใหม่ยืนยันกับ Min อีกทีว่าใช่ทางที่ต้องการจริงๆ (เขาสลับใจมาแล้ว 4 รอบในคืนเดียว)

**คลิปวิดีโอ Q2 ที่เพิ่งเสร็จ ยังไม่ได้เปิดให้ Min ดู** (แนบบอร์ดไว้แล้วเท่านั้น) — เปิดให้ดูตอนเขาตื่น
หรือรอเขาเปิดเองก็ได้ (path: `Desktop/manium/anim_q2_sliding_collar/Q2_full_combined.mp4`)

### ✅ อัปเดต (~02:40) — Manim research project เริ่มจริงแล้วคืนนี้เอง (Min บอก "เริ่มวันนี้เลย")

**Pipeline ที่ใช้จริง (คนละทางกับที่คุยกันตอนแรก):** ดาวน์โหลดคลิปเต็ม (ไม่ใช่แค่เสียง, ผ่าน yt-dlp,
ส่วนใหญ่**ผ่าน Gemini delegate** ตามที่ Min สั่งชัดเจน "งานจิปาถะอย่างดาวน์โหลดให้ Gemini ทำ") → อัป
Kaggle dataset → รัน Kaggle GPU kernel transcribe (faster-whisper large-v3, compute_type fallback
chain) → โหลด transcript.json กลับมา → Gemini สรุปฟีเจอร์ Manim ที่พูดถึงเป็น markdown → เขียนโน้ต
Obsidian → `/graphify` สร้าง knowledge graph

**สร้าง skill ใหม่ตามคำสั่ง Min:** `~/.claude/skills/delegate-menial-tasks/SKILL.md` — งานจิปาถะ
(ดาวน์โหลด, CLI setup ซ้ำๆ) ต้องส่งให้ Gemini ก่อนเสมอ ไม่ทำเองถ้าไม่จำเป็น

**เจอ+แก้บั๊กจริงระหว่างทาง (จำไว้กันเจอซ้ำ):**
- Kaggle CLI บน Windows: PowerShell `Out-File -Encoding utf8` ใส่ BOM มาด้วย → `kaggle` (Python)
  อ่าน JSON metadata ไม่ได้ (`Unexpected UTF-8 BOM`) — ต้องเขียนไฟล์ metadata แบบไม่มี BOM เสมอ
  (ใช้ `open(path,'w',encoding='ascii')` หรือ python `write_text` ธรรมดา ไม่ใช่ PowerShell Out-File)
- yt-dlp ต้องมี JS runtime (deno) เดี๋ยวนี้ถึงจะดาวน์โหลด YouTube ได้เต็มที่ — ติดตั้งแล้ว (winget,
  path: `C:\Users\wicha\AppData\Local\Microsoft\WinGet\Packages\DenoLand.Deno_...\deno.exe`)
  ใช้ `yt-dlp --js-runtimes "deno:<path>"` ถ้า PATH ยังไม่รีเฟรช
- **Gemini เดาลิงก์ YouTube ผิดบ่อย** — ตอนขอให้ Gemini search หาคลิปเพิ่ม ได้ URL มา 8 อัน แต่ **4 อัน
  ตายจริง** (private/unavailable, ตรวจสอบแล้วไม่ใช่ปัญหา yt-dlp) — ต้องลองดาวน์โหลดจริงเช็คก่อนเชื่อ
  ทุกครั้ง อย่าเอา URL จาก Gemini ไปใช้ต่อโดยไม่ verify
- Kaggle free tier จำกัด **GPU kernel รันพร้อมกันได้แค่ 2** — คิวเวลาจะช้าถ้าจะทำหลายคลิปพร้อมกัน
- comprehend_video (local) ใช้โมเดล **"small"** ไม่ใช่ large — เร็วแต่แม่นน้อยกว่า Kaggle (large-v3)
  แถมมีบั๊กเดิม (WinError 5 rename race บน digest.json.tmp→digest.json — สถานะค้าง error แต่ข้อมูล
  จริงๆ ครบ ต้องเช็คไฟล์ตรงๆ ไม่เชื่อ status field เฉยๆ)

**ผลลัพธ์สุดท้าย (Min สั่งหยุดที่ ~06:28 "พอละ" — งานปิดจบแล้ว ไม่ใช่ค้าง):**
- 6 คลิปประมวลผลจริงครบ: 3Blue1Brown demo (54min), Full Course for Beginners, Making This
  Animation, Theorem of Beethoven intro (สั้น 4.4min), Hackl E01 Invitation, Hackl E04 Updater
  Functions (ManimCE core dev, series "Mathematical Animations WITH EASE")
- โน้ต 6 ไฟล์ที่ `Desktop/Main_note/Manim_Reference/` (+ รูป keyframe 20 ใบจากคลิปแรกเท่านั้น —
  คลิปอื่นไม่มีรูปเพราะ Kaggle path ไม่ extract keyframe แค่ transcribe เสียง — ถ้าอยากได้รูปคลิปอื่น
  ต้องรัน local `comprehend_video` เพิ่มต่างหาก)
- Graph: `Desktop/Main_note/Manim_Reference/graphify-out/` — **105 nodes, 151 edges, 11
  communities**, `graph.html` เปิดดูได้เลย
- **ถ้าจะขยายต่อ**: ใช้ `/graphify Desktop/Main_note/Manim_Reference --update` (ไม่ต้องรื้อทำใหม่
  ทั้งหมด) — แต่ Min บอกพอแล้วคืนนี้ ไม่ต้องเริ่มเองโดยไม่ถาม
- **caveman skill เปิดใช้งานอยู่** (Min พิมพ์ "use cave man" ชัดเจนแล้ว, ก่อนหน้านี้เสียงถอดผิดหลายรอบ)
  — ตอบสั้นแบบถ้ำ ยังไม่ได้สั่งปิด ถ้า Min อยากกลับปกติ พิมพ์ "stop caveman"

**ถ้า Min สั่งทำต่อ:** หาคลิปเพิ่ม (Gemini ช่วยหา แต่ verify URL ก่อนดาวน์โหลดเสมอ), หรือรัน local
comprehend_video เพิ่มเพื่อได้ keyframe รูปของคลิป 2-4 ด้วย, หรือขยาย graph ต่อเมื่อมีโน้ตเพิ่ม
(`/graphify <path> --update`)

---

## 🔴 อัปเดต (2026-09-03 ~14:55) — W06 Hydraulic Valves ครบ 25 หน้า | usage-guard เตือน 85%

**สถานะ: งานหลักเสร็จครบแล้ว** — คลิปสอน W06 ครบทุกหน้าที่ยังไม่มี (21 คลิปใหม่ + ของเดิม 4 = ครบ 25 หน้า)

### สิ่งที่ทำเสร็จ
- **โค้ด:** `Desktop/manium/hydraulic_valves.py` (~1,270 บรรทัด) push ขึ้น `minmin2017/manium` แล้ว
- **คลิป:** 21 ไฟล์ `HV01,02,03,04,06,07,08,09,10,11,12,14,16,17,18,19,20,21,22,23,24,25` อยู่ใน
  `Desktop/Main_note/Exam_Prep/Fluid Power Control/anim/` — ฝังในโน้ต W06 ทุกหน้า + แนบบอร์ดครบแล้ว
  (บอร์ด box `box_mtfsfmd4z0m1q`) — **ทุกคลิปผ่าน [LAYOUT] สะอาด + ตรวจเฟรมจริงแล้ว**
- **spec ใหม่ (Min เสนอเอง):** `Desktop/Main_note/Claude_Specs/Manim — Hydraulic Valve Geometry Spec.md`
  = แหล่งความจริงเดียวของพิกัดตัวเรือนวาล์ว มีตารางทุกชิ้น + ช่อง check ผลรวม + checklist ก่อน render
  **session หน้าที่แตะ geometry ต้องอ่าน/อัปเดตไฟล์นี้ก่อน**
- **ลิงก์อ้างอิงที่ Min ส่ง** (5 ลิงก์ powermotiontech/fluidpowerworld/YouTube) บันทึกในโน้ต W06 ช่อง Reference แล้ว

### บทเรียนสำคัญจาก session นี้ (บันทึกลง skill §24 + memory แล้ว)
1. **ชิ้นส่วนหลายท่อนที่ต้องเป็นเนื้อเดียวกัน ต้องคำนวณความกว้างจากขอบชิ้นข้างเคียง** ไม่ใช่ตั้งเลขกลมๆ
   — บั๊กนี้ทำให้ผนังวาล์วมีรูโหว่/มุมแหว่ง Min จับได้จาก screenshot 2 รอบ
   ตอนนี้โค้ดมี `_wall_segments()` + `assert` ว่าผลรวมต้องเท่าความยาว bore เป๊ะ
2. **เห็นอะไรแปลกตอนเช็คเฟรม = ต้องไล่หาสาเหตุทันที** ห้ามคิดเองว่า "แค่ดูไม่สวย พอใช้ได้"
   (Min: "ถ้าเรารู้สาเหตุแล้วจะไปแก้ได้ ทำไมต้องทนทาน")
3. สปูลต้องเป็น **land+groove จริง** และเรียงพอร์ต **T–A–P–B–T** ไม่งั้นอธิบายไม่ได้ว่าพอร์ตไหนต่อกับพอร์ตไหน

### ✅ เคลียร์แล้วหลังโควตารีเซ็ต (2026-09-03 ~17:35)
- **HV20 Counterbalance แก้เสร็จแล้ว** — เขียน spec §2b ก่อนแล้วสร้างซีนใหม่: เพิ่ม**เส้น pilot เส้นประจากท่อ cap-end**
  (ตัวที่ขาดไป) + แยกวาล์วเป็น 2 ทางเดินขนานจริง (throttle สปริงปิด + check valve) + เล่าครบ 2 สถานะ
  (ยก = ผ่าน check ฟรี / ลด = pilot เปิด throttle) + ย้ำ "ไม่มี pilot = ล็อกค้าง" + เทียบกับ pilot operated
  check valve หน้า 5 — ผ่าน linter สะอาด ตรวจเฟรมแล้ว ก็อปเข้า `anim/` แล้ว
- **ฝังคลิปในโน้ตครบแล้วทั้ง 25 หน้า** (รอบก่อนค้างไว้ที่หน้า 18 — เติม 19,20,21,22,23,24,25 ครบแล้ว)
- **เพิ่มกฎ "เขียน spec ก่อนวาด" ลง skill §24** ตามที่ Min สั่ง (พิสูจน์แล้วว่าได้ผล: รอบที่ทำตาม spec
  เรขาคณิตถูกตั้งแต่ render แรก เทียบกับ 3 รอบที่กะเอาเองแล้วพัง)

### งานที่ยังค้าง
- โน้ต W06 มีบรรทัดขยะ " pcv F" ที่ Min พิมพ์ค้างไว้ (แจ้งแล้ว ไม่ได้ลบให้ — ให้ Min ตัดสินใจเอง)
- ยังไม่ได้เทียบเนื้อหากับลิงก์อ้างอิงที่เหลืออีก 3 อัน (directional control / valve versatility / YouTube)
  — อันที่เทียบแล้วคือ counterbalance (แก้ตามแล้ว) ส่วน hydraulic symbology โดน 403 เปิดไม่ได้

---

## ✅ อัปเดต 21:16 — งานทดสอบ 3 แพลตฟอร์ม + ขยายบท 7 เสร็จสมบูรณ์แล้ว

## ✅ อัปเดตล่าสุด (2026-09-01 ~00:50) — Min กำลังจะปิด session นี้ (ใหญ่มากแล้ว)

**งานทั้งหมดในเซสชันนี้เสร็จและ deliver แล้ว ไม่มีอะไรค้าง:**
1. EPS บท 6 — S4B_BB_AA_ConductorProof (zoom_to retrofit) ตรวจแล้ว ส่งแล้ว
2. EPS บท 7 — 11 ซีน (EP11-EP21) รวม 3:55 นาที ตรวจแล้วทุกซีน ฝังโน้ต+บอร์ดแล้ว
3. ทดสอบเรนเดอร์ 3 แพลตฟอร์ม (GitHub Actions/local/Kaggle) เสร็จ มีตัวเลขเวลาเปรียบเทียบใน HANDOFF ด้านล่าง
4. `handoff-continuity-skill` — แพ็คสกิลสำหรับเพื่อน Min วางไว้ที่ Desktop แล้ว (มี HANDOFF.md protocol + check-quota.js แบบไม่ต้องพึ่งเซิร์ฟเวอร์)
5. เจอสกิล `caveman` (โหมดตอบสั้น) ที่ `.agents/skills/caveman/` — Min เคยพยายามสั่งให้ใช้หลายครั้งแต่เสียงถอดผิด ยังไม่ได้เปิดใช้งานจริง (รอ Min ยืนยัน session หน้า)
6. Push โปรเจกต์ powerfull_note ขึ้น GitHub เรียบร้อย (commit `0770d26`) — กัน secret (.gmail_token.pickle, certs/*.pem) + เก็บกวาด scratch/cache ออกจาก git แล้ว
7. **สร้าง MCP ใหม่ `run-filtered`** (`mcp-run-filtered.js`, ลงทะเบียนใน `.mcp.json` แล้ว, commit `353695b`) — รันคำสั่งแล้วกรอง progress-bar ทิ้งก่อนส่งกลับ Claude ทดสอบแล้วว่าใช้ได้จริง **session หน้าควรใช้เครื่องมือนี้แทน Bash ธรรมดา** ทุกครั้งที่คาดว่าคำสั่งจะมี progress bar เยอะ (install/clone/render/download) — วิธีใช้ดูใน CLAUDE.md หัวข้อ "MCP run-filtered"

**ถ้าเปิด session ใหม่:** ไม่มีงานค้างให้ทำต่อจากนี้ รอ Min สั่งงานใหม่ได้เลย — ถ้า Min ถามเรื่อง caveman skill ให้เสนอเปิดใช้งาน (`.agents/skills/caveman/SKILL.md`)

---

**สรุปสุดท้าย (อัปเดตอีกรอบ 21:35):** ซีรีส์ EPS บทที่ 7 ตอนนี้มี **11 ซีน (EP11-EP21) รวม
235.2 วิ (3:55)** — เพิ่ม EP21 (ตัวอย่างที่ 7-1 เต็มข้อ) เพราะ Min ทวงว่ายังไม่ยาวเท่าบท 6
(~4:10) ใกล้เคียงมากแล้วแต่ยังไม่ถึงเป๊ะ ทุกซีนตรวจแล้วจริง (linter + ถอดเฟรมอ่าน) ไม่ใช่แค่เขียนแล้วเดา
ทั้งหมดอยู่ใน `anim/` + ฝังโน้ต + แนบบอร์ดครบแล้ว โค้ดล่าสุดที่ `D:\Desktop\manium\eps_ch7.py`
push ขึ้น GitHub แล้ว

**บั๊กที่เจอ+แก้ระหว่างทาง (สำคัญ อ่านก่อนแก้ซีนใหม่):**
1. ข้อความไทยใน `\text{}` ของ MathTex → LaTeX build พัง (แก้แบบแยก MathTex+Text)
2. `title()` ยาว + `page_ref()` ชนกันมุมขวาบน — **เกิดซ้ำ 3 รอบ** (EP17, EP13, EP14) บันทึกเป็น
   skill §20 แล้ว — กฎ: title ที่ผสมอังกฤษ+ไทย หรือยาวเกิน ~30 ตัวอักษรไทยที่ size≥25 ให้ตัดสั้น
   ไว้ก่อนเลย อย่าเดา

**ผลทดสอบ 3 แพลตฟอร์ม (ตามที่ Min ขอ) — ตัวเลขจริงแต่เทียบกันไม่ 100% แฟร์:**
- **GitHub Actions:** เร็วสุด ~90-110s ต่อรอบ 3-4 ซีน (Docker image พร้อม manim+latex) — แนะนำให้ใช้เป็นหลักต่อไป
- **Local:** ~166s สำหรับ 4 ซีน (warm cache — โค้ดเดิมไม่เปลี่ยนหลายซีนเลยเร็วผิดปกติ ไม่ใช่ตัวเลขบริสุทธิ์)
  ต้อง **explicit permission จาก Min ทุกครั้ง** ก่อนใช้ (กฎเดิม "ห้าม local" ยังอยู่หลังจบเทสต์นี้)
- **Kaggle:** ใช้ได้จริงแต่ **ช้ากว่ามาก** — ~617s (10+ นาที) ต่อรอบ 4 ซีน ส่วนใหญ่หมดไปกับ apt-get
  ติดตั้ง texlive เต็ม + pip install manim ใหม่ทุกครั้ง (ไม่มี cache แบบ Docker image ของ GH Actions)
  **บทเรียนสำคัญ:** notebook ต้อง clone repo ไปไว้นอก `/kaggle/working/` เสมอ (เช่น `/root/manium`)
  แล้ว copy เฉพาะไฟล์ผลลัพธ์ (mp4) มาไว้ที่ `/kaggle/working/output/` — ไม่งั้น Kaggle จะเซฟทั้ง repo
  (มี git history + cache หลายร้อยไฟล์) เป็น kernel output ทำให้ดาวน์โหลดกลับไม่ไหว (เจอปัญหานี้จริง
  รอบแรก ต้องเขียน notebook ใหม่ — เวอร์ชันที่ใช้ได้อยู่ที่ `kaggle_manim_ch7/render_eps_ch7.ipynb`)
- **สรุปเชิงปฏิบัติ:** GitHub Actions คือตัวเลือกที่ดีที่สุดสำหรับงานจริงต่อไป (เร็ว + ไม่ต้องขอ
  permission พิเศษ) Kaggle เก็บไว้เป็นทางเลือกสำรองเวลา GH Actions มีปัญหา (เช่น rate limit)

**ยังไม่ได้ทำ (ถ้า Min อยากให้ทำต่อ):**
- ยังไม่ถึง 4:00 เป๊ะ (ขาด ~25 วิ) — ถามว่าจะขยายอีกนิดไหม หรือ 3:35 พอแล้ว
- ยังไม่ได้ต่อคลิปทั้ง 10 ตัวเป็นวิดีโอเดียวด้วย ffmpeg xfade (ดู skill §17 เรื่อง `-pix_fmt yuv420p`)
- ยังไม่ได้ลบไฟล์ทดสอบเก่าที่เกลื่อน `D:\Desktop\manium\_dl_*`, `_local_test_render*` (ไม่กระทบอะไร
  แค่เปลืองพื้นที่ ลบได้เมื่อสะดวก)

---

> อัปเดตล่าสุด: 2026-08-31 ~19:26 (โควตา session ถึง 85% — usage-guard สั่งหยุดรับงานใหม่)

## 🔴 งานล่าสุดที่ค้างอยู่ (สำคัญที่สุด — อ่านก่อน)

**งาน:** Min ขอ "test render 4min++ วีดีโอบท 7 (EPS) โดยเตรียมเนื้อหาดีๆ บน github, kaggle และ local (ให้ทรัพยากรทั้งหมด)"
- Min **อนุญาต local render เฉพาะทดสอบนี้เท่านั้น** (ปกติห้ามเด็ดขาด — กฎเดิมยังอยู่หลังจบเทสต์นี้)
- ยืนยันขอบเขต: ครอบทั้งบท 17 หน้า (เหมือน EPS บท 6)
- Min ให้ฟีดแบ็กสำคัญระหว่างทำ: **"ต้องคิดด้วยว่าตอน zoom จะกระทบอะไรบ้าง"** (ห้ามแก้บั๊กทีละจุดที่เจอแล้วจบ ต้องคิดผลกระทบทั้งหมดก่อน) และ **"เช็คละเอียดๆ ไล่ตามเหมือนดูวิดีโอจริง เฟรมต้องสัมพันธ์กับเฟรมก่อนหน้า"** — กฎนี้ใช้กับงานเช็คคลิปทุกครั้งต่อจากนี้

### ทำไปแล้ว (ก่อนโควตาหมด)
- เจอว่ามีไฟล์ `D:\Desktop\manium\eps_ch7.py` อยู่แล้ว (EP11-14 คลุมหน้า 1-11 — **แต่ไม่เคย push ขึ้น GitHub มาก่อน**, `git commit` ครั้งนี้ขึ้น "create mode" แปลว่าเพิ่ง track ครั้งแรก)
- เขียนเพิ่ม 4 ซีนใหม่ต่อท้ายไฟล์เดียวกัน (ครอบหน้า 12-17 ที่ยังไม่มีคลิป):
  - `EP15_Example72_FullWalkthrough` — ตัวอย่าง 7-2 เต็มข้อ (แม่แบบทั้งบท)
  - `EP16_NoLoadComparison_Example75` — เทียบ 3 กรณีไม่มีโหลด (1252.46/800/500 W)
  - `EP17_LongVsShortShunt` — เทียบ long-shunt (7-6) vs short-shunt (7-7)
  - `EP18_ChapterSummary` — สรุปท้ายบท
- `python -m py_compile` ผ่าน (เช็ค syntax แล้ว ไม่ได้เช็ค runtime/frame ใดๆ เลย)
- `git push` ขึ้น `minmin2017/manium` แล้ว (commit `63d5434`)
- **สั่งเรนเดอร์ผ่าน GitHub Actions แล้ว 1 ครั้ง** — run `https://github.com/minmin2017/manium/actions/runs/33391643043`
  (`render_manim.yml`, scene_names=EP15,EP16,EP17,EP18, quality=h, fps=30) — **ยังไม่ได้เช็คผลว่าผ่านหรือพัง**

### ยังไม่ได้ทำเลย (เริ่มจากตรงนี้ตอนโควตารีเซ็ต)
1. **เช็คผล run 33391643043** — `gh run view 33391643043 --log` เช็ค `[LAYOUT]` + ว่า render ผ่านไหม (อาจพังเพราะไม่เคย local-render/verify syntax เชิงลึกมาก่อนเลย เขียนรวดเดียวไม่ได้ทดสอบทีละซีน)
2. **ถ้าผ่าน:** ดาวน์โหลด → ถอดเฟรมเช็ค **ละเอียดแบบ Min สั่ง** (ไล่ดูทุกช่วงเหมือนดูวิดีโอจริง ไม่ใช่สุ่มจุดเดียว) — ดูตาราง EP17 (arrange_in_grid ที่ไม่เคยทดสอบมาก่อน มีความเสี่ยงสูงสุดว่าจะล้น/ทับ)
3. **ยังไม่ได้แตะ Kaggle เลย** — ต้องตัดสินใจว่าจะ render ซีนไหนผ่าน Kaggle (`kaggle_manim/render_manim.ipynb` มีอยู่แล้วที่ `powerfull_note` root, kernel id `minmin2017/manim-render`, เช็คว่า kernel ยังใช้งานได้จริงก่อน — ไม่เคยทดสอบในเซสชันนี้)
4. **ยังไม่ได้แตะ local render เลย** — Min อนุญาตแล้วเฉพาะเทสต์นี้ (venv น่าจะอยู่ที่ `manium/.venv_community` ตาม memory `project-manim-video-pipeline`)
5. เมื่อ 3 แหล่งเรนเดอร์เสร็จหมด: รวม/สรุปเวลาที่ใช้แต่ละแหล่ง (นี่คือ "การทดสอบ" ที่ Min ขอ) + ประกอบคลิปรวมกับ EP11-14 เดิมให้ครบทั้งบท (น่าจะเกิน 4 นาทีรวมแล้ว: EP11-14 ยาว 69.9s + EP15-18 ประมาณการ ~160-220s)
6. ฝัง/แนบบอร์ด/ติวๆ ตามขั้นตอนมาตรฐาน (skill §17 ท้ายๆ) หลังยืนยันทุกคลิปสะอาดแล้วเท่านั้น

### ⚠️ ความเสี่ยงที่ยังไม่ตรวจ (บอก Min ตรงๆ ถ้าถามว่าเสร็จหรือยัง — ยังไม่เสร็จ)
- โค้ด EP15-18 เขียนรวดเดียวไม่เคยเห็นเฟรมจริงแม้แต่เฟรมเดียว — สไตล์ต่างจาก EP11-14 (ใช้ `caption_top` ไม่ใช่ `caption` เดิม, ผสมกันในไฟล์เดียวกันได้เพราะคนละคลาส แต่ต้องดูว่าดูแปลกๆ ตอนเรียงต่อกันไหม)
- ตัวเลขในสคริปต์ก็อปจากโน้ต `W06-07 บทที่7...md` มาตรงๆ (โน้ตตรวจเลขซ้ำแล้ว เชื่อได้) แต่ยังไม่ได้ตรวจว่าใส่ในโค้ด MathTex ถูกต้อง 100% (พิมพ์ผิดตัวเลขได้ง่าย)

### ✅ อัปเดต (12:40, โควตา Min ขยับเพดานเป็น 94% ให้ทำต่อ) — GitHub Actions เสร็จและตรวจแล้ว
1. **เจอบั๊กจริง 2 จุด แก้แล้ว:**
   - ข้อความไทยใน `\text{}` ของ MathTex (EP17 `l_form`/`r_form`) → LaTeX build พัง (`ValueError: latex error converting to dvi`) — แก้โดยแยกเป็น MathTex (แค่สูตร) + Text (ไทย) คนละก้อน วางเรียงด้วย VGroup().arrange() แทน (ตรงกับ memory `feedback-manim-verify-frames.md` ที่เคยเจอมาก่อน)
   - EP17 หัวเรื่องยาวเกินไปชนป้าย page_ref มุมขวาบน 21% (layout linter จับได้เอง) → ตัดหัวเรื่องให้สั้นลง
2. **เรนเดอร์ผ่าน GitHub Actions สำเร็จครบ 4 ซีน** — layout linter ผ่านสะอาดหมด (run `33392058892` สำหรับ EP15/16/18, run `33392347874` สำหรับ EP17 ที่แก้แล้ว)
3. **ดาวน์โหลด + ถอดเฟรม (contact sheet 4 จุด/ซีน) เช็คแล้ว — สะอาดทุกจุด** ตัวเลขตรงกับโน้ตทุกตัว (84.07%, 1252.46/800/500W, 82.00%/82.61%) — **แต่เป็นการเช็คแบบสุ่มจุด ไม่ใช่ไล่ดูทุกเฟรมต่อเนื่องแบบ "ดูวิดีโอจริง" ตามที่ Min สั่งไว้ (ยังไม่ได้ทำแบบนั้นเพราะเวลา/โควตาจำกัด)**
4. **คัดลอกเข้า `anim/` + ฝังในโน้ต + แนบบอร์ดครบทั้ง 4 คลิปแล้ว**

### ⏱️ ปัญหาที่พบ — ความยาวรวมยังไม่ถึง "4min++" ตามที่ขอ
- EP11-14 (เดิม) = 69.9s ; EP15-18 (ใหม่) = 69.1s (25.1+17.4+17.5+9.1) ; **รวม = 139s ≈ 2.3 นาทีเท่านั้น**
- ยังไม่ได้บอก Min เรื่องนี้ตรงๆ — **ต้องแจ้งเมื่อคุยกันรอบหน้า** และถามว่าจะขยายเนื้อหาเพิ่ม (เช่น หน้า 4-6 eddy/hysteresis แบบละเอียดกว่า EP13 เดิม, หรือทำ intro/roadmap สไตล์ ch6 S1) หรือพอแค่นี้

### 🔄 สถานะ local + Kaggle (ทดสอบ 3 ทางตามที่ Min สั่ง) — ค้างอยู่ตอนหยุด
- **Local:** รันอยู่ที่ `D:\Desktop\manium\.venv_community\Scripts\python.exe -m manim -qh --fps 30 eps_ch7.py EP15... EP16... EP17... EP18... --media_dir _local_test_render` log ที่ `D:\Desktop\manium\_local_render_log.txt` — ณ ตอนหยุด **เสร็จไปแล้ว 3/4 ซีน** (เช็คด้วย `grep -c "\[LAYOUT\] =====" _local_render_log.txt`) — **ใช้ eps_ch7.py เวอร์ชันเก่า (ก่อนแก้บั๊ก EP17!)** เพราะ start ก่อนแก้โค้ด → ถ้าจะเทียบเวลาให้แฟร์ ต้อง**รันใหม่**ด้วยโค้ดเวอร์ชันล่าสุด (commit `661b13b`) ไม่ใช่เอาผลรอบนี้มาเทียบตรงๆ
- **Kaggle:** kernel `minmin2017/render-eps-ch7` (สร้างใหม่แยกจาก kernel เดิม `manim-render` ที่เป็นโปรเจกต์ไฮดรอลิกคนละเรื่อง) — push แล้ว รันอยู่ ยังไม่เสร็จตอนหยุด เช็คด้วย `kaggle kernels status minmin2017/render-eps-ch7` แล้วดาวน์โหลดด้วย `kaggle kernels output minmin2017/render-eps-ch7 -p <dir>`
  - ไฟล์อยู่ที่ `C:\Users\wicha\Desktop\powerfull_note\kaggle_manim_ch7\` (แยกโฟลเดอร์เพื่อไม่ให้ทับ kernel เดิม — **สำคัญ:** `kaggle kernels push -p .` เจาะจงหาไฟล์ชื่อ `kernel-metadata.json` เป๊ะๆ ในไดเรกทอรีนั้น ถ้ามีหลาย notebook ต้องแยกคนละโฟลเดอร์เสมอ ห้ามใช้ชื่อไฟล์อื่นแล้วหวังว่าจะถูกหยิบ)

### ✅ อัปเดต (12:46, โควตา 90%) — local + Kaggle เสร็จทั้งคู่แล้ว
- **Local:** เสร็จครบ 4/4 ซีน 19:31:32-19:37:25 = **~5m53s** ไฟล์อยู่ที่ `D:\Desktop\manium\_local_test_render\videos\eps_ch7\1080p30\*.mp4` — **แต่ใช้โค้ดเวอร์ชันเก่าก่อนแก้บั๊ก LaTeX/EP17** (แปลกที่ไม่พังทั้งที่โค้ดมีบั๊ก Thai-in-MathTex — เครื่อง local อาจมี LaTeX toolchain ที่ทนกว่า cloud หรือ handle ต่างกัน ยังไม่ได้สืบสาเหตุ)
- **GitHub Actions run 33392058892** (รอบที่พังกลางคัน EP17): render step 12:30:47-12:32:28 = **~101s** สำหรับ 3 ซีนที่ทันเรนเดอร์ก่อนพัง (ไม่ใช่เวลาที่แฟร์ เพราะพังกลางคัน)
- **Kaggle:** kernel status = COMPLETE แล้ว กำลังดาวน์โหลด output ด้วย `kaggle kernels output minmin2017/render-eps-ch7 -p output` (ทำงานพื้นหลัง ยังไม่เสร็จตอนหยุด เช็คโฟลเดอร์ `C:\Users\wicha\Desktop\powerfull_note\kaggle_manim_ch7\output\`)
- **⚠️ ตัวเลขเวลาทั้งหมดข้างบนเทียบกันแบบแฟร์ไม่ได้** เพราะแก้บั๊กระหว่างทาง คนละเวอร์ชันโค้ด — **ถ้าต้องการตัวเลขเทียบจริง ต้องรันทั้ง 3 ทางพร้อมกันด้วยโค้ด commit `661b13b` (เวอร์ชันล่าสุด, แก้บั๊กครบแล้ว) ใหม่ทั้งหมด**

### ✅ อัปเดต (13:16, โควตา 91%, เพดานขยับเป็น 95%) — เจอปัญหาการออกแบบ Kaggle notebook
- **สาเหตุที่ดาวน์โหลด Kaggle output ช้ามาก/ไม่จบสักที:** notebook `render_eps_ch7.ipynb` ทำ `git clone` (ทั้ง repo `manium` — มี git history + `graphify-out/cache/ast/*.json` หลายร้อยไฟล์) **ลงตรง `/kaggle/working/` แล้ว `%cd manium`** — Kaggle เซฟทุกอย่างใต้ `/kaggle/working/` เป็น kernel output อัตโนมัติ ⇒ โดนแบกทั้ง repo (รวม `.git/`, cache, mp4 เก่าของโปรเจกต์อื่นอย่าง `ck40b_*.mp4`) ติดมาด้วย ทั้งที่ต้องการแค่ mp4 4 ไฟล์ใหม่
- ลอง `--file-pattern ".*\.mp4$"` แล้วก็ยังช้า/ไม่จบภายในเวลาที่มี — **ยังไม่ยืนยันได้ว่า Kaggle เรนเดอร์ 4 ซีนสำเร็จจริงหรือไม่** (kernel status = COMPLETE เฉยๆ ไม่ได้บอกว่า cell รันผ่านหรือ error กลางทาง)
- **แก้ตอนกลับมาทำต่อ:** เขียน notebook ใหม่ให้ clone ไปไว้ location อื่น (เช่น `/tmp/manium` หรือ `~/manium`) แล้ว copy **เฉพาะ mp4 ที่เรนเดอร์เสร็จ** มาไว้ที่ `/kaggle/working/output/` ก่อน — จะได้ output สะอาด ดาวน์โหลดไวขึ้นมาก ไม่ต้องแบกทั้ง repo
- ไฟล์ notebook ปัจจุบันอยู่ที่ `C:\Users\wicha\Desktop\powerfull_note\kaggle_manim_ch7\render_eps_ch7.ipynb` (kernel: `minmin2017/render-eps-ch7`)

### ขั้นต่อไปตอนโควตากลับมา
1. เช็ค local (`grep -c "\[LAYOUT\]" _local_render_log.txt` ควรได้ 4) + เช็ค Kaggle (`kaggle kernels status ...`) ให้เสร็จทั้งคู่
2. **รัน local ใหม่ด้วยโค้ดล่าสุด** (commit 661b13b ขึ้นไป) เพื่อเทียบเวลาแฟร์ๆ กับ GitHub Actions และ Kaggle
3. สรุปเวลาที่ใช้แต่ละทาง (นี่คือ "การทดสอบ" ที่ Min ขอจริงๆ) รายงานให้ Min
4. เช็คเฟรมแบบละเอียด "ไล่ดูเหมือนดูวิดีโอจริง" ตามที่ Min ย้ำ (ยังไม่ได้ทำ)
5. ถามเรื่องความยาว 2.3 นาที (ไม่ถึง 4min++) ว่าจะขยายไหม
6. ถ้าขยาย/ผ่านหมดแล้ว: ต่อคลิปทั้งชุด (EP11-18) ด้วย ffmpeg xfade (ดู skill §17 เรื่อง `-pix_fmt yuv420p`) เป็นวิดีโอเดียว

## 🎯 งานเก่าที่ทำเสร็จแล้ว (EPS บทที่ 6, ไม่ต้องแตะอีก)

**ชุดวิดีโอสอน EPS บทที่ 6 — 8 ซีน** เป็นงานหลักที่ Min สั่งไว้ก่อนนอน
คำสั่งเป๊ะๆ ของเขา: *"ผมจะไปนอน ฝากเรื่องวิดีโอด้วยนะ ทำต่อให้เสร็จ ถึงเปอร์เซ็นต์หมดก็ทำต่อตาม Hand off นั่นแหละ"*

### สถานะ ณ 01:55 — เกือบเสร็จแล้ว
- โค้ดครบ 8 ซีนที่ `D:\Desktop\manium\eps_ch6_master.py` (push แล้ว)
- **render เสร็จหมด · layout linter ผ่านสะอาดทั้ง 8 ซีน** (run `33328938131` + S1 แก้มุมกล้องใน `33329120935`)
- ✅ **คลิปทั้ง 8 ลงใน `anim\EPS6_*.mp4` แล้ว** (ปลอดภัยแล้ว ไม่หาย)
- ✅ **ฝังในโน้ต `W06-07 บทที่6 สอนทีละหน้า.md` แล้ว** (ตารางชุดวิดีโอด้านบนสุด)
- ✅ ส่งให้ Gemini รีวิวแล้ว (ถามไป 3 ข้อ: ความถูกต้อง BB/AA, ควรขยายตรงไหน, มุมอธิบาย emf=0)
- ✅ ตรวจเฟรมจริงของ S1 แล้ว (แก้มุมกล้อง phi 68°→34° เพราะแกนเพลาตั้งขึ้นผิดธรรมชาติ)

### ✅ รอบโควตาที่ 2 (05:50-06:15) ทำเพิ่มจนครบแล้ว
1. ✅ **แนบเข้ากระดาน + ลง ติวๆ ครบทั้ง 8 ซีนแล้ว**
   - กระดาน: `POST /api/videos/add` ผ่าน **Python** — ใช้ `os.path.join` อย่าเขียน backslash
     ตรงๆ ใน heredoc (มันกินตัว escape)
   - ติวๆ: MCP `register_video_study_auto` — **ถ้าเจอ `fetch failed` ให้ลองใหม่อีกรอบ**
     (เจอ transient error 1 ครั้ง ทั้งที่ study-app ตอบ HTTP 200 ปกติ ลองซ้ำแล้วผ่าน)
2. ✅ **ขยายเนื้อหาแล้ว** — รวม **3:37 → 4:10**
   - **S2** ใส่อุปมา "ใบมีดฟันเชือก" ของ Gemini (23.8 → 40.1 วิ)
   - **S3** ใส่ช่วงโหลดสวีป ลูกศร+ตัวเลขมุมเอียงวิ่งสด (27.6 → 37.8 วิ)
   - **S6** ใส่คู่คำถาม 6-12 vs 6-13 (31.5 → 38.0 วิ)
3. ✅ Gemini รีวิวแล้ว — **ยืนยันว่า BB/AA ที่ทำไว้ถูกต้อง ไม่ต้องแก้**

### ✅ รอบเช้า (06:15-10:50 ก่อน 93%) ทำเสร็จหมดแล้ว
1. ✅ ตรวจเฟรมจริง S4/S5/S7/S8 ครบ — S5 ตัวเลข 58+42=100 ถูก, S4 กลุ่มตัวนำถูกตามหนังสือ,
   S7/S8 ข้อความไม่ทับ ตารางเทียบครบ 4 แถวตรงหนังสือ
2. ✅ **รวมทั้ง 8 ซีนเป็นคลิปเดียว** `EPS6_FULL_บทที่6.mp4` (4:06, crossfade) — ฝังในโน้ต
   บนสุด (กล่อง ⭐), แนบกระดานแล้ว, เปิดให้ Min ดูแล้ว
3. ✅ ตอบคำถาม Min เรื่องความถูกต้อง — **เจอจุดที่ควรแก้จริง 1 จุด (ยังไม่ได้แก้):**
   **S4** ข้ามลำดับเหตุผลของหนังสือ (สนามเอียงก่อน → ค่อยแยกเป็น BB/AA) พูดแค่
   "ก้อนเดียวแยกดู 2 แง่" ทำให้ดูเหมือน 2 องค์ประกอบมีอยู่ตลอด ซึ่งไม่ตรงหนังสือหน้า 5
   → **เสนอแก้ให้ Min แล้ว ยังไม่ได้คำตอบ**
4. ✅ ตรวจจุดที่ Min ถาม (ลูกศรสีเหลืองชี้ซ้าย ใน S4) — **เทียบกับรูปหนังสือหน้า 6(ข) จริง**
   (มีลูกศรแดงในหนังสือชี้ทิศเดียวกัน) → **ยืนยันว่าถูกต้อง ไม่ต้องแก้จุดนี้**

### ✅ อัปเดต 11:35 — ปิดงานหลักครบแล้ว ทั้งบั๊กใหญ่และคำขอใหม่

**พบและแก้บั๊กเนื้อหาจริงจุดใหญ่:** S1/S4/S8/EP08B แบ่งกลุ่มกระแสตัวนำ ⊙/⊗ ผิดแกน
(เดิมบน/ล่าง ที่ถูกคือซ้าย/ขวาตามแนวแปรงถ่าน — ใกล้ N=เข้า ใกล้ S=ออก) ตรวจสอบกับ
ทั้งหนังสือ (รูป 6-2ข) และเว็บค้นหาแหล่งอ้างอิงภายนอก (GeeksforGeeks ฯลฯ) แล้ว
แก้ครบทุกไฟล์ + สร้าง S10 ใหม่ (หมุนทั้งระบบ, ระนาบเป็นกลางไม่หมุนตามล้อ) ตามที่ Min
ขอเพิ่ม — **render, ตรวจเฟรมจริง (ไม่ใช่แค่ผ่าน linter), เอาเข้าโน้ต/กระดาน/ติวๆ,
รวมคลิปเต็ม 10 ซีน (4:55) ครบหมดแล้ว** เปิดให้ Min ดูแล้ว

เพิ่ม skill §18 (ห้ามเชื่อฟิสิกส์ที่คิดเองโดยไม่เช็คแหล่งจริง) ตามที่ Min สั่งไว้ตรงๆ

## 🆕 คำขอใหม่ล่าสุดจาก Min — ยังไม่ได้เริ่มทำ (โควตาหมดพอดีตอนกำลังจะเริ่ม) [เก่า — ทำเสร็จแล้วด้านบน]
Min ขอ: *"อยากเห็นวิดีโอของอาร์เมเจอร์มันหมุน แบบพอมันหมุนแล้วสนามแต่ละจุดเปลี่ยนแปลงยังไง
ทำลูกศรเป็นเวกเตอร์ให้ดูหน่อย"*

**แผนที่วางไว้ (ยังไม่ได้เขียนโค้ด):** ซีนใหม่ (เช่น `S9_Bonus_RotatingConductorEMF`)
armature หมุนจริงผ่าน ValueTracker, มีตัวนำ ~12 เส้นรอบวง แต่ละเส้นมีเวกเตอร์ (ผ่าน
`always_redraw`) ความยาว ∝ |cos(a)| (a = มุมปัจจุบันเทียบแกนขั้ว) แสดง**แรงเคลื่อนเหนี่ยวนำ
ดิบก่อนผ่านคอมมิวเตเตอร์** (ไม่ใช่กระแส DC ที่เห็นใน S1/S4/S8!)

⚠️ **จุดที่ต้องระวังตอนเขียน (คิดไว้แล้ว อย่าลืม):** ต้องแคปชั่นบอกชัดว่านี่คือ EMF ดิบ
ในตัวนำแต่ละเส้น**ก่อน**คอมมิวเตเตอร์จัดกระแส ไม่ใช่ overturn ⊙/⊗ pattern คงที่ที่เห็นใน
S1/S4/S8 (นั่นคือกระแสหลังคอมมิวเตเตอร์แล้ว) — สองอย่างนี้เป็นคนละปริมาณกัน ถ้าไม่อธิบาย
แยกให้ชัด Min จะงงว่าทำไมขัดกับคลิปก่อนหน้า

Physics ที่ใช้: pole axis แนวนอน (N ซ้าย S ขวา), brush/neutral axis แนวตั้ง, ตัวนำที่มุม a
มีความเร็วเชิงสัมผัส (ทิศ a+90°), e ∝ sin(มุมระหว่าง v กับ B) = sin(a+90°) = cos(a)
→ max ตรงหน้าขั้ว (a=0,180°), เป็นศูนย์ตรงระนาบเป็นกลาง (a=90°,270°) — ตรงกับ EP07 เดิม
แค่ขยายจากติดตาม 1 ขดเป็นทั้งวงพร้อมกัน

### ขั้นตอนที่เหลือ (ทำตามลำดับ)
1. **เขียน+render `S9_Bonus_RotatingConductorEMF`** ตามแผนข้างบน
2. **ถาม/รอคำตอบ Min เรื่องแก้ S4** (ลำดับเหตุผล เอียงก่อนค่อยแยก) — ถ้าตอบมาแล้วให้ทำ
3. ตรวจเฟรม + เอาเข้าโน้ต/กระดาน/ติวๆ ตามขั้นตอนเดิม + รวมคลิปใหม่เข้า FULL อีกรอบถ้าต้องการ
4. เปิดให้ Min ดูด้วย **PowerShell tool** `Start-Process` (Bash `start` ไม่ขึ้นจอจริง)

## 🔍 ผลรีวิวจาก Gemini (ได้มาแล้ว 2026-08-31 ~02:00 · เอาไปใช้ได้เลย)

**1. BB/AA ที่ผมไม่ชัวร์ → ยืนยันว่าทำถูกแล้ว ✅** ตรงกับตำราสากล (Chapman / Fitzgerald / IEEE):
BB = ตัวนำบน-ล่าง = demagnetizing (สวน 180°) → แรงดันตก · AA = ตัวนำซ้าย-ขวา (ใต้หน้าขั้ว) =
cross-magnetizing (90°) → สนามบิด ระนาบเลื่อน → สปาร์ค **ไม่ต้องแก้คลิป S4**

**2. เห็นด้วยว่าควรขยาย S3 + S6 ก่อน** และเตือน 2 จุดที่ข้อสอบชอบออกแต่ผมยังใส่ไม่ครบ:
- **คำถาม 6-12 vs 6-13** (คู่เทียบ): แปรงถ่านที่ระนาบ**ทางกล** → สปาร์ค · ที่ระนาบ**ทางไฟฟ้า** →
  ไม่สปาร์ค **แต่เฉพาะที่กระแสโหลดค่านั้น** — ตอนนี้ S6 ใส่แค่คำถาม 6-11 ควรเพิ่มคู่นี้ด้วย
- ขอบเขตการแก้ของ interpole (เฉพาะโซนคอมมิวเตชั่น) vs ขดลวดชดเชย (ใต้หน้าขั้วทั้งหมด) —
  อันนี้ S7/S8 มีแล้ว แต่ควรเน้นให้ชัดขึ้น

**3. 🔪 มุมอธิบาย emf = 0 ที่ดีกว่าของผม — เอาไปใส่ S2 เลย** (ตอบคำแย้งของ Min ตรงๆ ว่า
"ฟลักซ์ยังไงก็ต้องมีตรงนั้น"):
> **เส้นแรง = เส้นเชือกขึงตึงแนวนอนจาก N ไป S · ตัวนำ = ใบมีด**
> - ใต้ขั้ว: ตัวนำวิ่งดิ่งลง → ใบมีด**ฟันขวางเชือก 90°** (sin90°=1) → ตัดเต็มที่ → emf สูงสุด
> - ที่ระนาบเป็นกลาง: ตัวนำวิ่งแนวนอน → ใบมีด**ลู่ไปตามเชือก** (sin0°=0) → **ไม่ได้ฟันโดนสักเส้น**
>   → emf = 0 **ทั้งที่เชือกยังอยู่หนาแน่นเท่าเดิม** ← จุดที่ Min เคยติด

## 📋 กติกาที่ Min กำหนดสำหรับวิดีโอชุดนี้ (ห้ามลืม)

1. **ข้อความอยู่โซนบนเท่านั้น** — แถบควบคุมโปรแกรมเล่นวิดีโอบังข้อความล่าง
   ใช้ `caption_top()` ไม่ใช่ `caption()` (mlib มีให้แล้ว)
2. **ป้ายอ้างอิงหน้า/รูป** มุมขวาบนทุกช่วง — `page_ref("หน้า 4 · รูปที่ 6-2")`
3. **สร้าง 3D จริง แต่เปิดฉากมองระนาบเดียวให้ดูเหมือน 2D แล้วหมุนกล้องเผยมิติ**
   เปลี่ยนฉากด้วยการเลื่อน/หมุน ไม่ใช่ตัดคลิป (ทำแล้วใน S1)
4. **เปิดด้วยแผนที่ทั้งบท** + ปิดแต่ละช่วงด้วยคำถามข้อสอบจริง (6-1..6-15)
5. **render บน cloud เท่านั้น** ห้าม local แม้แต่ตรวจ (skill §17)
6. **render ขนาน** ผ่าน `render_manim_parallel.yml` (matrix, ซีนละ runner)
7. ตรวจทั้งบทก่อนแตกซีน — *"การจะสอนคนที่ดี คุณต้องดูทั้งบทที่จะสอนก่อน แล้วค่อยมาแตกย่อย"*

## 🎬 โครงสร้าง 8 ซีน (เรียงตามหน้าหนังสือ)

| ซีน | หน้า | เนื้อหา |
|---|---|---|
| S1_Anatomy | 1-2 | แผนที่บท + กายวิภาค อาร์เมเจอร์/คอมมิวเตเตอร์/แปรงถ่าน **[3D reveal]** |
| S2_NeutralPlane | 1-2 | ระนาบเป็นกลางคืออะไร ทำไมแปรงถ่านต้องอยู่ตรงนั้น (รูป 6-1) |
| S3_TwoFields | 3-4 | สนาม 2 สนามบวกเวกเตอร์ → เบี่ยง (รูป 6-2) + เสริม vs หักล้าง |
| S4_BB_AA | 5-7 | BB=แรงดันตก / AA=สปาร์ค (รูป 6-3) |
| S5_Commutation | 7-8 | ส่งไม้ผลัดกระแส 100A (รูป 6-4) |
| S6_SelfInduction | 9-10 | เหนี่ยวนำในตัวเอง → ระนาบเลื่อนขยัก 2 (รูป 6-5, 6-6) |
| S7_Interpole | 11-12 | ขั้วแม่เหล็กเสริม (รูป 6-7) |
| S8_Compensating | 13-14 | ขดลวดชดเชย + ตารางเทียบ + สรุปบท (รูป 6-8) |

## ⚠️ บทเรียนจากรอบนี้ (อย่าทำซ้ำ)

- **ห้าม `self.play(FadeOut(capเก่า), FadeIn(capใหม่))`** — อยู่พิกัดเดียวกัน จะทับกัน 100%
  ระหว่างเปลี่ยน (บั๊กเดียวกับที่ทำให้คลิป EP09 เดิมอ่านไม่ออก)
  ใช้ `swap(เก่า, ใหม่)` ที่นิยามไว้ใน `eps_ch6_master.py` (ใช้ `Succession`)
- ป้ายกำกับต้องอยู่นอกวงกลม/เส้นสนาม — เช็คระยะจากรัศมีจริง ไม่ใช่กะเอา
- BB/AA: หนังสือหน้า 5 บอก **BB = ตัวนำบน-ล่าง** (สนามต่อต้าน → แรงดันตก),
  **AA = ตัวนำซ้าย-ขวา** (สนามขวาง → สปาร์ค) — ผมเคยสลับผิด แก้แล้ว
- ป้ายที่ `hud()` ไว้จะค้างที่จอตอนหมุนกล้อง → ต้อง FadeOut ก่อนหมุน (ทำแล้วใน S1)

## 🔧 งานอื่นที่เสร็จไปแล้วในเซสชันนี้

- **สร้าง GitHub Actions render pipeline จริง** (ก่อนหน้านี้ไม่เคยมี ทั้งที่แชทเก่าอ้างว่ามี)
  `render_manim.yml` (ซีนเดียว) + `render_manim_parallel.yml` (matrix ขนาน)
- **เร่งความเร็ว render 3 เท่า** วัดจริง 210s → 69s โดยเปลี่ยนไปใช้ Docker image
  `manimcommunity/manim:latest` แทนการ `apt-get install texlive` ทุกครั้ง
  (apt กิน 132s = 63% ของเวลาทั้งหมด, manim จริงแค่ 45s) — บันทึกใน skill §17 แล้ว
  ⚠️ shell default ใน container คือ `sh` ไม่ใช่ bash → ต้องใส่ `shell: bash`
- **EP05B** (ส่วนประกอบเครื่องกำเนิด ใครนิ่ง/ใครหมุน) + **EP08B** (สนามอาร์เมเจอร์
  มาจากไหน ทีละเส้นลวด) — เสร็จ ส่งให้ Min ดูแล้ว เข้าโน้ต/กระดาน/ติวๆ ครบ
- **ระบบ Hand off** — subagent แก้ให้ปลุก session เดิมแทนเปิดหน้าต่างใหม่แล้ว
  ยืนยันสดว่าใช้งานได้: `GET /api/agent/status?section=main` คืน `claude.online: true`
  ⚠️ agent ตัวนั้นแก้ `server.js` ด้วย → หน้าแอป Min น่าจะ reload ไปตอน ~01:31 (แจ้ง Min แล้ว)

## 📌 หมายเหตุ session

- section ที่ผูกอยู่: **`main`** (ตรงกับ env `CHAT_SECTION`) — arm Monitor ด้วย section นี้
- ตอบ Min เป็นภาษาไทยผ่าน `say_to_user` เสมอ
- Monitor ที่ poll สถานะ CI **ต้องเงียบ** emit เฉพาะตอนจบ (Min บ่นเรื่องเปลืองโทเคน)
