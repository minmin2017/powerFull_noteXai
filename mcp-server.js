// Powerfull Note — MCP server (stdio) for Claude Code
// Gives Claude tools to read and edit the mind map, talk to the left-hand
// chat panel, and pick up Thai voice the user spoke in the app.
//
// It does NOT touch the data file directly — it calls the running web server
// over HTTP so there is a single writer and the UI updates live.

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const PORT = Number(process.env.PORT) || 4321;
const BASE = process.env.NOTE_SERVER_URL || `http://localhost:${PORT}`;

async function api(pathname, method = "GET", body) {
  const res = await fetch(BASE + pathname, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`${method} ${pathname} → ${res.status} ${txt}`);
  }
  return res.json();
}

function ok(text) {
  return { content: [{ type: "text", text }] };
}
function fail(err) {
  const hint =
    "\n\n(ถ้าเชื่อมต่อไม่ได้ ให้แน่ใจว่าเปิดแอปไว้แล้ว: รัน `npm start` ในโฟลเดอร์ powerfull_note)";
  return {
    isError: true,
    content: [{ type: "text", text: `เกิดข้อผิดพลาด: ${err.message}${hint}` }],
  };
}

// Render the mind map as an indented tree so Claude can see structure + ids.
function renderTree(nodes) {
  if (!nodes.length) return "(ยังไม่มีโหนดในมายด์แมป)";
  const byParent = new Map();
  for (const n of nodes) {
    const key = n.parentId || "__root__";
    if (!byParent.has(key)) byParent.set(key, []);
    byParent.get(key).push(n);
  }
  const lines = [];
  const walk = (parentKey, depth) => {
    const kids = byParent.get(parentKey) || [];
    for (const n of kids) {
      lines.push(`${"  ".repeat(depth)}- ${n.text}  [id: ${n.id}]`);
      walk(n.id, depth + 1);
    }
  };
  walk("__root__", 0);
  return lines.join("\n");
}

const server = new McpServer({ name: "powerfull-note", version: "1.0.0" });

server.registerTool(
  "get_mindmap",
  {
    title: "อ่านมายด์แมปปัจจุบัน",
    description:
      "Read the current mind map: returns the topic tree with node ids, plus counts of drawings and recent chat. Call this first before editing so you know which node ids exist.",
    inputSchema: {},
  },
  async () => {
    try {
      const s = await api("/api/state");
      const tree = renderTree(s.nodes);
      const out =
        `หัวข้อ (Mind map): "${s.meta?.title || "Untitled"}"\n\n${tree}\n\n` +
        `รวมโหนด: ${s.nodes.length} | ลายเส้นวาด: ${s.drawings.length} | ข้อความแชท: ${s.chat.length}`;
      return ok(out);
    } catch (e) {
      return fail(e);
    }
  }
);

server.registerTool(
  "add_topic",
  {
    title: "เพิ่มหัวข้อ/หัวข้อย่อย",
    description:
      "Add a node to the mind map. Omit parentId to create a top-level topic. Pass parentId to add a sub-topic under an existing node (get ids from get_mindmap). Position is auto-laid-out unless x and y are given. Returns the new node id.",
    inputSchema: {
      text: z.string().describe("ข้อความของหัวข้อ"),
      parentId: z.string().optional().describe("id ของโหนดแม่ (เว้นว่าง = หัวข้อหลัก)"),
      color: z.string().optional().describe("สี hex เช่น #6366f1"),
      x: z.number().optional(),
      y: z.number().optional(),
    },
  },
  async ({ text, parentId, color, x, y }) => {
    try {
      const node = await api("/api/nodes", "POST", { text, parentId, color, x, y });
      return ok(`เพิ่มแล้ว: "${node.text}"  [id: ${node.id}]`);
    } catch (e) {
      return fail(e);
    }
  }
);

server.registerTool(
  "add_topics_bulk",
  {
    title: "เพิ่มหลายหัวข้อพร้อมกัน",
    description:
      "Add several nodes at once. Each item is {text, parentRef?}. parentRef may be the id of an already-existing node OR the 0-based index of an earlier item in THIS list (use 'i:<index>', e.g. 'i:0') to nest new nodes under each other in one call. Great for laying out a whole outline from one voice note.",
    inputSchema: {
      items: z
        .array(
          z.object({
            text: z.string(),
            parentRef: z
              .string()
              .optional()
              .describe("node id, or 'i:<index>' referring to an earlier item in this list"),
            color: z.string().optional(),
          })
        )
        .describe("รายการหัวข้อตามลำดับ"),
    },
  },
  async ({ items }) => {
    try {
      const created = [];
      for (const item of items) {
        let parentId = undefined;
        if (item.parentRef) {
          if (item.parentRef.startsWith("i:")) {
            const idx = Number(item.parentRef.slice(2));
            parentId = created[idx]?.id;
          } else {
            parentId = item.parentRef;
          }
        }
        const node = await api("/api/nodes", "POST", {
          text: item.text,
          parentId,
          color: item.color,
        });
        created.push(node);
      }
      return ok(`เพิ่ม ${created.length} หัวข้อแล้ว:\n` + created.map((n) => `- ${n.text} [id: ${n.id}]`).join("\n"));
    } catch (e) {
      return fail(e);
    }
  }
);

