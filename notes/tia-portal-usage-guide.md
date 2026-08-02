# TIA Portal — คู่มือใช้งานฉบับสรุป

เขียนไว้เพราะข้อมูลภาษาไทย (และแม้แต่ภาษาอังกฤษ) เกี่ยวกับ TIA Portal หายากและกระจัดกระจายมาก สรุปจากการเปิดใช้จริง + ความรู้ทั่วไปเกี่ยวกับ TIA Portal V20 (S7-1200 CPU 1211C + HMI KTP700 Basic PN) ในโปรเจกต์ `howeworkweek2_hw1`

## 1. โครงสร้างหน้าจอหลัก (Layout)

```
┌─────────────────────────────────────────────────────────┐
│ เมนูบาร์ (Project / Edit / View / Insert / Online / ...) │
├───────────┬─────────────────────────────┬───────────────┤
│           │                             │               │
│ Project   │      Editor area            │  Task cards / │
│ tree      │   (Device view / โค้ด /     │  Inspector    │
│ (ซ้าย)     │    ตารางแท็ก / HMI screen)   │  (ขวา)         │
│           │                             │               │
├───────────┴─────────────────────────────┴───────────────┤
│ Details view (ล่างซ้าย)          │  Status bar (ล่างสุด)  │
└─────────────────────────────────────────────────────────┘
```

- **Project tree** (ซ้าย): ทุกอย่างในโปรเจกต์อยู่ที่นี่ เป็นโครงสร้างแบบต้นไม้ พับ/กางได้
- **Editor area** (กลาง): พื้นที่แก้ไขหลัก เปลี่ยนเนื้อหาตามสิ่งที่ดับเบิลคลิกเปิดจาก project tree (มีแท็บด้านบนถ้าเปิดหลายอัน)
- **Task cards** (ขวา): เครื่องมือเสริมตามบริบท เช่น Hardware catalog (ตอนแก้ HW config), Instructions (ตอนเขียน ladder), Find and replace
- **Inspector / Details view** (ล่าง): แสดงรายละเอียด/properties ของสิ่งที่เลือกอยู่, หรือ error/warning list ตอน compile
- **Portal view vs Project view**: มุมล่างซ้ายมีปุ่มสลับ "Portal view" (เมนูแบบ wizard ง่ายๆ สำหรับมือใหม่) กับ "Project view" (แบบเต็ม ที่เห็น project tree — ใช้อันนี้เป็นหลัก)

## 2. Project tree — แต่ละส่วนคืออะไร

โครงสร้างทั่วไปเมื่อขยาย PLC ออกมา (จากโปรเจกต์จริงที่เจอ):

