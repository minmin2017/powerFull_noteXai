
// Flashcard Studio Client Engine
let currentDeck = null;
let cardsQueue = [];
let currentIndex = 0;
let isFlipped = false;

const deckSelect = document.getElementById("deckSelect");
const card3d = document.getElementById("flashcard");
const frontContent = document.getElementById("frontContent");
const backContent = document.getElementById("backContent");
const cardCategory = document.getElementById("cardCategory");
const progressBar = document.getElementById("progressBar");
const progressText = document.getElementById("progressText");
const dueCountEl = document.getElementById("dueCount");
const flipPrompt = document.getElementById("flipPrompt");
const srsActions = document.getElementById("srsActions");
const btnFlipMain = document.getElementById("btnFlipMain");
const btnLaunchDesktop = document.getElementById("btnLaunchDesktop");
const btnNewCard = document.getElementById("btnNewCard");
const cardModal = document.getElementById("cardModal");
const btnCloseModal = document.getElementById("btnCloseModal");
const btnCancelCard = document.getElementById("btnCancelCard");
const btnSaveCard = document.getElementById("btnSaveCard");
const btnSpeakFront = document.getElementById("btnSpeakFront");
const btnSpeakBack = document.getElementById("btnSpeakBack");
const btnMicAnswer = document.getElementById("btnMicAnswer");

// Load Decks
async function loadDecks() {
  try {
    const res = await fetch("/api/decks");
    const data = await res.json();
    deckSelect.innerHTML = "";
    (data.decks || []).forEach(d => {
      const opt = document.createElement("option");
      opt.value = d.id;
      opt.textContent = `${d.title} (${d.dueCards} ถึงกำหนด)`;
      deckSelect.appendChild(opt);
    });
    if (data.decks && data.decks.length > 0) {
      loadDeckDetails(data.decks[0].id);
    }
  } catch (err) {
    console.error("Failed to load decks:", err);
  }
}

async function loadDeckDetails(deckId) {
  try {
    const res = await fetch(`/api/decks/${deckId}`);
    currentDeck = await res.json();
    cardsQueue = (currentDeck.cards || []).slice();
    currentIndex = 0;
    renderCard();
  } catch (err) {
    console.error("Failed to load deck details:", err);
  }
}

function renderCard() {
  if (!cardsQueue || cardsQueue.length === 0 || currentIndex >= cardsQueue.length) {
    showCompletedView();
    return;
  }

  isFlipped = false;
  card3d.classList.remove("is-flipped");
  flipPrompt.style.display = "flex";
  srsActions.style.display = "none";

  const card = cardsQueue[currentIndex];
  cardCategory.textContent = currentDeck.category || "Engineering";
  
  frontContent.innerHTML = formatMarkdownMath(card.front);
  backContent.innerHTML = formatMarkdownMath(card.back);

  // Render LaTeX formulas
  if (window.renderMathInElement) {
    renderMathInElement(frontContent, {
      delimiters: [
        {left: "$$", right: "$$", display: true},
        {left: "$", right: "$", display: false},
        {left: "\\(", right: "\\)", display: false},
        {left: "\\[", right: "\\]", display: true}
      ]
    });
    renderMathInElement(backContent, {
      delimiters: [
        {left: "$$", right: "$$", display: true},
        {left: "$", right: "$", display: false},
        {left: "\\(", right: "\\)", display: false},
        {left: "\\[", right: "\\]", display: true}
      ]
    });
  }

  // Update Progress
  const pct = Math.round(((currentIndex) / cardsQueue.length) * 100);
  progressBar.style.width = `${pct}%`;
  progressText.textContent = `การ์ด ${currentIndex + 1} / ${cardsQueue.length}`;
  dueCountEl.textContent = `${cardsQueue.length - currentIndex} ใบ`;
}

function formatMarkdownMath(text) {
  if (!text) return "";
  let html = text
    .replace(/^> (.*$)/gim, '<blockquote>$1</blockquote>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>');
  return html;
}

function flipCard() {
  if (!cardsQueue || cardsQueue.length === 0) return;
  isFlipped = !isFlipped;
  if (isFlipped) {
    card3d.classList.add("is-flipped");
    flipPrompt.style.display = "none";
    srsActions.style.display = "block";
  } else {
    card3d.classList.remove("is-flipped");
    flipPrompt.style.display = "flex";
    srsActions.style.display = "none";
  }
}

