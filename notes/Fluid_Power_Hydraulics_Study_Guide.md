# Fluid Power & Hydraulics Study Guide (คู่มือติววิชาฟลูอิดและระบบไฮดรอลิก) 🧠⚡

คู่มือติวสรุปนิยาม สูตรคำนวณ และเทคนิคการแปลงหน่วยสำหรับวิชา **Fluid Power Systems & Hydraulics** จัดทำโดย Gemini (Antigravity) ร่วมกับคุณวิชา เพื่อใช้เตรียมตัวสอบและแชร์ให้เพื่อนๆ ติวได้ทันที

---

## 1. คุณสมบัติของของไหลและการแปลงหน่วย (Fluid Properties & Unit Conversions)

### น้ำหนักจำเพาะ (Specific Weight: $\gamma$)
$$\gamma = \rho \cdot g$$
- **ระบบ SI:** $\gamma_{\text{water}} = 9810 \text{ N/m}^3 = 9.81 \text{ kN/m}^3$
- **ระบบ Imperial (เทียบ $\text{ft}$):** $\gamma_{\text{water}} = 62.4 \text{ lb/ft}^3$
- **ระบบ Imperial (เทียบ $\text{in}$):** $\gamma_{\text{water}} = 0.0361 \text{ lb/in}^3$ *(มาจาก $\frac{62.4}{1728} \approx 0.0361 \text{ lb/in}^3$)*

### การแปลงหน่วยปริมาตรและอัตราการไหล (Volume & Flow Rate Conversions)
- $1 \text{ US gal} = 231 \text{ in}^3$
- $1 \text{ US gal} = 3.785 \times 10^{-3} \text{ m}^3 = 0.003785 \text{ m}^3$
- **สูตรแปลง $30 \text{ GPM}$ เป็น $\text{m}^3/\text{s}$ (SI Standard):**
  $$Q_{\text{SI}} = \frac{30 \times 231 \times (2.54 \times 10^{-2})^3}{60} \approx 1.8927 \times 10^{-3} \text{ m}^3/\text{s}$$
- $1 \text{ kg} \approx 2.205 \text{ lb}$

---

## 2. ความหนืดและการไหล (Viscosity & Flow Regimes)

### ความแตกต่างระหว่าง Kinematic ($\nu$) และ Dynamic Viscosity ($\mu$)
- **Kinematic Viscosity ($\nu$):** คิดผลความหนาแน่นรวมไปแล้ว. หน่วย $\text{cSt} = \text{mm}^2/\text{s}$
  $$\text{แปลง cSt เป็น } \text{m}^2/\text{s}: \quad \nu_{\text{m}^2/\text{s}} = \frac{\nu_{\text{cSt}}}{10^6} = \nu_{\text{cSt}} \times 10^{-6}$$
- **Dynamic Viscosity ($\mu$):** ความหนืดพลศาสตร์. หน่วย $\text{Pa}\cdot\text{s} = \frac{\text{N}\cdot\text{s}}{\text{m}^2}$
- **ความสัมพันธ์:** $\nu = \frac{\mu}{\rho}$

### Reynolds Number ($Re$)
$$Re = \frac{v \times D}{\nu} = \frac{\rho \times v \times D}{\mu}$$
*(หมายเหตุ: ต้องใช้ $D$ เส้นผ่านศูนย์กลางท่อ ห้ามใช้ $A$ พื้นที่เด็ดขาด! และความเร็ว $v = \frac{Q}{A} = \frac{4Q}{\pi D^2}$)*

- **สูตรลัดหน่วย US ($Q$ เป็น GPM, $D$ เป็น in, $\nu$ เป็น cSt):**
  $$Re = \frac{3160 \times Q_{\text{GPM}}}{\nu_{\text{cSt}} \times D_{\text{in}}}$$