```
howeworkweek2_hw1                    ← ชื่อโปรเจกต์ (root)
├─ Add new device                    ← เพิ่ม PLC/HMI/อุปกรณ์ใหม่
├─ Devices & networks                ← ภาพรวมเครือข่ายอุปกรณ์ทั้งหมด (topology)
├─ PLC_1 [CPU 1211C AC/DC/Rly]       ← ตัว PLC ที่ใช้งาน
│  ├─ Device configuration           ← ตั้งค่า hardware (racks, modules, IP)
│  ├─ Online & diagnostics           ← สถานะ PLC ตอนต่อออนไลน์ (LED, error)
│  ├─ Program blocks                 ← ★ ที่เก็บ ladder/โค้ดทั้งหมด
│  │  ├─ Add new block               ← สร้าง OB/FB/FC/DB ใหม่
│  │  ├─ Main [OB1]                  ← โปรแกรมหลัก รันวนทุก scan cycle
│  │  └─ Main_1 [OB123], Main_2 [OB124] ← OB เพิ่มเติม (เช่น interrupt/startup)
│  ├─ Technology objects             ← PID, motion control ฯลฯ (ถ้ามี)
│  ├─ External source files          ← import โค้ดจากไฟล์ข้างนอก (SCL ฯลฯ)
│  ├─ PLC tags                       ← ★ ตัวแปร/แท็กทั้งหมดของ PLC นี้
│  │  ├─ Show all tags               ← เปิดดูรวมทุกตารางแท็ก
│  │  ├─ Add new tag table            ← สร้างตารางแท็กใหม่ (จัดกลุ่มแท็ก)
│  │  └─ Default tag table [36]      ← ตารางแท็กเริ่มต้น (ในวงเล็บ = จำนวนแท็ก)
│  ├─ PLC data types                 ← UDT (User Data Type) ที่สร้างเอง
│  ├─ Watch and force tables         ← ★ มอนิเตอร์/บังคับค่าตัวแปรตอนออนไลน์
│  ├─ Online backups                 ← backup โปรแกรมที่ดึงมาจาก PLC จริง
│  ├─ Traces                         ← บันทึกค่าสัญญาณตามเวลา (คล้าย oscilloscope)
│  ├─ Device proxy data
│  ├─ Program info                   ← สรุปการใช้ resource (memory, ฯลฯ)
│  ├─ PLC alarm text lists           ← ข้อความ alarm ที่กำหนดเอง
│  └─ Local modules                  ← module บนตัว PLC เอง (ไม่ผ่าน rack)
├─ HMI_1 [KTP700 Basic PN]           ← จอ HMI ที่ต่อกับ PLC
├─ Ungrouped devices
├─ Security settings                 ← สิทธิ์ผู้ใช้, การเข้ารหัส
└─ Cross-device functions            ← ฟังก์ชันที่ทำงานข้ามอุปกรณ์ (เช่น alarm รวม)
```

★ = ส่วนที่ใช้งานบ่อยที่สุดในงานทั่วไป

## 3. ลำดับขั้นตอนทำงานทั่วไป (Workflow)

### 3.1 เริ่มโปรเจกต์ใหม่
1. **Create new project** → ตั้งชื่อ/ที่เก็บไฟล์
2. **Add new device** → เลือกรุ่น PLC จริงให้ตรง (เช่น CPU 1211C) — สำคัญมาก ถ้าเลือกผิดรุ่น ฟีเจอร์/จำนวน I/O จะไม่ตรงของจริง

### 3.2 ตั้งค่า Hardware
3. **Device configuration** → วาง/เช็ค module บน rack (ถ้ามี module เสริม เช่น digital input เพิ่ม)
4. ตั้งค่า **IP address** ของ PLC (ต้องตรงกับที่จะใช้จริงตอน download)

### 3.3 สร้างตัวแปร
5. **PLC tags → Add new tag table** (หรือใช้ Default tag table) → ใส่ชื่อแท็ก, data type (Bool/Int/Real ฯลฯ), address (%I/%Q/%M)
   - `%I` = Input จริง (เซนเซอร์/สวิตช์ภายนอก)
   - `%Q` = Output จริง (ต่อไปควบคุมมอเตอร์/หลอดไฟ)
   - `%M` = Memory bit (ตัวแปรช่วยภายในโปรแกรม ไม่ต่อ I/O จริง)

### 3.4 เขียนโปรแกรม (Ladder/Logic)
6. **Program blocks → Main [OB1]** → ดับเบิลคลิกเปิด แล้วเขียน ladder logic ในนี้ (นี่คือส่วนที่ "auto รันทุก scan cycle")
7. ถ้าโค้ดซับซ้อน แยกเป็น **FC (Function)** หรือ **FB (Function Block)** แล้วเรียกจาก OB1 (ไม่ต้องเขียนทุกอย่างในบล็อกเดียว)
8. ใช้ **PLC data types** สร้าง UDT ถ้ามีชุดข้อมูลที่ใช้ซ้ำหลายที่ (เช่น struct ของ motor 1 ตัว มี speed, status, fault)

