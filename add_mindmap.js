const BASE = "http://localhost:4321";

async function postNode(text, parentId, color) {
    const payload = { text };
    if (parentId) payload.parentId = parentId;
    if (color) payload.color = color;
    
    const res = await fetch(BASE + "/api/nodes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });
    return res.json();
}

async function run() {
    // 1. Create root at current viewport
    const root = await postNode("สรุป Fluid Week 2: Hydraulic Pumps", null, "#f59e0b");
    console.log("Root created:", root.id);

    // 2. Add children
    await postNode("1. Pumping Theory: สร้างสุญญากาศดูดน้ำมัน ผลักสร้างการไหล", root.id);
    await postNode("2. Pump Classification: แบ่งเป็น Nonpositive (หอยโข่ง) และ Positive (ให้อัตราไหลคงที่)", root.id);
    
    const p3 = await postNode("3. ชนิดของปั๊ม Positive Displacement", root.id, "#3b82f6");
    await postNode("Gear Pump (เฟืองนอก, ใน, Lobe, Gerotor, Screw)", p3.id);
    await postNode("Vane Pump (สมดุล, ไม่สมดุล, ปรับชดเชยความดันได้)", p3.id);
    await postNode("Piston Pump (Axial: Swash Plate/Bent-Axis, Radial)", p3.id);

    await postNode("4. Pump Efficiencies: ประสิทธิภาพปริมาตร, เชิงกล, รวม (Qt = Vd x N)", root.id);
    await postNode("5. Performance & Comparison: กราฟสมรรถนะ, ตารางเปรียบเทียบ", root.id);
    await postNode("6. Pump Cavitation: ฟองอากาศเข้าปั๊มสั่น (แก้โดยคุมความเร็ว, ลดท่อ/ข้อต่อ)", root.id);
    await postNode("7. Pump Selection: กระบอกสูบ -> อัตราไหล -> กำลัง -> ขนาดปั๊ม", root.id);

    // 3. Tidy layout for this subtree
    await fetch(BASE + "/api/layout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rootId: root.id })
    });
    console.log("Layout tidied");

    // 4. Send chat message
    await fetch(BASE + "/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role: "gemini", text: "ผมจัดทำสรุปลงใน Mind Map ตรงหน้าจอที่คุณดูอยู่ให้เรียบร้อยแล้วครับ ลองซูมดูได้เลยครับ!", section: "main" })
    });
}

run().catch(console.error);
