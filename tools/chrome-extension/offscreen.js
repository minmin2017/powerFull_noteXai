// offscreen.js — the only place in the extension that can touch a microphone.
//
// Web Speech is the fast, free path, but Chrome frequently refuses to run
// SpeechRecognition outside a real tab (it comes back "not-allowed" or
// "service-not-allowed" in an offscreen document, and the failure arrives
// asynchronously, after start() has already returned "fine"). So the first
// press probes it: if recognition doesn't actually reach onstart, this
// permanently switches over to recording the audio and posting it to
// powerNote's own local Whisper endpoint, which always works.

const SERVER = "http://127.0.0.1:4321";
const LANG = "th-TH";

let engine = null; // null = undecided, then "speech" or "whisper"
let listening = false;

// --- Web Speech path -------------------------------------------------------
let recognition = null;
let transcript = "";

// --- Whisper path ----------------------------------------------------------
let recorder = null;
let stream = null;
let chunks = [];

function report(text) {
  const t = (text || "").trim();
  if (!t) return;
  chrome.runtime.sendMessage({ target: "background", type: "transcript", text: t }).catch(() => {});
}

function startSpeech(onUnavailable) {
  const SR = self.SpeechRecognition || self.webkitSpeechRecognition;
  if (!SR) return onUnavailable("SpeechRecognition missing");

  recognition = new SR();
  recognition.continuous = true;
  recognition.interimResults = false;
  recognition.lang = LANG;

  let started = false;
  // start() resolves optimistically; onstart is the only proof it really runs.
  const probe = setTimeout(() => {
    if (started) return;
    try {
      recognition.abort();
    } catch {}
    recognition = null;
    onUnavailable("never reached onstart");
  }, 1200);

  recognition.onstart = () => {
    started = true;
    clearTimeout(probe);
    engine = "speech";
    listening = true;
    transcript = "";
  };

  recognition.onresult = (e) => {
    for (let i = e.resultIndex; i < e.results.length; i++) {
      if (e.results[i].isFinal) transcript += e.results[i][0].transcript;
    }
  };

  recognition.onerror = (e) => {
    clearTimeout(probe);
    if (!started) {
      recognition = null;
      onUnavailable(e.error);
    } else {
      console.error("[Offscreen] speech error:", e.error);
    }
  };

  recognition.onend = () => {
    listening = false;
    report(transcript);
    transcript = "";
  };

  try {
    recognition.start();
  } catch (err) {
    clearTimeout(probe);
    recognition = null;
    onUnavailable(String(err));
  }
}

async function startWhisper() {
  try {
    // Re-acquired per press on purpose: holding the stream open would leave
    // Chrome's "microphone in use" indicator lit the whole time.
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (e) {
    console.error("[Offscreen] microphone denied — open the extension's options page once to grant it:", e);
    return;
  }
  chunks = [];
  recorder = new MediaRecorder(stream);
  recorder.ondataavailable = (e) => {
    if (e.data && e.data.size) chunks.push(e.data);
  };
  recorder.onstop = async () => {
    listening = false;
    const blob = new Blob(chunks, { type: chunks[0]?.type || "audio/webm" });
    chunks = [];
    if (stream) {
      stream.getTracks().forEach((t) => t.stop());
      stream = null;
    }
    if (blob.size < 2000) return; // a tap, not speech
    try {
      const r = await fetch(`${SERVER}/api/transcribe-local?lang=${LANG.slice(0, 2)}`, {
        method: "POST",
        headers: { "Content-Type": blob.type },
        body: blob,
      });
      // The endpoint streams the transcript back as plain-text lines.
      const text = (await r.text())
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean)
        .join(" ");
      report(text);
    } catch (e) {
      console.error("[Offscreen] transcription failed:", e);
    }
  };
  recorder.start();
  engine = "whisper";
  listening = true;
}

function start() {
  if (listening) return;
  if (engine === "whisper") return void startWhisper();
  startSpeech((why) => {
    console.warn(`[Offscreen] Web Speech unavailable here (${why}) — using local Whisper from now on`);
    engine = "whisper";
    startWhisper();
  });
}

function stop() {
  if (recognition && listening) {
    try {
      recognition.stop();
    } catch {}
    return;
  }
  if (recorder && recorder.state === "recording") recorder.stop();
}

chrome.runtime.onMessage.addListener((message) => {
  if (!message || message.target !== "offscreen") return;
  if (message.type === "start") start();
  else if (message.type === "stop") stop();
});
