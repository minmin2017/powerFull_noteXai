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
// When this Claude Code instance is bound to ONE chat section (multi-instance
// setup), the launcher sets CHAT_SECTION (a section id or name). say_to_user
// then replies into that section, and get_inbox drains only that section.
const SECTION = (process.env.CHAT_SECTION || "").trim() || null;

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
      "Read the current mind map: returns the topic tree with node ids, counts of drawings and recent chat, AND the user's current viewport (the world-area they are looking at right now). Call this first before editing so you know which node ids exist and where the user is looking.",
    inputSchema: {},
  },
  async () => {
    try {
      const s = await api("/api/state");
      const tree = renderTree(s.nodes);
      let vpLine;
      const vp = s.viewport;
      if (vp && Number.isFinite(vp.cx)) {
        vpLine =
          `\n\nหน้าต่างที่ผู้ใช้กำลังดูอยู่ (current viewport): ` +
          `กึ่งกลางที่ (${Math.round(vp.cx)}, ${Math.round(vp.cy)}), ` +
          `ซูม ${Math.round((vp.scale || 1) * 100)}%, ` +
          `กรอบโลกที่เห็น x ${Math.round(vp.minX)}…${Math.round(vp.maxX)} · y ${Math.round(vp.minY)}…${Math.round(vp.maxY)}.` +
          `\n→ ถ้าผู้ใช้บอกให้เพิ่ม/วางของ "ตรงนี้/หน้านี้" ให้วางใกล้กึ่งกลางนี้ หรือเว้น x/y ไว้ ` +
          `(add_topic หัวข้อหลัก / add_image จะวางที่หน้าปัจจุบันให้เอง); ถ้าตั้งใจวางที่อื่นค่อยระบุ x/y เอง.`;
      } else {
        vpLine = `\n\n(ยังไม่รู้ว่าผู้ใช้กำลังดูตรงไหน — ยังไม่ได้เลื่อน/ซูม หรือเพิ่งสลับโปรเจกต์)`;
      }
      const out =
        `หัวข้อ (Mind map): "${s.meta?.title || "Untitled"}"\n\n${tree}${vpLine}\n\n` +
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
      "Add a node to the mind map. Omit parentId to create a top-level topic. Pass parentId to add a sub-topic under an existing node (get ids from get_mindmap). Position is auto-laid-out unless x and y are given — and when omitted, a new top-level topic is placed in the user's CURRENT VIEWPORT (where they are looking) instead of a fixed origin. Returns the new node id.",
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
    inputSchema: {
      text: z.string().describe("ข้อความ (ภาษาไทยได้)"),
      section: z
        .string()
        .optional()
        .describe("chat section id/ชื่อ ที่จะส่งเข้า (เว้นว่าง = ใช้ CHAT_SECTION ที่ผูกไว้ หรือ section ที่ active)"),
    },
  },
  async ({ text, section }) => {
    try {
      await api("/api/chat", "POST", { role: "claude", text, section: section || SECTION || undefined });
      return ok("ส่งข้อความเข้าพาเนลแล้ว" + (section || SECTION ? ` (section: ${section || SECTION})` : ""));
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
      const q = SECTION ? `/api/inbox?drain=true&section=${encodeURIComponent(SECTION)}` : "/api/inbox?drain=true";
      const { items } = await api(q);
      if (!items || !items.length)
        return ok("ยังไม่มีข้อความใหม่ในกล่องเข้า" + (SECTION ? ` (section: ${SECTION})` : ""));
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
      "Place an image onto the current mind map by URL — use this to paste an important picture you found while browsing the web. The server downloads the image and adds it to the active project; the user can then move, resize and rotate it. If you omit x/y the image is centered on the user's CURRENT VIEWPORT (where they are looking); optionally give world coordinates (x, y) and a target width/height.",
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
  "list_images",
  {
    title: "ดูตำแหน่งรูปภาพทั้งหมดบนมายด์แมป",
    description:
      "List every image on the active mind map with its id, x/y position and w/h size. Use this to check whether images overlap/clump before or after placing them, since get_mindmap does not include image data.",
    inputSchema: {},
  },
  async () => {
    try {
      const s = await api("/api/state");
      const imgs = s.images || [];
      if (!imgs.length) return ok("ยังไม่มีรูปในมายด์แมปนี้");
      const lines = imgs.map(
        (im) => `- [id: ${im.id}] x:${im.x} y:${im.y} w:${im.w} h:${im.h}`
      );
      return ok(`รูปทั้งหมด (${imgs.length}):\n` + lines.join("\n"));
    } catch (e) {
      return fail(e);
    }
  }
);

server.registerTool(
  "move_image",
  {
    title: "ย้าย/ปรับขนาดรูปภาพ",
    description:
      "Move and/or resize an image on the active mind map (move_node does NOT work on image ids — images live in a separate store from topic nodes). Use list_images to find ids and check current positions, e.g. to fix clumped/overlapping images after add_image.",
    inputSchema: {
      id: z.string().describe("id ของรูป (im_...)"),
      x: z.number().optional(),
      y: z.number().optional(),
      w: z.number().optional(),
      h: z.number().optional(),
    },
  },
  async ({ id, x, y, w, h }) => {
    try {
      const img = await api(`/api/images/${id}`, "PATCH", { x, y, w, h });
      return ok(`ย้ายรูป [id: ${img.id}] ไปที่ (${img.x}, ${img.y}) ขนาด ${img.w}x${img.h}`);
    } catch (e) {
      return fail(e);
    }
  }
);

server.registerTool(
  "list_aiboxes",
  {
    title: "ดูกรอบ AI Box (พื้นที่งานที่ผู้ใช้วาดให้)",
    description:
      "List the AI Boxes on the active mind map. An AI Box is a rectangle the user drew on the canvas to mark a working REGION, then spoke a command about it (e.g. 'put a mindmap in this box'). Each entry gives the box bounds in WORLD coordinates: x,y (top-left) and w,h. The newest box is marked (ล่าสุด) — when the user says 'in this box / ในกรอบนี้' without naming one, assume the newest. To place nodes INSIDE a box, pass add_topic x/y within [x .. x+w] and [y .. y+h] (keep a small margin), then run tidy_layout is NOT needed if you positioned them yourself.",
    inputSchema: {},
  },
  async () => {
    try {
      const s = await api("/api/state");
      const boxes = (s.boxes || []).filter((b) => b.kind === "aibox");
      if (!boxes.length)
        return ok("ยังไม่มี AI Box — ให้ผู้ใช้คลิกขวาบนพื้นที่ว่าง → เลือก 'AI Box' แล้วลากวาดกรอบก่อน");
      // newest last by createdAt
      const sorted = boxes.slice().sort((a, b) => (a.createdAt || 0) - (b.createdAt || 0));
      const newestId = sorted[sorted.length - 1].id;
      const lines = sorted.map((b) => {
        const tag = b.id === newestId ? " (ล่าสุด)" : "";
        return `- [id: ${b.id}]${tag} "${b.title || "AI Box"}" — x:${Math.round(b.x)} y:${Math.round(b.y)} w:${Math.round(b.w)} h:${Math.round(b.h)} → วางของในช่วง x ${Math.round(b.x)}…${Math.round(b.x + b.w)}, y ${Math.round(b.y)}…${Math.round(b.y + b.h)}`;
      });
      return ok(`AI Box ทั้งหมด (${boxes.length}):\n` + lines.join("\n"));
    } catch (e) {
      return fail(e);
    }
  }
);

server.registerTool(
  "delete_box",
  {
    title: "ลบกล่อง/กรอบ (รวม AI Box)",
    description:
      "Delete a box by id — works for any box kind (aibox, note, image, portal). Use list_aiboxes to get an AI Box id. Useful when the user asks you to remove an AI Box region after you're done working in it.",
    inputSchema: {
      id: z.string().describe("id ของกล่อง (box_...)"),
    },
  },
  async ({ id }) => {
    try {
      const r = await api(`/api/boxes/${id}`, "DELETE");
      return ok(r.removed ? `ลบกล่อง [id: ${id}] แล้ว` : `ไม่พบกล่อง [id: ${id}]`);
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
      "Auto-arrange nodes into a clean left-to-right tidy tree so nothing overlaps.\n\nPREFERRED: pass rootId to tidy ONLY that node's subtree, pinned where it currently sits — every OTHER branch and all images stay exactly put. The user dislikes the whole project reshuffling, so after add_topic/add_topics_bulk you should normally tidy just the affected branch: pass the new node's id (or its top-most ancestor you added under) as rootId. New nodes are already placed sensibly next to their parent, so often you don't need to tidy at all.\n\nWithout rootId it tidies the ENTIRE project (all nodes + spreads images into a row below) anchored to the current viewport — only use this when the user explicitly asks to re-arrange the whole board. Optional spacing overrides: colW (default 260), rowH (default 92).",
    inputSchema: {
      rootId: z.string().optional().describe("จัดเฉพาะ subtree ของโหนดนี้ (ตรึงตำแหน่งเดิม ไม่ยุ่งกิ่งอื่น) — เว้นว่าง = จัดทั้งโปรเจกต์"),
      colW: z.number().optional().describe("ระยะห่างคอลัมน์ตามความลึก (px)"),
      rowH: z.number().optional().describe("ระยะห่างแถว (px)"),
    },
  },
  async ({ rootId, colW, rowH }) => {
    try {
      const r = await api("/api/layout", "POST", { rootId, colW, rowH });
      return ok(
        rootId
          ? `จัดเฉพาะกิ่ง [${rootId}] แล้ว (${r.nodes} โหนด) — กิ่งอื่นไม่ขยับ`
          : `จัดเลย์เอาต์ใหม่ทั้งโปรเจกต์แล้ว (${r.nodes} โหนด) ไม่ทับกัน`
      );
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
        const url = /^https?:\/\//i.test(it.src) ? it.src : BASE + it.src;
        const resp = await fetch(url);
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

server.registerTool(
  "get_canvas_screenshot",
  {
    title: "ดูจอตรงที่ User เลื่อนอยู่ตอนนี้ (viewport)",
    description:
      "Returns a screenshot of ONLY what the user currently sees on screen — the current viewport, exactly where they panned/zoomed to. The browser captures and uploads automatically after each viewport change. Use when the user says 'ดูหน้าจอหน่อย' / 'เห็นไหม' / 'ตรงนี้มีอะไร'. For the WHOLE map at once, use get_full_map instead.",
    inputSchema: {},
  },
  async () => {
    try {
      const { dataUrl } = await api("/api/screenshot");
      const base64 = dataUrl.replace(/^data:image\/\w+;base64,/, "");
      const mimeType = dataUrl.match(/^data:(image\/\w+);/)?.[1] || "image/jpeg";
      return { content: [{ type: "image", data: base64, mimeType }] };
    } catch (e) {
      return fail("ยังไม่มี screenshot — ลอง pan หรือ zoom แผนที่ก่อนแล้วลองใหม่ครับ");
    }
  }
);

server.registerTool(
  "get_full_map",
  {
    title: "ดูภาพรวมทั้ง Mind Map (ทุกโหนด)",
    description:
      "Returns a screenshot of the ENTIRE mind map — every node fitted into one image, regardless of where the user is currently zoomed. The browser briefly fits the whole map, snapshots it, then restores the user's view (non-disruptive). Use this for an overview of the whole project, or when the user says 'ดูทั้งหมด' / 'ภาพรวม' / 'มีอะไรในแผนที่บ้าง'. For only the current on-screen area, use get_canvas_screenshot instead.",
    inputSchema: {},
  },
  async () => {
    try {
      const { dataUrl } = await api("/api/fullmap");
      const base64 = dataUrl.replace(/^data:image\/\w+;base64,/, "");
      const mimeType = dataUrl.match(/^data:(image\/\w+);/)?.[1] || "image/jpeg";
      return { content: [{ type: "image", data: base64, mimeType }] };
    } catch (e) {
      return fail("ถ่ายภาพรวมไม่สำเร็จ — เปิดหน้า http://localhost:4321 ในเบราว์เซอร์ไว้ก่อนนะครับ");
    }
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
console.error("[powerfull-note mcp] connected, talking to", BASE, SECTION ? `| bound to chat section: ${SECTION}` : "| (all sections)");
