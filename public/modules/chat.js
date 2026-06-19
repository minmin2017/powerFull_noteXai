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
      el.className = "msg " + (m.role || "claude");
      const t = new Date(m.ts).toLocaleTimeString("th-TH", {
        hour: "2-digit",
        minute: "2-digit",
      });
      const body = escapeHtml(m.text).replace(/\\r\\n|\\n|\\r/g, "\n");
      el.innerHTML = `${body}<span class="ts">${t}</span>`;
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

  return { renderChat, renderChatTabs };
}
