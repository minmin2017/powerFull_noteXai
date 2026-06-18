#!/usr/bin/env node
/**
 * Investment Council Simulation — 5 agents, 10 rounds
 * Topic: Investment philosophy (stocks, real estate, relationships, self-dev)
 * Results posted to main chat + saved as mind-map nodes in "Investment Council" project
 */

import { execFileSync } from "child_process";
import fs from "fs";
import path from "path";
import http from "http";
import { fileURLToPath } from "url";
const __dirname = path.dirname(fileURLToPath(import.meta.url));

const CLAUDE = process.env.USERPROFILE
  ? `${process.env.USERPROFILE}\\.local\\bin\\claude.exe`
  : "claude";
const SCENARIO_FILE = path.join(__dirname, "scenarios", "investment-philosophy.md");
const MAX_ROUNDS = 10;
const PROJECT_ID = "p_mqicytti9z413"; // Investment Council project

const AGENTS = [
  {
    id: "index_investor",
    name: "Emma",
    persona:
      "You are Emma, a 42-year-old FIRE (Financial Independence, Retire Early) advocate. " +
      "You believe in low-cost index funds, living below your means, and compound interest. " +
      "You retired at 38 by putting 70% of income into index funds for 15 years. " +
      "You're skeptical of get-rich-quick schemes and believe consistency beats cleverness.",
  },
  {
    id: "real_estate",
    name: "David",
    persona:
      "You are David, a 50-year-old real estate investor with 12 rental properties. " +
      "You believe real estate is the best wealth builder because of leverage, cash flow, " +
      "tax advantages, and tangibility. You distrust 'paper' assets and love that you can " +
      "touch your investments. You acknowledge it takes work but say the returns are worth it.",
  },
  {
    id: "self_investor",
    name: "Priya",
    persona:
      "You are Priya, a 32-year-old startup founder who sold her first company for $3M. " +
      "You believe investing in yourself — skills, network, health, mindset — gives the " +
      "highest ROI of anything. You spent your 20s learning obsessively rather than saving. " +
      "You think financial assets matter less than the ability to generate value.",
  },
  {
    id: "relationship_investor",
    name: "Carlos",
    persona:
      "You are Carlos, a 45-year-old family man and community organizer. " +
      "You believe relationships and social capital are the most underrated investments. " +
      "Your network got you three job opportunities, two business deals, and helped you " +
      "through a health crisis. You invest time and energy into people, not portfolios. " +
      "You're not anti-money but believe humans optimize for the wrong things.",
  },
  {
    id: "pragmatic_skeptic",
    name: "Alex",
    persona:
      "You are Alex, a 28-year-old financial journalist who has interviewed hundreds of " +
      "wealthy and unsuccessful investors alike. You're deeply skeptical of everyone's " +
      "survivorship bias — including the people in this room. You push back on all claims, " +
      "ask for evidence, and remind people that context matters enormously (country, class, " +
      "timing, luck). You don't have a strong investment thesis of your own — you expose flaws.",
  },
];

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function apiPost(apiPath, body, retries = 3) {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const result = await new Promise((resolve, reject) => {
        const data = JSON.stringify(body);
        const req = http.request(
          {
            hostname: "localhost", port: 4321, path: apiPath, method: "POST",
            headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(data) },
          },
          (res) => { let s = ""; res.on("data", (c) => (s += c)); res.on("end", () => { try { resolve(JSON.parse(s)); } catch { resolve({}); } }); }
        );
        req.on("error", reject);
        req.write(data);
        req.end();
      });
      return result;
    } catch (err) {
      if (attempt < retries) {
        console.warn(`  [apiPost] ${apiPath} failed (attempt ${attempt}): ${err.message} — retrying in 2s`);
        await sleep(2000);
      } else {
        console.error(`  [apiPost] ${apiPath} failed after ${retries} attempts: ${err.message}`);
        return {};
      }
    }
  }
}

function apiGet(apiPath) {
  return new Promise((resolve, reject) => {
    http.get({ hostname: "localhost", port: 4321, path: apiPath },
      (res) => { let s = ""; res.on("data", (c) => (s += c)); res.on("end", () => { try { resolve(JSON.parse(s)); } catch { resolve({}); } }); }
    ).on("error", reject);
  });
}

