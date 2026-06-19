/**
 * modules/calendar.js
 * Calendar right panel — load, render (grid + day view), and WS listener.
 * Receives app internals via dependency injection (setup pattern).
 */
export default function setupCalendar({ api, toast, escapeHtml }) {
  const calPanel = document.getElementById("cal-panel");
  const calBody = document.getElementById("cal-body");
  const calFetchedAt = document.getElementById("cal-fetched-at");

  function toggleCalPanel(open) {
    const show = open !== undefined ? open : calPanel.classList.toggle("open");
    calPanel.classList.toggle("open", show);
    calPanel.setAttribute("aria-hidden", String(!show));
    document.getElementById("btn-toggle-cal").classList.toggle("active", show);
    if (show) loadCalendarFromServer();
  }

  async function loadCalendarFromServer() {
    try {
      const data = await api("/api/calendar");
      if (data) renderCalendar(data);
    } catch {}
  }

  let calEvents = [];
  let calDayView = null; // currently zoomed-in date string "YYYY-MM-DD" or null

  const thTime = (iso) => {
    if (!iso || iso.length === 10) return "ทั้งวัน";
    return new Date(iso).toLocaleTimeString("th-TH", { hour: "2-digit", minute: "2-digit" });
  };

  function renderCalendar({ events, fetchedAt }) {
    calEvents = events || [];
    if (!fetchedAt) {
      calFetchedAt.textContent = "";
      calBody.innerHTML = `<div class="cal-empty">กด 🔄 Refresh เพื่อโหลดตาราง 2 สัปดาห์จาก Google Calendar</div>`;
      return;
    }
    calFetchedAt.textContent = "อัปเดตล่าสุด: " + new Date(fetchedAt).toLocaleString("th-TH");
    if (calDayView) renderDayView(calDayView);
    else renderGridView();
  }

  function eventsByDate() {
    const g = {};
    for (const ev of calEvents) {
      const d = (ev.start || "").slice(0, 10);
      if (!g[d]) g[d] = [];
      g[d].push(ev);
    }
    return g;
  }

  function renderGridView() {
    calDayView = null;
    const groups = eventsByDate();
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const DOW = ["อา", "จ", "อ", "พ", "พฤ", "ศ", "ส"];
    const cells = [];
    const localISO = (dt) =>
      `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, "0")}-${String(dt.getDate()).padStart(2, "0")}`;
    for (let i = 0; i < 14; i++) {
      const d = new Date(today);
      d.setDate(today.getDate() + i);
      const iso = localISO(d);
      const evs = groups[iso] || [];
      const isToday = i === 0;
      cells.push({ iso, d, evs, isToday });
    }
    const header = DOW.map((w) => `<div class="cgrid-hd">${w}</div>`).join("");
    const startDow = cells[0].d.getDay();
    const blanks = Array(startDow).fill(`<div class="cgrid-cell cgrid-blank"></div>`).join("");
    const dayCells = cells
      .map(({ iso, d, evs, isToday }) => {
        const dots = evs.slice(0, 3).map(() => `<span class="cgrid-dot"></span>`).join("");
        const more = evs.length > 3 ? `<span class="cgrid-more">+${evs.length - 3}</span>` : "";
        return `<div class="cgrid-cell${isToday ? " cgrid-today" : ""}" data-date="${iso}">
          <span class="cgrid-num">${d.getDate()}</span>
          <div class="cgrid-dots">${dots}${more}</div>
        </div>`;
      })
      .join("");
    calBody.innerHTML = `
      <div class="cgrid-wrap">
        <div class="cgrid-header">${header}</div>
        <div class="cgrid-grid">${blanks}${dayCells}</div>
      </div>
      <div class="cal-hint">ดับเบิลคลิกวันเพื่อดู schedule</div>`;
    calBody.querySelectorAll(".cgrid-cell[data-date]").forEach((el) => {
      el.addEventListener("dblclick", () => {
        calDayView = el.dataset.date;
        renderDayView(calDayView);
      });
    });
  }

  function renderDayView(iso) {
    calDayView = iso;
    const groups = eventsByDate();
    const evs = (groups[iso] || [])
      .slice()
      .sort((a, b) => (a.start || "").localeCompare(b.start || ""));
    const d = new Date(iso + "T00:00:00");
    const label = d.toLocaleDateString("th-TH", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    });
    const evHtml = evs.length
      ? evs
          .map(
            (ev) => `
          <div class="cal-event">
            <div class="cal-event-time">${thTime(ev.start)}${
              ev.end && ev.end !== ev.start ? " – " + thTime(ev.end) : ""
            }</div>
            <div class="cal-event-title">${escapeHtml(ev.title || "(ไม่มีชื่อ)")}</div>
            ${ev.location ? `<div class="cal-event-loc">📍 ${escapeHtml(ev.location)}</div>` : ""}
          </div>`
          )
          .join("")
      : `<div class="cal-empty">ไม่มี event วันนี้</div>`;
    calBody.innerHTML = `
      <button class="cal-back-btn">← กลับ</button>
      <div class="cal-day-title">${label}</div>
      <div class="cal-events-list">${evHtml}</div>`;
    calBody.querySelector(".cal-back-btn").addEventListener("click", renderGridView);
  }

  // Wire up buttons
  document.getElementById("btn-toggle-cal").addEventListener("click", () => toggleCalPanel());
  document.getElementById("cal-close").addEventListener("click", () => toggleCalPanel(false));
  document.getElementById("cal-refresh").addEventListener("click", async () => {
    calBody.innerHTML = `<div class="cal-empty">⏳ กำลังขอให้ Claude ดึงข้อมูล…</div>`;
    await api("/api/inbox", "POST", { text: "[refresh-calendar]", section: "main" });
    toast("ส่งคำขอให้ Claude ดึง Calendar แล้ว — รอสักครู่ 🗓️");
  });

  // Listen for real-time calendar updates pushed from the server via WebSocket
  window.__wsOnCalendar = (data) => {
    if (data.type === "calendar") renderCalendar(data);
  };
}
