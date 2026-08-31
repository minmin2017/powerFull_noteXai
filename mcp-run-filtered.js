// mcp-run-filtered — MCP server (stdio) exposing ONE tool: run a shell command
// and get back the exit code + a de-noised tail of its output, with
// progress-bar spam (tqdm %, git "Receiving objects", curl/pip progress
// lines that rely on \r to overwrite themselves) stripped BEFORE it ever
// reaches Claude's context. Built 2026-09-01 because raw progress-bar output
// from things like local Manim renders and `gh run download`/kaggle logs was
// measured to be the single largest source of wasted tokens across sessions
// working in this project — see HANDOFF.md.
//
// This does not replace the harness's own background-task "done/failed"
// notifications (those already work fine for "is it finished") — it only
// covers the case where the actual log CONTENT is needed afterward.

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { spawn } from "node:child_process";

const server = new McpServer({ name: "run-filtered", version: "1.0.0" });

// A line is "progress noise" if it looks like a self-overwriting progress
// indicator: contains a carriage return, or is dominated by repeated
// percent-style tokens (tqdm "12%|###", git "Receiving objects:  45%",
// pip/curl "|████  60%", apt "Get:1 ... 23%"). Real log lines (errors,
// summaries, file paths) essentially never match this shape.
const PROGRESS_LINE = /\r|(\d{1,3}%\|)|(\d{1,3}%\s*$)|Receiving objects:\s*\d{1,3}%|Resolving deltas:\s*\d{1,3}%|^\s*\d+%\s*\[/;

function stripProgressNoise(text) {
  // Carriage-returns inside a single stdout chunk mean "many progress frames
  // squashed onto one line" — split on \r first so each frame can be judged
  // on its own, THEN drop the ones that are pure progress.
  const rawLines = text.split(/\r?\n/).flatMap((l) => l.split("\r"));
  const kept = [];
  let dropped = 0;
  for (const line of rawLines) {
    const trimmed = line.trim();
    if (trimmed === "") continue;
    if (PROGRESS_LINE.test(line)) {
      dropped++;
      continue;
    }
    kept.push(line);
  }
  return { kept, dropped, totalRaw: rawLines.length };
}

server.registerTool(
  "run_filtered",
  {
    title: "Run a shell command with progress-bar noise stripped",
    description:
      "Run a shell command (bash on POSIX, cmd/PowerShell-compatible on Windows via the system shell) and return only the exit code plus a de-noised tail of its combined stdout+stderr. Lines that look like self-overwriting progress bars (tqdm %, git clone \"Receiving objects\", pip/curl/apt progress) are stripped BEFORE the output is returned, so Claude never sees them. Use this instead of the regular shell tool whenever a command is expected to produce noisy progress output (installs, clones, long renders) and only the final result/error actually matters.",
    inputSchema: {
      command: z.string().describe("The shell command to run"),
      cwd: z.string().optional().describe("Working directory (defaults to this server's cwd)"),
      tailLines: z
        .number()
        .int()
        .positive()
        .max(2000)
        .default(60)
        .describe("Max number of cleaned lines to return, counted from the end"),
      timeoutMs: z
        .number()
        .int()
        .positive()
        .max(600000)
        .default(120000)
        .describe("Kill the command after this many milliseconds"),
    },
  },
  async ({ command, cwd, tailLines, timeoutMs }) => {
    const result = await new Promise((resolve) => {
      const isWin = process.platform === "win32";
      const child = spawn(command, {
        shell: isWin ? "powershell.exe" : "/bin/bash",
        cwd: cwd || process.cwd(),
        windowsHide: true,
      });

      let buf = "";
      let timedOut = false;
      const timer = setTimeout(() => {
        timedOut = true;
        child.kill();
      }, timeoutMs);

      child.stdout.on("data", (d) => (buf += d.toString()));
      child.stderr.on("data", (d) => (buf += d.toString()));
      child.on("close", (code) => {
        clearTimeout(timer);
        resolve({ code, buf, timedOut });
      });
      child.on("error", (err) => {
        clearTimeout(timer);
        resolve({ code: null, buf: buf + `\n[spawn error] ${err.message}`, timedOut: false });
      });
    });

    const { kept, dropped, totalRaw } = stripProgressNoise(result.buf);
    const tail = kept.slice(-tailLines);
    const summary =
      `exit_code=${result.code}${result.timedOut ? " (TIMED OUT, process killed)" : ""}\n` +
      `filtered ${dropped} of ${totalRaw} raw lines as progress-bar noise` +
      (kept.length > tail.length ? ` — showing last ${tail.length} of ${kept.length} kept lines\n` : "\n") +
      "---\n" +
      tail.join("\n");

    return { content: [{ type: "text", text: summary }] };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
