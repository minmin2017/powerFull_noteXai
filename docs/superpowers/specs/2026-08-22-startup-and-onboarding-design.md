# ใบสั่งงาน — เปิดแอปให้เร็วขึ้น + ให้เพื่อนติดตั้งเองได้

> **สถานะ:** Min อนุมัติแล้ว (2026-08-22) — ทางเลือก A + B + Gemini headless แบบต่อบทสนทนา
> **ผู้เขียน:** Claude chat1 (วิเคราะห์/ออกแบบ) — **ผู้ลงมือ:** chat2 (Sonnet)
> **ขอบเขต:** ความเร็วตอนเปิด + ความง่ายในการติดตั้ง + เปลี่ยนวิธีปลุก Gemini
> **ไม่อยู่ในขอบเขต:** การรื้อ WebSocket broadcast / รูปแบบการเซฟไฟล์ (ทางเลือก C — เก็บไว้ทำทีหลัง)

---

## 1. ที่มา — ปัญหาที่ Min เจอจริง

Min รายงาน 3 อย่าง:

1. แอปเปิดนาน
2. ต้อง set up หลายระบบมาก ถ้าจะส่งให้เพื่อนใช้ยาก
3. ระบบเปิด Gemini อัตโนมัติตอนบูตเครื่อง รอ 20 วิไม่พอ พิมพ์ตกหล่น

## 2. ผลการวัดจริงบนเครื่องนี้ (2026-08-22)

ทุกตัวเลขวัดเอง ไม่ได้ประมาณ

| # | อาการ | หลักฐาน | ผลกระทบ |
|---|---|---|---|
| 1 | `pip install` รันทุกครั้งที่เปิด | `start.cmd:13-16` รัน `python -m pip install -q -r requirements.txt` **ก่อน** `node --watch server.js` — จับเวลาได้ **11,978 ms** ทั้งที่แพ็กเกจครบแล้ว | เซิร์ฟเวอร์ไม่ขึ้นเลย ~12 วิแรก |
| 2 | เปิด 6 หน้าต่างพร้อมกัน | `start.cmd:18-29` | แย่ง disk/CPU ตอนเครื่องเพิ่งบูต |
| 3 | ปลุก Gemini ด้วยการพิมพ์ลงจอ | `tools/antigravity_startup_bot.py:74-75` — `time.sleep(20)` แล้ว `pyautogui.typewrite()` | **ต้นเหตุพิมพ์ตกหล่น** + แย่งเมาส์คีย์บอร์ด |
| 4 | ใช้ `localhost` แทน `127.0.0.1` | วัดได้ `localhost` connect = **204 ms** / `127.0.0.1` = **1.4 ms** | `claude-listen.cmd:22` วน 15 รอบ = เสียเปล่าได้ถึง ~3 วิ |
| 5 | ติดตั้งเองยาก | ไม่มี `.env.example`, ไม่มี `setup.cmd`, ต้องเตรียมเอง 6 อย่าง | เพื่อนตันตั้งแต่ก้าวแรก |

**หมายเหตุความซื่อสัตย์:** เดิมในหน่วยความจำบันทึกว่า `localhost` เสีย 2 วินาที — วัดวันนี้ได้ 0.2 วินาที
น้อยกว่าที่จำไว้ 10 เท่า แต่ยังคุ้มที่จะแก้เพราะเปลี่ยนคำเดียว

## 3. เป้าหมายที่วัดผลได้

| เป้า | ก่อน | หลัง (ต้องวัดให้ได้จริง) |
|---|---|---|
| เวลาจากดับเบิลคลิก `start.cmd` จนเซิร์ฟเวอร์ตอบ | ~12+ วิ | **ต่ำกว่า 3 วิ** |
| Gemini พิมพ์ตกหล่น | เกิดได้ | เกิดไม่ได้ (ไม่มีการพิมพ์ลงจอแล้ว) |
| ขั้นตอนที่เพื่อนต้องทำเอง | 6 | **1** (ดับเบิลคลิก `setup.cmd`) |

---

## 4. งานที่ต้องทำ

### งาน A1 — ข้าม `pip` ถ้าแพ็กเกจครบแล้ว

**ไฟล์:** `start.cmd` บรรทัด 13-16