server.registerTool(
  "update_node",
  {
    title: "แก้ไขโหนด",
    description: "Change a node's text and/or color. Use get_mindmap to find the id.",
    inputSchema: {
      id: z.string(),
      text: z.string().optional(),
      color: z.string().optional(),
    },
  },
  async ({ id, text, color }) => {
    try {
      const node = await api(`/api/nodes/${id}`, "PATCH", { text, color });
      return ok(`แก้ไขแล้ว: "${node.text}" [id: ${node.id}]`);
    } catch (e) {
      return fail(e);
    }
  }
);

server.registerTool(
  "move_node",
  {
    title: "ย้ายตำแหน่งโหนด",
    description: "Move a node to absolute world coordinates (x, y).",
    inputSchema: { id: z.string(), x: z.number(), y: z.number() },
  },
  async ({ id, x, y }) => {
    try {
      const node = await api(`/api/nodes/${id}`, "PATCH", { x, y });
      return ok(`ย้าย "${node.text}" ไปที่ (${x}, ${y})`);
    } catch (e) {
      return fail(e);
    }
  }
);

server.registerTool(
  "delete_node",
  {
    title: "ลบโหนด",
    description: "Delete a node and all of its descendants. Returns how many were removed.",
    inputSchema: { id: z.string() },
  },
  async ({ id }) => {
    try {
      const r = await api(`/api/nodes/${id}`, "DELETE");
      return ok(`ลบไป ${r.removed} โหนด`);
    } catch (e) {
      return fail(e);
    }
  }
);

server.registerTool(
  "say_to_user",
  {
    title: "ส่งข้อความเข้าพาเนลแชทซ้าย",
    description:
      "Post a message into the app's left-hand chat panel so the user can read it. Use this to explain what you just did, ask a question, or give a summary in Thai.",
    inputSchema: { text: z.string().describe("ข้อความ (ภาษาไทยได้)") },
  },
  async ({ text }) => {
    try {
      await api("/api/chat", "POST", { role: "claude", text });
      return ok("ส่งข้อความเข้าพาเนลแล้ว");
    } catch (e) {
      return fail(e);
    }
  }
);

server.registerTool(
  "get_voice_input",
  {
    title: "ดึงข้อความเสียงล่าสุดที่ผู้ใช้พูด",
    description:
      "Fetch the most recent Thai voice transcription the user spoke in the app (the mic button). Marks it as consumed. Use this when the user says they spoke a note, or call it to check if there is new spoken input. Returns the transcribed Thai text.",
    inputSchema: {},
  },
  async () => {
    try {
      const v = await api("/api/voice/latest?consume=true");
      if (!v || !v.text) return ok("ยังไม่มีข้อความเสียงใหม่");
      const age = Math.round((Date.now() - v.ts) / 1000);
      return ok(`ผู้ใช้พูดว่า (${age} วินาทีที่แล้ว):\n"${v.text}"`);
    } catch (e) {
      return fail(e);
    }
  }
);

server.registerTool(
  "get_inbox",
  {
    title: "ดึงข้อความที่ผู้ใช้พิมพ์/พูดส่งเข้ามา (ล้างคิว)",
    description:
      "Drain the user's inbox: returns ALL messages the user typed or spoke and sent from the app (the 'ส่งเข้า Claude' button / mic), then clears the queue. Use this to receive what the user wants to tell you without them copy-pasting. Call it when the user says they sent something, or poll it to stay in sync.",
    inputSchema: {},
  },
  async () => {
    try {
      const { items } = await api("/api/inbox?drain=true");
      if (!items || !items.length) return ok("ยังไม่มีข้อความใหม่ในกล่องเข้า");
      const lines = items.map((m) => {
        const age = Math.round((Date.now() - m.ts) / 1000);
        return `• (${age}s ago) ${m.text}`;
      });
      return ok(`ผู้ใช้ส่งมา ${items.length} ข้อความ:\n` + lines.join("\n"));
    } catch (e) {
      return fail(e);
    }
  }
);

server.registerTool(
  "list_projects",
  {
    title: "ดูรายชื่อโปรเจกต์ทั้งหมด",
    description:
      "List all mind-map projects and which one is currently active. Each project is an independent mind map with its own nodes, drawings and chat.",
    inputSchema: {},
  },
  async () => {
    try {
      const { activeId, projects } = await api("/api/projects");
      if (!projects?.length) return ok("(ยังไม่มีโปรเจกต์)");
      const lines = projects.map(
        (p) => `${p.id === activeId ? "➤" : " "} ${p.title}  [id: ${p.id}]`
      );
      return ok(`โปรเจกต์ทั้งหมด:\n${lines.join("\n")}`);
    } catch (e) {
      return fail(e);
    }
  }
);

