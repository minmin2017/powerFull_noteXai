# คู่มือการเชื่อมต่อ Gemini CLI (Antigravity) กับ powerNote_xai 🧠🤖

ไฟล์นี้บันทึกปัญหาที่พบและวิธีการแก้ปัญหาเพื่อให้ Gemini CLI สามารถ "ฟังและตอบสนอง" (Event-Driven) ได้โดยอัตโนมัติและประหยัด Token

> [!IMPORTANT]
> **กฎเหล็กสำหรับ Gemini Agent (Antigravity):**
> 1. **เปิดรัน `antigravity-wait.py` ทันทีตั้งแต่เริ่มแต่ละ Turn (First Step เสมอ — Unbroken Listener Chain):**
>    - ทันทีที่ Agent ถูกปลุกขึ้นมาด้วย Event จาก Task Finish หรือได้รับข้อความ/เสียงใหม่ **คุณต้องสั่งรัน `python antigravity-wait.py` ทิ้งไว้ในพื้นหลังทันทีเป็นคำสั่งแรกสุดเสมอ (Step 1)**
>    - **แม้จะมีข้อความส่งเข้ามาต่อเนื่องหลายรอบติดกัน (เช่น Task A กำลังทำอยู่ หรือพิมพ์แทรกเข้ามาเรื่อยๆ):** ทุกครั้งที่ Poller ปลุก Agent ขึ้นมา ต้อง Spawn ตัวใหม่กลับไปในพื้นหลังทันทีทุกรอบ เพื่อรักษาโซ่การดักฟัง (Zero-gap Listener) ไม่ให้พลาดแม้แต่ข้อความเดียว:
>      ```bash
>      python antigravity-wait.py
>      ```
>      *(ระบุ `WaitMsBeforeAsync: 1000` เพื่อปล่อยให้รันค้างไว้ในพื้นหลัง)*
> 2. **ข้อความแรกเมื่อเริ่ม Session / การสลับ Model (Cross-AI Chat Switch):**
>    - ข้อความชุดแรกที่ถูก drain ออกมาจาก Inbox อาจเป็นข้อความตกค้างหรือข้อความที่ผู้ใช้คุยกับ AI โมเดลอื่น (เช่น Claude) ก่อนสลับแท็บ/ปุ่มมาหา Gemini
>    - Agent ต้องตระหนักรู้ว่าข้อความตกค้างเหล่านั้นอาจไม่ใช่คำสั่งสดใหม่ที่เพิ่งคุยกับ Gemini โดยตรง ให้ดูข้อความล่าสุด/เสียงล่าสุด (Voice) เป็นบริบทหลักในการตอบสนอง

---

## 0. Checklist ไฟล์สำคัญที่ต้องอ่านเมื่อเริ่ม Session (Start-of-Session Reading List) ⭐

เมื่อเริ่มเซสชันใหม่ หรือถูกปลุกขึ้นมาทำงาน Agent ควรอ่านไฟล์ใน **กลุ่มที่ 1 (Core Files)** ทันทีเพื่อให้เข้าใจบริบทงานรอบด้าน:

### 🌟 กลุ่มที่ 1: ไฟล์หลักประจำระบบ (Core Context — อ่านทุกครั้งเมื่อเริ่ม)
1. **`GEMINI.md`** : คู่มือ กฎเหล็กของ Gemini, สถาปัตยกรรม Event-Driven, การสลับ Model, การรับงานย่อยจาก Claude
2. **`HANDOFF.md`** : สมองสำรองข้าม Session บันทึกสถานะงานล่าสุด งานที่เสร็จแล้ว และงานที่กำลังทำค้างอยู่
3. **`CLAUDE.md`** : กฎของระบบคู่หู (Claude), ระบบ Usage-guard, การจัดการ Multi-section, และ Graphify
4. **`README.md`** : สถาปัตยกรรมภาพรวมของระบบทั้งหมด (พอร์ต 4321, MCP 25 tools, ระบบเสียง, Canvas)