**หลักการ:** เก็บ hash ของ `requirements.txt` ไว้ ถ้าไม่เปลี่ยนก็ไม่ต้องรัน pip ซ้ำ
ใช้ `certutil` (มากับ Windows ไม่ต้องเรียก PowerShell ซึ่งช้ากว่า)

แทนที่ของเดิม:

```cmd
where python >nul 2>nul && (
  echo   Installing/checking Python dependencies...
  python -m pip install -q -r requirements.txt
)
```

ด้วย:

```cmd
rem ---- Python deps: ข้ามถ้า requirements.txt ไม่เปลี่ยนตั้งแต่ลงครั้งล่าสุด ----
rem ของเดิมรัน pip ทุกครั้ง = เสียเปล่า 12 วินาทีต่อการเปิด 1 ครั้ง
where python >nul 2>nul && (
  if not exist ".setup" mkdir ".setup"
  set "REQHASH="
  for /f "skip=1 tokens=* delims=" %%h in ('certutil -hashfile requirements.txt SHA256') do (
    if not defined REQHASH set "REQHASH=%%h"
  )
  set "OLDHASH="
  if exist ".setup\deps.hash" set /p OLDHASH=<".setup\deps.hash"
  if not "%REQHASH%"=="%OLDHASH%" (
    echo   Installing/checking Python dependencies ^(requirements.txt changed^)...
    python -m pip install -q -r requirements.txt && >".setup\deps.hash" echo %REQHASH%
  )
)
```

**ระวัง — ตัวแปรใน block วงเล็บของ cmd:** `%VAR%` ถูกแทนค่าตอน *อ่าน* ทั้ง block ไม่ใช่ตอนรัน
ถ้าเซ็ตค่าแล้วอ่านค่าใน block เดียวกันจะได้ค่าเก่า **ต้องใส่ `setlocal EnableDelayedExpansion` บนหัวไฟล์
แล้วเปลี่ยน `%REQHASH%` / `%OLDHASH%` เป็น `!REQHASH!` / `!OLDHASH!`**
ข้อนี้พลาดง่ายมาก ถ้าไม่ทำ เงื่อนไขจะเทียบค่าว่างกับค่าว่างแล้วข้าม pip ตลอด (ดูเหมือนใช้ได้แต่ผิด)

**เพิ่ม `.setup/` เข้า `.gitignore`**

**วิธีตรวจ:**
```bash
# ครั้งแรก: ต้องเห็นข้อความว่ากำลังลง แล้วได้ไฟล์ hash
rm -rf .setup && ./start.cmd --no-claude   # ปิดหน้าต่างหลังเซิร์ฟเวอร์ขึ้น
cat .setup/deps.hash    # ต้องมีค่า hash

# ครั้งที่สอง: ต้องข้าม ไม่เห็นข้อความ pip เลย
```

---

### งาน A2 — เปิดเซิร์ฟเวอร์ก่อน แล้วค่อยทยอยเปิดตัวช่วย

**ไฟล์:** `start.cmd` (แก้) + `poststart.cmd` (สร้างใหม่)

**ปัญหาของเดิม:** `start.cmd` เปิดเบราว์เซอร์และตัวช่วยอีก 5 ตัว *ก่อน* บรรทัดสุดท้ายที่สั่งรันเซิร์ฟเวอร์
เบราว์เซอร์เลยเปิดไปเจอหน้าเปล่า และทุกตัวแย่งทรัพยากรกันตอนเครื่องเพิ่งบูต

**ของใหม่:** `start.cmd` โยนงานเปิดตัวช่วยให้ `poststart.cmd` แล้วรันเซิร์ฟเวอร์ทันที
ส่วน `poststart.cmd` รอจนพอร์ตตอบก่อน ค่อยทยอยเปิดทีละตัว

`start.cmd` — ส่วนท้ายเปลี่ยนเป็น:

```cmd
rem ตัวช่วยทั้งหมดย้ายไป poststart.cmd ซึ่งจะรอให้เซิร์ฟเวอร์ตอบก่อนแล้วค่อยทยอยเปิด
rem ส่ง argument ต่อไปด้วย เพื่อให้ --no-claude / --no-gemini / --lite ยังใช้ได้
start "Powerfull Note - startup helpers" /min cmd /c "poststart.cmd %*"

node --watch server.js
```

