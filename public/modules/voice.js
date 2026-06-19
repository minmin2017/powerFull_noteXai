/**
 * modules/voice.js
 * STT model switching, mic recording (Web Speech + Groq/Local Whisper),
 * text input, send button, and submitUserInput.
 *
 * localActiveSectionRef is { value: "main" } — mutations here stay in sync
 * with the ref object shared by chat.js and app.js.
 */
export default function setupVoice({ api, toast, localActiveSectionRef }) {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recog = null;
  let listening = false;
  let finalBuf = "";

  // STT model selector — persisted in localStorage
  let sttModel = localStorage.getItem("pn.sttModel") || "local";
  let whisperModel = localStorage.getItem("pn.whisperModel") || "large-v3-turbo";

  function applyWhisperModelUI() {
    const row = document.getElementById("whisper-model-row");
    if (row) row.hidden = sttModel !== "local";
    document.querySelectorAll(".whisper-btn").forEach((b) =>
      b.classList.toggle("active", b.dataset.wm === whisperModel)
    );
  }

  (function setupSttBtns() {
    document.querySelectorAll(".stt-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.stt === sttModel);
      btn.addEventListener("click", () => {
        sttModel = btn.dataset.stt;
        localStorage.setItem("pn.sttModel", sttModel);
        document.querySelectorAll(".stt-btn").forEach((b) =>
          b.classList.toggle("active", b.dataset.stt === sttModel)
        );
        applyWhisperModelUI();
        applyLang();
      });
    });
    applyWhisperModelUI();

    document.querySelectorAll(".whisper-btn").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const wm = btn.dataset.wm;
        if (wm === whisperModel) return;
        whisperModel = wm;
        localStorage.setItem("pn.whisperModel", whisperModel);
        applyWhisperModelUI();
        await fetch("/api/whisper-model", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ model: wm }),
        }).catch(() => {});
      });
    });

    // Sync server's current whisper model on load
    fetch("/api/whisper-model")
      .then((r) => r.json())
      .then(({ model }) => {
        if (model !== whisperModel) {
          fetch("/api/whisper-model", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ model: whisperModel }),
          }).catch(() => {});
        }
      })
      .catch(() => {});
  })();

  // Mic language: a two-state toggle (ไทย ↔ EN), persisted.
  const langToggle = document.getElementById("voice-lang");
  let currentLang = localStorage.getItem("pn.voiceLang") || "th-TH";
  function voiceLang() { return currentLang; }
  function isThai() { return currentLang.startsWith("th"); }
  function idleStatus() { return isThai() ? "กดไมค์เพื่อพูดภาษาไทย" : "Tap the mic to speak English"; }

  function applyLang() {
    const th = isThai();
    if (langToggle) langToggle.classList.toggle("en", !th);
    if (recog) recog.lang = currentLang;
    const label = sttModel === "groq" ? "Groq Whisper" : "Web Speech";
    document.getElementById("mic-btn").title =
      (th ? "พูดภาษาไทย" : "Speak English") + ` (${label})`;
    if (!listening) document.getElementById("voice-status").textContent = idleStatus();
  }

  if (langToggle) {
    applyLang();
    langToggle.addEventListener("click", () => {
      currentLang = isThai() ? "en-US" : "th-TH";
      localStorage.setItem("pn.voiceLang", currentLang);
      applyLang();
    });
  }

  // --- Web Speech API setup ---
  function setupWebSpeech() {
    if (!SR) {
      if (sttModel === "webspeech") {
        document.getElementById("voice-status").textContent =
          "เบราว์เซอร์นี้ไม่รองรับ Web Speech — เปลี่ยนเป็น Groq หรือใช้ Chrome/Edge";
      }
      return;
    }
    recog = new SR();
    recog.lang = voiceLang();
    recog.continuous = true;
    recog.interimResults = true;
    recog.onresult = (e) => {
      let interim = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const r = e.results[i];
        if (r.isFinal) finalBuf += r[0].transcript;
        else interim += r[0].transcript;
      }
      document.getElementById("voice-interim").textContent = interim;
    };
    recog.onerror = (e) => {
      document.getElementById("voice-status").textContent = "ข้อผิดพลาดเสียง: " + e.error;
    };
    recog.onend = () => {
      if (listening && sttModel === "webspeech") {
        try { recog.start(); } catch {}
      }
    };
  }
  setupWebSpeech();

  // --- Groq / Local Whisper (MediaRecorder) ---
  let mediaRecorder = null;
  let audioChunks = [];

  async function startGroqRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];
      mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunks.push(e.data); };
      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const shouldSubmit = listening;
        listening = false;
        setMicUI(false);
        if (!shouldSubmit) return; // cancelled
        const blob = new Blob(audioChunks, { type: "audio/webm" });
        const isLocal = sttModel === "local";
        try {
          const lang = isThai() ? "th" : "en";
          let fullText = "";
          if (isLocal) {
            const res = await fetch(`/api/transcribe-local?lang=${lang}`, {
              method: "POST",
              headers: { "Content-Type": "audio/webm" },
              body: blob,
            });
            if (!res.ok) {
              const err = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
              throw new Error(err.error || `HTTP ${res.status}`);
            }
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buf = "";
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;
              buf += decoder.decode(value, { stream: true });
              const lines = buf.split("\n");
              buf = lines.pop();
              for (const line of lines) {
                if (line.trim()) {
                  fullText += (fullText ? " " : "") + line.trim();
                  document.getElementById("voice-interim").textContent = fullText;
                }
              }
            }
            if (buf.trim()) fullText += (fullText ? " " : "") + buf.trim();
          } else {
            const res = await fetch(`/api/transcribe?lang=${lang}`, {
              method: "POST",
              headers: { "Content-Type": "audio/webm" },
              body: blob,
            });
            const data = await res.json();
            if (data.error) throw new Error(data.error);
            fullText = data.text || "";
          }
          document.getElementById("voice-interim").textContent = "";
          if (fullText) {
            const inp = document.getElementById("text-input");
            inp.value = fullText;
            inp.focus();
            inp.select();
            document.getElementById("voice-status").textContent =
              "แก้ข้อความได้ แล้วกด Enter หรือ ส่ง";
            setTimeout(() => {
              if (!listening)
                document.getElementById("voice-status").textContent = idleStatus();
            }, 4000);
          }
        } catch (err) {
          document.getElementById("voice-status").textContent = "STT error: " + err.message;
          setTimeout(() => {
            if (!listening)
              document.getElementById("voice-status").textContent = idleStatus();
          }, 3000);
          return;
        }
        if (!listening) document.getElementById("voice-status").textContent = idleStatus();
      };
      mediaRecorder.start();
    } catch (err) {
      listening = false;
      setMicUI(false);
      document.getElementById("voice-status").textContent =
        "ไม่สามารถเข้าถึงไมค์: " + err.message;
    }
  }

  function setMicUI(active) {
    document.getElementById("mic-btn").classList.toggle("listening", active);
    document.getElementById("mic-cancel").hidden = !active;
  }

  function startListening() {
    finalBuf = "";
    listening = true;
    setMicUI(true);
    if (sttModel === "groq" || sttModel === "local") {
      document.getElementById("voice-status").textContent = isThai()
        ? "กำลังอัดเสียง… (กดไมค์ = ส่ง · ✕ = ยกเลิก)"
        : "Recording… (mic = send · ✕ = cancel)";
      startGroqRecording();
    } else {
      if (!recog) { listening = false; setMicUI(false); return; }
      recog.lang = voiceLang();
      try { recog.start(); } catch {}
      document.getElementById("voice-status").textContent = isThai()
        ? "กำลังฟัง… พูดได้เลย (กดไมค์ = ส่ง · ✕ = ยกเลิก)"
        : "Listening… speak now (mic = send · ✕ = cancel)";
    }
  }

  function stopListening() {
    if (sttModel === "groq" || sttModel === "local") {
      if (mediaRecorder && mediaRecorder.state !== "inactive") mediaRecorder.stop();
    } else {
      listening = false;
      try { recog.stop(); } catch {}
      setMicUI(false);
      const text = (
        finalBuf + " " + document.getElementById("voice-interim").textContent
      ).trim();
      document.getElementById("voice-interim").textContent = "";
      if (text) {
        const inp = document.getElementById("text-input");
        inp.value = text;
        inp.focus();
        inp.select();
        document.getElementById("voice-status").textContent =
          "แก้ข้อความได้ แล้วกด Enter หรือ ส่ง";
        setTimeout(() => {
          if (!listening)
            document.getElementById("voice-status").textContent = idleStatus();
        }, 4000);
      } else {
        document.getElementById("voice-status").textContent = idleStatus();
      }
    }
  }

  function cancelListening() {
    listening = false;
    if (sttModel === "groq" || sttModel === "local") {
      if (mediaRecorder && mediaRecorder.state !== "inactive") mediaRecorder.stop();
    } else {
      try { recog.stop(); } catch {}
    }
    setMicUI(false);
    finalBuf = "";
    document.getElementById("voice-interim").textContent = "";
    document.getElementById("voice-status").textContent = isThai() ? "ยกเลิกแล้ว" : "Cancelled";
    setTimeout(() => {
      if (!listening) document.getElementById("voice-status").textContent = idleStatus();
    }, 1500);
  }

  // --- Submit user input ---
  async function submitUserInput(text) {
    const section = localActiveSectionRef.value || "main";
    await api("/api/chat", "POST", { role: "user", text, section });
    await api("/api/inbox", "POST", { text, section });
    await api("/api/voice", "POST", { text });
    toast("ส่งเข้า Claude แล้ว ✓ — ให้ Claude เรียก get_inbox เพื่อรับ");
  }

  // --- Wire up voice area event listeners ---
  document.getElementById("mic-btn").addEventListener("click", () =>
    listening ? stopListening() : startListening()
  );
  document.getElementById("mic-cancel").addEventListener("click", cancelListening);

  const textInput = document.getElementById("text-input");
  function sendFromInput() {
    const v = textInput.value.trim();
    if (!v) return;
    submitUserInput(v);
    textInput.value = "";
  }
  textInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendFromInput();
  });
  document.getElementById("send-btn").addEventListener("click", sendFromInput);
}
