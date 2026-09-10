# Production Spec — Aerodynamics + 7-Cylinder Radial Engine

สถานะ: Phase 3 — approved brief, shot-by-shot design

## North-star lesson

ผู้เรียนต้องตอบได้ด้วยภาพและสมการว่า:

> เครื่องยนต์ไม่ได้ยกเครื่องบินโดยตรง เครื่องยนต์สร้าง thrust และ airspeed; ปีกเปลี่ยนการไหลของอากาศให้เกิด lift.

เส้นเรื่องเดียวตลอดคลิป:

`throttle → combustion → piston force → rods/crank → propeller thrust → V∞ → wing flow turn/pressure → L`

## Presentation contract

- รูปแบบ: continuous film แบ่งเป็น beats ที่มี visual callback ไม่ใช่คลิปย่อยที่ตัดขาดกัน
- Physical-first ใน aero: flow visualization คือหลักฐานหลัก
- Dashboard-first ใน engine timing: HUD ช่วยอ่าน cylinder sequence ที่ตาเปล่าแยกยาก
- Hybrid เฉพาะจุดที่ HUD ช่วยตรวจ causal link หรือค่าเชิงตัวเลข
- ใช้ native/lightweight primitives และ 2.5D extrusion; ไม่ใช้ dense imported mesh
- ฉาก 3D ใช้ `SafeThreeDScene`; ข้อความทุกชิ้นใช้ `self.hud(...)` ยกเว้นป้ายที่ตั้งใจอยู่ในโลก 3D
- ลูกศร/เส้น 3D ใช้ `arrow3()` และ `line3()` จาก `mlib.py`; ห้าม `Arrow3D`/`Line3D`
- กล้องล็อกระหว่างสอนแต่ละ proof beat; ใช้ designated proving angles แทนการ orbit ต่อเนื่อง
- ยังไม่ render local; render จริงผ่าน cloud workflow ตามมาตรฐานโปรเจกต์

## Visual language

| สิ่งที่สื่อ | สี/รูปแบบ |
|---|---|
| Lift / reaction up | เขียว `#66BB6A` |
| Thrust / airspeed | ฟ้า `#42A5F5` |
| Pressure suction | ไล่ฟ้าเข้ม → ส้มตาม magnitude พร้อม legend |
| Master rod | ทอง `#FFB300` |
| Articulating rods | ฟ้าอ่อน |
| Piston/cylinder | เทาโลหะ |
| Combustion flash | ส้ม/แดง |
| Verified result | cyan `#26C6DA` |
| Unresolved/schematic note | เทาอ่อน ไม่ใช้เป็น claim จริง |

หลักสี: ปริมาณเดียวใช้สีเดิมตลอดวิดีโอ และสีของสมการต้องตรงกับวัตถุที่กำลังอธิบาย

## Shot-by-shot design

> เวลาเป็น elastic beat ไม่ใช่ duration lock. การเปลี่ยนฉากต้องรักษา object หรือ flow marker อย่างน้อยหนึ่งอย่างให้เป็นสะพานต่อเนื่อง

### S1 — “เครื่องยนต์ทำให้เครื่องบินบินไหม?”

**Teaching job:** แก้ misconception ตั้งแต่เฟรมแรก

**ภาพ:** เครื่องบิน simplified 3D ใน cruise; ลูกศร `T` ไปข้างหน้า, `D` ถอยหลัง, `L` ขึ้น, `W` ลง

**HUD:** `T ≈ D`, `L ≈ W` และคำว่า `engine → thrust / wing → lift`

**Proof requirement:** ลูกศร thrust ติดกับ propeller/engine; ลูกศร lift ติดกับ wing และสองเวกเตอร์ตั้งฉากกันอย่างเห็นได้ชัด

**Transition:** กล้องตามเส้นทาง `T` ไปที่ propeller แล้วส่ง flow marker ไปยังปีก

### S2 — Relative wind และ angle of attack

**Teaching job:** ให้ผู้เรียนรู้ว่า `V∞` มาจากไหนก่อนแตะ Bernoulli

**ภาพ:** เครื่องบินหยุดในเฟรม แต่ลมไหลสวน; หมุน airfoil ทีละน้อยเพื่อแสดง AoA

**HUD:** `V∞`, `α`, relative wind และเส้น chord

**Proof requirement:** ห้ามให้ engine ถูกวาดเป็นตัวสร้าง lift; engine เพียงเพิ่ม thrust/airspeed ใน callback จาก S1

**Transition:** ขยาย airfoil จากปีกเป็น cutaway cross-section

### S3 — Flow turning และ downwash

**Teaching job:** สร้าง Newton/momentum view ก่อนใช้ pressure map

**ภาพ:** streamlines/particles ผ่าน upper และ lower surface; wake ด้านหลังต้องมี downward component