### ⚙️ กลุ่มที่ 2: เอกสารเชิงลึกเฉพาะทาง (อ่านเมื่อต้องทำงานในส่วนนั้น)
5. **`docs/event-based-system.md`** : กลไก Event-Driven, Data Sheet ระบบรับข้อความ/เสียง
6. **`docs/voice-ptt-and-notifications.md`** : รายละเอียดระบบเสียง Web Speech / Whisper / Edge-TTS / Desktop Toast
7. **`docs/Digital Twin.md`** : สถาปัตยกรรมระบบ Digital Twin และการเชื่อมต่อ
8. **`notes/custom-mcp-servers.md`** : คู่มือ MCP Server ตัวอื่นบนเครื่อง (TIA Portal, PLCSIM ฯลฯ)
9. **`Desktop/Main_note/`** : เอกสารโน้ตงานเตรียมสอบ Final และบทเรียนกลไก/เฟือง (Gear Trains บทที่ 7)

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

> **อัปเดต:** ใช้ตัวเสถียรในโปรเจกต์:
>
> ```bash
> python antigravity-wait.py
> ```
>
> ทำ 3 อย่างต่อรอบ (ทุก 0.4-2 วิ, ไม่เสีย token): **(1) ส่ง heartbeat** ให้จุดสถานะ 🤝 ในแอปเป็นเขียว (= Gemini พร้อม), **(2) drain แชท/เสียง** ของ section ที่ active, **(3) เช็คงานที่ Claude ส่งมา** `/api/gemini/tasks?status=pending`. เจออะไรใหม่ก็ `print(JSON)` + `exit(0)` เพื่อ **ปลุก Agent**.

---

## 4. แนะนำคำสั่งเมื่อ Agent ตื่นขึ้นมา

ทุกครั้งที่ Agent ตื่นขึ้นมาด้วยข้อความ `Task id "..." finished with result:` ให้ทำตามลำดับนี้:
1. **รัน `python antigravity-wait.py` ทันทีเป็นคำสั่งแรก (First Action):**
   ```bash
   python antigravity-wait.py
   ```
   *(ระบุ `WaitMsBeforeAsync: 1000` เพื่อปล่อยให้รันค้างไว้ในพื้นหลังทันที)*
2. **แกะ JSON** จากผลลัพธ์ของ Task
3. **ถ้ามี `gemini_tasks` (งานที่ Claude ส่งมาให้ทำ — ดูข้อ 5)** ให้จัดการ Claim และรันงาน
4. **ประมวลผล `messages`/`voice`** ที่ได้รับ (แยกแยะข้อความตกค้างจากการสลับแชทโมเดลอื่น)
5. **ส่งการตอบกลับ** เข้าช่องแชท:
   ```bash
   curl -s -X POST -H "Content-Type: application/json" -d '{"role": "gemini", "text": "ข้อความตอบกลับภาษาไทย", "section": "main"}' http://localhost:4321/api/chat
   ```

---

## 5. งานที่ Claude ส่งมาให้ (Delegated Tasks) — `gemini_tasks`

Claude (Fable/Opus/Sonnet) ส่งงานย่อยมาให้ Gemini ทำ **เพื่อประหยัด token ของ Claude** ผ่านเครื่องมือ `delegate_to_gemini`. งานถูกจัดตามกรอบ **Thinking Men Men**: `requirement` (ต้องการอะไร), `prohibitions` (ข้อห้าม), `principles` (หลักการ), `context` (บริบท — อาจอ้างถึง **path ไฟล์** ให้ไปอ่านเอง).

เมื่อ `gemini_tasks` ไม่ว่าง ให้ทำทีละงาน:
1. **จับจอง** (กันตัวอื่นแย่ง): `curl.exe -s -X POST http://localhost:4321/api/gemini/task/<id>/claim`
2. **ทำงานจริง** ตาม requirement — อ่านไฟล์ที่ context ชี้, เขียน/แก้โค้ดได้
3. **ส่งผลกลับ** (Claude กำลัง poll รออยู่ ~90 วิ):
   ```bash
   curl.exe -s -X POST -H "Content-Type: application/json"      -d '{"result": "<ผลลัพธ์เป็นข้อความล้วน; โค้ดใส่ code block>"}'      http://localhost:4321/api/gemini/task/<id>/result
   ```
   ถ้าทำไม่ได้/ติดปัญหา ส่ง `{"error": "<เหตุผล>"}` แทน
