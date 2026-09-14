# Delta Academy — Video Edit Plan (A_LineOverview / B_Changeover)

เขียนโดย Claude 2026-09-14 สำหรับส่งต่อให้ Gemini ทำงานตัดต่อ
**เป้าหมายของคลิป:** ทำให้กรรมการเข้าใจ *กลไก* ของ Zero-Downtime Changeover Cell
(ส่วน ROI/ต้นทุนเป็นของเพื่อนร่วมทีม — **ห้ามใส่เนื้อหาเรื่องเงิน/ROI/ประหยัดกี่บาท ในคลิปนี้**)

---

## 0. ไฟล์ต้นทาง (ทุกไฟล์ 1280x720, 30fps, h264 — สเปกตรงกันหมด concat ได้โดยไม่ต้อง re-encode)

| ไฟล์ | ความยาว | เนื้อหา |
|---|---|---|
| `D:\unity_project\delta_academy\Recordings\A_LineOverview_DRAFT_25690914_020259.mp4` | 10.533s | ช็อตกล้องเคลื่อนที่เปิดเรื่อง (traveling establishing shot) วิ่งไปตามไลน์ |
| `D:\unity_project\delta_academy\Recordings\A_LineOverview_ZONES_25690914_132308.mp4` | 80.033s | 5 ช็อตล็อกมุมตามโซน (ดูตาราง §1.1) |
| `D:\unity_project\delta_academy\Recordings\B_Changeover_MULTICAM_25690914_132124.mp4` | 45.033s | ลำดับ changeover S1→S10 ตัดกล้องตามสถานะจริง |

> ⚠️ ใช้ไฟล์ตาม timestamp นี้เป๊ะๆ — ในโฟลเดอร์ `Recordings/` มีไฟล์เก่าหลายเวอร์ชันที่ยังมีบั๊ก
> (เช่น `A_LineOverview_ZONES_25690914_063523.mp4` มีบั๊กขวดทะลุเสา **ห้ามใช้**)

### 1.1 ตารางเวลาช็อตของ A (หลัง concat แล้ว)

| ช่วงเวลา | ช็อต | เนื้อหาที่เห็น |
|---|---|---|
| 0.0 – 10.5 | Traveling establishing | กล้องวิ่งดูภาพรวมทั้งไลน์ |
| 10.5 – 24.5 | Infeed Zone (14s) | Bottle Unscrambler, Star Wheel, Bottle Present Sensor, Stopper Cylinder |
| 24.5 – 48.5 | Filling Zone (24s) | Product Tank, Pump, Flow Meter, Anti-Drip Valve, หัวฉีด + ขวด |
| 48.5 – 58.5 | Capping Zone (10s) | Cap Feeder Hopper, Capping Head, Cap Present Sensor |
| 58.5 – 70.5 | End of Line (12s) | Checkweigher, Reject Station, Labeler, Outfeed Conveyor |
| 70.5 – 90.5 | Control Cabinet & HMI (20s) | ตู้คอนโทรล Delta, จอ HMI แสดงสถานะ/checklist |

**รวม 90.567s** — ตรงเป้า ~90s พอดี ไม่ต้องตัดทอน

---

## 2. งานที่ต้องทำ — เรียงตามลำดับ

### งาน A1 — Concat คลิป A (ทำก่อน ง่ายสุด ได้ของจริงทันที)

สเปกตรงกันหมด → ใช้ concat demuxer + stream copy (ไม่ re-encode = ไม่เสียคุณภาพ + เร็วมาก)

```bash
# สร้างไฟล์ list (path ต้องเป็น forward slash หรือ escape ให้ถูกบน Windows)
cat > /d/unity_project/delta_academy/Recordings/concat_A.txt <<'EOF'
file 'A_LineOverview_DRAFT_25690914_020259.mp4'
file 'A_LineOverview_ZONES_25690914_132308.mp4'
EOF

cd /d/unity_project/delta_academy/Recordings
ffmpeg -y -f concat -safe 0 -i concat_A.txt -c copy A_LineOverview_JOINED.mp4
```

**ตรวจหลังทำ:** `ffprobe` ต้องได้ duration ≈ 90.57s และต้องสกัดเฟรมที่ t=10.4 กับ t=10.7
มาดูจริงว่ารอยต่อไม่กระตุก/ไม่ดำค้าง (`ffmpeg -ss 10.4 -i ... -frames:v 1 -update 1 out.png`)

> ถ้า stream copy แล้วรอยต่อมีปัญหา (บางทีเกิดกับ h264 ที่ keyframe ไม่ตรง) ให้ fallback เป็น
> re-encode: `-c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p` แทน `-c copy`