**HUD:** `Δp_y/Δt → reaction force` หรือ `L ≈ ṁ ΔV_y`

**Proof requirement:** เส้นการไหลเบนลงอย่างอ่านได้ และลูกศร reaction ชี้ขึ้น; ต้องเห็นว่าทั้งสองผิวมีส่วนต่อการเปลี่ยนทิศ flow

**Transition:** ใช้ streamline เดิมเป็นเส้นนำเข้าการไล่สี pressure

### S4 — Pressure, Bernoulli และ myth correction

**Teaching job:** แก้ equal-transit-time โดยไม่สร้างสงคราม “Bernoulli vs Newton”

**ภาพ:** pressure-color map บน airfoil + markers สองชุดที่ไม่ถูกบังคับให้มาถึง trailing edge พร้อมกัน

**HUD:** Bernoulli แบบมีเงื่อนไข และป้าย `equal transit time = incorrect`

**Proof requirement:** คำบรรยายต้องไม่บอกว่า “ทางบนยาวกว่าเลยต้องเร็วกว่า”; ให้บอกว่า velocity distribution ที่แท้จริงทำให้ pressure distribution เกิดขึ้น และ pressure กับ momentum เป็นสองวิธีอ่านแรงเดียวกัน

**Transition:** รวม pressure arrows ทั้งผิวเป็นเวกเตอร์ lift เดียว

### S5 — Lift equation dashboard

**Teaching job:** เปลี่ยนภาพฟิสิกส์เป็นสมการวิศวกรรมโดยไม่โยนตัวแปรพร้อมกันทั้งหมด

**ภาพ:** เริ่มจาก dynamic pressure แล้วเติม `ρ`, `V²`, `S`, `C_L` ทีละตัว

**สมการ:** `L = 1/2 ρ V² S C_L`

**Proof requirement:** เพิ่ม `V` เป็นสองเท่าแล้ว dashboard แสดงผลของ `V²` เป็นสี่เท่า ภายใต้เงื่อนไขที่ล็อก `ρ,S,C_L`

**Transition:** `V∞` ที่เพิ่มขึ้นย้อนตาม flow marker ไปยัง propeller

### S6 — Four-stroke engine core

**Teaching job:** ปูเส้นทางแรงจาก combustion ถึง crank ก่อนแสดง radial geometry

**ภาพ:** cutaway หนึ่ง cylinder: intake → compression → power → exhaust; spark/combustion ดัน piston ลง

**HUD:** ชื่อ stroke ปัจจุบันและลูกศร force ลงบน piston

**Proof requirement:** ต้องเห็นว่า piston force กลายเป็น torque ผ่าน rod/crank ไม่ใช่หายไปเป็น animation flash

**Transition:** crankpin ขยายออกเป็นศูนย์กลางของ radial layout

### S7 — Master rod + six articulating rods

**Teaching job:** ทำให้กลไกที่ไม่ intuitive เห็นเป็นชิ้นส่วนจริง

**ภาพ:** เริ่มจาก master rod สีทองและ cylinder 1; ค่อยเผย rods 2–7, knuckle pins และ piston axes

**HUD:** `1 master rod + 6 articulating rods`

**Proof requirement:** ทุก rod ต้องเชื่อมถึง piston pin และ knuckle pin จริงในภาพ; ห้ามใช้เส้นลอยที่ดูเหมือนเป็น decorative line

**Transition:** freeze crank angle แล้วเปิด ghost trace ของ knuckle pin

### S8 — Elliptical knuckle-pin path

**Teaching job:** แสดงเหตุผลของ geometry ไม่ใช่เพิ่มความสวยงามเฉย ๆ

**ภาพ:** master rod rock ผ่านมุมหลายค่า; จุด knuckle pin ทิ้งเส้นทาง ghost; เปรียบเทียบกับ crankpin circle

**HUD:** `crankpin: circle / knuckle pin: ellipse` และป้าย `schematic — not to scale` หากยังไม่ใช้ geometry ของ W670 ที่ยืนยันแล้ว

**Proof requirement:** path ต้องเกิดจาก motion ของกลไกใน scene หรือระบุชัดว่าเป็น schematic; ห้ามใส่ค่า eccentricity, β(θ), TDC offset ของ W670 โดยไม่มี source

**Transition:** กล้องเปลี่ยนเป็น rear-view และคง cylinder numbering ไว้

### S9 — Firing order 720°

**Teaching job:** พิสูจน์ firing sequence และ “odd per row” อย่างไม่ overgeneralize

**ภาพ:** radial rear-view; cylinder 1 อยู่บน; numbering ตาม convention ที่ระบุบน HUD; combustion flash ไล่ `1–3–5–7–2–4–6` สองรอบ crank

**HUD:** crank angle `0° → 720°`, active cylinder และ `Δθ = 720°/7 = 102.857°`

