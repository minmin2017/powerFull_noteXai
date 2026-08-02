# เครื่องมือ MCP ที่เราสร้าง/ติดตั้งเอง (2026-07-16)

บันทึก MCP server ทั้งหมดที่ทำเองสำหรับงาน Siemens TIA Portal V20 — มีอะไรบ้าง ใช้ยังไง ทำอะไรได้/ไม่ได้ เผื่อกลับมาใช้อีก

> **แนวคิดรวม:** MCP server = โปรแกรมตัวกลางที่ Claude เรียกใช้เป็น "เครื่องมือ" ได้ตรงๆ ผ่านภาษาธรรมชาติ แทนการคลิกเมาส์ UI automation ตัวที่เกี่ยวกับ TIA ทั้งหมดคุยกับ Openness API / Simulation API ของ Siemens
>
> ทั้ง 3 ตัวลงทะเบียนแบบ **user scope** (`claude mcp add ... -s user`) → ใช้ได้ทุกโปรเจกต์ ต้อง **restart Claude Code** ทุกครั้งหลังเพิ่ม/แก้ ถึงจะโหลด tool ใหม่

---

## เงื่อนไขร่วม (ต้องมีก่อนใช้ได้จริง)

- **.NET Framework 4.8** + **.NET SDK 9** (build) — มีครบแล้ว
- **TIA Portal V20** ติดตั้งที่ `D:\sieman_plc\Portal V20`
- **กลุ่ม Windows `Siemens TIA Openness`** — user `wicha` ถูกเพิ่มแล้ว แต่ **ต้อง sign out/in** ให้มีผล (ไม่งั้น `Connect` fail)
- env var `TiaPortalLocation = D:\sieman_plc\Portal V20`
- License: มีแค่ **Trial** STEP7 Professional + WinCC Advanced (Openness รวมอยู่ใน license หลัก ไม่แยกซื้อ) — Trial น่าจะครอบคลุม Openness เพราะ binary เดียวกับตัวเต็ม

---

## 1. `tiaportal-mcp` — PLC block/type พื้นฐาน (clone มา)

- **ที่มา:** clone จาก `github.com/heilingbrunner/tiaportal-mcp` (MIT, ฟรี)
- **ที่อยู่:** `tools/tiaportal-mcp/` → exe: `src/TiaMcpServer/bin/Debug/net48/TiaMcpServer.exe`
- **ทำได้:** connect/open project, ดู project tree, อ่าน/export/import PLC block (FB/FC/OB/DB) + UDT, compile, save
- **ทำไม่ได้:** PLC tag table, HMI ทั้งหมด, simulation
- **สร้าง/build:** `dotnet build TiaMcpServer.sln -c Debug`

## 2. `tia-openness-full` — ครบเครื่อง PLC + HMI (clone มา, 189 tools)

- **ที่มา:** clone จาก `github.com/bulaofen0036-coder/TIA_Portal_Openness_MCP` (MIT, ฟรี, ไม่มี license key)
- **ที่อยู่:** `tools/TIA_Portal_Openness_MCP/` → exe (V20): `tools/tiaportal-mcp/src/TiaMcpServer/bin-v20/Release/net48/TiaMcpServer.exe`
- **build V20:** `dotnet build tools/tiaportal-mcp/src/TiaMcpServer/TiaMcpServer.V20.csproj -c Release` (มี V20/V21 แยก build เพราะ DLL คนละโครง)
- **ทำได้ (เยอะสุด):**
  - Project/Hardware: สร้างโปรเจกต์, เพิ่ม PLC/HMI, PROFINET, ค้น hardware catalog, GSD 3rd-party
  - PLC: block, UDT, **tag table**, import SCL/LAD, compile+diagnose, cross-reference, technology object (axis/cam)
  - **HMI ทั้ง Classic/Basic (ตรงกับ KTP700) และ Unified** — screen, tag table, connection, import/export, dynamization, button action
  - Alarms: alarm class, text list, instance text
  - Online (read-only): go online, download to PLC, เทียบ offline↔online, อ่านค่าสดผ่าน S7/OPC UA, อ่าน RUN/STOP จริง
  - Reflection bridge: เรียก Openness API ตัวไหนก็ได้ผ่าน `InvokeObject`/`InvokeService`
- **ยังไม่มี:** PLCSIM control, force ต่อเนื่อง, security/user mgmt, safety F-block, TIA Trace, diagnostic buffer แบบ decode เต็ม
- **เริ่มใช้:** `GetApiStatus`/`Bootstrap` → `Connect` → `OpenProject` → `GetProjectTree` (อ่าน path จริงก่อนสั่งต่อ)
- ครั้งแรกที่ Connect: TIA จะเด้ง popup ให้ authorize external application → กด allow

