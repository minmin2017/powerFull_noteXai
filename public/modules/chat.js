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
    checkForNewClaudeMessages();
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
      const rawHtml = (window.marked && typeof window.marked.parse === "function")
        ? window.marked.parse(m.text)
        : escapeHtml(m.text).replace(/\n/g, "<br>");
      // marked() passes raw HTML through untouched — sanitize before innerHTML so a
      // malicious <script>/onerror payload relayed through Gemini or OCR'd text can't
      // execute with this app's full read/write API access.
      const bodyHtml = window.DOMPurify ? window.DOMPurify.sanitize(rawHtml) : escapeHtml(m.text).replace(/\n/g, "<br>");
      
      let header = "";
      if (role === "claude") {
        header = '<div class="msg-sender-label">🤖 Claude Code</div>';
      } else if (role === "gemini") {
        header = '<div class="msg-sender-label">♊ Gemini</div>';
      }
      
      el.innerHTML = `${header}<div class="msg-body">${bodyHtml}</div><span class="ts">${t}</span>`;
      box.appendChild(el);
    }
    // Auto-render KaTeX math equations if available
    if (window.renderMathInElement) {
      window.renderMathInElement(box, {
        delimiters: [
          { left: "$$", right: "$$", display: true },
          { left: "$", right: "$", display: false },
          { left: "\\(", right: "\\)", display: false },
          { left: "\\[", right: "\\]", display: true }
        ],
        throwOnError: false
      });
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

  // ---------------------------------------------------------------------
  // 🔊 Text-to-speech — speaks new Claude messages in Thai as they arrive.
  // Toggle state lives in localStorage so it persists across reloads.
  // seenChatIds starts as `null`; the FIRST renderChat() call (page load,
  // whatever history the server sends) only records ids as a baseline —
  // it never speaks. Only ids that show up in a LATER render are new.
  // ---------------------------------------------------------------------
  let ttsEnabled = localStorage.getItem("ttsEnabled") !== "false"; // default ON
  let ttsVoice = localStorage.getItem("pn.ttsVoice") || "female";
  let seenChatIds = null;
  const ttsQueue = [];
  let ttsPlaying = false;
  let currentAudioEl = null;
  const ttsToggleBtn = document.getElementById("tts-toggle-btn");

  document.querySelectorAll(".tts-voice-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.voice === ttsVoice);
    btn.addEventListener("click", () => {
      ttsVoice = btn.dataset.voice;
      localStorage.setItem("pn.ttsVoice", ttsVoice);
      document.querySelectorAll(".tts-voice-btn").forEach((b) =>
        b.classList.toggle("active", b.dataset.voice === ttsVoice)
      );
    });
  });

  function updateTtsButton() {
    if (!ttsToggleBtn) return;
    ttsToggleBtn.textContent = ttsEnabled ? "🔊" : "🔇";
    ttsToggleBtn.title = ttsEnabled ? "ปิดเสียงอ่านข้อความ Claude" : "เปิดเสียงอ่านข้อความ Claude";
    ttsToggleBtn.classList.toggle("tts-off", !ttsEnabled);
  }

  function setTtsEnabled(v) {
    ttsEnabled = v;
    localStorage.setItem("ttsEnabled", v ? "true" : "false");
    updateTtsButton();
    if (!v) {
      // Stop whatever is speaking right now and drop anything queued.
      ttsQueue.length = 0;
      if (currentAudioEl) {
        try { currentAudioEl.pause(); } catch {}
        currentAudioEl = null;
      }
      try { window.speechSynthesis && window.speechSynthesis.cancel(); } catch {}
      ttsPlaying = false;
    }
  }

  ttsToggleBtn?.addEventListener("click", () => setTtsEnabled(!ttsEnabled));
  updateTtsButton();

  // Global OS-wide hotkey (Ctrl+Alt+M via AutoHotkey) posts to /api/tts/toggle,
  // which broadcasts this over WS so it works even when Chrome isn't focused.
  window.__wsOnTtsToggle = () => setTtsEnabled(!ttsEnabled);

  // Keyboard shortcut: M toggles TTS mute (ignored while typing in a field).
  window.addEventListener("keydown", (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    const t = e.target;
    if (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.getAttribute?.("contenteditable") === "true") return;
    if (e.code === "KeyM") {
      e.preventDefault();
      setTtsEnabled(!ttsEnabled);
    }
  });

  // Strip markdown noise so the voice doesn't read out symbols/URLs/code.
  function sanitizeForSpeech(text) {
    let t = String(text || "");
    t = t.replace(/```[\s\S]*?```/g, " "); // fenced code blocks
    t = t.replace(/`[^`]*`/g, " "); // inline code
    t = t.replace(/\[([^\]]*)\]\(([^)]*)\)/g, "$1"); // [label](url) -> label
    t = t.replace(/https?:\/\/\S+/g, " "); // bare URLs
    t = t.replace(/[#*_~>`]+/g, ""); // markdown symbols
    t = t.replace(/[ \t]+/g, " ").replace(/\n{2,}/g, "\n").trim();
    return t;
  }

  // Fallback: browser's own speech synthesis, only if a Thai voice exists.
  function speakFallback(text, done) {
    try {
      if ("speechSynthesis" in window) {
        const voices = window.speechSynthesis.getVoices();
        const thVoice = voices.find((v) => /^th(-|_)?TH/i.test(v.lang) || /thai/i.test(v.name));
        if (thVoice) {
          const utter = new SpeechSynthesisUtterance(text);
          utter.voice = thVoice;
          utter.lang = thVoice.lang;
          utter.onend = done;
          utter.onerror = done;
          window.speechSynthesis.speak(utter);
          return;
        }
      }
    } catch {}
    done(); // no Thai voice available — stay silent, no error popups
  }

  function playNextTts() {
    if (ttsPlaying || !ttsEnabled) return;
    const text = ttsQueue.shift();
    if (text === undefined) return;
    ttsPlaying = true;
    let settled = false;
    const finish = () => {
      if (settled) return;
      settled = true;
      ttsPlaying = false;
      currentAudioEl = null;
      playNextTts();
    };
    try {
      const audio = new Audio(`/api/tts?text=${encodeURIComponent(text)}&voice=${ttsVoice}`);
      currentAudioEl = audio;
      audio.addEventListener("ended", finish);
      audio.addEventListener("error", () => speakFallback(text, finish));
      audio.play().catch(() => speakFallback(text, finish));
    } catch {
      speakFallback(text, finish);
    }
  }

  // Speak the whole message in one shot instead of per-sentence chunks —
  // the /api/tts backend already streams audio as it synthesizes, so
  // chunking here only added gaps (a new fetch + Audio element per sentence)
  // without saving latency. Only split when text would exceed the backend's
  // 3000-char cap (server.js /api/tts).
  const TTS_MAX_CHUNK = 2800;
  function splitTextForSpeech(text) {
    const clean = text.trim();
    if (!clean) return [];
    if (clean.length <= TTS_MAX_CHUNK) return [clean];
    const words = clean.split(/\s+/);
    const chunks = [];
    let current = "";
    for (const word of words) {
      if ((current + " " + word).length > TTS_MAX_CHUNK) {
        if (current.trim()) chunks.push(current.trim());
        current = word;
      } else {
        current = current ? current + " " + word : word;
      }
    }
    if (current.trim()) chunks.push(current.trim());
    return chunks;
  }

  function enqueueSpeech(text) {
    if (!ttsEnabled) return;
    const clean = sanitizeForSpeech(text);
    if (!clean) return;
    const chunks = splitTextForSpeech(clean);
    for (const chunk of chunks) {
      ttsQueue.push(chunk);
    }
    playNextTts();
  }

  // Cross-tab mutex: only the first same-origin tab to see a message id
  // speaks it — prevents every open tab from playing the same audio.
  const TTS_CLAIM_KEY = "pn_tts_claimed_ids";
  function claimForSpeech(id) {
    let claimed;
    try {
      claimed = JSON.parse(localStorage.getItem(TTS_CLAIM_KEY) || "[]");
      if (!Array.isArray(claimed)) claimed = [];
    } catch {
      claimed = [];
    }
    if (claimed.includes(id)) return false;
    claimed.push(id);
    if (claimed.length > 300) claimed = claimed.slice(claimed.length - 300);
    try {
      localStorage.setItem(TTS_CLAIM_KEY, JSON.stringify(claimed));
    } catch {}
    return true;
  }

  // In-app Messenger-style popup for new agent replies — separate from the
  // browser's native Notification API (which only fires when the window is
  // unfocused). Min wanted this even while the app itself has focus but he's
  // looking at the canvas/another section, so he doesn't have to keep
  // checking the chat panel. Toggleable via the settings checkbox.
  const BANNER_ENABLED_KEY = "pn_msg_banner_enabled";
  function bannerEnabled() {
    const v = localStorage.getItem(BANNER_ENABLED_KEY);
    return v === null ? true : v === "1";
  }
  const bannerToggle = document.getElementById("msg-banner-toggle");
  if (bannerToggle) {
    bannerToggle.checked = bannerEnabled();
    bannerToggle.addEventListener("change", () => {
      localStorage.setItem(BANNER_ENABLED_KEY, bannerToggle.checked ? "1" : "0");
    });
  }
  function showMsgBanner(role, text, sectionId) {
    if (!bannerEnabled()) return;
    let el = document.getElementById("msg-banner");
    if (!el) {
      el = document.createElement("div");
      el.id = "msg-banner";
      el.className = "msg-banner";
      document.body.appendChild(el);
    }
    el.innerHTML = "";
    const closeBtn = document.createElement("button");
    closeBtn.className = "msg-banner-close";
    closeBtn.textContent = "✕";
    closeBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      el.classList.remove("show");
    });
    const head = document.createElement("div");
    head.className = "msg-banner-head";
    head.textContent = role === "gemini" ? "Gemini ตอบกลับ 💎" : "Claude ตอบกลับ 🧠";
    const body = document.createElement("div");
    body.className = "msg-banner-body";
    body.textContent = text.slice(0, 160);
    el.append(closeBtn, head, body);
    el.onclick = () => {
      if (sectionId && sectionId !== STATE.activeSection) {
        const tab = document.querySelector(`.chat-tab[data-id="${sectionId}"]`);
        if (tab) tab.click();
      }
      el.classList.remove("show");
    };
    el.classList.add("show");

    const startTimer = () => {
      clearTimeout(el._t);
      el._t = setTimeout(() => el.classList.remove("show"), 6000);
    };

    el.onmouseenter = () => {
      clearTimeout(el._t);
    };
    el.onmouseleave = () => {
      startTimer();
    };

    startTimer();
  }

  // Called from renderChat() on every state broadcast. Diffs STATE.chat
  // against ids already seen; speaks new role:"claude" messages only,
  // scoped to this tab's active section and claimed cross-tab. Also pops
  // the on-screen banner for any new claude/gemini message, any section.
  function checkForNewClaudeMessages() {
    const all = STATE.chat || [];
    if (seenChatIds === null) {
      // First render after page load — record the baseline, speak nothing.
      seenChatIds = new Set(all.map((m) => m.id));
      return;
    }
    const active = STATE.activeSection || "main";
    for (const m of all) {
      if (!m || seenChatIds.has(m.id)) continue;
      seenChatIds.add(m.id);
      if (m.role === "claude" || m.role === "gemini")
        showMsgBanner(m.role, m.text, m.section || "main");
      if (m.role === "claude" && (m.section || "main") === active && claimForSpeech(m.id))
        enqueueSpeech(m.text);
    }
  }

  return { renderChat, renderChatTabs };
}
