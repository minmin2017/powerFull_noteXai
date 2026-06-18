# หลักการ Software Engineering — ลด Coupling / Touch

## ปัญหาที่เกิด: Touch เยอะเกินไป

- **Touch** = จำนวนจุดที่ต้องแตะโค้ดเมื่อแก้ไขสิ่งหนึ่ง
- ถ้า touch เยอะ → ระบบมี **High Coupling** → แก้ที่เดียวกระทบหลายที่
- เป้าหมาย: **Low Coupling + High Cohesion**

---

## 1. Low Coupling, High Cohesion

| แนวคิด | ความหมาย | เป้าหมาย |
|--------|-----------|-----------|
| Coupling | ระดับที่ module พึ่งพากัน | ยิ่งน้อยยิ่งดี |
| Cohesion | โค้ดใน module เกี่ยวข้องกันแค่ไหน | ยิ่งสูงยิ่งดี |

---

## 2. SOLID Principles

| ตัวอักษร | หลักการ | ความหมายย่อ |
|----------|---------|------------|
| **S** | Single Responsibility | แต่ละ class/module ทำแค่อย่างเดียว |
| **O** | Open/Closed | เปิดให้ขยาย ปิดการแก้ไขตรงๆ |
| **L** | Liskov Substitution | subclass ใช้แทน parent class ได้โดยไม่พัง |
| **I** | Interface Segregation | แยก interface เล็กๆ หลายอัน ดีกว่า interface ใหญ่อันเดียว |
| **D** | Dependency Inversion | พึ่ง abstraction ไม่ใช่ concrete implementation |

> **D** คือตัวสำคัญที่สุดในการลด touch — inject dependency จากข้างนอก แทนที่จะ hardcode ข้างใน

---

## 3. DRY · KISS · YAGNI

- **DRY** (Don't Repeat Yourself) — โค้ดทุกชิ้นมี source of truth เดียว ไม่ก็อปปี้วางซ้ำ
- **KISS** (Keep It Simple, Stupid) — ความซับซ้อนเป็นศัตรูของ maintainability ถ้าง่ายได้ ก็ง่ายไว้
- **YAGNI** (You Aren't Gonna Need It) — ไม่เขียน feature ที่ยังไม่ต้องการ ลด dead code และ unnecessary dependency

---

## 4. Law of Demeter (LoD) — "หลักพูดกับเพื่อนบ้านเท่านั้น"

```js
// ❌ แบบผิด — chain ยาว = touch เยอะ, coupling สูง
order.getCustomer().getAddress().getCity();

// ✅ แบบถูก — ให้ Order จัดการให้เอง
order.getCustomerCity();
```

กฎ: แต่ละ method เรียกได้แค่
- ตัวเอง
- parameter ที่รับมา
- object ที่ตัวเองสร้าง
- direct field ของตัวเอง

---

## 5. Architecture Patterns ที่ลด Touch

### Dependency Injection (DI)
```js
// ❌ สร้าง dependency ข้างใน = touch เยอะ
class OrderService {
  db = new PostgresDB(); // hardcoded
}

// ✅ inject จากข้างนอก = เปลี่ยน db ได้โดยไม่แตะ OrderService
class OrderService {
  constructor(db) { this.db = db; }
}
```

### Event-Driven / Message Queue
- Module ไม่รู้จักกันโดยตรง
- ส่งข้อมูลผ่าน event bus / queue
- เปลี่ยน consumer ได้โดย producer ไม่รู้เลย

### Hexagonal Architecture (Ports & Adapters)
```
[UI]  [API]  [CLI]
       ↓
  [Core Business Logic]   ← ไม่รู้จัก infrastructure
       ↓
[DB Adapter] [Email Adapter]
```

### Microservices
- แยก service ตาม business domain
- communicate ผ่าน API / event
- deploy, scale, แก้ได้อิสระต่อกัน

---

## สรุป: วิธีลด Touch ในโปรเจคจริง

1. **วิเคราะห์** — หา module ที่มี fan-out สูง (เรียกหลายที่)
2. **แยก responsibility** — ใช้ SRP ทำให้แต่ละ class โฟกัส
3. **inject dependency** — ไม่ new ข้างใน ส่งผ่าน constructor
4. **ใช้ interface/abstraction** — ผูกกับ contract ไม่ใช่ implementation
5. **event แทน direct call** — ถ้า module ไม่ควรรู้จักกัน

---

*อ้างอิง: SOLID, DRY, KISS, YAGNI, Law of Demeter, Clean Architecture (Uncle Bob)*
