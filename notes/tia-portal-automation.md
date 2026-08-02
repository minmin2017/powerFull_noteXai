# TIA Portal Automation — สิ่งที่รู้แล้ว (2026-07-16)

บันทึกจากการลองหาทางเชื่อม AI เข้ากับ Siemens TIA Portal (โปรเจกต์ `howeworkweek2_hw1`, license แบบการศึกษา ไม่มี Openness)

## 1. ไฟล์โปรเจกต์
- ไม่มีไฟล์ "ladder" แยกต่างหาก — ทุกอย่าง (ladder, tag table, HW config, HMI) เก็บรวมในไฟล์เดียว `<ชื่อโปรเจกต์>.ap20` (เข้ารหัส binary)
- ตัวอย่าง: `D:\Documents\Automation\howeworkweek2_hw1\howeworkweek2_hw1.ap20`
- แก้ไข/อ่านไฟล์นี้ตรงๆ นอก TIA Portal ไม่ได้เลย

## 2. License / MCP ที่มีขายอยู่
- มี MCP server จริง (TiaCommander, T-IA Connect) แต่ทั้งคู่ต้องมี **TIA Portal Openness API license** ซึ่งเป็น option แยกที่ปกติไม่แถมมากับ license การศึกษา → ใช้ไม่ได้กับเครื่องนี้
- ไม่มีทางลัดอื่นที่ Siemens เปิดให้ scripting ฝั่ง engineering software โดยไม่มี license นี้

## 3. ทางที่ใช้ได้จริง: UI Automation (pywinauto) — ไม่ต้องมี license
กติกาที่เจอจากการลองจริง:

- **ต้องรันแบบ Administrator (elevated)** เสมอ เพราะ TIA Portal รันแบบ elevated และ Windows มีกลไก **UIPI** บล็อกโปรเซสสิทธิ์ต่ำกว่าไม่ให้ตรวจสอบโปรเซสสิทธิ์สูงกว่า
- **ต่อผ่าน PID หรือ title matching ใช้ไม่ได้** — จะได้ window ปลอมว่างๆ (เจอ title "ADWorkbench" ขนาด 0x0)
- **วิธีที่ได้ผล**: ต่อผ่าน **window handle (HWND) โดยตรง**
  ```python
  from pywinauto import Application
  app = Application(backend="uia").connect(handle=HANDLE)
  win = app.window(handle=HANDLE)
  ```
  หา handle ด้วย: `Get-Process -Name "Siemens.Automation.Portal" | Select MainWindowHandle`
- เมื่อต่อสำเร็จ จะเห็นโครงสร้างจริง: `EditorMainFrame`, `TaskCardContainerFrame`, `StatusBarView`, `ApplicationNavigationContainer` ฯลฯ

### ข้อจำกัดสำคัญ: Project tree / tag table เป็น virtualized grid
- ไม่ใช่ TreeItem/HeaderItem มาตรฐาน — Windows UIA จะสร้าง element ให้เห็นเฉพาะแถวที่ "แสดงผลอยู่บนจอจริง" เท่านั้น
- แถวที่พับ/ซ่อนอยู่ (เช่น PLC tags ที่ยังไม่กาง) **ไม่มีตัวตนให้ query เจอเลย**
- แปลว่า **นำทาง/ไล่หาโหนดในต้นไม้แบบเดา path ทำไม่ได้** ต้องเปิดหน้าที่ต้องการให้แสดงบนจอก่อน แล้วค่อยสแกนเฉพาะ element ที่ render อยู่

### Screenshot: ใช้ได้ แต่ต้องระวัง
- `win.capture_as_image()` (ของ pywinauto) → panel ที่ GPU-render (project tree, hardware catalog) ออกมา **ดำสนิท** ใช้ไม่ได้
- ใช้ `PIL.ImageGrab.grab(bbox=win32gui.GetWindowRect(handle))` แทน → เห็นภาพครบทุก panel จริง ใช้งานได้

### ความเสี่ยงของการคลิกอัตโนมัติ (auto-click)
- หน้าต่าง terminal ที่ elevate ขึ้นมาอาจ **แย่ง foreground focus** ทำให้พิกัดคลิกคลาดเคลื่อน (เคยคลิกโดนแถวผิด: ไป "Program blocks" แทน "PLC tags")
- ถ้ามีหน้าต่างอื่น (เช่นเกม) มาซ้อนทับบริเวณเดียวกันบนจอ การแคป+คลิกแบบ blind coordinate จะ**เสี่ยงคลิกโดนโปรแกรมผิดตัว**
- **สรุป: ยังไม่ปลอดภัยพอสำหรับ auto-click แบบเต็มรูปแบบ** ต้องมีการยืนยันว่า TIA Portal เป็นหน้าต่าง topmost จริงก่อนคลิกทุกครั้ง (ยังไม่ได้ implement)