`poststart.cmd` (ไฟล์ใหม่):

```cmd
@echo off
chcp 65001 >nul
cd /d "%~dp0"

rem รอเซิร์ฟเวอร์ตอบ เช็คถี่ ๆ (ทุก ~200 ms) นานสุด 30 วิ
rem ใช้ 127.0.0.1 ไม่ใช่ localhost — วัดแล้วต่างกัน 204 ms vs 1.4 ms ต่อครั้ง
set "UP="
for /l %%i in (1,1,150) do (
  if not defined UP (
    curl -s -m 2 -o nul http://127.0.0.1:4321/api/state && set "UP=1"
    if not defined UP ping -n 1 -w 200 127.0.0.1 >nul
  )
)
if not defined UP (
  echo Server did not come up within 30s - helpers not started.
  exit /b 1
)

start "" http://127.0.0.1:4321

rem โหมด --lite: แค่แอปโน้ต ไม่เปิดตัวช่วยอะไรเลย (สำหรับเพื่อน)
echo %* | find /i "--lite" >nul && exit /b 0

rem ทยอยเปิด เว้นระยะ ~1.5 วิ กันแย่งดิสก์ตอนเครื่องเพิ่งบูต
start "PTT Listener (Alt+P)" cmd /c ptt-listen.cmd
ping -n 2 -w 1000 127.0.0.1 >nul
start "Desktop Notifications" cmd /c notify-listen.cmd
ping -n 2 -w 1000 127.0.0.1 >nul
start "Usage Guard (85%% handoff / auto-resume)" cmd /c "node usage-guard.js main"
ping -n 2 -w 1000 127.0.0.1 >nul

echo %* | find /i "--no-gemini" >nul || (
  start "Gemini Bridge" /min cmd /c "node gemini-bridge.js"
  ping -n 2 -w 1000 127.0.0.1 >nul
)

echo %* | find /i "--no-claude" >nul || (
  start "Claude Code (main)" cmd /c claude-listen.cmd main
)
```

**หมายเหตุ:** ใช้ `ping -n` หน่วงเวลาแทน `timeout /t` เพราะ `timeout` พังเมื่อ stdin ถูก redirect
(เกิดขึ้นได้เวลา cmd ถูกเรียกจาก process อื่น) — `ping` ปลอดภัยกว่าในทุกกรณี

**วิธีตรวจ:** จับเวลาจริงตั้งแต่สั่งเปิดจนเซิร์ฟเวอร์ตอบ ต้องได้ **ต่ำกว่า 3 วินาที**

```bash
python - <<'PY'
import subprocess, time, urllib.request
t0 = time.time()
subprocess.Popen(["cmd", "/c", "start.cmd", "--no-claude", "--no-gemini"])
while True:
    try:
        urllib.request.urlopen("http://127.0.0.1:4321/api/state", timeout=1)
        break
    except Exception:
        if time.time() - t0 > 60:
            print("TIMEOUT"); break
        time.sleep(0.1)
print(f"server up in {time.time()-t0:.2f}s")
PY
```

---

### งาน A3 — `localhost` → `127.0.0.1`

**ไฟล์:** `claude-listen.cmd` บรรทัด 22 และ 39 (ในข้อความ prompt ที่ส่งให้ Claude ด้วย)

เปลี่ยนทุกที่ที่เป็น `http://localhost:4321` ให้เป็น `http://127.0.0.1:4321`

**หาให้ครบก่อนแก้:**
```bash
grep -rn "localhost:4321" --include="*.cmd" --include="*.js" --include="*.py" . | grep -v node_modules
```

**ข้อยกเว้น — อย่าแก้:**
- `README.md` และเอกสารอื่น (คนอ่านเข้าใจ `localhost` ง่ายกว่า)
- URL ที่เปิดในเบราว์เซอร์ให้ผู้ใช้ดู ถ้าจะแก้ก็ได้ แต่ไม่ใช่คอขวด

---

### งาน A4 — เลิกใช้ pyautogui ปลุก Gemini เปลี่ยนเป็น `agy` headless