---

### งาน A2 — ใส่ section title ลงคลิป A

ใส่ข้อความบอกชื่อโซนตอนเปลี่ยนช็อต ให้กรรมการรู้ว่ากำลังดูอะไรอยู่
(ในฉากมี label ชื่ออุปกรณ์ราย ๆ ชิ้นอยู่แล้ว — อันนี้คือ **หัวข้อระดับโซน** คนละชั้นกัน ไม่ซ้ำซ้อน)

**ข้อความ (ภาษาอังกฤษล้วน — ให้ตรงกับ label ในฉากที่เป็นอังกฤษอยู่แล้ว):**

| แสดงช่วง | ข้อความ |
|---|---|
| 1.0 – 9.0 | `ZERO-DOWNTIME CHANGEOVER CELL` |
| 11.5 – 17.5 | `1 / INFEED — Unscrambler & Star Wheel` |
| 25.5 – 31.5 | `2 / FILLING — Servo Nozzle, Controlled Point` |
| 49.5 – 55.5 | `3 / CAPPING — Cap Feeder & Capping Head` |
| 59.5 – 65.5 | `4 / END OF LINE — Checkweigher, Reject, Labeler` |
| 71.5 – 77.5 | `5 / CONTROL — Delta PLC + HMI` |

**ตำแหน่ง:** ล่างซ้าย (lower-third) — `x=60`, `y=h-110`
**สไตล์:** ตัวขาว ขนาด 30px มีกล่องดำโปร่ง 55% รองหลัง (`box=1:boxcolor=black@0.55:boxborderw=14`)
เพื่อให้อ่านออกทั้งบนพื้นสว่างและมืด

```bash
# ตัวอย่าง 1 บรรทัด — ทำทั้ง 6 อันในคำสั่งเดียวโดยคั่นด้วย comma ใน -vf
ffmpeg -y -i A_LineOverview_JOINED.mp4 -vf "\
drawtext=fontfile='C\:/Windows/Fonts/arialbd.ttf':text='ZERO-DOWNTIME CHANGEOVER CELL':\
fontcolor=white:fontsize=30:x=60:y=h-110:box=1:boxcolor=black@0.55:boxborderw=14:\
enable='between(t,1,9)',\
drawtext=fontfile='C\:/Windows/Fonts/arialbd.ttf':text='1 / INFEED — Unscrambler & Star Wheel':\
fontcolor=white:fontsize=30:x=60:y=h-110:box=1:boxcolor=black@0.55:boxborderw=14:\
enable='between(t,11.5,17.5)'\
" -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -c:a copy A_LineOverview_FINAL.mp4
```

> ⚠️ **กับดักที่เสียเวลาบ่อยบน Windows:** path ฟอนต์ใน `drawtext` ต้อง escape colon เป็น `C\:/Windows/...`
> (ใช้ forward slash) ไม่งั้น ffmpeg จะ parse `C:` เป็นชื่อ protocol แล้ว error แบบงงๆ
> และถ้าข้อความมีเครื่องหมาย `—` (em dash) แล้วมีปัญหา encoding ให้เปลี่ยนเป็น `-` ธรรมดาได้เลย
> **ตรวจด้วยการสกัดเฟรมจริงเสมอ** ว่าตัวหนังสือขึ้นครบทุกอัน ตรงเวลา ไม่ล้นจอ

---

### งาน B1 — คลิป B: ตัดสินใจเรื่องความยาวก่อน

**ปัญหา:** B ยาว 45.03s แต่เป้าเดิมคือ ~90s

**อย่าแก้ด้วยการ slow motion 2 เท่า** — คลิปนี้ขายเรื่อง "เปลี่ยนรุ่นได้เร็วโดยไม่ต้องหยุดไลน์"
การทำให้ดูช้าลงคือการทำลายสารหลักของตัวเอง

**ทางที่แนะนำ:** เพิ่มความยาวด้วย **การ์ดอธิบาย (title card)** คั่นเป็นช่วงๆ ซึ่งได้ 2 เด้ง —
ยาวขึ้น *และ* อธิบายกลไกชัดขึ้น (ตรงเป้าหมาย "ให้กรรมการเข้าใจกลไก" พอดี)

โครงที่เสนอ (รวม ~90s):
1. **การ์ดเปิด 6s** — `RECIPE CHANGEOVER: 250ml → 500ml` / บรรทัดรอง `No line teardown. No manual shimming.`
2. **คลิป B ช่วงแรก** (0–22s ของต้นฉบับ) — หยุดป้อนขวด, เติมขวดค้างท่อให้จบ, เคลียร์โซน
3. **การ์ดคั่น 5s** — `SAFETY INTERLOCK: nozzle retracts to home BEFORE rails move`
4. **คลิป B ช่วงหลัง** (22–45s ของต้นฉบับ) — ปรับความกว้างราง, ปรับความสูงหัวฉีด, First Article Check
5. **การ์ดปิด 6s** — `ONE RECIPE SELECT → SERVO-POSITIONED. REPEATABLE EVERY TIME.`

