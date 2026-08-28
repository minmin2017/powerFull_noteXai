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
} else {
  loadPicker();
}

document.getElementById("btn-back-to-list").addEventListener("click", () => {
  location.search = "";
});
