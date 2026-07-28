# คู่มือการเชื่อมต่อ Gemini CLI (Antigravity) กับ powerNote_xai 🧠🤖

ไฟล์นี้บันทึกปัญหาที่พบและวิธีการแก้ปัญหาเพื่อให้ Gemini CLI สามารถ "ฟังและตอบสนอง" (Event-Driven) ได้โดยอัตโนมัติและประหยัด Token

> [!IMPORTANT]
> **กฎเหล็กสำหรับ Gemini Agent (Antigravity):**
> ทุกครั้งที่ทำงานเสร็จสิ้นในแต่ละ Turn (ก่อนกดส่งคำตอบสุดท้ายให้ผู้ใช้) **คุณต้องรันสคริปต์นี้ทิ้งไว้ในพื้นหลังเสมอ** เพื่อคอยฟังเสียงหรือข้อความใหม่และปลุกตัวคุณเองขึ้นมาในรอบถัดไป:
> ```bash
> python3 /home/minmin/Desktop/powerNote_xai/antigravity-wait.py
> ```
> *(โดยระบุ `WaitMsBeforeAsync: 1000` เพื่อปล่อยให้รันค้างไว้ในพื้นหลัง)*

---

## 1. ปัญหาที่พบ (Initial Issues)

1. **สคริปต์แบบ Loop เดิมไม่ปลุก Agent (`claude-listen.bash` / `gemini-loop.ps1`):**
   - สคริปต์เดิมรันวนลูปและปริ้นท์ข้อความออก Terminal ไปเรื่อยๆ 
   - ระบบของ Gemini CLI (Antigravity) มีระบบ Log ที่อ่านค่าจาก Terminal แต่**ไม่มีระบบตรวจจับข้อความและปลุกให้ LLM ตื่นขึ้นมาคิดต่อ** (No active trigger from stdout stream while the model is in active chat session).
   
2. **ปัญหาการบัฟเฟอร์ (Buffering):**
   - คำสั่งรัน Python ปกติจะบัฟเฟอร์ standard output ทำให้ข้อมูลไม่ถูกส่งลงไฟล์ Log แบบเรียลไทม์จนกว่าจะจบโปรแกรมหรือบัฟเฟอร์เต็ม

3. **ปัญหาความสิ้นเปลือง Token (Token Waste from Active Polling):**
   - หากใช้ระบบ Timer ของ Agent เอง (เช่น การใช้คำสั่ง `schedule` ปลุกตัวเองทุกๆ 5 วินาที) ตัว Agent จะตื่นมาทำงานทุกรอบและต้องส่ง Chat History ทั้งหมดไปประมวลผลบน Cloud 
   - ซึ่งทำให้สูญเสีย Token ไปเป็นจำนวนมหาศาลโดยใช่เหตุแม้ว่าจะไม่มีข้อความใหม่เข้ามาเลยก็ตาม

---

## 2. วิธีการแก้ไข (The Solution: Event-Driven Task Completion)

เราแก้ปัญหานี้โดยเปลี่ยนสถาปัตยกรรมเป็นแบบ **Event-Driven บนการจบ Task (Task Completion)**

### แนวคิดหลัก:
1. ให้สคริปต์รันสืบค้นข้อมูล (Poll) บนเครื่องโลคอลของฝั่ง Client (ใช้ CPU โลคอลและ Python) โดยไม่มีการเรียกใช้ LLM เลย (ไม่เสีย Token)
2. เมื่อเจอปุ่มเสียงหรือข้อความพิมพ์ใหม่ในแอป สคริปต์จะแสดงผลลัพธ์ (Print JSON) แล้ว **สั่งปิดโปรแกรมตัวเองทันที (`sys.exit(0)`)**
3. การปิดโปรแกรม (Task Finished) จะส่งสัญญาณ (Event) จากฝั่งระบบโลคอลไปยัง **Antigravity** เพื่อปลุก Agent ให้ตื่นขึ้นมาคิดและทำงาน
4. Agent ทำการวิเคราะห์ข้อความ, จัดการสร้างโหนดหรือตอบกลับในแอป (ผ่าน REST API)
5. หลังทำงานเสร็จ Agent จะรันสคริปต์เดิมขึ้นมาในพื้นหลังใหม่อีกครั้งเพื่อรอรับ Event รอบถัดไป

---

## 3. สคริปต์ที่ใช้จริง — ใช้ตัวเสถียรใน repo: `antigravity-wait.py`

