const params = new URLSearchParams(location.search);

async function loadPicker() {
  const videos = await fetch("/videos").then((r) => r.json());
  const list = document.getElementById("video-list");
  list.innerHTML = "";
  if (videos.length === 0) {
    list.innerHTML = "<p>ยังไม่มีวิดิโอ — สั่งสร้างจากแชทด้านล่างได้เลย</p>";
    return;
  }
  for (const v of videos) {
    const card = document.createElement("div");
    card.className = "video-card";
    card.textContent = v.title;
    card.addEventListener("click", () => {
      location.search = "?v=" + encodeURIComponent(v.id);
    });
    list.appendChild(card);
  }
}

const videoId = params.get("v");
if (videoId) {
  document.getElementById("picker").classList.add("hidden");
  document.getElementById("player-view").classList.remove("hidden");
  document.getElementById("btn-back-to-list").classList.remove("hidden");

  let currentVideo = null;

  async function loadVideo(id) {
    currentVideo = await fetch("/videos/" + id).then((r) => r.json());
    document.getElementById("video").src = "/videos/" + id + "/media";
    renderSegments(currentVideo);
  }

  function renderSegments(video) {
    const wrap = document.getElementById("segments");
    wrap.innerHTML = "";
    video.segments.forEach((seg, i) => {
      const card = document.createElement("div");
      card.className = "segment-card";
      card.dataset.index = String(i);
      card.dataset.start = String(seg.start);
      card.dataset.end = String(seg.end);

      const time = document.createElement("div");
      time.className = "seg-time";
      time.textContent = formatT(seg.start);

      const text = document.createElement("div");
      text.className = "seg-text";
      text.contentEditable = "true";
      text.textContent = seg.text;
      text.addEventListener("blur", async () => {
        const newText = text.textContent.trim();
        if (newText === seg.text) return;
        await fetch(`/videos/${video.id}/segments/${i}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: newText }),
        });
        seg.text = newText;
      });

      card.appendChild(time);
      card.appendChild(text);

      const warpBtn = document.createElement("button");
      warpBtn.className = "warp-btn";
      warpBtn.textContent = "⤴ ไปวินาทีนี้";
      warpBtn.addEventListener("click", () => {
        document.getElementById("video").currentTime = seg.start;
        document.getElementById("video").play();
      });
      card.appendChild(warpBtn);

      const ttsBtn = document.createElement("button");
      ttsBtn.className = "tts-btn";
      ttsBtn.textContent = "🔊 อ่านออกเสียง";
      ttsBtn.addEventListener("click", () => {
        const url = "http://127.0.0.1:4321/api/tts?voice=female&text=" + encodeURIComponent(seg.text);
        new Audio(url).play();
      });
      card.appendChild(ttsBtn);

      wrap.appendChild(card);
    });
  }

  function formatT(s) {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return m + ":" + String(sec).padStart(2, "0");
  }

  document.getElementById("video").addEventListener("timeupdate", (e) => {
    const t = e.target.currentTime;
    document.querySelectorAll(".segment-card").forEach((card) => {
      const start = Number(card.dataset.start);
      const end = Number(card.dataset.end);
      card.classList.toggle("active", t >= start && t < end);
    });
  });

  if (videoId) loadVideo(videoId);
} else {
  loadPicker();
}

document.getElementById("btn-back-to-list").addEventListener("click", () => {
  location.search = "";
});

document.getElementById("chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = document.getElementById("chat-input");
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  await fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  refreshChatLog();
});

async function refreshChatLog() {
  try {
    const { messages } = await fetch("/chat-log").then((r) => r.json());
    const log = document.getElementById("chat-log");
    log.innerHTML = messages
      .map((m) => `<div class="chat-msg ${m.role}"><b>${m.role === "user" ? "Min" : "Claude"}:</b> ${escapeHtml(m.text)}</div>`)
      .join("");
    log.scrollTop = log.scrollHeight;
  } catch {
    // main server unreachable — leave the log as-is, chat form still queues via /chat's own error handling
  }
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

refreshChatLog();
setInterval(refreshChatLog, 3000);
