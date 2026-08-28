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
      text.textContent = seg.text;

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