**ลบ:** `tools/antigravity_startup_bot.py` (ไม่ใช้แล้ว — ย้ายไป `tools/_deprecated/` ไม่ต้องลบทิ้งถาวร)
**สร้าง:** `gemini-bridge.js`

**ทำไมต้องเปลี่ยน:** ของเดิมเดาเวลา 20 วิแล้วพิมพ์ลงจอ ซึ่ง (ก) เดาผิดได้เสมอ
(ข) แย่งเมาส์คีย์บอร์ด Min ซึ่ง Min เคยบอกชัดว่าไม่เอา

**Antigravity มี CLI ชื่อ `agy` รันแบบไม่เปิดหน้าต่างได้** — ยืนยันจากเอกสารทางการแล้ว

**ข้อสำคัญเรื่องค่าใช้จ่าย:** Min ยืนยันว่า **ไม่เอาวิธี API key เพราะเสียเงิน**
เอกสารระบุชัดว่า headless ใช้ credentials ที่ล็อกอินไว้ได้ ไม่ต้องใช้ API key:
> "Headless mode uses your cached credentials. Authenticate once with an interactive `agy` session first."

**ห้ามตั้ง `GEMINI_API_KEY` หรือแก้ `modelProvider` เป็น `gemini` เด็ดขาด** — นั่นคือทางที่เสียเงิน

**ต้องจำบทสนทนาได้** (Min ระบุว่าใช้แบบต่อแชท) → ใช้ `--conversation <id>` เก็บ id ไว้ต่อรอบถัดไป

**โครงของ `gemini-bridge.js`:**

1. อ่านคิวงานจาก `GET http://127.0.0.1:4321/api/gemini/tasks?status=pending`
2. `POST /api/gemini/task/:id/claim` เพื่อจอง
3. รัน `agy -p "<task>" --output-format json` — รอบแรกไม่ใส่ `--conversation`
   รอบต่อไปใส่ `--conversation <id ที่ได้จากรอบแรก>` เพื่อให้จำบริบทเดิม
4. เก็บ `conversation_id` จาก JSON ที่ได้ ลงไฟล์ `.setup/gemini-conversation.id`
5. `POST /api/gemini/task/:id/result` ส่งผลกลับ
6. วนรอ ใช้ WebSocket แบบเดียวกับ `ws-inbox.js` ไม่ต้อง poll ถี่

**ปิดได้ด้วย 3 ทาง (Min ขอให้ปิดได้):**
- `start.cmd --no-gemini` — ไม่เปิดตัวเชื่อมเลยรอบนี้
- `.env` ตั้ง `GEMINI_BRIDGE=0` — ปิดถาวร (`gemini-bridge.js` เช็คแล้วออกทันที)
- ปุ่ม Gemini ในแอป — ของเดิมมีอยู่แล้ว (`state.geminiHandoff.enabled`) ตัวเชื่อมต้องเคารพค่านี้ด้วย

**ขั้นที่ต้องให้ Min ทำเอง (chat2 ทำแทนไม่ได้):**

```powershell
# 1) ติดตั้ง CLI
irm https://antigravity.google/cli/install.ps1 | iex

# 2) ล็อกอินครั้งเดียว (เปิดเบราว์เซอร์ ต้องมีคนกด)
agy
```

**ตรวจก่อนเขียนโค้ดจริง — ถ้าข้อนี้ไม่ผ่าน หยุดแล้วรายงาน Min:**
```bash
agy -p "reply with exactly OK" --output-format json
```
ต้องได้ JSON ที่มี `conversation_id` กลับมา ถ้าเจอ `authentication required` แปลว่ายังไม่ได้ล็อกอิน

**แผนสำรอง:** ถ้า `agy` ติดตั้งไม่ได้จริง ๆ → **อย่ากลับไปใช้ pyautogui**
ให้ปิดการปลุก Gemini อัตโนมัติไปเลย แล้วให้ Min กดปุ่ม Gemini ในแอปเอาเมื่อต้องการ
(บูตเร็วขึ้น + ไม่มีใครมาแย่งจอ ถือว่ายังดีกว่าเดิม)

---

### งาน B1 — `.env.example`