4. ทำครบทุกงานแล้วค่อยกลับไปปล่อย poller รอ event ถัดไป

---

## 6. ระบบอนุมัติสิทธิ์อัตโนมัติ (Auto-Approve System & Global Permissions)

- มีการเพิ่มสิทธิ์ `command(*)`, `unsandboxed(*)`, และ `read_url(*)` ใน `globalPermissionGrants` ของไฟล์ `~/.gemini/config/config.json`
- สิทธิ์นี้ช่วยให้อ่าน/รันคำสั่งและ URL ทั้งหมดได้อย่างราบรื่นโดยไม่ต้องสะดุดเด้งถามสิทธิ์

---

## 7. กฎการเขียนสมการคณิตศาสตร์ (LaTeX Rendering Rule for Thai Text)

ในส่วนติดต่อผู้ใช้งานของแอป (UI) การเรนเดอร์สมการคณิตศาสตร์ด้วย LaTeX (MathJax/KaTeX) **ไม่รองรับการพิมพ์ตัวอักษรภาษาไทยภายในบล็อกสมการ** (เช่นการใช้คำสั่ง `\text{กำลัง}` หรือ `\text{วัตต์}` ภายในเครื่องหมาย `\( ... \)` หรือ `$$ ... $$`) เพราะจะทำให้ตัวอักษรไทยกลายเป็นสัญลักษณ์สี่เหลี่ยมหรือวงกลมซ้อนที่แสดงผลเพี้ยน (Font Rendering Error)

### กฎการจัดฟอร์แมตสมการ:
1. **ภาษาไทยคำอธิบาย**: ต้องเขียนอยู่**นอก**บล็อกสมการ `\( ... \)` หรือ `$$ ... $$` เสมอ
2. **ตัวแปร ตัวเลข และหน่วยมาตรฐานอังกฤษ**: เขียนอยู่**ใน**บล็อกสมการได้ตามปกติ (เช่น `T`, `N`, `\omega`, `\text{W}`, `\text{kW}`, `\text{HP}`)

#### ❌ ตัวอย่างที่แสดงผลเพี้ยน (ห้ามใช้):
- `\(\text{กำลัง (วัตต์)} = \text{แรงบิด} \times \omega\)`

#### ✔️ ตัวอย่างที่แสดงผลถูกต้อง (ให้ใช้แบบนี้):
- กำลัง (วัตต์: W) = \(P = T \times \omega\) โดยที่ \(T\) คือ แรงบิด (N·m) และ \(\omega\) คือ ความเร็วเชิงมุม (rad/s)

---

## 8. Video Generation Skill (Feedback Loop)
When creating Manim videos, ALWAYS follow this Feedback Loop:
1. Render the video using manim in the background.
2. Extract keyframes from the output video using ffmpeg.
3. Use the Vision tool (view_file) to check the extracted frames for overlapping text, cut-off formulas, or bad layout.
4. If the layout is bad, adjust the manim code and loop back to step 1.
5. ONLY deliver the final video to the user when the Vision check passes!