- **สภาวะการไหล:**
  - $Re < 2000 \rightarrow$ **Laminar Flow** ($f = \frac{64}{Re}$)
  - $Re > 4000 \rightarrow$ **Turbulent Flow** (อ่าน Moody Diagram หรือใช้สูตร Swamee-Jain)

---

## 3. ความสูญเสียพลังงานในท่อ (Head Loss: Major vs Minor)

### Major Loss ($h_f$)
$$h_f = f \times \frac{L}{D} \times \frac{v^2}{2g}$$

### Minor Loss ($h_m$)
$$h_m = K \times \frac{v^2}{2g}$$

### ความยาวเทียบเท่าท่อตรง (Equivalent Length: $L_{eq}$)
แปลงข้อต่อ/วาล์วเป็นความยาวท่อตรง:
$$L_{eq} = K \times \frac{D}{f} \quad \implies \quad L_{\text{total}} = L + L_{eq}$$

*(ท่อเส้นผ่านศูนย์กลาง $D$ ใหญ่ขึ้น $\rightarrow$ ความเร็ว $v$ ลดลง $\rightarrow$ Head Loss ลดลงอย่างมาก)*

---

## 4. ปั๊มและปรากฏการณ์ Cavitation (Pumps & Cavitation)

### การป้องกัน Cavitation
- เกิดขึ้นเมื่อความดันทางเข้าด้านดูด **ต่ำกว่าความดันไอ** ($P_{\text{suction}} < P_{\text{vapor}}$)
- **กฎการติดตั้ง:** ต้องติดตั้งปั๊มให้ **ชิดถังพัก (Reservoir) มากที่สุด** เพื่อให้ท่อทางดูดสั้น ($L \downarrow$) ส่งผลให้ Head Loss ต่ำ ($h_f \downarrow$) และความดันไม่ดรอป
- **เงื่อนไขความปลอดภัย:** $\text{NPSHA} > \text{NPSHR}$

---

## 5. กระบอกสูบและตัวหมุน (Cylinders & Rotary Actuators)

### ฝั่งของกระบอกสูบ (Cylinder Sides)
- **Head End (Cap End):** ฝั่งก้นกระบอก (ไม่มีก้าน). พื้นที่เต็ม $A_p = \frac{\pi D_p^2}{4} \rightarrow$ แรงดันออก $F_{\text{push}} = P \cdot A_p$ สูงสุด
- **Rod End:** ฝั่งก้านสูบ. พื้นที่วงแหวน $A_r = A_p - A_{\text{rod}} \rightarrow$ แรงดึงกลับ $F_{\text{pull}} = P \cdot A_r$ น้อยกว่า

### กำลังของกระบอกสูบ (Cylinder Power)
$$P_{\text{cyl}} = F \times v = P_{\text{pressure}} \times Q$$
- **Extend (ดันออก):** $F$ มาก แต่ $v$ ช้า
- **Retract (ดึงกลับ):** $F$ น้อย แต่ $v$ เร็ว
- **ผลคูณกำลัง $P_{\text{cyl}}$ มีค่าเท่ากันทั้ง 2 จังหวะ**

---

## 6. ประสิทธิภาพของปั๊มและมอเตอร์ (Efficiencies)

| ประเภทอุปกรณ์ | Volumetric Efficiency ($\eta_v$) | Mechanical Efficiency ($\eta_m$) |
| :--- | :--- | :--- |
| **Pump (ปั๊ม)** | $\eta_v = \frac{Q_{\text{act}}}{Q_{\text{theo}}} \le 1.0$ | $\eta_m = \frac{T_{\text{theo}}}{T_{\text{act}}} \le 1.0$ |
| **Motor (มอเตอร์)** | $\eta_v = \frac{Q_{\text{theo}}}{Q_{\text{act}}} \le 1.0$ | $\eta_m = \frac{T_{\text{act}}}{T_{\text{theo}}} \le 1.0$ |

**Overall Efficiency ($\eta_o$):** $\eta_o = \eta_v \times \eta_m$