**สร้าง:** `.env.example` (ห้ามใส่ค่าจริง ใส่แต่ชื่อ + คำอธิบาย)

```bash
# คัดลอกไฟล์นี้เป็น .env แล้วเติมค่า — ทุกตัวไม่บังคับ แอปโน้ตทำงานได้โดยไม่ต้องมีสักตัว

# พอร์ตของเซิร์ฟเวอร์
PORT=4321

# ย่อยวิดีโอด้วย AI (ไม่ใส่ = ปิดฟีเจอร์นี้) — ขอคีย์ที่ https://aistudio.google.com/app/api-keys
GOOGLE_API_KEY=

# ซิงก์โน้ตขึ้น GitHub (ไม่ใส่ = ปิดฟีเจอร์นี้)
GITHUB_TOKEN=
GITHUB_REPO=
GITHUB_BRANCH=main

# ตัวเชื่อม Gemini อัตโนมัติ — ตั้ง 0 เพื่อปิด
GEMINI_BRIDGE=1
```

**ตรวจว่า `.env` อยู่ใน `.gitignore` แล้วจริง ๆ ก่อนทำอย่างอื่น:**
```bash
git check-ignore -v .env    # ต้องมีบรรทัดตอบกลับ ถ้าเงียบ = ยังไม่ถูก ignore ให้เพิ่มทันที
```

---

### งาน B2 — `setup.cmd` ตัวเดียวจบ

**สร้าง:** `setup.cmd`

**สิ่งที่ต้องทำ ตามลำดับ:**

1. เช็ค Node — ไม่มีก็บอกลิงก์ https://nodejs.org แล้วออก
2. เช็ค Python — ไม่มีก็บอกลิงก์ แล้วบอกว่า "ข้ามได้ แต่จะไม่มีเสียงกับ notification"
3. `npm install`
4. `python -m pip install -r requirements.txt` (ถ้ามี Python) แล้วเขียน `.setup/deps.hash`
5. ถ้ายังไม่มี `.env` → คัดลอกจาก `.env.example`
6. สรุปท้ายสุดว่าอะไรพร้อม/ไม่พร้อม แล้วบอกขั้นถัดไป

**หลักการเขียนข้อความ:** ทุกครั้งที่มีอะไรขาด **ต้องบอกว่าต้องทำอะไรต่อ** ไม่ใช่แค่บอกว่าพัง
ตัวอย่างที่ดี: `ไม่พบ Python — โหลดที่ https://python.org/downloads (ตอนติดตั้งติ๊ก "Add to PATH" ด้วย)`
ตัวอย่างที่แย่: `Python not found. Exiting.`

**ท้ายไฟล์ต้องมีบรรทัดนี้เสมอ** เพราะเพื่อนดับเบิลคลิกแล้วหน้าต่างจะปิดทันทีถ้าไม่มี:
```cmd
pause
```

---

### งาน B3 — `start-lite.cmd` สำหรับเพื่อน

**สร้าง:** `start-lite.cmd`

```cmd
@echo off
cd /d "%~dp0"
call start.cmd --lite
```

เปิดแค่เซิร์ฟเวอร์ + เบราว์เซอร์ ไม่มี Claude Code / PTT / notification / usage guard / Gemini
= เพื่อนไม่ต้องลง Claude Code หรือ Antigravity เลย ก็ใช้แอปโน้ตได้ครบ

---

### งาน B4 — เพิ่มหัวข้อ "เริ่มใช้งานใน 1 นาที" ใน README

**ไฟล์:** `README.md` — แทรก **ก่อน** หัวข้อ `## เริ่มใช้งาน` เดิม

`README.md` มีอยู่แล้ว 438 บรรทัด เนื้อหาครบดี แต่เขียนสำหรับคนที่รู้จักโปรเจกต์แล้ว
เพื่อนที่เพิ่งได้ไฟล์มาต้องเจอทางลัดก่อน