## 3. `plcsim-mcp` — คุม PLCSIM simulation (**เขียนเองทั้งหมด** ✍️)

- **ที่มา:** เขียนเองใหม่ทั้งตัว (ไม่มีในเน็ต) wrap `Siemens.Simatic.Simulation.Runtime.Api.x64.dll` v7.0
- **ที่อยู่:** `tools/plcsim-mcp/` → exe: `bin/Release/net48/PlcSimMcp.exe`
- **build:** `dotnet build PlcSimMcp.csproj -c Release` (x64, net48)
- **โครงไฟล์:** `Program.cs` (host + AssemblyResolve หา DLL จาก PLCSIM install), `Sim.cs` (instance cache + แปลงค่า), `McpTools.cs` (27 tools)
- **โหมดทดสอบ:** `PlcSimMcp.exe --selftest` → เช็คว่า API โหลด + runtime manager ต่อได้ไหม
- **27 tools ที่ทำได้:**
  - สถานะ: `GetApiStatus`, `ListInstances`, `ListCpuTypes`
  - สร้าง/ลบ vPLC: `RegisterInstance` (ระบุ CPU), `RegisterUnspecifiedInstance` (ให้ download กำหนด — ใช้กับ S7-1200), `RegisterCustomInstance` (ระบุ Vplc dll), `UnregisterInstance`
  - วงจรชีวิต: `PowerOn`/`PowerOff`, `Run`/`Stop` (RUN/STOP), `MemoryReset`
  - ข้อมูล: `GetInstanceInfo`, `GetOperatingState`
  - tag: `UpdateTagList`, `GetTagList`, `ReadTag`, `WriteTag` (ชื่อ symbolic)
  - address ตรง (ไม่ต้อง tag list): `ReadBit`/`WriteBit`, `ReadBytes`/`WriteBytes` (Input/Output/Marker) — เช่น `WriteBit Input 0 0 true` = กดปุ่ม I0.0
  - เน็ต/เก็บสถานะ: `SetIp`, `ArchiveStorage`/`RetrieveStorage`, `SetOperatingMode`, `ShutdownRuntimeManager`

### ⚠️ ข้อจำกัดสำคัญของ plcsim-mcp (ยังใช้จริงไม่ได้ตอนนี้)

1. **ต้องมี PLCSIM Advanced runtime** — API v7.0 นี้เป็นของ **PLCSIM Advanced** (คนละตัวกับ PLCSIM ธรรมดาที่มากับ STEP7) ตอนนี้เครื่องมีแค่ PLCSIM ธรรมดา (`PLCSIM_V20` แบบ Electron) → **ไม่มี runtime manager backend** ให้ API ต่อ → ทุก tool คืน `RuntimeManagerReachable: false` / error `-1 InvalidErrorCode`
   - โค้ด + การโหลด DLL ทำงานถูกหมดแล้ว (ทดสอบ selftest ผ่าน API โหลดได้) ติดแค่ backend ไม่มี
   - **วิธีแก้:** ติดตั้ง **PLCSIM Advanced** (แยก install/license มี trial ~21 วัน) → plcsim-mcp ใช้ได้ทันที
2. **API ไม่มี enum S7-1200** — `ECPUType` มีแต่ตระกูล S7-1500/ET200SP โปรเจกต์ Min เป็น **CPU 1211C (S7-1200)** → ต้องใช้ `RegisterUnspecifiedInstance` (ให้ download กำหนด CPU) หรือ `RegisterCustomInstance` กับ `Siemens.Simatic.PlcSim.Vplc1200.dll` (มีในเครื่องแล้ว, ยังไม่ได้ทดสอบว่ารับ 1200 จริงไหม)
3. ทางเลือกถ้าไม่ลง Advanced: simulate ผ่านปุ่ม **"Start Simulation" ใน TIA** (PLCSIM ธรรมดา) แล้วคุมด้วย UI automation แบบเดิม — แต่ตัว backend gRPC ภายในของ PLCSIM ธรรมดาเป็น API ปิด/ไม่มีเอกสาร ถ้าจะ wrap ต้อง reverse engineer (งานใหญ่)

---

## วิธีเพิ่ม/แก้ MCP ในอนาคต

```bash
# เพิ่ม
claude mcp add <ชื่อ> -s user -- "<path ถึง exe>"
# ดูสถานะ
claude mcp get <ชื่อ>
claude mcp list
# ลบ
claude mcp remove <ชื่อ> -s user
```
แก้โค้ดแล้ว **rebuild + restart Claude Code** เสมอ (tool โหลดตอนเปิด session)

## เชื่อมโยง
- [[tia-portal-automation]]
- [[tia-portal-usage-guide]]