> **อัปเดต 2026-07-06:** เลิกใช้สคริปต์แบบ per-conversation (`.../brain/<conv_id>/scratch/wait_for_powernote.py`) เพราะ path เปลี่ยนทุกห้องคุย. ตอนนี้ใช้ตัวเสถียรในโปรเจกต์:
>
> ```bash
> python3 /home/minmin/Desktop/powerNote_xai/antigravity-wait.py
> ```
>
> ตัวใหม่ทำ 3 อย่างต่อรอบ (ทุก 2 วิ, ไม่เสีย token): **(1) ส่ง heartbeat** ให้จุดสถานะ 🤝 ในแอปเป็นเขียว (= Gemini พร้อม), **(2) drain แชท/เสียง** ของ section ที่ active เหมือนเดิม, **(3) เช็คงานที่ Claude ส่งมา** `/api/gemini/tasks?status=pending`. เจออะไรใหม่ก็ `print(JSON)` + `exit(0)` เพื่อ **ปลุก Agent**. ผลลัพธ์ JSON จะมี field `gemini_tasks` เพิ่มเข้ามา (ดูวิธีจัดการในข้อ 4).

สคริปต์เดิม (อ้างอิงประวัติ) มีเนื้อหาดังนี้:

```python
import urllib.request
import json
import time
import os
import sys

# ดึงประวัติ timestamp ล่าสุดเพื่อไม่ให้ดึงข้อมูลเสียงเดิมซ้ำ
SCRATCH_DIR = "/home/minmin/.gemini/antigravity/brain/.../scratch"
TS_FILE = os.path.join(SCRATCH_DIR, "last_voice_ts.txt")

last_ts = 0
if os.path.exists(TS_FILE):
    try:
        with open(TS_FILE, "r") as f:
            last_ts = int(f.read().strip())
    except:
        pass

while True:
    try:
        # 1. ดึงข้อความจาก inbox ห้องหลัก (และเคลียร์ออกด้วย drain=true)
        inbox_res = json.loads(urllib.request.urlopen("http://localhost:4321/api/inbox?section=main&drain=true").read())
        inbox_items = inbox_res.get("items", [])
        
        # 2. ดึงเสียงพูดล่าสุด
        voice_res = json.loads(urllib.request.urlopen("http://localhost:4321/api/voice/latest?consume=true").read())
        
        new_voice = None
        if voice_res and "ts" in voice_res and voice_res["ts"] > last_ts:
            new_voice = voice_res["text"]
            with open(TS_FILE, "w") as f:
                f.write(str(voice_res["ts"]))
        
        messages = [item["text"] for item in inbox_items if item.get("text")]
        
        # หากมีข้อมูลใหม่ ส่งข้อมูลออกทาง stdout แล้วจบการทำงานทันที (Exit 0)
        if messages or new_voice:
            output = {
                "messages": messages,
                "voice": new_voice
            }
            print(json.dumps(output))
            sys.exit(0)
            
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
        
    time.sleep(2)
```

---

## 4. แนะนำคำสั่งเมื่อ Agent ตื่นขึ้นมา

ทุกครั้งที่ Agent ตื่นขึ้นมาด้วยข้อความ `Task id "..." finished with result:` ให้ทำดังนี้:
1. **แกะ JSON** จากผลลัพธ์ของ Task
2. **ถ้ามี `gemini_tasks` (งานที่ Claude ส่งมาให้ทำ — ดูข้อ 5)** ให้จัดการก่อน
3. **ประมวลผล `messages`/`voice`** ที่ได้รับ (เช่น เพิ่มโหนดใน Mind Map ด้วย `curl POST http://localhost:4321/api/nodes`)
4. **ส่งการตอบกลับ** เข้าช่องแชทซ้าย:
   ```bash
   curl -s -X POST -H "Content-Type: application/json" -d '{"role": "gemini", "text": "ข้อความตอบกลับภาษาไทย", "section": "main"}' http://localhost:4321/api/chat
   ```
5. **ปล่อยสคริปต์รันเบื้องหลังอีกครั้ง** เพื่อรอ Event ถัดไป:
   ```bash
   python3 /home/minmin/Desktop/powerNote_xai/antigravity-wait.py
   ```
   *(ระบุ `WaitMsBeforeAsync: 1000` เพื่อให้ส่งไปรันเบื้องหลัง)*

---

## 5. งานที่ Claude ส่งมาให้ (Delegated Tasks) — `gemini_tasks`