## 4. วิธีที่ปลอดภัยและใช้ได้ตอนนี้
1. ให้ผู้ใช้เปิด view ที่ต้องการเอง (เช่น PLC tags > Show all tags) หนึ่งครั้ง
2. จากนั้นสแกนเฉพาะ element ที่ render อยู่ ณ ตอนนั้น (เร็ว เพราะพื้นที่ค้นหาเล็กลงมาก)
3. อ่าน/รายงานค่ากลับมาให้

## 5. อัปเดต: auto-click สำเร็จแล้ว (ใช้ toolkit ด้านล่าง)
- สร้าง `tools/tia_tool.py` + `tools/tia_run.ps1` — wrapper ที่ทำ elevate ให้อัตโนมัติ และ **เช็ค foreground window ตรงกับ TIA Portal ก่อนคลิกทุกครั้ง** (ถ้าไม่ตรง จะ REFUSE ไม่คลิก กันปัญหาคลิกโดนหน้าต่างผิดที่เจอก่อนหน้า)
- คำสั่งที่มี: `handle`, `shot [outfile]`, `foreground-check`, `focus`, `click X Y [--double]`, `keys "text"`
- Flow ที่ใช้ได้จริง: `focus` (คืนจาก minimize + ยกขึ้นหน้าสุด) → `shot` (ดูตำแหน่ง) → `click x y --double` (คลิกตามพิกัดที่เห็นในภาพ) → `shot` ซ้ำ (ยืนยันผล)
- ทดสอบจริงแล้ว: เปิด PLC tags > Show all tags ได้เองทั้งหมดโดยไม่ต้องให้ผู้ใช้คลิกเลย แล้วอ่านค่า tag table จากภาพได้ถูกต้อง

## 6. ครั้งหน้าควรทำอะไรต่อ
- เขียน wrapper ฟังก์ชันสำหรับ: อ่าน error/diagnostics panel, แก้ค่า tag ผ่านการพิมพ์จำลองแบบเต็มรูปแบบ (ตอนนี้ทำ ladder logic ง่ายๆ ได้แล้ว ดูข้อ 8)
- พิจารณาถามมหาวิทยาลัยว่ามี SIMATIC Academic license ที่รวม Openness ไหม — ถ้ามีจะตัดปัญหาทั้งหมดนี้ทันที

## 7. จุกจิกที่ต้องระวัง (สำหรับรุ่นน้อง/session หน้า) — เจอจริงระหว่างทำ Main_3

**7.1 ห้ามพิมพ์ `%` ผ่าน pywinauto `keyboard.send_keys()` ตรงๆ**
`%` (เหมือน `^`, `+`, `~`, `{`, `}`) เป็นอักขระพิเศษของ pywinauto (หมายถึงปุ่ม Alt) — พิมพ์ `%I0.0` แล้วจะกลายเป็นกด Alt+I แทนที่จะพิมพ์ % จริง
**วิธีแก้:** พิมพ์แค่ `I0.0` (ไม่ต้องใส่ %) — TIA Portal เติม % ให้เองอัตโนมัติเวลา parse เป็น address

**7.2 `{ENTER}` / `{TAB}` แบบ string พังข้าม shell layer**
คำสั่งที่ซ้อนกันหลายชั้น (PowerShell tool → powershell.exe → tia_run.ps1 → Start-Process elevate → python) ทำให้ syntax `{ENTER}` ของ pywinauto ถูก mangle ระหว่างทาง (PowerShell ตีความ `{}` เป็น script block)
**วิธีแก้:** ส่งคีย์พิเศษด้วย raw VK code ผ่าน `win32api.keybd_event()` แทน (ดู `tia_tool.py` คำสั่ง `key enter|tab|esc|f2`) ไม่ใช้ pywinauto string-based key codes เลย

**7.3 กด Enter/Tab ไม่ confirm ช่องพิมพ์ชื่อแท็กในตาราง ladder**
พิมพ์ชื่อ/address ลงช่อง `<??.?>` แล้วกด Enter หรือ Tab ไม่ยอม commit ค่า (ช่องยังเปิดค้าง หรือ text ถูก select ใหม่)
**วิธีแก้ที่ได้ผล:** คลิกที่ว่างบน canvas (เช่น พื้นที่เปล่าใต้ rung) เพื่อ blur ช่องพิมพ์ — ค่าที่พิมพ์ไว้จะ commit ทันที