### 3.5 ตรวจสอบก่อนรันจริง
9. **Compile** (ไอคอนรูปสามเหลี่ยม/ปุ่ม compile บน toolbar) → เช็ค error/warning ใน Inspector ล่าง — **ต้องไม่มี error สีแดงก่อนไป download**
10. ถ้าไม่มี PLC จริง ใช้ **PLCSIM** (Simulation) แทนได้ — จำลอง PLC ในเครื่องเพื่อทดสอบ logic ก่อน

### 3.6 Download และทดสอบ
11. **Go online** (ต้องต่อ PLC จริงหรือ PLCSIM ผ่าน network/USB) → **Download to device**
12. **Online & diagnostics** → เช็คสถานะ PLC, ดู error code จริงจากฮาร์ดแวร์
13. **Watch and force tables** → มอนิเตอร์ค่าตัวแปรแบบ real-time ตอนออนไลน์, หรือบังคับค่า (force) เพื่อทดสอบ logic โดยไม่ต้องมี sensor จริงครบ

### 3.7 ถ้ามี HMI
14. เปิด **HMI_1** → ออกแบบหน้าจอ (screens), เชื่อม tag ของ HMI เข้ากับ PLC tag
15. Compile + Download HMI แยกจาก PLC (แต่ต้องทำหลังจาก PLC tag structure นิ่งแล้ว ไม่งั้นต้อง sync ใหม่)

## 4. ฟังก์ชันเสริมที่ควรรู้จักไว้

| ฟังก์ชัน | ใช้ทำอะไร | ใช้ตอนไหน |
|---|---|---|
| **Cross-references** | ดูว่าตัวแปร/บล็อกนี้ถูกเรียกใช้ที่ไหนบ้าง | ก่อนแก้/ลบอะไร เช็คก่อนว่ามีที่อื่นใช้อยู่ไหม |
| **Traces** | กราฟค่าสัญญาณตามเวลาจริง | debug จังหวะ timing ที่ ladder logic ธรรมดาดูไม่ออก |
| **Program info** | สรุป resource ที่ใช้ (memory, block ทั้งหมด) | เช็คว่าใกล้เต็ม PLC หรือยัง |
| **PLC alarm text lists** | ตั้งข้อความ alarm ที่กำหนดเอง | ทำระบบแจ้งเตือนที่มีความหมายกว่า error code เฉยๆ |
| **Security settings** | ล็อกสิทธิ์เข้าถึงโปรเจกต์/PLC | งานที่ต้องกันคนแก้ไขโดยไม่ได้รับอนุญาต |
| **Online backups** | ดึงโปรแกรมจาก PLC จริงมาเก็บ | เผื่อไฟล์โปรเจกต์ต้นฉบับหาย แต่ PLC จริงยังมีโปรแกรมอยู่ |

## 5. ข้อผิดพลาดที่พบบ่อย (จากประสบการณ์ทั่วไป)

- เลือกรุ่น PLC ผิดตอนสร้างโปรเจกต์ → I/O address ไม่ตรงของจริง ต้องลบอุปกรณ์แล้วเพิ่มใหม่ (เปลี่ยนรุ่นทีหลังทำยาก)
- ลืม compile ก่อน download → บาง TIA Portal เวอร์ชันจะ auto-compile ให้ แต่บางทีต้อง compile เองก่อนเสมอเพื่อเช็ค error
- แก้ tag address ทีหลังโดยไม่เช็ค cross-reference → logic ที่อื่นอ้างอิง address เดิมอาจพังแบบไม่รู้ตัว
- โปรเจกต์อยู่บน network drive → ช้ามาก แนะนำเก็บบน local SSD (ดู `sw-engineering-principles.md` หรือโน้ตอื่นเรื่อง performance)

## 6. อ้างอิงเพิ่มเติมในระบบนี้
- การ automate/scan TIA Portal ด้วย AI (ไม่มี Openness license) → ดู `tia-portal-automation.md`
- ไฟล์โปรเจกต์จริงที่ใช้เขียนคู่มือนี้: `D:\Documents\Automation\howeworkweek2_hw1\howeworkweek2_hw1.ap20`
