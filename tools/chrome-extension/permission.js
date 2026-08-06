// Grants the extension origin microphone access once, from a real page with a
// user gesture. The offscreen document cannot raise this prompt itself, so
// without this step getUserMedia there fails silently.
const status = document.getElementById("status");

document.getElementById("grant").addEventListener("click", async () => {
  status.textContent = "กำลังขอสิทธิ์…";
  status.className = "";
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    stream.getTracks().forEach((t) => t.stop()); // only needed to trigger the prompt
    status.textContent = "✅ เรียบร้อย — กด Alt+P ได้เลย ไม่ต้องเปิดหน้านี้อีก";
    status.className = "ok";
  } catch (e) {
    status.textContent = `❌ ไม่ได้รับสิทธิ์ (${e.name}) — ลองกดไอคอนกล้อง/ไมค์บนแถบที่อยู่ของ Chrome แล้วเลือกอนุญาต`;
    status.className = "bad";
  }
});