function runAgent(agent, scenario, recentEvents, round) {
  const eventsText = recentEvents.length
    ? recentEvents.map((e) => `Round ${e.round}: ${e.summary}`).join("\n")
    : "None yet.";

  const prompt = [
    `You are playing a character in a roundtable investment discussion. Stay fully in character.`,
    ``,
    `YOUR PERSONA: ${agent.persona}`,
    ``,
    `SCENARIO:\n${scenario}`,
    ``,
    `RECENT EVENTS:\n${eventsText}`,
    ``,
    `TASK (Round ${round} of ${MAX_ROUNDS}): What does your character say in this round? ` +
    `React to what others said, make your point, challenge or agree with specific people. ` +
    `As rounds progress, allow your thinking to evolve or deepen.`,
    ``,
    `Reply ONLY with a valid JSON object, nothing else:`,
    `{"agent_id":"${agent.id}","name":"${agent.name}","speech":"<what you say out loud, 2-4 sentences>","key_point":"<your main argument this round in one sentence>","directed_at":"<name of person you're responding to, or 'group'>"}`,
  ].join("\n");

  try {
    const raw = execFileSync(CLAUDE, ["-p", prompt], {
      encoding: "utf8", timeout: 90000, maxBuffer: 1024 * 1024,
    }).trim();
    const jsonMatch = raw.match(/\{[\s\S]*\}/);
    if (jsonMatch) return JSON.parse(jsonMatch[0]);
    return { agent_id: agent.id, name: agent.name, speech: raw.slice(0, 300), key_point: "", directed_at: "group" };
  } catch (err) {
    console.error(`  [${agent.id}] error:`, err.message?.slice(0, 100));
    return { agent_id: agent.id, name: agent.name, speech: "(no response)", key_point: "", directed_at: "group" };
  }
}

async function run() {
  const scenario = fs.readFileSync(SCENARIO_FILE, "utf8").trim();

  console.log("\n╔══════════════════════════════════════╗");
  console.log("║  Investment Council Simulation       ║");
  console.log("║  5 agents · 10 rounds                ║");
  console.log("╚══════════════════════════════════════╝");
  console.log(`Agents: ${AGENTS.map((a) => a.name).join(", ")}\n`);

  // Switch to Investment Council project
  await apiPost(`/api/projects/${PROJECT_ID}/activate`, {});

  const recentEvents = [];
  const allRounds = [];

  for (let round = 1; round <= MAX_ROUNDS; round++) {
    console.log(`\n━━━ Round ${round} / ${MAX_ROUNDS} ━━━`);

    const responses = await Promise.all(
      AGENTS.map((agent) => {
        console.log(`  [${agent.name}] thinking...`);
        return Promise.resolve(runAgent(agent, scenario, recentEvents, round));
      })
    );

    for (const r of responses) {
      console.log(`  ✓ [${r.name}] → ${r.directed_at}: "${r.speech?.slice(0, 70)}..."`);
    }

    await sleep(1000); // let server settle after parallel claude processes

    const summary = responses.map((r) => `${r.name}: ${r.key_point || r.speech?.slice(0, 60)}`).join(" | ");
    recentEvents.push({ round, summary, detail: responses });
    allRounds.push({ round, responses });

    // Save round log
    const logPath = path.join(__dirname, "results", `council_round_${round}.json`);
    fs.mkdirSync(path.dirname(logPath), { recursive: true });
    fs.writeFileSync(logPath, JSON.stringify({ round, responses }, null, 2));

    // Post round summary to main chat
    const roundText = [
      `**รอบที่ ${round}/${MAX_ROUNDS}** — Investment Council`,
      ...responses.map((r) => `**${r.name}** (→ ${r.directed_at}): ${r.speech}`),
    ].join("\n\n");
    await apiPost("/api/chat", { role: "claude", text: roundText, section: "main" });
  }

  // Build mind-map nodes in Investment Council project
  console.log("\n[council] Building mind-map...");

  // Root node
  const root = await apiPost("/api/nodes", {
    text: "Investment Council — 10 Rounds",
    parentId: null,
  });
  const rootId = root.id;

  for (const rd of allRounds) {
    const roundNode = await apiPost("/api/nodes", {
      text: `Round ${rd.round}`,
      parentId: rootId,
    });
    for (const r of rd.responses) {
      if (r.key_point) {
        await apiPost("/api/nodes", {
          text: `${r.name}: ${r.key_point}`,
          parentId: roundNode.id,
        });
      }
    }
  }

  // Tidy layout
  await apiPost("/api/layout", {});

  // Final summary to main chat
  const finalLines = [
    `## ✅ Investment Council — สรุปผล 10 รอบ`,
    ``,
    `**ผู้เข้าร่วม:** ${AGENTS.map((a) => a.name).join(", ")}`,
    ``,
    `**ประเด็นหลักแต่ละคน:**`,
    ...AGENTS.map((a) => {
      const lastRound = allRounds[allRounds.length - 1].responses.find((r) => r.agent_id === a.id);
      return `- **${a.name}**: ${lastRound?.key_point || "(no summary)"}`;
    }),
    ``,
    `📁 Logs: simulation/results/council_round_*.json`,
    `🗺️ Mind map: เปิด "Investment Council" project เพื่อดูโครงสร้าง`,
  ];

  await apiPost("/api/chat", { role: "claude", text: finalLines.join("\n"), section: "main" });
  console.log("\n[council] Done!");
}

run().catch((err) => {
  console.error("[council] Fatal:", err);
  process.exit(1);
});