```markdown
## เริ่มใช้งานใน 1 นาที (สำหรับคนที่เพิ่งได้ไฟล์มา)

1. ดับเบิลคลิก **`setup.cmd`** — ลงของให้อัตโนมัติ ขาดอะไรมันจะบอก
2. ดับเบิลคลิก **`start-lite.cmd`** — เปิดแอป
3. เบราว์เซอร์จะเปิด http://127.0.0.1:4321 ให้เอง

เท่านี้ใช้ได้เลย — เขียน วาด อัดเสียง ทำ mind-map ได้ครบ

> อยากได้ AI ตอบในแอปด้วย (Claude Code / Gemini) ต้องตั้งเพิ่ม — ดู [เริ่มใช้งาน](#เริ่มใช้งาน) ข้างล่าง
```

---

## 5. ลำดับการทำและการตรวจ

ทำเรียงตามนี้ **ตรวจให้ผ่านทีละข้อก่อนไปข้อถัดไป** ห้ามทำรวดเดียวแล้วค่อยตรวจ

| ลำดับ | งาน | ตรวจว่าผ่านเมื่อ |
|---|---|---|
| 1 | A1 ข้าม pip | เปิดรอบสองไม่เห็นข้อความ pip และมีไฟล์ `.setup/deps.hash` |
| 2 | A3 เปลี่ยนเป็น 127.0.0.1 | `grep -rn "localhost:4321" --include="*.cmd" .` ไม่เจอในสคริปต์แล้ว |
| 3 | A2 แยก poststart | สคริปต์จับเวลาได้ **ต่ำกว่า 3 วินาที** |
| 4 | B1 `.env.example` | `git check-ignore -v .env` ตอบกลับ และ `.env.example` ไม่มีค่าจริงสักตัว |
| 5 | B2 `setup.cmd` | ลบ `node_modules` + `.setup` แล้วรันใหม่ ต้องกลับมาใช้งานได้ |
| 6 | B3 `start-lite.cmd` | เปิดแล้วมีแค่ 2 หน้าต่าง (เซิร์ฟเวอร์ + เบราว์เซอร์) |
| 7 | B4 README | อ่านแล้วทำตามได้โดยไม่ต้องถามใคร |
| 8 | A4 Gemini bridge | `agy -p "reply with exactly OK" --output-format json` ผ่านก่อน แล้วค่อยเขียนโค้ด |

## 6. กฎที่ห้ามลืม

1. **วัดจริงก่อนเคลมว่าเสร็จ** — Min เคยบอกไว้ชัด อย่าบอกว่า "แก้แล้ว" จากตรรกะอย่างเดียว
   ต้องรันสถานการณ์จริงแล้วเอาผลจริงมาโชว์
2. **ห้าม automation หน้าจอ** — ห้ามใช้ pyautogui หรืออะไรที่แย่งโฟกัสจอ โดยไม่ขอ Min ก่อนทีละครั้ง
3. **ใช้ `python` ไม่ใช่ `python3`** — `python3` บนเครื่องนี้เป็น stub ที่ตายแล้ว
4. **`.env` ห้ามหลุดขึ้น git** — เช็คก่อน commit ทุกครั้ง
5. **ห้ามแตะ WebSocket broadcast หรือรูปแบบการเซฟไฟล์** — นั่นคือทางเลือก C ยังไม่อนุมัติ
6. **ห้ามรีสตาร์ตเซิร์ฟเวอร์ระหว่างทำงาน** — รอจนจบทุกงานแล้วรีครั้งเดียวตอนท้าย

## 7. เรื่องที่ยังไม่ทำ (ทางเลือก C)

เก็บไว้ทำวันหลัง ตอนนี้ยังไม่เจ็บเพราะโปรเจกต์ที่เปิดอยู่เล็ก (0.15 MB)

- `server.js:665` — `broadcast()` แปลง state ทั้งก้อนเป็น JSON ทุกครั้งที่มีการแก้
  โปรเจกต์ใหญ่สุด = 14.1 MB ต่อครั้ง ใช้เวลา stringify 116 ms
- เซฟด้วย `JSON.stringify(data, null, 2)` ทำให้ไฟล์ใหญ่ขึ้นเกือบ 2 เท่า (14.1 MB → 25.9 MB)
- ลายเส้น 3,698 เส้นอยู่ในไฟล์ JSON ก้อนเดียวกับข้อมูลอื่น

**วันที่จะเจ็บจริง:** วันที่ Min เปิดกระดานใหญ่ ๆ ขึ้นมาใช้
