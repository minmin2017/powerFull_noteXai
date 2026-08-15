# Fluid Power Textbook Concepts & Unit Conversions Guide (ข้อสรุปสูตรและเทคนิคการตัดหน่วยจากหนังสือ) 📘⚡

ไฟล์แยกสรุปแนวคิด สูตรคำนวณเพิ่มเติม และเทคนิคการตัดหน่วยที่พบในหนังสือเรียนวิชา **Fluid Power Systems & Hydraulics**

---

## 1. การตัดหน่วยในสูตรอัตราการไหลทฤษฎี ($Q_T = V_D \times N$)

### ตัวอย่างการคำนวณและตัดหน่วย:
กำหนดให้ $V_D = 82 \text{ cm}^3/\text{rev}$ และ $N = 500 \text{ RPM} = 500 \text{ rev/min}$

1. **คำนวณได้หน่วย $\text{cm}^3/\text{min}$:**
   $$Q_T = \left(82 \frac{\text{cm}^3}{\text{rev}}\right) \times \left(500 \frac{\text{rev}}{\text{min}}\right) = 82 \times 500 \frac{\text{cm}^3 \cdot \cancel{\text{rev}}}{\cancel{\text{rev}} \cdot \text{min}} = \mathbf{41,000 \text{ cm}^3/\text{min}}$$

2. **แปลงเป็น $\text{L/min}$ (ลิตรต่อนาที):**
   $$Q_T = \frac{41,000 \text{ cm}^3/\text{min}}{1,000 \text{ cm}^3/\text{L}} = \mathbf{41 \text{ L/min}}$$

3. **แปลงเป็นหน่วยมาตรฐาน SI ($\text{m}^3/\text{s}$):**
   $$Q_T = \frac{41,000 \text{ cm}^3/\text{min}}{10^6 \text{ cm}^3/\text{m}^3 \times 60 \text{ s/min}} = \mathbf{6.833 \times 10^{-4} \text{ m}^3/\text{s}}$$

---

## 2. ตัวเลขคงที่แปลงหน่วยลัดในระบบ US Customary Units

### ตัวเลข 449 (GPM to $\text{ft}^3/\text{s}$)
มาจาก $1 \text{ ft}^3 = 7.4805 \text{ gal}$ และ $1 \text{ min} = 60 \text{ s}$:
$$1 \text{ GPM} = \frac{1 \text{ gal}}{1 \text{ min}} = \frac{1}{7.4805 \times 60} = \frac{1}{448.83} \approx \frac{1}{\mathbf{449}} \text{ ft}^3/\text{s}$$
$$\implies Q (\text{ft}^3/\text{s}) = \frac{Q (\text{GPM})}{449}$$

### ตัวเลข 0.408 (สูตรลัดหาความเร็ว $v$ ในท่อ)
$$v (\text{ft/s}) = \frac{0.408 \times Q_{\text{GPM}}}{D_{\text{in}}^2}$$

### ตัวเลข 7740 (สูตรลัดหา Reynolds Number $Re$)
$$Re = \frac{7740 \times v \times D_{\text{in}}}{\nu_{\text{cSt}}}$$
ที่มา: $\frac{1}{12 \text{ in/ft} \times 1.07639 \times 10^{-5} \text{ ft}^2/\text{s/cSt}} \approx \mathbf{7740}$

---

## 3. ที่มาของสมการ $v^2 = 2 a s$ ในกระบอกสูบไฮดรอลิก

มาจากสมการความเร่งคงที่ ($a = \text{const}$) เมื่อเริ่มเคลื่อนที่จากจุดหยุดนิ่ง ($u = 0$):
$$v^2 = u^2 + 2 a s \implies v^2 = 2 a s \implies v = \sqrt{2 a s}$$
ใช้ในการคำนวณการเบรกชะลอลูกสูบ (**Cylinder Cushioning / Braking Distance**)

---

## 4. ประสิทธิภาพปั๊ม vs มอเตอร์ ($\eta_v, \eta_m, \eta_o$)

### กฎเหล็ก (Golden Universal Rule)
$$\text{Efficiency } (\eta) = \frac{\text{ตัวเลขที่น้อยกว่า}}{\text{ตัวเลขที่มากกว่า}} \le 1.0 \quad (\le 100\%)$$

- **ปั๊ม (Pump):**
  - $\eta_v = \frac{Q_{\text{act}}}{Q_{\text{theo}}} \le 1.0$ (น้ำมันรั่ว $\rightarrow Q_{\text{act}}$ น้อยกว่าอยู่บน)
  - $\eta_m = \frac{T_{\text{theo}}}{T_{\text{act}}} \le 1.0$ (ความฝืด $\rightarrow T_{\text{act}}$ ออกแรงบิดจริงแพงกว่า/มากกว่าอยู่ล่าง)
  - $\eta_o = \frac{P \cdot Q_{\text{act}}}{T_{\text{act}} \cdot \omega}$

- **มอเตอร์ (Hydraulic Motor):**
  - $\eta_v = \frac{Q_{\text{theo}}}{Q_{\text{act}}} \le 1.0$ (น้ำมันรั่ว $\rightarrow$ ต้องป้อน $Q_{\text{act}}$ มากกว่าอยู่ล่าง)
  - $\eta_m = \frac{T_{\text{act}}}{T_{\text{theo}}} \le 1.0$ (ความฝืด $\rightarrow T_{\text{act}}$ ได้แรงบิดออกน้อยกว่าอยู่บน)
