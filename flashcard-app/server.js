import express from "express";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.FLASHCARD_PORT) || 4323;
const NOTE_BASE = process.env.NOTE_SERVER_URL || "http://127.0.0.1:4321";
const DATA_DIR = path.join(__dirname, "data");

if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

function seedInitialData() {
  const seedFiles = [
    {
      id: "mechanics_w07",
      title: "⚙️ Mechanics of Machinery — Gear Trains (บทที่ 7)",
      description: "ชุดเฟือง Simple, Compound, Planetary Gear Train, กฎเครื่องหมาย และสูตรทอง",
      category: "Engineering",
      cards: [
        {
          id: "c1",
          front: "นิยามของ **Velocity Ratio** หรือ **Train Value (e)** ของชุดเฟืองคืออะไร และมีความสัมพันธ์กับจำนวนฟัน (N) อย่างไร?",
          back: "Train value ($e$) คืออัตราส่วนความเร็วของเฟืองตามต่อเฟืองขับ:\n\n$$e = \\frac{\\omega_{\\text{driven}}}{\\omega_{\\text{driver}}} = \\frac{N_{\\text{driver}}}{N_{\\text{driven}}}$$\n\n> สำหรับเฟืองขบภายนอก (External) จะมีเครื่องหมายเป็น **ลบ (-)**\n> สำหรับเฟืองขบภายใน (Internal) จะมีเครื่องหมายเป็น **บวก (+)**",
          interval: 1,
          repetition: 0,
          efactor: 2.5,
          nextReview: Date.now()
        },
        {
          id: "c2",
          front: "หน้าที่และผลลัพธ์ของ **Idler Gear (เฟืองสะพาน)** ใน Simple Gear Train คืออะไร?",
          back: "1. **เปลี่ยนทิศทางการหมุน** ของเฟืองตามให้หมุนทิศเดียวกับเฟืองขับ (ถ้ามี 1 ตัว)\n2. **เชื่อมระยะห่าง** ระหว่างเพลาขับกับเพลาตาม\n3. **ไม่มีผลต่ออัตราทดรวม (Overall Train Value)** เพราะค่า $N_{\\text{idler}}$ จะตัดกันหมดในการคำนวณ",
          interval: 1,
          repetition: 0,
          efactor: 2.5,
          nextReview: Date.now()
        },
        {
          id: "c3",
          front: "เขียน **สูตรทอง (Golden Formula)** สำหรับวิเคราะห์ Planetary Gear Train เมื่อ Arm (ก้านต่อ A) เคลื่อนที่",
          back: "สูตรสัมพัทธ์เทียบกับ Arm ($A$):\n\n$$\\frac{\\omega_L - \\omega_A}{\\omega_F - \\omega_A} = e_{L/F}$$\n\n- $\\omega_L$: ความเร็วเชิงมุมของ Last Gear\n- $\\omega_F$: ความเร็วเชิงมุมของ First Gear\n- $\\omega_A$: ความเร็วเชิงมุมของ Arm ($A$)\n- $e_{L/F}$: Train value เมื่อตรึง Arm ให้อยู่นิ่ง ($A$ fixed)",
          interval: 1,
          repetition: 0,
          efactor: 2.5,
          nextReview: Date.now()
        },
        {
          id: "c4",
          front: "Degree of Freedom (DOF) ของ Planetary Gear Train ทั่วไปมีกี่ DOF และต้องกำหนดกี่ค่าจึงจะหาความเร็วรอบของทุกชิ้นส่วนได้?",
          back: "Planetary Gear Train ทั่วไปมี **2 Degree of Freedom (2 DOF)**\n\nดังนั้นจำเป็นต้อง **ทราบค่า Input อย่างน้อย 2 ค่า** (เช่น รู้ความเร็วของ Sun Gear และความเร็วของ Arm) จึงจะสามารถคำนวณหาความเร็วรอบของทุกเกียร์ที่เหลือได้สมบูรณ์",
          interval: 1,
          repetition: 0,
          efactor: 2.5,
          nextReview: Date.now()
        }
      ]
    },
    {
      id: "electrical_power",
      title: "⚡ Electrical Power Systems & Motor Winding",
      description: "การพันมอเตอร์ แม่เหล็กไฟฟ้า ฟลักซ์ และสมการพื้นฐาน",
      category: "Engineering",
      cards: [
        {
          id: "el1",
          front: "ความสัมพันธ์ระหว่าง **แรงบิด (T), กำลังงาน (P), และความเร็วเชิงมุม (omega)** เขียนเป็นสมการอย่างไร?",
          back: "กำลังงานกล (Mechanical Power):\n\n$$P = T \\times \\omega = T \\times \\left(\\frac{2\\pi N}{60}\\right)$$\n\n- $P$ คือ กำลังงาน (Watts: $\\text{W}$)\n- $T$ คือ แรงบิด (Torque: $\\text{N}\\cdot\\text{m}$)\n- $\\omega$ คือ ความเร็วเชิงมุม ($\\text{rad/s}$)\n- $N$ คือ ความเร็วรอบ ($\\text{rpm}$)",
          interval: 1,
          repetition: 0,
          efactor: 2.5,
          nextReview: Date.now()
        },
        {
          id: "el2",
          front: "กฎของฟาราเดย์ (Faraday's Law of Electromagnetic Induction) และเครื่องหมายลบของ Lenz's Law สื่อถึงอะไร?",
          back: "แรงดันไฟฟ้าเหนี่ยวนำ (Electromotive Force: $e$):\n\n$$e = -N \\frac{d\\Phi}{dt} = -\\frac{d\\lambda}{dt}$$\n\n- $\\Phi$ คือ Magnetic Flux ($\\text{Weber: Wb}$)\n- $\\lambda = N\\Phi$ คือ Flux Linkage ($\\text{Wb-turns}$)\n- **เครื่องหมายลบ (-)** สื่อถึงทิศทางของกระแสเหนี่ยวนำที่เกิดขึ้นจะสร้างสนามแม่เหล็กมา **ต้านการเปลี่ยนแปลงของฟลักซ์เดิม** เสมอ",
          interval: 1,
          repetition: 0,
          efactor: 2.5,
          nextReview: Date.now()
        }
      ]
    }
  ];

  for (const deck of seedFiles) {
    const file = path.join(DATA_DIR, `${deck.id}.json`);
    if (!fs.existsSync(file)) {
      fs.writeFileSync(file, JSON.stringify(deck, null, 2), "utf8");
    }
  }
}