server.registerTool(
  "create_project",
  {
    title: "สร้างโปรเจกต์ใหม่",
    description:
      "Create a new, empty mind-map project. Does NOT switch to it automatically — call switch_project with the returned id if you want to start editing it.",
    inputSchema: { title: z.string().describe("ชื่อโปรเจกต์") },
  },
  async ({ title }) => {
    try {
      const p = await api("/api/projects", "POST", { title });
      return ok(`สร้างโปรเจกต์แล้ว: "${p.title}"  [id: ${p.id}]`);
    } catch (e) {
      return fail(e);
    }
  }
);

server.registerTool(
  "switch_project",
  {
    title: "สลับไปโปรเจกต์อื่น",
    description:
      "Switch the active project. All subsequent mind-map tools (get_mindmap, add_topic, …) operate on this project, and the app's view follows. Get ids from list_projects.",
    inputSchema: { id: z.string().describe("id ของโปรเจกต์") },
  },
  async ({ id }) => {
    try {
      const r = await api(`/api/projects/${id}/activate`, "POST");
      const active = r.projects?.find((p) => p.id === r.activeId);
      return ok(`สลับไปโปรเจกต์: "${active?.title || id}"`);
    } catch (e) {
      return fail(e);
    }
  }
);

server.registerTool(
  "add_image",
  {
    title: "วางรูปภาพลงบนมายด์แมป",
    description:
      "Place an image onto the current mind map by URL — use this to paste an important picture you found while browsing the web. The server downloads the image and adds it to the active project; the user can then move, resize and rotate it. Optionally give world coordinates (x, y) and a target width/height.",
    inputSchema: {
      url: z.string().describe("URL ของรูปภาพ (เช่นรูปที่เจอจากการค้นเว็บ)"),
      x: z.number().optional().describe("ตำแหน่ง x ในพิกัดโลก (เว้นว่าง = ค่าเริ่มต้น)"),
      y: z.number().optional().describe("ตำแหน่ง y ในพิกัดโลก"),
      w: z.number().optional().describe("ความกว้างเป้าหมาย (px)"),
      h: z.number().optional().describe("ความสูงเป้าหมาย (px)"),
    },
  },
  async ({ url, x, y, w, h }) => {
    try {
      const img = await api("/api/images/from-url", "POST", { url, x, y, w, h });
      return ok(`วางรูปลงมายด์แมปแล้ว [id: ${img.id}]`);
    } catch (e) {
      return fail(e);
    }
  }
);

server.registerTool(
  "tidy_layout",
  {
    title: "จัดเลย์เอาต์มายด์แมปให้สวยอัตโนมัติ",
    description:
      "Auto-arrange ALL nodes into a clean left-to-right tidy tree so nothing overlaps: siblings stack in rows, parents center on their children, top-level branches are separated by a gap. Call this RIGHT AFTER add_topic/add_topics_bulk (their auto-positioning tends to clump). Optional spacing overrides: colW (column gap, default 260), rowH (row gap, default 92).",
    inputSchema: {
      colW: z.number().optional().describe("ระยะห่างคอลัมน์ตามความลึก (px)"),
      rowH: z.number().optional().describe("ระยะห่างแถว (px)"),
    },
  },
  async ({ colW, rowH }) => {
    try {
      const r = await api("/api/layout", "POST", { colW, rowH });
      return ok(`จัดเลย์เอาต์ใหม่แล้ว (${r.nodes} โหนด) ไม่ทับกัน`);
    } catch (e) {
      return fail(e);
    }
  }
);

server.registerTool(
  "get_user_images",
  {
    title: "ดูรูปที่ผู้ใช้ส่งมาให้ดู (ล้างคิว)",
    description:
      "Drain the image inbox: returns every image the user explicitly sent for you to LOOK at (the 👁 'ส่งให้ Claude ดู' button on an image in the app), as actual viewable image content, then clears the queue. Call this when the user says they sent you a picture, or right after a get_inbox message that mentions sending an image. Each image may carry a short text note.",
    inputSchema: {},
  },
  async () => {
    try {
      const { items } = await api("/api/image-inbox?drain=true");
      if (!items || !items.length)
        return ok("ยังไม่มีรูปใหม่ที่ผู้ใช้ส่งมาให้ดู");
      const content = [];
      content.push({
        type: "text",
        text: `ผู้ใช้ส่งรูปมาให้ดู ${items.length} รูป:`,
      });
      for (const it of items) {
        const resp = await fetch(BASE + it.src);
        if (!resp.ok) {
          content.push({ type: "text", text: `(โหลดรูปไม่ได้: ${it.src})` });
          continue;
        }
        const mimeType = resp.headers.get("content-type") || "image/png";
        const data = Buffer.from(await resp.arrayBuffer()).toString("base64");
        if (it.note) content.push({ type: "text", text: `หมายเหตุ: ${it.note}` });
        content.push({ type: "image", data, mimeType });
      }
      return { content };
    } catch (e) {
      return fail(e);
    }
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
console.error("[powerfull-note mcp] connected, talking to", BASE);
