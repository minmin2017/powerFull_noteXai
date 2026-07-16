/**
 * modules/chat.js
 * Chat panel: tab rendering, message rendering, new-section button.
 *
 * localActiveSectionRef is { value: "main" } — mutations keep the ref in sync
 * with app.js and voice.js which share the same object.
 *
 * Returns { renderChat, renderChatTabs } so applyState can call renderChat().
 */
export default function setupChat({ STATE, api, toast, escapeHtml, localActiveSectionRef }) {
  function renderChatTabs() {
    const list = document.getElementById("chat-tab-list");
    if (!list) return;
    const sections =
      STATE.chatSections && STATE.chatSections.length
        ? STATE.chatSections
        : [{ id: "main", name: "แชทหลัก" }];
    const active = STATE.activeSection || sections[0].id;
    localActiveSectionRef.value = active;
    list.innerHTML = "";
    for (const sec of sections) {
      const tab = document.createElement("div");
      tab.className = "chat-tab" + (sec.id === active ? " active" : "");
      tab.dataset.id = sec.id;
      const label = document.createElement("span");
      label.className = "chat-tab-name";
      label.textContent = sec.name || "แชท";
      tab.appendChild(label);
      // switch section on click
      tab.addEventListener("click", () => {
        localActiveSectionRef.value = sec.id;
        if (sec.id !== (STATE.activeSection || "main"))
          api(`/api/chat-sections/${sec.id}/activate`, "POST");
      });
      // double-click to rename
      label.addEventListener("dblclick", (e) => {
        e.stopPropagation();
        const name = prompt("เปลี่ยนชื่อแชท:", sec.name || "");
        if (name && name.trim())
          api(`/api/chat-sections/${sec.id}`, "PATCH", { name: name.trim() });
      });
      if (sections.length > 1) {
        const del = document.createElement("button");
        del.className = "chat-tab-del";
        del.textContent = "×";
        del.title = "ลบแชทนี้ (พร้อมข้อความข้างใน)";
        del.addEventListener("click", (e) => {
          e.stopPropagation();
          if (confirm(`ลบแชท "${sec.name}" และข้อความทั้งหมดในนั้น?`))
            api(`/api/chat-sections/${sec.id}`, "DELETE");
        });
        tab.appendChild(del);
      }
      list.appendChild(tab);
    }
  }

  function renderChat() {
    renderChatTabs();
    const box = document.getElementById("chat");
    const active = STATE.activeSection || "main";
    const msgs = (STATE.chat || []).filter((m) => (m.section || "main") === active);
    if (!msgs.length) {
      box.innerHTML =
        '<div class="chat-empty">ยังไม่มีข้อความในแชทนี้<br>เมื่อ Claude ใช้เครื่องมือ <code>say_to_user</code><br>ข้อความจะมาโผล่ที่นี่ ✨</div>';
      return;
    }
    const atBottom = box.scrollHeight - box.scrollTop - box.clientHeight < 60;
    box.innerHTML = "";
    for (const m of msgs) {
      const el = document.createElement("div");
      const role = m.role || "claude";
      el.className = "msg " + role;
      const t = new Date(m.ts).toLocaleTimeString("th-TH", {
        hour: "2-digit",
        minute: "2-digit",
      });
      const body = escapeHtml(m.text).replace(/\\r\\n|\\n|\\r/g, "\n");
      
      let header = "";
      if (role === "claude") {
        header = '<div class="msg-sender-label">🤖 Claude Code</div>';
      } else if (role === "gemini") {
        header = '<div class="msg-sender-label">♊ Gemini</div>';
      }
      
      el.innerHTML = `${header}${body}<span class="ts">${t}</span>`;
      box.appendChild(el);
    }
    if (atBottom) box.scrollTop = box.scrollHeight;
  }

  // New chat section (tab) button
  document.getElementById("chat-tab-add").addEventListener("click", async () => {
    const name = prompt("ชื่อแชทใหม่:", "แชทใหม่");
    if (name === null) return;
    const trimmed = name.trim() || "แชทใหม่";
    await api("/api/chat-sections", "POST", { name: trimmed });
    const launch = await api("/api/launch-claude", "POST", { section: trimmed });
    if (launch?.ok) toast(`เปิด Claude สำหรับ "${trimmed}" แล้ว 🚀`);
    else toast(`สร้างแชทแล้ว — เปิด claude-listen.cmd "${trimmed}" เองได้เลยครับ`);
  });

  // Clear old chat messages (current section) — keeps things lean / saves tokens
  document.getElementById("chat-clear-btn")?.addEventListener("click", async () => {
    const active = STATE.activeSection || localActiveSectionRef.value || "main";
    if (!confirm("ล้างข้อความแชทนี้ทั้งหมด? (ย้อนกลับไม่ได้)")) return;
    const res = await api("/api/chat/clear", "POST", { section: active });
    if (res?.ok) toast(`ล้างแชทแล้ว (${res.cleared} ข้อความ) 🗑`);
    else toast("ล้างแชทไม่สำเร็จ");
  });

  // Gemini handoff toggle — lets Claude delegate cheap subtasks to Gemini.
  // Polls /api/agent/status to drive the online dot + reflect the server's
  // handoff flag, without stomping on a checkbox the user is mid-click on.
  const geminiToggle = document.getElementById("gemini-handoff-toggle");
  const geminiDot = document.getElementById("gemini-status-dot");
  let geminiMidToggle = false;

  async function pollGeminiStatus() {
    try {
      const status = await api("/api/agent/status");
      if (!status) return;
      geminiDot?.classList.toggle("on", !!status.gemini?.online);
      if (geminiToggle && !geminiMidToggle) geminiToggle.checked = !!status.handoff;
    } catch {
      geminiDot?.classList.remove("on");
    }
  }

  geminiToggle?.addEventListener("change", async () => {
    geminiMidToggle = true;
    const enabled = geminiToggle.checked;
    const res = await api("/api/gemini/handoff", "POST", { enabled });
    if (res) toast(enabled ? "เปิดโหมด Gemini handoff แล้ว 🤝" : "ปิดโหมด Gemini handoff แล้ว");
    geminiMidToggle = false;
  });

  if (geminiToggle) {
    pollGeminiStatus();
    setInterval(pollGeminiStatus, 5000);
  }

  // Claude Usage Badge polling
  const usageBadge = document.getElementById("claude-usage-badge");
  async function pollClaudeUsage() {
    if (!usageBadge) return;
    try {
      const res = await api("/api/claude-usage");
      usageBadge.hidden = false;
      if (!res || res.error) {
        usageBadge.textContent = "⚡ —";
        usageBadge.style.color = "inherit";
        usageBadge.title = res?.detail || "Unavailable";
        return;
      }
      let text = "";
      if (res.session) text += `⚡ ${Math.round(res.session.percent)}%`;
      if (res.weekly) text += ` · W ${Math.round(res.weekly.percent)}%`;
      usageBadge.textContent = text || "⚡ —";
      
      let maxPct = 0;
      if (res.session) maxPct = Math.max(maxPct, res.session.percent);
      
      if (maxPct >= 90) usageBadge.style.color = "#ef4444";
      else if (maxPct >= 70) usageBadge.style.color = "#f59e0b";
      else usageBadge.style.color = "#22c55e";
      
      let title = "Claude API Usage\n";
      const fmtTime = (ts) => ts ? new Date(ts).toLocaleString() : "N/A";
      if (res.session) title += `- Session: ${res.session.percent}% (reset: ${fmtTime(res.session.resets_at)})\n`;
      if (res.weekly) title += `- Weekly: ${res.weekly.percent}% (reset: ${fmtTime(res.weekly.resets_at)})\n`;
      if (res.weekly_model) title += `- Weekly (${res.weekly_model.name || 'Model'}): ${res.weekly_model.percent}% (reset: ${fmtTime(res.weekly_model.resets_at)})\n`;
      usageBadge.title = title.trim();
    } catch (e) {
      usageBadge.hidden = false;
      usageBadge.textContent = "⚡ —";
      usageBadge.title = String(e);
    }
  }

  if (usageBadge) {
    pollClaudeUsage();
    setInterval(pollClaudeUsage, 60000);
  }

  // 🎬 Local video comprehension — drop a URL or pick a video file. The machine
  // extracts keyframes + a transcript locally (zero API cost); when ready the
  // server pushes a "🎬 video digest ready" message into this section's inbox so
  // the listening Claude wakes.
  function showVideoNotice() {
    const box = document.getElementById("chat");
    if (!box) return;
    const el = document.createElement("div");
    el.className = "msg claude video-notice";
    el.appendChild(document.createTextNode("กำลังย่อยวิดีโอ… 🎬"));
    el.appendChild(document.createElement("br"));
    const sub = document.createElement("span");
    sub.style.opacity = ".7";
    sub.style.fontSize = "12px";
    sub.textContent = "แยกคีย์เฟรม + ถอดเสียงในเครื่อง (ไม่มีค่า API) — เดี๋ยว Claude จะแจ้งเมื่อเสร็จ";
    el.appendChild(sub);
    box.appendChild(el);
    box.scrollTop = box.scrollHeight;
  }

  async function startVideoDigest(source) {
    const section = STATE.activeSection || localActiveSectionRef.value || "main";
    showVideoNotice();
    toast("เริ่มย่อยวิดีโอ… 🎬");
    const r = await api("/api/video-inbox", "POST", { source, section });
    if (r?.id) toast(`กำลังย่อยวิดีโอ (id: ${r.id}) 🎬`);
    else toast("เริ่มย่อยวิดีโอไม่สำเร็จ");
  }

  const videoFileInput = document.getElementById("video-file-input");
  videoFileInput?.addEventListener("change", async () => {
    const file = videoFileInput.files && videoFileInput.files[0];
    videoFileInput.value = ""; // allow re-picking the same file later
    if (!file) return;
    try {
      const ext = (file.name.split(".").pop() || "mp4").toLowerCase();
      toast("กำลังอัปโหลดวิดีโอ…");
      const up = await fetch(`/api/video-upload?ext=${encodeURIComponent(ext)}`, {
        method: "POST",
        headers: { "Content-Type": "application/octet-stream" },
        body: file,
      }).then((r) => r.json());
      if (!up?.path) return toast("อัปโหลดวิดีโอไม่สำเร็จ");
      await startVideoDigest(up.path);
    } catch (e) {
      toast("อัปโหลดวิดีโอไม่สำเร็จ");
    }
  });

  document.getElementById("video-btn")?.addEventListener("click", () => {
    const url = prompt(
      "วางลิงก์วิดีโอ (YouTube/URL) เพื่อย่อย\nหรือกด OK โดยเว้นว่างไว้เพื่อเลือกไฟล์วิดีโอจากเครื่อง:",
      ""
    );
    if (url === null) return; // cancelled
    const trimmed = url.trim();
    if (trimmed) startVideoDigest(trimmed);
    else videoFileInput?.click();
  });

  return { renderChat, renderChatTabs };
}