seedInitialData();

app.get("/api/decks", (req, res) => {
  try {
    const files = fs.readdirSync(DATA_DIR).filter(f => f.endsWith(".json"));
    const decks = files.map(file => {
      const content = JSON.parse(fs.readFileSync(path.join(DATA_DIR, file), "utf8"));
      const dueCount = (content.cards || []).filter(c => !c.nextReview || c.nextReview <= Date.now()).length;
      return {
        id: content.id || file.replace(".json", ""),
        title: content.title || "Untitled Deck",
        description: content.description || "",
        category: content.category || "General",
        totalCards: (content.cards || []).length,
        dueCards: dueCount
      };
    });
    res.json({ decks });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/decks/:id", (req, res) => {
  const file = path.join(DATA_DIR, `${req.params.id}.json`);
  if (!fs.existsSync(file)) {
    return res.status(404).json({ error: "Deck not found" });
  }
  try {
    const deck = JSON.parse(fs.readFileSync(file, "utf8"));
    res.json(deck);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post("/api/decks", (req, res) => {
  try {
    const { id, title, description, category, cards } = req.body;
    const deckId = id || `deck_${Date.now()}`;
    const data = {
      id: deckId,
      title: title || "New Deck",
      description: description || "",
      category: category || "General",
      cards: cards || []
    };
    fs.writeFileSync(path.join(DATA_DIR, `${deckId}.json`), JSON.stringify(data, null, 2), "utf8");
    res.json({ success: true, deck: data });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post("/api/cards/:deckId/:cardId/review", (req, res) => {
  const { deckId, cardId } = req.params;
  const { rating } = req.body;
  
  const file = path.join(DATA_DIR, `${deckId}.json`);
  if (!fs.existsSync(file)) {
    return res.status(404).json({ error: "Deck not found" });
  }

  try {
    const deck = JSON.parse(fs.readFileSync(file, "utf8"));
    const card = (deck.cards || []).find(c => c.id === cardId);
    if (!card) return res.status(404).json({ error: "Card not found" });

    let { interval = 1, repetition = 0, efactor = 2.5 } = card;
    const score = Number(rating);
    const sm2Score = score === 1 ? 1 : score === 2 ? 3 : score === 3 ? 4 : 5;

    if (sm2Score >= 3) {
      if (repetition === 0) {
        interval = 1;
      } else if (repetition === 1) {
        interval = 6;
      } else {
        interval = Math.round(interval * efactor);
      }
      repetition += 1;
    } else {
      repetition = 0;
      interval = 1;
    }

    efactor = efactor + (0.1 - (5 - sm2Score) * (0.08 + (5 - sm2Score) * 0.02));
    if (efactor < 1.3) efactor = 1.3;

    const nextReviewTime = Date.now() + (interval * 24 * 60 * 60 * 1000);

    card.interval = interval;
    card.repetition = repetition;
    card.efactor = Number(efactor.toFixed(2));
    card.nextReview = nextReviewTime;
    card.lastReviewed = Date.now();

    fs.writeFileSync(file, JSON.stringify(deck, null, 2), "utf8");
    res.json({ success: true, card });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Robust launcher for Native Desktop Window
app.post("/api/launch-window", (req, res) => {
  try {
    const url = `http://127.0.0.1:${PORT}`;
    const edgePath = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
    const chromePath = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
    const tempProfile = path.join(os.tmpdir(), "flashcard_desktop_profile");

    if (fs.existsSync(edgePath)) {
      const child = spawn(edgePath, [
        `--app=${url}`,
        `--user-data-dir=${tempProfile}`,
        "--window-size=1150,820",
        "--window-position=120,60"
      ], { detached: true, stdio: "ignore" });
      child.unref();
      return res.json({ success: true, mode: "edge-app", pid: child.pid });
    } else if (fs.existsSync(chromePath)) {
      const child = spawn(chromePath, [
        `--app=${url}`,
        `--user-data-dir=${tempProfile}`,
        "--window-size=1150,820",
        "--window-position=120,60"
      ], { detached: true, stdio: "ignore" });
      child.unref();
      return res.json({ success: true, mode: "chrome-app", pid: child.pid });
    } else {
      spawn("cmd", ["/c", "start", url], { detached: true, stdio: "ignore" });
      return res.json({ success: true, mode: "browser-tab" });
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`[Flashcard Studio] Running on http://127.0.0.1:${PORT}`);
});