**Proof requirement:** ลำดับแสง, piston motion และ crank angle ต้อง sync กัน; เพิ่ม inset เปรียบเทียบ `N=7` กับ `N=6` แบบ modular stepping เพื่อบอกว่า odd เป็นเงื่อนไขต่อ row สำหรับ equal firing intervals

**Caveat:** ห้ามพูดว่า radial ที่มีจำนวนสูบรวมเป็นเลขคู่ทำงานไม่ได้; multi-row เช่น 2×7 หรือ 2×9 เป็นคนละกรณี

**Transition:** power pulse ทุกครั้งรวมเป็น torque arrow เดียวที่ crankshaft

### S10 — Throttle-to-lift integration

**Teaching job:** ปิด loop ทั้งบทในภาพเดียว

**ภาพ:** throttle เพิ่ม → combustion flashes เร็ว/แรงขึ้น → crank/propeller หมุน → `V∞` เพิ่ม → flow ผ่าน wing แรงขึ้น → lift vector เพิ่ม

**HUD:** causal chain เดิมจาก opening และแยกสี `T` กับ `L`

**Proof requirement:** engine effect จบที่ thrust/airspeed; wing effect จบที่ lift. ห้ามให้ลูกศรจาก combustion กระโดดตรงไปหา lift

**End card:** “เครื่องยนต์สร้างเงื่อนไขให้ปีกสร้างแรงยก”

## Optional beat — AoA to stall

ใส่ได้เมื่อ source-check เรื่อง separation เรียบร้อยเท่านั้น:

- เพิ่ม `α` ทีละน้อย
- แสดง separation เริ่มจาก trailing edge และขยายไปด้านหน้า
- แสดง `C_L` ถึงค่าสูงสุดแล้วลดลง
- ห้ามบอกว่า stall คือ “ความเร็วหายอย่างเดียว”

ถ้ายังไม่มี source/animation ที่เชื่อถือได้ ให้ตัด beat นี้ออกจาก first render เพื่อปกป้องแกนหลัก

## Scene architecture proposal

ใช้ไฟล์หลักหนึ่งไฟล์และ class เดียวสำหรับ continuous timeline:

```text
radial_aero_lesson.py
└── AeroRadialLesson(SafeThreeDScene)
    ├── build_aircraft()
    ├── build_airfoil_flow()
    ├── build_radial_engine()
    ├── build_hud()
    ├── show_force_balance()
    ├── show_aero_proofs()
    ├── show_engine_mechanism()
    └── show_firing_cycle()
```

Implementation constraints:

- ใช้ `ValueTracker` กับ crank angle และค่าที่เปลี่ยนสด
- สร้าง rods/pistons ด้วย flat 3D projected primitives ก่อนพิจารณา solid เพิ่ม
- แยก camera states สำหรับ side profile, wing proof, radial rear-view และ integrated shot
- ทำ `shot_log` เป็น comment/metadata ในไฟล์ เพื่อให้ทุก shot map กับ proof requirement ได้
- ทุก HUD element ต้องอยู่ใน fixed frame และอยู่ใน top/panel zone ของ `mlib.py`

## Pre-render acceptance checklist

- [ ] ไม่มีคำบรรยายว่า engine สร้าง lift โดยตรง
- [ ] equal-transit-time ถูก debunk อย่างชัดเจน
- [ ] Bernoulli/Newton ถูกวางเป็น compatible views ไม่ใช่ false equivalence
- [ ] เห็นทั้ง flow turning/downwash และ pressure map
- [ ] สมการแสดงทีละตัวแปรและ `V²` ถูกพิสูจน์ด้วย dashboard
- [ ] master rod และ articulating rods เชื่อมกับชิ้นส่วนจริง
- [ ] ellipse shot ระบุ schematic หรือใช้ geometry ที่ตรวจแล้ว
- [ ] firing order sync กับ 720° และมี rear-view convention
- [ ] odd-count claim จำกัดอยู่ที่ “ต่อ row”
- [ ] ทุกข้อความ 3D ใช้ HUD/world-text contract ถูกต้อง
- [ ] ไม่มี Arrow3D/Line3D/dense mesh
- [ ] first render ใช้ cloud workflow และหลัง render ต้องตรวจภาพจริงทุก proving shot

## Open gates before code/render

1. เลือกว่าจะใช้ generic stylized radial หรือ lock geometry เป็น Continental W670
2. ถ้าเลือก W670 ให้เพิ่ม source ของ master-rod dimensions, crankpin offset, knuckle-pin locations, rotation convention และ timing
3. ตัดสินใจว่าจะใส่ optional stall beat ใน first render หรือเก็บเป็น revision
4. หลัง gate ทั้งหมดผ่าน ค่อยสร้าง `radial_aero_lesson.py` และส่ง cloud render preview แบบ low quality เพื่อตรวจ proving shots