> **จุดที่ต้องถาม Min ก่อนลงมือ (อย่าเดาเอง):** 90s เป็นข้อกำหนดจริงของการแข่ง หรือเป็นแค่
> ตัวเลขประมาณ? เพราะถ้า 45s ใช้ได้ ก็ **ไม่ต้องยืดเลย** — คลิป 45s ที่กระชับดีกว่าคลิป 90s ที่ยืด
> ให้ทำงาน A1/A2 ให้เสร็จก่อน แล้วค่อยรอคำตอบเรื่องนี้

---

### งาน B2 — ใส่ callout ลงคลิป B (ทำได้เลย ไม่ต้องรอคำตอบข้อ B1)

จอ HMI ในฉากแสดงชื่อ state อยู่แล้ว **จึงไม่ต้องใส่ overlay ชื่อ state ซ้ำ** — ให้ใส่เฉพาะ
จุดที่ HMI มองไม่เห็น/อ่านไม่ทัน คือ 2 จังหวะที่เป็นหัวใจของกลไก:

| แสดงช่วง (โดยประมาณ — **ต้องสกัดเฟรมหาเวลาจริงก่อนใส่**) | ข้อความ |
|---|---|
| ตอนรางเลื่อนกว้างออก | `GUIDE RAIL — servo-positioned to recipe width` |
| ตอนหัวฉีดปรับความสูง | `FILL NOZZLE — Z-axis to recipe clear height` |

**วิธีหาเวลาจริง:** สกัดเฟรมทุก 2 วิตลอด 45s (`ffmpeg -ss N -frames:v 1`) แล้วดูว่าเฟรมไหน
เป็นภาพมุมบนของราง (RailTopCam) และเฟรมไหนเป็นมุมข้างหัวฉีด (NozzleSideCam) — **ห้ามเดาเวลา**
ให้รายงานเวลาจริงที่หาได้กลับมาด้วย

สไตล์/ตำแหน่ง: เหมือนงาน A2 ทุกอย่าง (ล่างซ้าย ขาว 30px กล่องดำโปร่ง) เพื่อให้ 2 คลิปดูเป็นชุดเดียวกัน

---

## 3. กฎการตรวจงาน (สำคัญที่สุด — โปรเจกต์นี้เคยพลาดเพราะข้อนี้มาแล้ว)

**`ffprobe` บอกว่าไฟล์ไม่เสีย ≠ เนื้อหาถูกต้อง** — บั๊กที่เจอในโปรเจกต์นี้ทุกตัว (กล้องผิด, ขวดทะลุเสา,
ตัวหนังสือกลับด้าน, ตัวหนังสือเล็กจนมองไม่เห็น) **ไม่มีตัวไหนเลย**ที่ `ffprobe` จับได้

ดังนั้นทุกครั้งที่ทำ output ใหม่ ต้อง:
1. สกัดเฟรมจริงออกมา **ดูด้วยตา** ที่จุดเปลี่ยนช็อตทุกจุด + ทุกจุดที่มีตัวหนังสือขึ้น
2. เช็คว่าตัวหนังสือ: อ่านออกไหม / สะกดถูกไหม / ไม่ล้นจอ / ไม่ทับของสำคัญ / ขึ้น-ลงตรงเวลา
3. รายงานกลับมาว่า **ตรวจเฟรมไหนบ้าง** (บอกเวลาเป็นวินาที) ไม่ใช่แค่บอกว่า "เสร็จแล้ว"

---

## 4. ไฟล์ผลลัพธ์ที่ต้องการ

| ไฟล์ | คำอธิบาย |
|---|---|
| `Recordings/A_LineOverview_JOINED.mp4` | ผลของงาน A1 (ยังไม่มีตัวหนังสือ) |
| `Recordings/A_LineOverview_FINAL.mp4` | ผลของงาน A2 (มี section title ครบ) ← **ตัวส่งจริง** |
| `Recordings/B_Changeover_FINAL.mp4` | ผลของงาน B2 (+B1 ถ้า Min ตอบเรื่องความยาวแล้ว) ← **ตัวส่งจริง** |

**ห้ามลบ/ทับไฟล์ต้นฉบับใน `Recordings/`** — สร้างไฟล์ใหม่เสมอ
