#!/usr/bin/env node
/**
 * Simulation Coordinator v2 — uses "claude -p" (print mode) for each agent turn.
 * No separate terminals. Each agent response is a one-shot claude subprocess.
 *
 * Usage:
 *   node coordinator.js [scenario_file] [rounds]
 *   node coordinator.js scenarios/anthropic-ipo.md 5
 */

import { execFileSync } from "child_process";
import fs from "fs";
import path from "path";
import http from "http";
import { fileURLToPath } from "url";
const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ── Config ────────────────────────────────────────────────────────────────────
const CLAUDE = process.env.USERPROFILE
  ? `${process.env.USERPROFILE}\\.local\\bin\\claude.exe`
  : "claude";
const SCENARIO_FILE = process.argv[2] || path.join(__dirname, "scenarios", "default.md");
const MAX_ROUNDS    = parseInt(process.argv[3] || "5", 10);

// ── Agents ────────────────────────────────────────────────────────────────────
const AGENTS = [
  {
    id: "bull_analyst",
    persona:
      "You are Sarah Kim, a senior tech equity analyst at Goldman Sachs. " +
      "Bullish on AI infrastructure plays. You believe Anthropic has a defensible moat " +
      "through safety research and enterprise trust. You look at TAM, revenue growth rate, " +
      "and strategic partnerships (Google, Amazon). You recommend BUY with nuanced price targets.",
  },
  {
    id: "bear_analyst",
    persona:
      "You are Marcus Webb, a value investor and former hedge fund manager. " +
      "Deeply skeptical of unprofitable AI companies at sky-high valuations. " +
      "You compare this to the dot-com bubble and question whether Anthropic can ever outpace " +
      "compute costs. You see OpenAI and Google as existential threats. You lean SELL or AVOID.",
  },
  {
    id: "retail_investor",
    persona:
      "You are Jay, a 35-year-old software engineer who invests on the side. " +
      "You use Claude Code every day and love the product. But you got burned buying " +
      "Rivian and Palantir at IPO. You're torn: buy day 1, wait for the dip, or skip?",
  },
];

// ── HTTP helper ───────────────────────────────────────────────────────────────
function apiPost(apiPath, body) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const req = http.request(
      {
        hostname: "localhost", port: 4321, path: apiPath, method: "POST",
        headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(data) },
      },
      (res) => { let s = ""; res.on("data", (c) => (s += c)); res.on("end", () => resolve(JSON.parse(s))); }
    );
    req.on("error", reject);
    req.write(data);
    req.end();
  });
}

// ── Run one agent turn via "claude -p" ───────────────────────────────────────
function runAgent(agent, scenario, recentEvents, round) {
  const eventsText = recentEvents.length
    ? recentEvents.map((e) => `Round ${e.round}: ${e.summary}`).join("\n")
    : "None yet.";

  const prompt = [
    `You are playing a character in a financial simulation. Stay fully in character.`,
    ``,
    `YOUR PERSONA: ${agent.persona}`,
    ``,
    `SCENARIO:\n${scenario}`,
    ``,
    `RECENT EVENTS:\n${eventsText}`,
    ``,
    `TASK (Round ${round}): What does your character do and say in response to the latest developments?`,
    ``,
    `Reply ONLY with a valid JSON object, nothing else:`,
    `{"agent_id":"${agent.id}","action":"<what your character does>","speech":"<what your character says out loud>","reasoning":"<brief in-character thinking>"}`,
  ].join("\n");

  try {
    const raw = execFileSync(CLAUDE, ["-p", prompt], {
      encoding: "utf8",
      timeout: 90000,
      maxBuffer: 1024 * 1024,
    }).trim();

    // Extract JSON even if claude wraps it in markdown
    const jsonMatch = raw.match(/\{[\s\S]*\}/);
    if (jsonMatch) return JSON.parse(jsonMatch[0]);
    return { agent_id: agent.id, action: raw.slice(0, 200), speech: "", reasoning: "" };
  } catch (err) {
    console.error(`  [${agent.id}] error:`, err.message?.slice(0, 100));
    return { agent_id: agent.id, action: "(no response)", speech: "", reasoning: "" };
  }
}

// ── Main ──────────────────────────────────────────────────────────────────────
async function run() {
  if (!fs.existsSync(SCENARIO_FILE)) {
    console.error(`Scenario file not found: ${SCENARIO_FILE}`);
    process.exit(1);
  }
  const scenario = fs.readFileSync(SCENARIO_FILE, "utf8").trim();

  console.log("\n╔═══════════════════════════════════╗");
  console.log("║  Simulation Coordinator v2.0      ║");
  console.log("║  (claude -p per agent turn)       ║");
  console.log("╚═══════════════════════════════════╝");
  console.log(`Scenario : ${path.basename(SCENARIO_FILE)}`);
  console.log(`Agents   : ${AGENTS.map((a) => a.id).join(", ")}`);
  console.log(`Rounds   : ${MAX_ROUNDS}\n`);

  const recentEvents = [];
  const allRounds = [];

  for (let round = 1; round <= MAX_ROUNDS; round++) {
    console.log(`\n━━━ Round ${round} / ${MAX_ROUNDS} ━━━`);

    // Run all agents in parallel
    const responses = await Promise.all(
      AGENTS.map((agent) => {
        console.log(`  [${agent.id}] thinking...`);
        return Promise.resolve(runAgent(agent, scenario, recentEvents, round));
      })
    );

    for (const r of responses) {
      console.log(`  ✓ [${r.agent_id}] ${r.action?.slice(0, 80)}`);
    }

    // Update state
    const summary = responses.map((r) => `${r.agent_id}: ${r.action}`).join(" | ");
    recentEvents.push({ round, summary, detail: responses });
    allRounds.push({ round, responses });

    // Save round log
    const logPath = path.join(__dirname, "results", `round_${round}.json`);
    fs.mkdirSync(path.dirname(logPath), { recursive: true });
    fs.writeFileSync(logPath, JSON.stringify({ round, responses }, null, 2));
  }

  // Build report
  console.log("\n[coordinator] Building report...");
  const lines = [
    `## Simulation: ${path.basename(SCENARIO_FILE)} — ${MAX_ROUNDS} rounds`,
    `**Agents:** ${AGENTS.map((a) => a.id).join(", ")}`,
    "",
    ...allRounds.flatMap((rd) => [
      `### Round ${rd.round}`,
      ...rd.responses.flatMap((r) => [
        `- **${r.agent_id}**: ${r.action}`,
        r.speech ? `  > *"${r.speech}"*` : null,
      ].filter(Boolean)),
    ]),
    "",
    `📁 Full logs: simulation/results/`,
  ];

  const report = lines.join("\n");
  await apiPost("/api/chat", { role: "claude", text: report, section: "main" });
  console.log("\n[coordinator] Done! Report posted to main chat.");
}

run().catch((err) => {
  console.error("[coordinator] Fatal:", err);
  process.exit(1);
});
