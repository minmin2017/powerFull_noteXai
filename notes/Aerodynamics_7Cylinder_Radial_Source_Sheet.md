# Source Sheet — Aerodynamics + 7-Cylinder Radial Engine

สถานะ: Phase 3 design gate หลัง Min อนุมัติ Phase 2 brief

จุดประสงค์ของไฟล์นี้คือแยก **ข้อเท็จจริงที่ล็อกแล้ว**, **การย่อเพื่อการสอน**, และ **สิ่งที่ยังห้ามสมมติ** ก่อนเริ่มเขียนฉาก Manim

## Audience และ learning contract

- ผู้เรียนระดับมหาวิทยาลัย แต่เริ่มจากศูนย์เรื่อง Bernoulli และ radial engine
- วิดีโอเป็นเรื่องเดียวต่อเนื่อง ไม่กำหนดเวลาตายตัว
- แกนเหตุผลต้องไหลจาก `throttle → combustion → torque → propeller thrust → airspeed → wing lift`
- ทุก claim เชิงกลไกต้องมี proving shot หรือระบุชัดว่าเป็น schematic

## Locked facts

### Aerodynamics

1. เครื่องยนต์/ใบพัดสร้าง thrust; ปีกสร้าง lift. ใน steady level flight ใช้ `T ≈ D` และ `L ≈ W` เป็นกรอบสมดุล ไม่ใช่การบอกว่า engine ยกเครื่องบินโดยตรง
2. Equal-transit-time/longer-path เป็นคำอธิบายที่ผิด ห้ามใช้เป็นเหตุผลว่าอากาศด้านบนต้องไปถึง trailing edge พร้อมอากาศด้านล่าง
3. Bernoulli และ Newton ใช้เป็นสองมุมมองที่สอดคล้องกันได้: pressure distribution กับ momentum/flow turning. ห้ามเปิดเรื่องด้วยคำว่า “เป็นสมการเดียวกัน” และห้ามใช้ Bernoulli แบบไม่มีสมมติฐานเป็นคำอธิบายทั้งหมด
4. Lift equation ที่ใช้สรุปเชิงวิศวกรรม:

   `L = 1/2 ρ V² S C_L`

   โดย `C_L` รวมผลจากรูปร่าง มุมปะทะ และสภาพการไหลที่ซับซ้อน

5. Flow-deflection shot ต้องแสดงทั้ง upper และ lower surface ที่ร่วมทำให้ flow turn และ wake มี downwash

แหล่งหลัก: [NASA Glenn — Bernoulli and Newton](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/bernoulli-and-newton/) และ [NASA Glenn — Lift Equation](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/lift-equation-2/)

### Radial engine

1. ใน radial 7 สูบแถวเดียว: ลูกสูบหนึ่งสูบต่อกับ crankshaft ด้วย master rod; อีก 6 สูบต่อกับ master rod ด้วย articulating rods
2. ศูนย์ knuckle pins ไม่ตรงกับศูนย์ crankpin จึงเกิดเส้นทางแบบ ellipse และทำให้ piston position ของแต่ละสูบไม่เท่ากันทุกมุม crank
3. FAA ระบุ convention ว่า single-row radial เริ่มสูบ 1 ด้านบน และนับตามเข็มเมื่อมองจากด้านหลัง
4. Firing order ที่ใช้ในบทเรียนคือ `1–3–5–7–2–4–6`
5. คำอธิบายจำนวนสูบต้องเป็น “odd number per row เพื่อให้ firing intervals เท่ากันใน four-stroke radial” ไม่ใช่ “จำนวนสูบรวมของ radial ต้องเป็นเลขคี่” เพราะ multi-row radials อาจมีจำนวนสูบรวมเป็นเลขคู่ได้

แหล่งหลัก: [FAA AC 65-12A — Powerplant Handbook](https://www.faa.gov/documentlibrary/media/advisory_circular/ac_65-12a.pdf), [FAA AMT Handbook — Powerplant, Chapter 1](https://www.faa.gov/sites/faa.gov/files/03_amtp_ch1.pdf), และ [NASA NTRS 19810005452](https://ntrs.nasa.gov/citations/19810005452)

## Derivation policy

### ใช้ได้ในวิดีโอหลัก

- `L ≈ Δ(momentum_y)/Δt` เป็นภาพ control-volume แบบย่อ เพื่อเชื่อม downwash กับ reaction force
- Bernoulli แบบระบุว่าใช้ดู pressure/velocity distribution ในบริบทของ flow ที่เหมาะสม
- `L = 1/2 ρ V² S C_L` เป็น synthesis หลังผู้เรียนเห็นกลไกแล้ว
- `720° / 7 = 102.857°` เป็นช่วง crank angle ต่อ power event ของ 7 สูบในหนึ่ง four-stroke cycle
- modular stepping แบบ “ข้ามทีละ 2 ตำแหน่ง” อธิบายได้เฉพาะ single-row radial: เมื่อ `N` เป็นเลขคี่จะวนครบทุกสูบ; เมื่อ `N` เป็นเลขคู่จะวนซ้ำเพียงครึ่งหนึ่งหากรักษาระยะ firing เท่ากัน

### ยังห้าม hard-code

- สูตรมุม rocking `β(θ)` ของ master rod สำหรับ W670 รุ่นใดรุ่นหนึ่ง
- ค่า eccentricity/แกน ellipse ของ knuckle-pin path สำหรับ W670
- ค่า TDC offset, valve timing และ ignition timing ของ engine รุ่นจริง
- ทิศการหมุนที่ผูกกับ firing order โดยไม่ระบุรุ่น, ด้านที่มอง และ convention ให้ชัด

สำหรับ shot ellipse ให้สร้างจาก geometry ที่ระบุในโมเดลของเรา หรือวาดเป็น **schematic, not to scale**. ถ้าจะอ้างว่าเป็น W670 จริง ต้องเพิ่มคู่มือ/แบบ drawing ของรุ่นเป้าหมายและตรวจซ้ำก่อน render

## Source status before production

| Item | Status | Production rule |
|---|---|---|
| Equal-transit-time myth | ล็อกแล้ว | ต้อง debunk เป็น named beat |
| Bernoulli/Newton framing | ล็อกแล้ว | pressure + momentum เป็นคู่มุมมอง ไม่ใช่คู่แข่ง |
| Lift equation | ล็อกแล้ว | แสดงตัวแปรทีละตัวและผูกสี `V` กับ relative wind |
| Engine vs wing roles | ล็อกแล้ว | ต้องมี thrust/lift orthogonality shot |
| Master + 6 articulating rods | ล็อกแล้ว | แสดงเป็น physical mechanism |
| Elliptical knuckle-pin path | ล็อกเชิงหลักการ | ห้ามอ้างสเกล W670 จนกว่าจะล็อก geometry |
| Firing order 1-3-5-7-2-4-6 | ล็อกตาม FAA convention | ใส่ rear-view/numbering convention บน HUD |
| Odd number per row | ล็อกแล้ว | ห้าม generalize เป็น odd total cylinders |
| Stall separation | ยังต้อง source-check | เป็น optional shot และยังไม่เป็นแกนหลัก |