async function rateCard(rating) {
  if (currentIndex >= cardsQueue.length) return;
  const card = cardsQueue[currentIndex];
  try {
    await fetch(`/api/cards/${currentDeck.id}/${card.id}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rating })
    });
  } catch (e) {
    console.error("SRS review error:", e);
  }

  currentIndex++;
  renderCard();
}

function showCompletedView() {
  progressBar.style.width = "100%";
  progressText.textContent = `เสร็จสิ้นครบทุกใบ! 🎉`;
  dueCountEl.textContent = `0 ใบ`;
  flipPrompt.style.display = "none";
  srsActions.style.display = "none";
  
  frontContent.innerHTML = `
    <div style="text-align: center; padding: 20px;">
      <div style="font-size: 3.5rem; margin-bottom: 12px;">🏆</div>
      <h2 style="font-size: 1.5rem; margin-bottom: 8px; color: #38bdf8;">ยอดเยี่ยมมาก! ทบทวนครบทุกใบแล้ว</h2>
      <p style="font-size: 0.95rem; color: #9ca3af; margin-bottom: 16px;">สมองของคุณบันทึกความจำระยะยาวเรียบร้อยแล้ว</p>
      <button class="glass-btn accent-btn" style="margin: 0 auto;" onclick="loadDeckDetails(currentDeck.id)">
        <i class="fa-solid fa-rotate-right"></i> ทบทวนใหม่อีกรอบ
      </button>
    </div>
  `;
  backContent.innerHTML = "";

  // Trigger celebration confetti
  if (window.confetti) {
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 }
    });
  }
}

// Speak aloud via Web Speech
function speakText(text) {
  if (!('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const clean = text.replace(/\$[^$]+\$/g, 'สูตรคณิตศาสตร์').replace(/<[^>]+>/g, '');
  const ut = new SpeechSynthesisUtterance(clean);
  ut.lang = 'th-TH';
  ut.rate = 1.0;
  window.speechSynthesis.speak(ut);
}

// Speech Recognition for Voice Answer
function startVoiceRecognition() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) {
    alert("เบราว์เซอร์นี้ไม่รองรับ Speech Recognition ให้ใช้ Chrome/Edge ครับ");
    return;
  }
  const rec = new SpeechRec();
  rec.lang = 'th-TH';
  btnMicAnswer.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> กำลังฟัง...';
  rec.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    btnMicAnswer.innerHTML = '<i class="fa-solid fa-microphone"></i> พูดตอบ';
    alert(`คุณตอบว่า: "${transcript}"\n\nกดพลิกดูเฉลยเพื่อตรวจความถูกต้อง!`);
    flipCard();
  };
  rec.onerror = () => {
    btnMicAnswer.innerHTML = '<i class="fa-solid fa-microphone"></i> พูดตอบ';
  };
  rec.start();
}

// Event Listeners
card3d.addEventListener("click", (e) => {
  if (e.target.closest("button") || e.target.closest("a")) return;
  flipCard();
});

btnFlipMain.addEventListener("click", flipCard);
deckSelect.addEventListener("change", (e) => loadDeckDetails(e.target.value));

document.querySelectorAll(".srs-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const rating = btn.getAttribute("data-rating");
    rateCard(rating);
  });
});

btnLaunchDesktop.addEventListener("click", async () => {
  // 1. Direct browser popup window (instant standalone window on client)
  window.open(
    window.location.href,
    "FlashcardStudioStandalone",
    "width=1120,height=820,left=120,top=60,menubar=no,toolbar=no,location=no,status=no,resizable=yes"
  );

  // 2. Also trigger backend launcher
  try {
    const res = await fetch("/api/launch-window", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      btnLaunchDesktop.innerHTML = '<i class="fa-solid fa-check"></i> เปิดแล้ว';
      setTimeout(() => {
        btnLaunchDesktop.innerHTML = '<i class="fa-solid fa-desktop"></i> <span>Desktop Window</span>';
      }, 2000);
    }
  } catch (err) {
    console.error("Failed to launch desktop window:", err);
  }
});

btnSpeakFront.addEventListener("click", (e) => {
  e.stopPropagation();
  if (cardsQueue[currentIndex]) speakText(cardsQueue[currentIndex].front);
});

btnSpeakBack.addEventListener("click", (e) => {
  e.stopPropagation();
  if (cardsQueue[currentIndex]) speakText(cardsQueue[currentIndex].back);
});

btnMicAnswer.addEventListener("click", (e) => {
  e.stopPropagation();
  startVoiceRecognition();
});

btnNewCard.addEventListener("click", () => { cardModal.style.display = "flex"; });
btnCloseModal.addEventListener("click", () => { cardModal.style.display = "none"; });
btnCancelCard.addEventListener("click", () => { cardModal.style.display = "none"; });

btnSaveCard.addEventListener("click", async () => {
  const front = document.getElementById("inpFront").value.trim();
  const back = document.getElementById("inpBack").value.trim();
  if (!front || !back || !currentDeck) return;

  const newCard = {
    id: `c_${Date.now()}`,
    front,
    back,
    interval: 1,
    repetition: 0,
    efactor: 2.5,
    nextReview: Date.now()
  };

  currentDeck.cards = currentDeck.cards || [];
  currentDeck.cards.push(newCard);

  await fetch("/api/decks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(currentDeck)
  });

  cardModal.style.display = "none";
  document.getElementById("inpFront").value = "";
  document.getElementById("inpBack").value = "";
  loadDeckDetails(currentDeck.id);
});

// Keyboard Shortcuts (Space = Flip, 1-4 = SRS rating)
document.addEventListener("keydown", (e) => {
  if (cardModal.style.display === "flex") return;
  if (e.code === "Space") {
    e.preventDefault();
    flipCard();
  } else if (isFlipped) {
    if (e.key === "1") rateCard(1);
    else if (e.key === "2") rateCard(2);
    else if (e.key === "3") rateCard(3);
    else if (e.key === "4") rateCard(4);
  }
});

// Initialize
loadDecks();
