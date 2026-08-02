/**
 * modules/github.js
 * Save active project to GitHub via /api/github/push
 */
export default function setupGitHub({ api, toast }) {
  const btn = document.getElementById("btn-github");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    btn.disabled = true;
    btn.textContent = "🐙 กำลังส่ง…";
    try {
      const res = await fetch("/api/github/push", { method: "POST" });
      const data = await res.json();
      if (res.ok) {
        toast(`✓ บันทึกไป GitHub แล้ว (${data.repo})`);
      } else {
        toast("❌ " + (data.error || "เกิดข้อผิดพลาด"));
      }
    } catch (e) {
      toast("❌ " + String(e));
    } finally {
      btn.textContent = "🐙 GitHub";
      btn.disabled = false;
    }
  });
}