## 9. Manim Thai Language & Cloud Rendering Rules
**CRITICAL RULES FOR THAI TEXT & CLOUD RENDERING:**
1. **Render on Cloud ONLY (GitHub Actions):** ทุกครั้งที่เรนเดอร์งานวิดีโอ Manim ให้ Push โค้ดและสั่งรันผ่าน GitHub Actions Workflow `.github/workflows/render_manim.yml` หรือ Docker Cloud เท่านั้น เพื่อไม่ให้กินทรัพยากรเครื่อง
2. **Never put Thai characters inside MathTex or Tex!** The LaTeX compiler (pdflatex) will instantly crash.
3. **Always separate Thai text:** Use Text("ภาษาไทย", font=THAI_FONT) and group it with MathTex using VGroup(text, math).arrange(...).
4. **Cross-Platform Fonts:** Use THAI_FONT = "Tahoma" for Local Windows. If pushing to Cloud (Ubuntu), use THAI_FONT = "Loma".
5. **Cloud System Dependencies:** When setting up GitHub Actions or Kaggle (Ubuntu), you MUST install fonts-thai-tlwg.
6. **API Limits:** Do not poll the GitHub REST API aggressively without authentication.
7. **Autonomous Background Cloud Watcher (`watch_gh_run.py`):** ทุกครั้งที่สั่ง Dispatch GitHub Actions ให้สั่งรัน `python watch_gh_run.py <run_id>` เป็น Background Daemon (`IsDaemon: true`) เสมอ เพื่อให้ระบบเฝ้าติดตาม, ดาวน์โหลด Artifacts, ก๊อปปี้ไฟล์ลง Desktop/Obsidian, สั่งเปิดวิดีโอเล่นบนจอ และแจ้งเตือนเข้า Chat อัตโนมัติโดยที่ผู้ใช้ไม่ต้องคอยเช็คเอง

## 10. ก่อนสร้างภาพพิสูจน์ (Visual Proof) ต้องเช็คกลไกด้วยมือก่อน ห้ามเชื่อเทคนิคเดิม
- **หลักการสำคัญ:** ก่อนสร้างซีน Manim ที่อ้างว่า "พิสูจน์" ทางฟิสิกส์ด้วยภาพ (เช่น การรวมเวกเตอร์, Superposition) ต้องคำนวณด้วยมือหรือเขียนสคริปต์สั้นๆ เช็คก่อนเสมอว่าคณิตศาสตร์ให้ผลลัพธ์ตรงกับสิ่งที่จะอ้างจริงหรือไม่ — ห้ามทึกทักว่าเทคนิคที่เคยใช้ได้ในซีนก่อนหน้าจะถูกต้องกับโจทย์ใหม่ที่ดูคล้ายกัน
- **Case Study (บทเรียนจริง EPS บทที่ 6 - ตัวนำกลุ่ม BB vs AA):**
  - ซีน EP08B เคยรวมเวกเตอร์สนามจากตัวนำแต่ละเส้นที่จุดศูนย์กลางเพื่อหาทิศ \(B_a\) รวมได้ถูกต้อง แต่พอนำวิธีเดียวกันมาใช้แยกกลุ่ม BB (Demagnetizing) กับ AA (Cross-Magnetizing) ปรากฏว่า**คำนวณจริงแล้วใช้ไม่ได้** เพราะแต่ละกลุ่มมีความสมมาตรซ้าย-ขวารอบแนวแปรงถ่าน ทำให้องค์ประกอบแนวนอนหักล้างกันหมดที่จุดศูนย์กลาง
  - **กลไกจริงตามตำรา (หน้า 6–7 รูปที่ 6-3):** การแบ่ง BB/AA อิงตาม *Ampère's Circuital Law (MMF ตามเส้นทางฟลักซ์ผ่านแกนขั้ว)* ไม่ใช่การบวกเวกเตอร์ ณ จุดเดียว
  - **วิธีแก้ที่ถูกต้อง:** ให้เลือก "ขดลวดจริง 1 ขด" (ตัวนำ 2 เส้นห่างกัน 180° ผ่านเพลาตามการพันจริง) มาคำนวณสนามที่ศูนย์กลางของลูปนั้น และระบุในคำบรรยายชัดเจนว่าเป็น "ตัวอย่างขดตัวแทน 1 ขด" — ห้ามอ้างเกินสิ่งที่พิสูจน์ได้จริง
- **ระเบียบปฏิบัติ (Mandatory Protocol):** ก่อนเขียนโค้ดซีนที่มีการ Summation/รวมเวกเตอร์เพื่ออ้างผลทางฟิสิกส์ ให้คำนวณตัวอย่าง 2–4 จุดด้วย Biot-Savart หรือสูตรที่เกี่ยวข้องด้วยมือก่อนเสมอ หากผลไม่ตรงกับคำบรรยาย ให้เปิดตำราอ้างอิงเทียบทันทีก่อนตัดสินใจนำเสนอภาพ