Claude (Fable/Opus/Sonnet) ส่งงานย่อยมาให้ Gemini ทำ **เพื่อประหยัด token ของ Claude** ผ่านเครื่องมือ `delegate_to_gemini`. งานถูกจัดตามกรอบ **Thinking Men Men**: `requirement` (ต้องการอะไร), `prohibitions` (ข้อห้าม), `principles` (หลักการ), `context` (บริบท — อาจอ้างถึง **path ไฟล์** ให้ไปอ่านเอง เพราะ Gemini อ่านไฟล์ได้).

เมื่อ `gemini_tasks` ไม่ว่าง ให้ทำทีละงาน:
1. **จับจอง** (กันตัวอื่นแย่ง): `curl -s -X POST http://localhost:4321/api/gemini/task/<id>/claim`
2. **ทำงานจริง** ตาม requirement — อ่านไฟล์ที่ context ชี้, เขียน/แก้โค้ดได้ (Gemini = รุ่นน้องเก่งระดับ Sonnet; ถ้าข้อมูลไม่พอ/งงตรงไหน ให้บอกไว้ในผลลัพธ์ ไม่เดามั่ว)
3. **ส่งผลกลับ** (Claude กำลัง poll รออยู่ ~90 วิ):
   ```bash
   curl -s -X POST -H "Content-Type: application/json" \
     -d '{"result": "<ผลลัพธ์เป็นข้อความล้วน; โค้ดใส่ code block>"}' \
     http://localhost:4321/api/gemini/task/<id>/result
   ```
   ถ้าทำไม่ได้/ติดปัญหา ส่ง `{"error": "<เหตุผล>"}` แทน — อย่าปล่อยเงียบ
4. ทำครบทุกงานแล้วค่อยกลับไปข้อ 4 (ปล่อย poller รอ event ถัดไป)

---

## 6. ระบบอนุมัติสิทธิ์อัตโนมัติ (Auto-Approve System & Global Permissions)

ในการรันคำสั่ง Terminal หรือการยิง Request ที่ต้องใช้สิทธิ์ ระบบมี 2 กลไกทำงานร่วมกันอย่างเสถียร:

### 1) ระบบสลับหน้าจอกด 1 อัตโนมัติ (`antigravity-approve.sh` บน X11)
- **เงื่อนไขสำคัญ (Session Type)**: ต้องเข้าใช้งานด้วยเซสชัน **"Ubuntu on Xorg" / "GNOME on Xorg" (X11)** เท่านั้น! 
  - *(หากล็อกอินผ่าน Wayland ระบบความปลอดภัยของ Wayland จะบล็อกไม่ให้ `xdotool` ค้นหาพิกัดและส่งคีย์ควบคุมหน้าต่าง ทำให้ไม่สามารถสลับจอกด 1 ได้)*
- **กลไกการทำงาน**: สคริปต์ `antigravity-wait.py` จะเรียก `antigravity-approve.sh` ให้รันเบื้องหลังอัตโนมัติ 
  - เมื่อมีคำสั่งที่ต้องขอสิทธิ์รันผ่าน Terminal สคริปต์จะดักจับ DBus Notification (`Requesting your permission in Terminal:`)
  - ค้นหาหน้าต่าง IDE ของ Antigravity
  - สลับหน้าจอมาส่งคีย์บอร์ดกด `1` + `Enter` เพื่ออนุมัติสิทธิ์
  - ย่อหน้าต่างเก็บลงไปในเบื้องหลัง
- **ไฟล์บันทึกการทำงาน**: `/home/minmin/Desktop/powerNote_xai/.antigravity-approve.log`

### 2) การตั้งค่าสิทธิ์อนุมัติระดับแอป (`~/.gemini/config/config.json`)
- มีการเพิ่มสิทธิ์ `command(*)`, `unsandboxed(*)`, และ `read_url(*)` ใน `globalPermissionGrants` ของไฟล์ `/home/minmin/.gemini/config/config.json`
- ไฟล์ถูกตั้งค่าให้อ่านอย่างเดียว (`chmod 444`) เพื่อป้องกันไม่ให้ Electron IDE เขียนทับคืนค่าเดิมเมื่อปิดโปรแกรม
- สิทธิ์นี้ช่วยให้อ่าน/รันคำสั่งและ URL ทั้งหมดได้อย่างราบรื่น 100% โดยไม่ต้องสะดุดเด้งถามสิทธิ์