**7.4 พิมพ์ "ชื่อ" เฉยๆ (ไม่ใช่ address) ใส่ contact ไม่ได้สร้างแท็กอัตโนมัติ**
พิมพ์ `Start` เป็นชื่อ symbolic เข้าไปตรงๆ (ไม่มี address อ้างอิง) — TIA แสดงเป็นข้อความปกติ (ไม่ใช่ `<??.?>` สีแดง) ดูเหมือนสำเร็จ **แต่จริงๆ ไม่ได้สร้างแท็กในตารางไหนเลย** (เช็คด้วย Show all tags แล้วไม่เจอ) — Network ยังมี error ค้างอยู่
**วิธีแก้:** พิมพ์ **address ดิบ** เข้าไปแทน (เช่น `I0.0`) — TIA จะ auto-create แท็กใหม่ให้จริง (ตั้งชื่อ default `Tag_1`, `Tag_2`, ... ให้เอง) พร้อม address ที่ถูกต้อง แล้วค่อยไป rename ทีหลังถ้าต้องการชื่อที่สื่อความหมายกว่า
**อย่าเชื่อแค่ตาเปล่าว่า "ไม่ใช่สีแดงแล้ว = สำเร็จ"** — เช็ค error icon ข้างชื่อ Network ประกอบด้วยเสมอ (วงกลมสีแดงที่ "Network 1:") ว่าหายไปจริง

**7.5 พิกัดคลิกขยับเมื่อ label ยาวขึ้น (1 บรรทัด → 2 บรรทัด)**
พอ contact ผูก address สำเร็จ (เช่น `%I0.0` บรรทัดบน + `"Tag_1"` บรรทัดล่าง) มันจะกลายเป็น label 2 บรรทัดแทนที่จะเป็น 1 บรรทัด (ตอนยังเป็น `<??.?>`) ทำให้ contact/label **ถัดไป** ในแถวเดียวกันขยับตำแหน่งเล็กน้อย ถ้าใช้พิกัดเดิม (จากก่อนที่ contact แรกจะ resolve) ไปคลิก contact ที่ 2 จะพลาด (เคยดับเบิลคลิกโดน contact แรกซ้ำ แทนที่จะโดน "Stop" ตัวที่ 2)
**วิธีแก้:** ถ่าย screenshot ใหม่ทุกครั้งหลัง confirm ค่าไปแล้ว อย่าใช้พิกัดเก่าซ้ำข้ามหลาย action

**7.6 หน้าต่างอื่นแย่ง foreground ได้ตลอดเวลา (ไม่ใช่แค่ตอนเริ่ม)**
เจออย่างน้อย 3 แบบ: (ก) เกมที่เปิดอยู่ (Harry Potter: Magic Awakened) มาซ้อนทับ (ข) Chrome แท็บ Powernote แย่ง focus (ค) **หน้าต่าง terminal ของ Claude เอง** (ที่ผู้ใช้ดูผ่าน remote control) ก็มาซ้อนทับ TIA Portal ได้เหมือนกัน
**วิธีแก้:** เรียก `foreground-check` (เช็คด้วย process name ไม่ใช่ HWND ตรงๆ เพราะ dialog ลูกมี HWND คนละตัวกับหน้าต่างหลัก) ก่อนคลิกทุกครั้งที่สงสัย ไม่ใช่แค่ตอนเริ่ม sequence — `tia_tool.py` ทำเช็คนี้ให้อัตโนมัติใน `click`/`keys` อยู่แล้ว แต่ถ้า refuse ต้องเรียก `focus` ใหม่เสมอ ห้าม `--force` มั่ว

**7.7 หน้าต่าง TIA Portal คืนจาก minimize มาเป็นขนาดเล็ก ไม่ maximize อัตโนมัติ**
เรียก `focus` แล้วหน้าต่างกลับมาเป็นขนาด restore (~1025x1017) ไม่ใช่ maximize (~1938x1038) ทำให้พิกัดที่จำไว้ตอน maximize ใช้ไม่ได้เลย
**วิธีแก้:** เช็ค `rect` ที่ `shot` คืนมาทุกครั้ง ถ้าขนาดเล็กกว่าที่คาด ให้คลิกปุ่ม maximize (มุมขวาบนของหน้าต่าง) ก่อนคลิกอย่างอื่นต่อ

**7.8 กด Escape กู้คืนค่าที่พิมพ์ผิดได้จริง**
ถ้าพลาดดับเบิลคลิกไปโดน field ที่มีค่าอยู่แล้ว (เช่นตั้งใจจะแก้ contact ตัวที่ 2 แต่ดันไปเปิด edit box ของตัวที่ 1 ที่ resolve ไปแล้ว) — กด Escape (`key esc`) จะยกเลิก edit แล้วคืนค่าเดิมให้ ไม่กระทบข้อมูลที่ confirm ไปแล้วก่อนหน้า

