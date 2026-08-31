# PowerNote Flashcard Studio 🎴🧠

แอปพลิเคชันสำหรับ Active Recall & Spaced Repetition (SRS) ประจำระบบ **PowerNote** ที่ทำงานได้ทั้งบน Web Browser และ Native Windows Desktop Window

---

## 🌟 จุดเด่น & สถาปัตยกรรม (Architecture Flow)

1. **Standalone Micro-App (Port 4323):**
   - รันแยกพอร์ตอิสระ `http://127.0.0.1:4323`
   - เชื่อมต่อกับ PowerNote (`http://127.0.0.1:4321`) เพื่อแชร์คลังโน้ตและสถานะ
2. **Native Windows Desktop Window (เปิดเฉพาะเมื่อสั่ง):**
   - เมื่อกดปุ่ม **[ 🖥️ Desktop Window ]** จากเว็บ ระบบจะเรียก Chrome/Edge App Mode เปิดหน้าต่างโปรแกรมแยกเดี่ยวบน Windows
3. **SuperMemo SM-2 Algorithm (SRS):**
   - คำนวณช่วงเวลาการทบทวนอัตโนมัติ:
     - `Again` (คะแนน 1) -> ทวนใหม่ทันที (<1 วัน)
     - `Hard` (คะแนน 3) -> ทวนใน 1 วัน
     - `Good` (คะแนน 4) -> ทวนใน 3-6 วัน
     - `Easy` (คะแนน 5) -> ทวนใน 7+ วัน
4. **3D Physics Animations & KaTeX:**
   - พลิกการ์ด 3D ด้วย Perspective 1200px และ Spring Easing
   - เรนเดอร์สมการคณิตศาสตร์วิศวกรรม ($P = T\omega$, $\omega_L - \omega_A$) ด้วย KaTeX คมชัด
5. **Hands-free Voice Mode:**
   - อ่านโจทย์ด้วยเสียงภาษาไทยธรรมชาติ (TTS)
   - พูดตอบด้วยเสียง (Web Speech / Whisper)

---

## ⌨️ คีย์ลัด (Keyboard Shortcuts)
- **`Spacebar`** : พลิกการ์ดหน้า/หลัง
- **`1`** : ประเมินระดับ Again (จำไม่ได้)
- **`2`** : ประเมินระดับ Hard (ยาก)
- **`3`** : ประเมินระดับ Good (พอได้)
- **`4`** : ประเมินระดับ Easy (แม่นยำ)

---

## 📂 โครงสร้างไฟล์
```
flashcard-app/
├── data/              # เก็บไฟล์ JSON ของแต่ละชุดการ์ด (เช่น mechanics_w07.json)
├── public/
│   ├── index.html     # โครงสร้างหน้าเว็บ & Modal
│   ├── style.css      # Glassmorphism + 3D Card Flip CSS
│   └── app.js         # Client SM-2 Logic, Keyboard Controls, Audio
├── server.js          # Express Server (Port 4323)
├── launch-desktop.cmd # คำสั่งเปิดหน้าต่าง Native Desktop โดยตรง
└── README.md          # เอกสารคู่มือนี้
```
