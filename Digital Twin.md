# Digital Twin — สรุปโปรเจคของมิน

> สร้างจากการคุยและรูปลายมือที่ส่งมาให้อ่านในแชท "main" — อัปเดตล่าสุดเมื่อมีรูป/ข้อมูลใหม่

## ภาพรวม
ระบบ Digital Twin จำลองเครื่องจักร/ชิ้นส่วนอุตสาหกรรม (เช่น CNC, มอเตอร์) ผสม ML
เพื่อพยากรณ์ "พังเมื่อไหร่" (predictive maintenance) แทนการพึ่งค่าที่ผู้ผลิตกำหนดมาตรฐานไว้

## จุดขาย (Value proposition)
- ใช้ AI/DL พยากรณ์อายุการใช้งานจริงของเครื่อง/ชิ้นส่วน แม่นยำกว่าค่ามาตรฐานจากผู้ผลิต
  - ตัวอย่าง: ผู้ผลิตระบุไว้ 20,000 ชม. (20k hr) แต่ AI พยากรณ์พบว่าใช้งานได้จริงถึง 50,000 ชม. (50k hr)
  - ผลลัพธ์: รู้ "จุดคุ้มทุน" จริง ไม่ต้องเปลี่ยนชิ้นส่วนเร็วเกินความจำเป็น

## จุดต่างจากคู่แข่ง
- เก็บข้อมูลระดับฮาร์ดแวร์จริง (เช่น มอเตอร์) ว่าพฤติกรรม/แพทเทิร์นของข้อมูลเซนเซอร์เป็นอย่างไร
  ก่อนที่มันจะพังจริง — ไม่ใช่แค่ทำนาย "พัง/ไม่พัง" แต่รู้สัญญาณเตือนล่วงหน้าจากข้อมูลจริง

## Workflow ของระบบ
มี 2 เส้นทางคู่กัน:

1. **เส้นเร็ว (real-time)**
   `Unity/sensor → Node-RED → MQTT → Dashboard`

2. **เส้นวิเคราะห์/พยากรณ์**
   `Unity/sensor → Server → Database`
   `Server → ML → ทำนาย "พังกี่ชม." → ส่งผลขึ้น Dashboard`

## Simulation
- โค้ด simulate มอเตอร์ AC จาก Healthy → Failed: `simulations/ac_motor_degradation_sim.py`
  (bearing wear driver, เซนเซอร์ vibration/temperature/current/speed, label + RUL อัตโนมัติ)

## Research: สาเหตุการพังของมอเตอร์ AC และแบริ่ง

### สถิติรวม (มอเตอร์ AC)
- **51–64%** ของการพังทั้งหมด = สาเหตุเชิงกล (mechanical)
- **35–37%** = ความเสียหายจากความร้อนที่ฉนวนขดลวด (thermal/insulation)
- ในกลุ่ม stator fault, **76%** เป็นปัญหาที่ขดลวด (winding insulation failure)

### 1) สาเหตุไฟฟ้า (Electrical)
- **Overcurrent** — สาเหตุพังอันดับต้นๆของระบบไฟฟ้า ทำให้ขดลวดสึกเร็วขึ้น
- **Voltage surge / high dv/dt** (เช่นจาก inverter/VFD) — เร่งการเสื่อมของฉนวนขดลวด
- **Voltage/current unbalance** — ทำให้ขดลวดร้อนไม่เท่ากัน เกิด hotspot
- **สิ่งปนเปื้อนทางเคมี** (น้ำมันตัด, สารเคมี, coolant) — กัดกร่อนฉนวนขดลวดให้เสื่อมเร็ว
- **Stator winding fault** — inter-turn fault, phase-to-ground fault (สาเหตุหลักของ stator fault ทั้งหมด)

### 2) สาเหตุความร้อน (Thermal / Insulation)
- กฎทั่วไป: **อุณหภูมิเพิ่มทุก 10°C (18-20°F) อายุฉนวนลดลงครึ่งหนึ่ง** (Arrhenius-based aging) — เป็นค่าที่ควรใช้คำนวณ degradation model
- Power quality แย่ (แรงดันไม่บาลานซ์) → ขดลวดร้อนเกิน
- รอบ start-stop บ่อย → ขดลวด/ฉนวน expand-contract สลับซ้ำ เร่งความล้า

### 3) สาเหตุเชิงกล (Mechanical) — ที่มอเตอร์/เพลา
- แบริ่งเสีย/สึก (สาเหตุเชิงกลอันดับ 1 — ดูรายละเอียดด้านล่าง)
- Rotor/stator eccentricity (เพลาเยื้องศูนย์)
- ความสั่นสะเทือนผิดปกติจากโครงสร้างเสื่อม/ฐานยึดหลวม

### 4) สาเหตุการพังของแบริ่งโดยเฉพาะ (Bearing failure modes)
- **Fatigue (ความล้าของผิวสัมผัส)** — แรงกดซ้ำๆระหว่างลูกปืนกับราง ทำให้เกิด subsurface crack ลามถึงผิว เกิด spalling/flaking แม้ใช้งานในสภาพอุดมคติก็เกิดได้ตามอายุ
- **Lubrication failure (สาเหตุอันดับ 1 — 40-50% ของเคสพังทั้งหมด)** — น้ำมัน/จารบีผิดความหนืด, น้อยเกินไป, เสื่อมสภาพ, เปลี่ยนช้าเกินรอบ → ผิวแบริ่งมีลักษณะ "frosty gray" ก่อนลอกเป็น spall
- **Contamination** — ฝุ่น/น้ำ/เศษโลหะหลุดเข้าไป (silica/alumina ส่วนใหญ่) → ทำให้สึกแบบ abrasive (three-body abrasion) และทำให้ lubrication failure ตามมา
- **Misalignment** — เพลา/housing เยื้องศูนย์ ทำให้โหลดกระจุกผิดตำแหน่ง — ความเยื้อง 0.001 นิ้ว/นิ้ว ลดอายุแบริ่งได้ 30-50%
- **Electrical fluting** — กระแสไฟรั่วไหลผ่านลูกปืน/ราง (พบมากกับมอเตอร์ที่ขับด้วย VFD) เกิดเป็นรอย pit/fluting เล็กๆทั่วราง

### นัยต่อโปรเจค Digital Twin
- เซนเซอร์ที่ "ครอบคลุม" สาเหตุพังให้มากที่สุดควรมี: **vibration** (จับ fatigue/misalignment/contamination), **temperature** (จับ thermal/insulation aging — ใช้กฎ "ทุก 10°C ลดอายุครึ่งหนึ่ง" ได้), **current** (จับ overcurrent/electrical fault/fluting ทางอ้อม), และถ้าเป็นไปได้ **กระแสรั่ว/ground fault sensor** (จับ electrical fluting/insulation breakdown ตรงจุด)
- โมเดล simulation ปัจจุบัน (`ac_motor_degradation_sim.py`) ครอบคลุม mechanical/bearing wear path เป็นหลัก — ยังไม่ได้ใส่ thermal-insulation aging model หรือ electrical fault path แยก ถ้าต้องการความสมจริงเพิ่มสามารถเพิ่ม failure mode เหล่านี้ทีหลังได้

## รออัปเดตเพิ่ม
มินจะส่งรูปลายมือ/สไลด์เพิ่มเป็นระยะ — ไฟล์นี้จะถูกอัปเดตตามเนื้อหาที่ได้รับใหม่