**7.9 Drag-and-drop จาก Toolbox (HMI screen editor) ต้อง "jiggle" ก่อนถึงจะเริ่ม drag จริง**
ลาก element จาก Toolbox (เช่น Button) มาวางบน canvas ด้วย `SetCursorPos` + `mouse_event` ตรงๆ (กด-ลาก-ปล่อยเป็นเส้นตรง) **ไม่ทำงาน** — WPF drag-source ต้องเห็นการขยับเมาส์เล็กน้อยก่อน (เกิน "drag threshold") ถึงจะเริ่มกระบวนการ drag จริง
**วิธีแก้:** ในคำสั่ง `drag` ของ `tia_tool.py` เพิ่มการขยับเมาส์เล็กๆ (3px, 6px, 10px) ทันทีหลังกดปุ่มลงก่อนค่อยลากไปตำแหน่งจริงแบบ multi-step (25 steps) แล้วค่อยปล่อย — ทำให้ drag สำเร็จ

**7.10 Docked panel (Properties) ต้องลาก splitter ขึ้นถึงจะเห็นเนื้อหา**
คลิกแท็บ "Properties" ที่แถบล่างสุดแล้วจะเปิดเป็นแถบเล็กๆ ไม่พอเห็นเนื้อหา ต้อง `drag` เส้นแบ่ง (splitter) ที่อยู่เหนือแถบแท็บขึ้นไปด้านบน (เช่นจาก y=962 ไป y=700) ถึงจะเห็น property form เต็มๆ — ทั้งแอปของ Siemens ใช้ pattern เส้นแบ่งแบบนี้เกือบทุกที่ (คำเตือนจาก Min เอง หลังสังเกตเห็น pattern นี้ซ้ำๆ)

**7.11 Property/Event dropdown ที่มีลูกศร ▼ ต้องคลิกแม่นตรงลูกศรจริงๆ**
field แบบ combo (เช่น "Add function" ใน Events tab) มีปุ่ม ▼ เล็กๆ ชิดขวา — ถ้าคลิกไม่ตรงเป๊ะ (คลาดไปไม่กี่ px) popup จะไม่เปิดเลยแบบเงียบๆ (ไม่มี error ให้เห็น) ต้อง zoom-crop ภาพดูตำแหน่งปุ่มจริงก่อนคลิกเสมอถ้าพลาดครั้งแรก

**7.12 เมนู tree แบบ nested (System functions > Edit bits > SetBit) ต้อง "ดับเบิลคลิก" หรือคลิกที่ตัวหนังสือ ไม่ใช่ลูกศร ▶ ถึงจะขยาย**
ลองคลิกลูกศร ▶ ตรงๆ ไม่ขยาย (แค่ select แถวเฉยๆ) แต่ดับเบิลคลิกที่ข้อความ (เช่น "Edit bits") ทำให้ขยาย submenu ได้ทันที

**7.13 Ctrl+A / Ctrl+C / Ctrl+V ใช้ `win32api.keybd_event` แบบ 2 คีย์พร้อมกันได้**
เพิ่มใน `tia_tool.py` เป็น tuple `(modifier_vk, key_vk)` ใน `_VK` dict แล้ว keydown modifier ก่อน, keydown+keyup คีย์หลัก, แล้วค่อย keyup modifier — ใช้ select-all ก่อนพิมพ์ทับข้อความเดิมในช่อง (กันปัญหาพิมพ์ต่อท้ายกลายเป็น "TextStart" แทนที่จะเป็น "Start")

**7.14 HMI Button ผูก PLC tag ได้ตรงๆ ผ่าน Events tab**
ไม่ต้องสร้าง HMI tag แยกก่อน — เลือก element (Button) > แท็บ Events > เลือก event (เช่น "Press") > คลิกลูกศร dropdown ที่ "<Add function>" > System functions > Edit bits > SetBit (หรือ ResetBit) > กรอกชื่อ PLC tag ตรงในช่อง "Tag (Input/output)" ได้เลย (เช่น "Tag_1") — พื้นหลังสีชมพูของช่องนี้คือ **สไตล์ปกติของ parameter ประเภท input/output ไม่ใช่ error** (ยืนยันแล้วว่าค่ายังอยู่ถูกต้องหลังสลับแท็บไปมา)

**สรุปผลงานจริงที่ทำสำเร็จ:** สร้างปุ่ม "Start" บน Root screen ผูกกับ event Press → SetBit(Tag_1 / %I0.0) แบบ end-to-end ด้วย automation ล้วนๆ (ลาก Button จาก Toolbox, ตั้ง label, ตั้ง event, save project) โดยไม่กระทบ element เดิม (A-F) ที่มีอยู่ในหน้าจอ
