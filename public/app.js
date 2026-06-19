/* Powerfull Note — frontend
 * Mind map (nodes + edges), freehand pen layer, pan/zoom, Thai voice,
 * live sync with the server over WebSocket, and a Claude chat panel.
 */
import setupExport from './modules/export.js';
import setupCalendar from './modules/calendar.js';
import setupVoice from './modules/voice.js';
import setupChat from './modules/chat.js';

"use strict";

  // ----------------------------------------------------------------------
  // State
  // ----------------------------------------------------------------------
  let STATE = { meta: { title: "" }, nodes: [], drawings: [], chat: [], voice: {} };
  let PROJECTS = [];
  let ACTIVE_ID = null;
  const view = { x: 200, y: 160, scale: 1 };
  let mode = "select"; // 'select' | 'draw'
  let eraser = false;
  let selectedId = null;
  let selectedIds = new Set(); // multi-select (marquee)
  let selectedStrokeIds = new Set(); // marquee-selected drawing strokes
  let strokeDragOffset = null; // {dx,dy} world coords applied to selectedStrokeIds while dragging
  let marquee = null; // (legacy) rectangular rubber-band — replaced by lasso
  let lasso = null; // freeform selection path: { pts:[{x,y}] } in canvas/screen coords
  let justMarqueed = false; // skip next canvas click after a marquee/lasso drag
  let selectTarget = "nodes"; // 'nodes' | 'strokes' — marquee grabs only this kind
  let resizing = null; // active scale gesture (see startResize)
  let strokeResize = null; // { pivot:{x,y world}, s } live preview for selected strokes
  let reparentDrag = null; // { fromId, sx, sy, ex, ey, targetId }
  let drag = null; // node drag (may include strokeOnly:true and origStrokePoints)
  let pan = null; // canvas pan
  let stroke = null; // active freehand stroke
  let spaceDown = false;
  let serverBootId = null; // detect server restarts for live reload
  let eraseDelete = new Set(); // server ids of strokes touched during an erase drag
  let tmpCounter = 0; // temp ids for stroke pieces created while erasing
  let drawBusy = false; // a pen/erase/stroke-resize/stroke-move gesture is mid-flight
  let pendingState = null; // newest server broadcast deferred while drawBusy
  // Strokes drawn locally but not yet confirmed by a server broadcast. Kept here
  // so a stale/out-of-order broadcast can't momentarily wipe a just-drawn stroke
  // ("letters disappear then come back" while writing a lot). id -> stroke.
  const inflightStrokes = new Map();
  let lastEraseW = null; // last eraser position (world) for motion interpolation
  let lastBoxEraseW = null; // last box-eraser position (normalized) for interpolation
  let localActiveSection = "main"; // mirrors activeSection but updates immediately on tab click
  let chatModule = null; // set after setupChat() runs at bottom of file

  const $ = (s) => document.querySelector(s);
  const canvas = $("#canvas");
  const world = $("#world");
  const nodesLayer = $("#nodes");
  const imagesLayer = $("#images");
  const boxesLayer = $("#boxes");
  const edgesCanvas = $("#edges");
  const fxCanvas = $("#fx");
  const marqueeEl = $("#marquee-box");
  const ectx = edgesCanvas.getContext("2d");
  const fctx = fxCanvas.getContext("2d");
  const nodeEls = new Map();
  const nodeSize = new Map(); // id -> {w,h} world-space size, refreshed each full render()
  const imgEls = new Map();
  const boxEls = new Map();
  let boxInteract = null; // active box move/resize
  let selectedBoxId = null;
  const linkBadges = new Map(); // box-link id -> delete-badge element
  let selectedImgId = null;
  let imgInteract = null; // active image move/resize/rotate

  // ----------------------------------------------------------------------
  // Server helpers
  // ----------------------------------------------------------------------
  async function api(path, method = "GET", body) {
    const res = await fetch(path, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
    return res.ok ? res.json() : null;
  }

  // ----------------------------------------------------------------------
  // WebSocket live sync
  // ----------------------------------------------------------------------
  function connectWS() {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${location.host}/ws`);
    ws.onopen = () => $("#conn-dot").classList.add("on");
    ws.onclose = () => {
      $("#conn-dot").classList.remove("on");
      setTimeout(connectWS, 1500);
    };
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.type === "reload") { location.reload(); return; }
        if (msg.type === "capture-fullmap") { if (window.__captureFullMap) window.__captureFullMap(msg.reqId); return; }
        if (msg.type === "calendar") { if (window.__wsOnCalendar) window.__wsOnCalendar(msg); return; }
        if (msg.type === "state") {
          // Server restarted with new code → refresh to pick it up.
          if (msg.bootId) {
            if (serverBootId && serverBootId !== msg.bootId) { location.reload(); return; }
            serverBootId = msg.bootId;
          }
          if (msg.projects) applyProjects(msg.projects, msg.activeId);
          applyState(msg.state);
          if (msg.history) updateHistoryButtons(msg.history);
        }
      } catch {}
    };
  }

  function applyState(s) {
    // A pen/erase/resize gesture holds optimistic local edits that aren't saved
    // yet. Defer the broadcast (keep the newest) so it can't wipe them mid-stroke
    // — that was the "erased bits vanish then come back / letters disappear" bug.
    if (drawBusy) { pendingState = s; return; }
    // Preserve a node we're actively dragging so the broadcast doesn't snap it.
    if (drag) {
      const local = STATE.nodes.find((n) => n.id === drag.id);
      const incoming = s.nodes.find((n) => n.id === drag.id);
      if (local && incoming) {
        incoming.x = local.x;
        incoming.y = local.y;
      }
    }
    // Same guard for an image or box being moved/resized/rotated right now, so a
    // broadcast can't snap it back mid-gesture.
    if (imgInteract) {
      const local = (STATE.images || []).find((i) => i.id === imgInteract.id);
      const incoming = (s.images || []).find((i) => i.id === imgInteract.id);
      if (local && incoming) Object.assign(incoming, { x: local.x, y: local.y, w: local.w, h: local.h, rotation: local.rotation });
    }
    if (boxInteract) {
      const local = (STATE.boxes || []).find((b) => b.id === boxInteract.id);
      const incoming = (s.boxes || []).find((b) => b.id === boxInteract.id);
      if (local && incoming) Object.assign(incoming, { x: local.x, y: local.y, w: local.w, h: local.h });
    }
    maybeNotifyClaude(s);
    // Re-pin any locally-drawn strokes the server hasn't echoed back yet, so this
    // broadcast can't make a just-drawn stroke flicker out. Once the server state
    // includes one, stop tracking it (its canonical copy is now authoritative).
    if (inflightStrokes.size) {
      s.drawings = s.drawings || [];
      for (const [id, st] of inflightStrokes) {
        if (s.drawings.some((d) => d.id === id)) inflightStrokes.delete(id);
        else s.drawings.push(st);
      }
    }
    // Replace STATE's *contents* in place — DO NOT reassign (STATE = s). The
    // extracted modules (setupChat/setupExport) captured this STATE object by
    // reference at setup time; reassigning would orphan those captures and freeze
    // the chat panel / export on the empty initial state. Keep the identity stable.
    for (const k of Object.keys(STATE)) delete STATE[k];
    Object.assign(STATE, s);
    if (chatModule) chatModule.renderChat();
    syncTitle();
    render();
  }

  // Call when a drawing gesture has fully persisted: stop deferring and flush the
  // newest broadcast so we reconcile to the canonical server state (real ids).
  function endDrawBusy() {
    drawBusy = false;
    if (pendingState) { const s = pendingState; pendingState = null; applyState(s); }
  }

  // ----------------------------------------------------------------------
  // Desktop notification when Claude replies (say_to_user)
  // ----------------------------------------------------------------------
  let lastNotifiedTs = 0;
  let notifyReady = false;
  function initNotifications() {
    if (!("Notification" in window)) return;
    if (Notification.permission === "granted") { notifyReady = true; return; }
    if (Notification.permission !== "denied") {
      // Some browsers require a user gesture; ask on first interaction too.
      Notification.requestPermission().then((p) => { notifyReady = p === "granted"; });
      window.addEventListener("pointerdown", function once() {
        if (Notification.permission === "default") Notification.requestPermission().then((p) => { notifyReady = p === "granted"; });
        window.removeEventListener("pointerdown", once);
      }, { once: true });
    }
  }
  function maybeNotifyClaude(s) {
    const chat = s.chat || [];
    const lastClaude = [...chat].reverse().find((m) => m.role === "claude");
    if (!lastClaude) return;
    if (lastNotifiedTs === 0) { lastNotifiedTs = lastClaude.ts; return; } // skip backlog on first load
    if (lastClaude.ts <= lastNotifiedTs) return;
    lastNotifiedTs = lastClaude.ts;
    if (document.hasFocus()) return; // already looking at the app
    if ("Notification" in window && Notification.permission === "granted") {
      const n = new Notification("Claude ตอบกลับแล้ว 🧠", {
        body: lastClaude.text.slice(0, 180),
        tag: "powerfull-note-claude",
      });
      n.onclick = () => { window.focus(); n.close(); };
    }
  }

  // ----------------------------------------------------------------------
  // Coordinate transforms
  // ----------------------------------------------------------------------
  const worldToScreen = (x, y) => ({ x: x * view.scale + view.x, y: y * view.scale + view.y });
  const screenToWorld = (x, y) => ({ x: (x - view.x) / view.scale, y: (y - view.y) / view.scale });
  function eventCanvasPos(e) {
    const r = canvas.getBoundingClientRect();
    return { x: e.clientX - r.left, y: e.clientY - r.top };
  }
  // Ray-casting point-in-polygon test (poly = [{x,y}], same coord space as px,py).
  function pointInPolygon(px, py, poly) {
    let inside = false;
    for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      const xi = poly[i].x, yi = poly[i].y, xj = poly[j].x, yj = poly[j].y;
      const intersect = (yi > py) !== (yj > py) &&
        px < ((xj - xi) * (py - yi)) / (yj - yi) + xi;
      if (intersect) inside = !inside;
    }
    return inside;
  }

  // ----------------------------------------------------------------------
  // Hidden set (collapsed subtrees)
  // ----------------------------------------------------------------------
  function computeHidden() {
    const byId = new Map(STATE.nodes.map((n) => [n.id, n]));
    const hidden = new Set();
    for (const n of STATE.nodes) {
      let p = n.parentId ? byId.get(n.parentId) : null;
      const seen = new Set([n.id]); // guard against a stray parent cycle (don't hang)
      while (p && !seen.has(p.id)) {
        seen.add(p.id);
        if (p.collapsed) {
          hidden.add(n.id);
          break;
        }
        p = p.parentId ? byId.get(p.parentId) : null;
      }
    }
    return hidden;
  }
  function hasChildren(id) {
    return STATE.nodes.some((n) => n.parentId === id);
  }

  // ----------------------------------------------------------------------
  // Render
  // ----------------------------------------------------------------------
  function render() {
    world.style.transform = `translate(${view.x}px, ${view.y}px) scale(${view.scale})`;
    $("#zoom-label").textContent = Math.round(view.scale * 100) + "%";
    if (typeof updateEraserCursor === "function") updateEraserCursor();

    renderImages();
    renderBoxes();
    if (typeof renderObjectPanel === "function") renderObjectPanel();
    scheduleReportViewport(); // keep the server's notion of the visible area fresh

    const hidden = computeHidden();
    const present = new Set();

    for (const n of STATE.nodes) {
      present.add(n.id);
      let el = nodeEls.get(n.id);
      if (!el) {
        el = createNodeEl(n);
        nodeEls.set(n.id, el);
        nodesLayer.appendChild(el);
      }
      // position (world coords; #world is scaled)
      el.style.left = n.x + "px";
      el.style.top = n.y + "px";
      el.style.display = hidden.has(n.id) ? "none" : "";
      el.classList.toggle("root", !n.parentId);
      el.classList.toggle("selected", n.id === selectedId || selectedIds.has(n.id));
      el.style.borderColor = n.color || "var(--accent)";
      // text (skip while editing to avoid caret jumps); URLs become links
      const txt = el.querySelector(".node-text");
      if (document.activeElement !== txt) setNodeText(txt, n.text);
      // tag chips
      const tagsEl = el.querySelector(".node-tags");
      const nodeTags = n.tags || [];
      const tagKey = nodeTags.join(",");
      if (tagsEl.dataset.key !== tagKey) {
        tagsEl.dataset.key = tagKey;
        tagsEl.innerHTML = nodeTags.map((t) => {
          const def = TAGS.find((x) => x.name === t);
          return `<span class="node-tag" style="background:${def?.color || "#6366f1"}">${def?.emoji || "🏷"} ${t}</span>`;
        }).join("");
      }
      // collapse toggle
      let tog = el.querySelector(".collapse-toggle");
      if (hasChildren(n.id)) {
        if (!tog) {
          tog = document.createElement("button");
          tog.className = "handle collapse-toggle";
          tog.addEventListener("pointerdown", (e) => e.stopPropagation());
          tog.addEventListener("click", (e) => {
            e.stopPropagation();
            updateNodeLocal(n.id, { collapsed: !n.collapsed });
            api(`/api/nodes/${n.id}`, "PATCH", { collapsed: !n.collapsed });
          });
          el.appendChild(tog);
        }
        tog.textContent = n.collapsed ? "+" : "−";
        tog.style.display = "";
      } else if (tog) {
        tog.style.display = "none";
      }
    }
    // remove gone nodes
    for (const [id, el] of nodeEls) {
      if (!present.has(id)) {
        el.remove();
        nodeEls.delete(id);
      }
    }

    $("#empty-hint").style.display = STATE.nodes.length ? "none" : "";
    // Cache each node's world-space size once (one batched layout read, after all
    // the style writes above). drawEdges then positions edges analytically with
    // no per-node getBoundingClientRect — so panning never triggers a reflow storm.
    for (const [id, el] of nodeEls) {
      if (el.style.display === "none") continue;
      nodeSize.set(id, { w: el.offsetWidth, h: el.offsetHeight });
    }
    drawEdges(hidden);
    drawFx();
    renderResizeBox();
  }

  // Linkify URLs in node text. While editing we show the raw text so the user
  // can edit the URL; otherwise URLs render as clickable links.
  const URL_RE = /(https?:\/\/[^\s<]+)/g;
  function escapeHtml(s) {
    return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  }
  function linkifyHtml(text) {
    return escapeHtml(text).replace(URL_RE, '<a href="$1" target="_blank" rel="noopener" class="node-link">$1</a>');
  }
  function setNodeText(txt, text) {
    const key = (/https?:\/\//.test(text) ? "L:" : "T:") + text;
    if (txt.dataset.rendered === key) return;
    if (key[0] === "L") txt.innerHTML = linkifyHtml(text);
    else txt.textContent = text;
    txt.dataset.rendered = key;
  }
  function beginEditNode(txt) {
    const id = txt.closest(".node")?.dataset.id;
    const node = STATE.nodes.find((x) => x.id === id);
    txt.textContent = node ? node.text : txt.textContent; // raw text for editing
    txt.dataset.rendered = "";
    txt.setAttribute("contenteditable", "true");
    txt.focus();
    document.getSelection().selectAllChildren(txt);
  }

  function createNodeEl(n) {
    const el = document.createElement("div");
    el.className = "node";
    el.dataset.id = n.id;
    el.innerHTML = `<div class="node-text"></div><div class="node-tags"></div><button class="handle tag-btn" title="แท็ก">🏷</button><button class="handle add-child" title="เพิ่มหัวข้อย่อย">+</button><button class="handle reparent-btn" title="ลากไปวางบนโหนดอื่นเพื่อเปลี่ยน parent">⛓</button><button class="handle del-node" title="ลบหัวข้อนี้ (และหัวข้อย่อย)">×</button>`;
    const txt = el.querySelector(".node-text");

    el.addEventListener("pointerdown", (e) => onNodePointerDown(e, n.id));
    el.addEventListener("click", (e) => {
      if (e.target.closest("a")) return; // let link clicks open
      e.stopPropagation();
      selectedId = n.id;
      render();
    });
    el.addEventListener("dblclick", (e) => {
      e.stopPropagation();
      beginEditNode(txt);
    });

    txt.addEventListener("dblclick", (e) => {
      e.stopPropagation();
      beginEditNode(txt);
    });
    txt.addEventListener("blur", () => {
      txt.removeAttribute("contenteditable");
      const node = STATE.nodes.find((x) => x.id === n.id);
      const val = txt.textContent.trim();
      if (node && val !== node.text) {
        node.text = val;
        api(`/api/nodes/${n.id}`, "PATCH", { text: val });
      }
      txt.dataset.rendered = "";
      setNodeText(txt, node ? node.text : val); // restore link rendering
    });
    txt.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        txt.blur();
      }
    });

    el.querySelector(".add-child").addEventListener("pointerdown", (e) => e.stopPropagation());
    el.querySelector(".add-child").addEventListener("click", async (e) => {
      e.stopPropagation();
      const child = await api("/api/nodes", "POST", { parentId: n.id, text: "" });
      if (child) {
        selectedId = child.id;
        // focus once the element exists
        setTimeout(() => {
          const cel = nodeEls.get(child.id);
          if (cel) beginEditNode(cel.querySelector(".node-text"));
        }, 60);
      }
    });

    el.querySelector(".del-node").addEventListener("pointerdown", (e) => e.stopPropagation());
    el.querySelector(".del-node").addEventListener("click", (e) => {
      e.stopPropagation();
      const node = STATE.nodes.find((x) => x.id === n.id);
      const kids = hasChildren(n.id);
      const label = (node?.text || "หัวข้อนี้").slice(0, 40);
      if (kids && !confirm(`ลบ "${label}" และหัวข้อย่อยทั้งหมด?`)) return;
      if (selectedId === n.id) selectedId = null;
      api(`/api/nodes/${n.id}`, "DELETE");
    });

    el.querySelector(".tag-btn").addEventListener("pointerdown", (e) => e.stopPropagation());
    el.querySelector(".tag-btn").addEventListener("click", (e) => openTagPicker(e, n.id));

    const reparentBtn = el.querySelector(".reparent-btn");
    reparentBtn.addEventListener("pointerdown", (e) => {
      e.stopPropagation();
      const r = canvas.getBoundingClientRect();
      const p = { x: e.clientX - r.left, y: e.clientY - r.top };
      reparentDrag = { fromId: n.id, sx: p.x, sy: p.y, ex: p.x, ey: p.y, targetId: null };
      reparentBtn.setPointerCapture?.(e.pointerId);
      window.addEventListener("pointermove", onReparentMove);
      window.addEventListener("pointerup", onReparentUp, { once: true });
    });

    return el;
  }

  function updateNodeLocal(id, patch) {
    const n = STATE.nodes.find((x) => x.id === id);
    if (n) Object.assign(n, patch);
    render();
  }

  // ----------------------------------------------------------------------
  // Image objects (paste / drag-drop, resizable + rotatable)
  // ----------------------------------------------------------------------
  function renderImages() {
    const images = STATE.images || [];
    const present = new Set();
    for (const im of images) {
      present.add(im.id);
      let el = imgEls.get(im.id);
      if (!el) {
        el = createImgEl(im);
        imgEls.set(im.id, el);
        imagesLayer.appendChild(el);
      }
      const img = el.querySelector("img");
      if (img.getAttribute("src") !== im.src) img.setAttribute("src", im.src);
      el.style.left = im.x + "px";
      el.style.top = im.y + "px";
      el.style.width = im.w + "px";
      el.style.height = im.h + "px";
      el.style.transform = `rotate(${im.rotation || 0}deg)`;
      el.classList.toggle("selected", im.id === selectedImgId);
    }
    for (const [id, el] of imgEls) {
      if (!present.has(id)) {
        el.remove();
        imgEls.delete(id);
      }
    }
  }

  function createImgEl(im) {
    const el = document.createElement("div");
    el.className = "img-obj";
    el.dataset.id = im.id;
    el.innerHTML = `<img alt="" draggable="false" />
      <div class="img-handle h-rot" title="หมุน"></div>
      <div class="img-handle h-se" title="ปรับขนาด"></div>
      <div class="img-handle h-send" title="ส่งรูปนี้ให้ Claude ดู">👁</div>
      <div class="img-handle h-del" title="ลบรูป">×</div>`;

    // select + move
    el.addEventListener("pointerdown", (e) => {
      if (mode !== "select") return;
      if (e.target.closest(".img-handle")) return; // handled below
      e.stopPropagation();
      selectedImgId = im.id;
      selectedId = null;
      startImgMove(e, im.id);
      render();
    });

    el.querySelector(".h-se").addEventListener("pointerdown", (e) => {
      e.stopPropagation();
      startImgResize(e, im.id);
    });
    el.querySelector(".h-rot").addEventListener("pointerdown", (e) => {
      e.stopPropagation();
      startImgRotate(e, im.id);
    });
    el.querySelector(".h-del").addEventListener("pointerdown", (e) => e.stopPropagation());
    el.querySelector(".h-del").addEventListener("click", (e) => {
      e.stopPropagation();
      if (selectedImgId === im.id) selectedImgId = null;
      api(`/api/images/${im.id}`, "DELETE");
    });
    el.querySelector(".h-send").addEventListener("pointerdown", (e) => e.stopPropagation());
    el.querySelector(".h-send").addEventListener("click", async (e) => {
      e.stopPropagation();
      // queue the image for Claude to look at, plus a text marker so the
      // inbox Monitor wakes Claude to actually call get_user_images.
      await api("/api/image-inbox", "POST", { id: im.id });
      await api("/api/inbox", "POST", { text: "[ผู้ใช้ส่งรูปให้ดู — เรียก get_user_images]" });
      toast("ส่งรูปให้ Claude ดูแล้ว 👁");
    });
    return el;
  }

  function imgById(id) {
    return (STATE.images || []).find((i) => i.id === id);
  }

  function startImgMove(e, id) {
    const im = imgById(id);
    if (!im) return;
    const start = screenToWorld(...Object.values(eventCanvasPos(e)));
    imgInteract = { kind: "move", id, ox: im.x, oy: im.y, sx: start.x, sy: start.y };
    bindImgInteract();
  }
  function startImgResize(e, id) {
    const im = imgById(id);
    if (!im) return;
    const start = screenToWorld(...Object.values(eventCanvasPos(e)));
    imgInteract = { kind: "resize", id, ow: im.w, oh: im.h, sx: start.x, sy: start.y, ratio: im.w / im.h };
    bindImgInteract();
  }
  function startImgRotate(e, id) {
    const im = imgById(id);
    if (!im) return;
    const cx = im.x + im.w / 2;
    const cy = im.y + im.h / 2;
    const start = screenToWorld(...Object.values(eventCanvasPos(e)));
    const a0 = Math.atan2(start.y - cy, start.x - cx);
    imgInteract = { kind: "rotate", id, cx, cy, a0, r0: im.rotation || 0 };
    bindImgInteract();
  }
  function bindImgInteract() {
    window.addEventListener("pointermove", onImgInteractMove);
    window.addEventListener("pointerup", onImgInteractUp, { once: true });
  }
  function onImgInteractMove(e) {
    if (!imgInteract) return;
    const im = imgById(imgInteract.id);
    if (!im) return;
    const w = screenToWorld(...Object.values(eventCanvasPos(e)));
    if (imgInteract.kind === "move") {
      im.x = imgInteract.ox + (w.x - imgInteract.sx);
      im.y = imgInteract.oy + (w.y - imgInteract.sy);
      // Highlight the image box the floating image is hovering over.
      const imgEl = imgEls.get(imgInteract.id);
      if (imgEl) {
        const ir = imgEl.getBoundingClientRect();
        const icx = ir.left + ir.width / 2;
        const icy = ir.top + ir.height / 2;
        for (const [, boxEl] of boxEls) {
          if (boxEl.dataset.kind !== "image") continue;
          const br = boxEl.getBoundingClientRect();
          const over = icx >= br.left && icx <= br.right && icy >= br.top && icy <= br.bottom;
          boxEl.classList.toggle("drop-target", over);
        }
      }
    } else if (imgInteract.kind === "resize") {
      let nw = Math.max(24, imgInteract.ow + (w.x - imgInteract.sx));
      let nh = nw / imgInteract.ratio; // keep aspect ratio
      im.w = nw;
      im.h = nh;
    } else if (imgInteract.kind === "rotate") {
      const a = Math.atan2(w.y - imgInteract.cy, w.x - imgInteract.cx);
      im.rotation = imgInteract.r0 + ((a - imgInteract.a0) * 180) / Math.PI;
    }
    renderImages();
  }
  function onImgInteractUp() {
    window.removeEventListener("pointermove", onImgInteractMove);
    const it = imgInteract;
    imgInteract = null;
    for (const [, boxEl] of boxEls) boxEl.classList.remove("drop-target");
    if (!it) return;
    const im = imgById(it.id);
    if (!im) return;

    // If a floating image is moved over an image-box, drop it into that box's gallery.
    if (it.kind === "move") {
      const imgEl = imgEls.get(it.id);
      if (imgEl) {
        const ir = imgEl.getBoundingClientRect();
        const icx = ir.left + ir.width / 2;
        const icy = ir.top + ir.height / 2;
        for (const [boxId, boxEl] of boxEls) {
          if (boxEl.dataset.kind !== "image") continue;
          const br = boxEl.getBoundingClientRect();
          if (icx >= br.left && icx <= br.right && icy >= br.top && icy <= br.bottom) {
            addItemToBox(boxId, { src: im.src, url: "", caption: "" });
            api(`/api/images/${it.id}`, "DELETE");
            toast("เพิ่มรูปเข้ากล่องแล้ว 🖼️");
            return;
          }
        }
      }
    }

    api(`/api/images/${it.id}`, "PATCH", { x: im.x, y: im.y, w: im.w, h: im.h, rotation: im.rotation });
  }

  // Add an image from a data URL, dropped at a given screen point (or view center).
  async function addImageDataUrl(dataUrl, screenPt) {
    const tmp = new Image();
    tmp.onload = () => {
      let w = tmp.naturalWidth || 240;
      let h = tmp.naturalHeight || 180;
      const max = 360;
      if (w > max || h > max) {
        const k = max / Math.max(w, h);
        w = Math.round(w * k);
        h = Math.round(h * k);
      }
      const r = canvas.getBoundingClientRect();
      const pt = screenPt || { x: r.width / 2, y: r.height / 2 };
      const wpt = screenToWorld(pt.x, pt.y);
      api("/api/images", "POST", { dataUrl, x: wpt.x - w / 2, y: wpt.y - h / 2, w, h });
    };
    tmp.src = dataUrl;
  }

  function fileToImage(file, screenPt) {
    if (!file || !file.type.startsWith("image/")) return;
    const reader = new FileReader();
    reader.onload = () => addImageDataUrl(reader.result, screenPt);
    reader.readAsDataURL(file);
  }

  // edges between node centers (screen space, behind nodes)
  function drawEdges(hidden) {
    const r = canvas.getBoundingClientRect();
    sizeCanvas(edgesCanvas, ectx, r);
    ectx.clearRect(0, 0, r.width, r.height);
    const byId = new Map();
    for (const nn of STATE.nodes) byId.set(nn.id, nn);
    // Screen-space rect of a node, computed from its world position + cached
    // size (no getBoundingClientRect → no forced layout, even during a pan).
    const rect = (id) => {
      const nn = byId.get(id);
      const el = nodeEls.get(id);
      if (!nn || !el || el.style.display === "none") return null;
      const sz = nodeSize.get(id);
      const w = (sz ? sz.w : el.offsetWidth) * view.scale;
      const h = (sz ? sz.h : el.offsetHeight) * view.scale;
      const s = worldToScreen(nn.x, nn.y);
      return { l: s.x, t: s.y, cx: s.x + w / 2, cy: s.y + h / 2, w, h };
    };
    for (const n of STATE.nodes) {
      if (!n.parentId || hidden.has(n.id)) continue;
      const a = rect(n.parentId);
      const b = rect(n.id);
      if (!a || !b) continue;
      // anchor on facing sides
      const ax = b.cx >= a.cx ? a.l + a.w : a.l;
      const ay = a.cy;
      const bx = b.cx >= a.cx ? b.l : b.l + b.w;
      const by = b.cy;
      const dx = Math.abs(bx - ax) * 0.5 + 12;
      ectx.beginPath();
      ectx.moveTo(ax, ay);
      ectx.bezierCurveTo(ax + (bx >= ax ? dx : -dx), ay, bx - (bx >= ax ? dx : -dx), by, bx, by);
      ectx.strokeStyle = n.color || "#6366f1";
      ectx.globalAlpha = 0.55;
      ectx.lineWidth = Math.max(1.5, 2.2 * view.scale);
      ectx.stroke();
      ectx.globalAlpha = 1;
    }
    drawBoxLinks(r);
  }

  // Connections between boxes (dashed teal lines) + a "×" delete badge at each
  // midpoint, plus the rubber-band line while dragging a new link.
  function drawBoxLinks(r) {
    const center = (id) => {
      const el = boxEls.get(id) || nodeEls.get(id);
      if (!el) return null;
      const b = el.getBoundingClientRect();
      return { x: b.left - r.left + b.width / 2, y: b.top - r.top + b.height / 2 };
    };
    const links = STATE.boxLinks || [];
    const seen = new Set();
    ectx.save();
    ectx.setLineDash([7, 5]);
    ectx.strokeStyle = "#14b8a6";
    ectx.lineWidth = Math.max(1.5, 2 * view.scale);
    for (const l of links) {
      const a = center(l.from);
      const b = center(l.to);
      if (!a || !b) continue;
      ectx.beginPath();
      ectx.moveTo(a.x, a.y);
      ectx.lineTo(b.x, b.y);
      ectx.stroke();
      // delete badge at midpoint
      seen.add(l.id);
      let badge = linkBadges.get(l.id);
      if (!badge) {
        badge = document.createElement("button");
        badge.className = "box-link-badge";
        badge.textContent = "×";
        badge.title = "ลบเส้นโยง";
        badge.addEventListener("pointerdown", (e) => e.stopPropagation());
        badge.addEventListener("click", (e) => { e.stopPropagation(); api(`/api/box-links/${l.id}`, "DELETE"); });
        canvas.appendChild(badge);
        linkBadges.set(l.id, badge);
      }
      badge.style.left = (a.x + b.x) / 2 + "px";
      badge.style.top = (a.y + b.y) / 2 + "px";
    }
    for (const [id, el] of linkBadges) {
      if (!seen.has(id)) { el.remove(); linkBadges.delete(id); }
    }
    // rubber-band while dragging a new link
    if (linkDrag) {
      const a = center(linkDrag.from);
      if (a) {
        ectx.beginPath();
        ectx.moveTo(a.x, a.y);
        ectx.lineTo(linkDrag.pt.x, linkDrag.pt.y);
        ectx.stroke();
      }
    }
    ectx.restore();
  }

  // freehand drawings + active stroke (screen space, above nodes).
  // Throttled to one paint per animation frame so a burst of pointermove
  // samples collapses into a single render instead of N.
  let fxRaf = 0;
  function drawFx() {
    if (fxRaf) return;
    fxRaf = requestAnimationFrame(() => { fxRaf = 0; drawFxNow(); });
  }
  // Paint right now, cancelling any frame queued by drawFx(). Used before code
  // that reads the canvas pixels (PNG export) so it can't capture a stale frame.
  function flushFx() {
    if (fxRaf) { cancelAnimationFrame(fxRaf); fxRaf = 0; }
    drawFxNow();
  }

  // Offscreen cache of the committed strokes, rendered a bit larger than the
  // viewport (a margin all around). During a draw OR a pan the scale is fixed,
  // so we render every committed stroke once and then just blit this bitmap —
  // translated by how far we've panned — instead of re-rendering them each
  // frame. That keeps drawing AND panning O(1) no matter how many strokes are on
  // the page (re-rendering every stroke each frame is what made both lag once a
  // lot had been drawn). The cache is only rebuilt when the view drifts past the
  // margin or the scale changes.
  const STROKE_CACHE_MARGIN = 256; // CSS px of slack so short pans don't rebuild
  const strokeCache = document.createElement("canvas");
  const sctx = strokeCache.getContext("2d");
  let strokeCacheValid = false;
  let strokeCacheView = null; // view the cache was rendered at
  function buildStrokeCache(r) {
    const dpr = window.devicePixelRatio || 1;
    const m = STROKE_CACHE_MARGIN;
    const w = Math.round((r.width + 2 * m) * dpr), h = Math.round((r.height + 2 * m) * dpr);
    if (strokeCache.width !== w) strokeCache.width = w;
    if (strokeCache.height !== h) strokeCache.height = h;
    // Shift the origin by the margin so screen (0,0) maps to (m,m) in the cache.
    sctx.setTransform(dpr, 0, 0, dpr, m * dpr, m * dpr);
    sctx.clearRect(-m, -m, r.width + 2 * m, r.height + 2 * m);
    for (const d of STATE.drawings) drawStroke(d, sctx);
    strokeCacheValid = true;
    strokeCacheView = { x: view.x, y: view.y, scale: view.scale };
  }
  // Stale if invalidated, the scale changed, the canvas resized, or the pan has
  // moved far enough that the margin no longer covers the viewport.
  function strokeCacheStale(r) {
    if (!strokeCacheValid || !strokeCacheView) return true;
    if (strokeCacheView.scale !== view.scale) return true;
    if (Math.abs(view.x - strokeCacheView.x) > STROKE_CACHE_MARGIN) return true;
    if (Math.abs(view.y - strokeCacheView.y) > STROKE_CACHE_MARGIN) return true;
    const dpr = window.devicePixelRatio || 1, m = STROKE_CACHE_MARGIN;
    return strokeCache.width !== Math.round((r.width + 2 * m) * dpr) ||
           strokeCache.height !== Math.round((r.height + 2 * m) * dpr);
  }
  // Blit the cache onto the fx canvas, offset by however far we've panned since
  // it was built (the -m undoes the margin origin).
  function blitStrokeCache(r) {
    const m = STROKE_CACHE_MARGIN;
    const dx = view.x - strokeCacheView.x, dy = view.y - strokeCacheView.y;
    fctx.drawImage(strokeCache, dx - m, dy - m, r.width + 2 * m, r.height + 2 * m);
  }

  function drawFxNow() {
    const r = canvas.getBoundingClientRect();
    sizeCanvas(fxCanvas, fctx, r);
    fctx.clearRect(0, 0, r.width, r.height);
    const drawingPen = stroke && !stroke.eraser;
    if (drawingPen || pan) {
      // Draw or pan gesture: scale is fixed, so blit the cached committed strokes
      // (rebuilding only when the view drifts past the margin) and, while
      // drawing, lay just the live stroke on top.
      if (strokeCacheStale(r)) buildStrokeCache(r);
      blitStrokeCache(r);
      if (drawingPen) drawStroke(stroke, fctx);
    } else {
      // Full repaint (idle / erasing / dragging). Cache rebuilt next gesture.
      strokeCacheValid = false;
      for (const d of STATE.drawings) drawStroke(d, fctx);
    }
    if (reparentDrag) {
      fctx.save();
      fctx.strokeStyle = reparentDrag.targetId ? "rgba(99,241,130,0.9)" : "rgba(99,102,241,0.9)";
      fctx.lineWidth = 2;
      fctx.setLineDash([6, 4]);
      fctx.beginPath();
      fctx.moveTo(reparentDrag.sx, reparentDrag.sy);
      fctx.lineTo(reparentDrag.ex, reparentDrag.ey);
      fctx.stroke();
      fctx.restore();
    }
    if (lasso && lasso.pts.length > 1) {
      fctx.save();
      fctx.strokeStyle = "rgba(99,102,241,0.9)";
      fctx.fillStyle = "rgba(99,102,241,0.10)";
      fctx.lineWidth = 1.5;
      fctx.lineJoin = "round";
      fctx.setLineDash([5, 4]);
      fctx.beginPath();
      fctx.moveTo(lasso.pts[0].x, lasso.pts[0].y);
      for (const p of lasso.pts.slice(1)) fctx.lineTo(p.x, p.y);
      fctx.closePath();
      fctx.fill();
      fctx.stroke();
      fctx.restore();
    }
  }

  function drawStroke(d, ctx = fctx) {
    if (!d.points || d.points.length < 1) return;
    const isSel = selectedStrokeIds.has(d.id);
    const off = (isSel && strokeDragOffset) ? strokeDragOffset : null;
    const rs = (isSel && strokeResize) ? strokeResize : null; // live scale preview
    const wmul = rs ? rs.s : 1; // stroke width scales with the drawing
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    const pts = d.points.map((p) => {
      let wx = p.x, wy = p.y;
      if (off) { wx += off.dx; wy += off.dy; }
      else if (rs) { wx = rs.pivot.x + (wx - rs.pivot.x) * rs.s; wy = rs.pivot.y + (wy - rs.pivot.y) * rs.s; }
      const s = worldToScreen(wx, wy);
      return { x: s.x, y: s.y, p: p.p ?? 0.5 };
    });
    // selection highlight pass
    if (isSel && !off) {
      ctx.save();
      ctx.strokeStyle = "rgba(99,102,241,0.45)";
      ctx.lineWidth = (d.width * wmul + 8) * view.scale;
      ctx.beginPath();
      if (pts.length === 1) { ctx.arc(pts[0].x, pts[0].y, (d.width * wmul + 8) * view.scale / 2, 0, Math.PI * 2); ctx.fillStyle = "rgba(99,102,241,0.45)"; ctx.fill(); }
      else { ctx.moveTo(pts[0].x, pts[0].y); for (const pt of pts.slice(1)) ctx.lineTo(pt.x, pt.y); ctx.stroke(); }
      ctx.restore();
    }
    ctx.strokeStyle = d.color;
    if (pts.length === 1) {
      ctx.beginPath();
      ctx.arc(pts[0].x, pts[0].y, (d.width * wmul * view.scale) / 2, 0, Math.PI * 2);
      ctx.fillStyle = d.color;
      ctx.fill();
      return;
    }
    // Zoomed out the per-segment pressure taper is sub-pixel, so draw the whole
    // polyline as ONE path (a single stroke() call) — dramatically cheaper when
    // there are many strokes. Up close, keep the per-segment width for the nice
    // tapered handwriting look.
    if (view.scale < 0.5) {
      ctx.lineWidth = Math.max(0.6, d.width * wmul * view.scale);
      ctx.beginPath();
      ctx.moveTo(pts[0].x, pts[0].y);
      for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
      ctx.stroke();
      return;
    }
    for (let i = 1; i < pts.length; i++) {
      const a = pts[i - 1];
      const b = pts[i];
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.lineWidth = Math.max(0.6, d.width * wmul * view.scale * (0.35 + 1.3 * b.p));
      ctx.stroke();
    }
  }

  function sizeCanvas(cv, ctx, r) {
    const dpr = window.devicePixelRatio || 1;
    const w = Math.round(r.width * dpr);
    const h = Math.round(r.height * dpr);
    if (cv.width !== w || cv.height !== h) {
      cv.width = w;
      cv.height = h;
      cv.style.width = r.width + "px";
      cv.style.height = r.height + "px";
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  // ----------------------------------------------------------------------
  // Node drag
  // ----------------------------------------------------------------------
  function captureStrokePoints() {
    const map = new Map();
    for (const id of selectedStrokeIds) {
      const d = STATE.drawings.find((x) => x.id === id);
      if (d) map.set(id, d.points.map((p) => ({ ...p })));
    }
    return map;
  }

  async function commitStrokeMove(origMap, dx, dy) {
    drawBusy = true; // keep the moved strokes from snapping back on a mid-save broadcast
    try {
      for (const [id, origPts] of origMap) {
        const newPts = origPts.map((p) => ({ ...p, x: p.x + dx, y: p.y + dy }));
        const d = STATE.drawings.find((x) => x.id === id);
        if (d) d.points = newPts; // update local state too
        await api(`/api/drawings/${id}`, "PATCH", { points: newPts });
      }
      strokeDragOffset = null;
      drawFx();
    } finally {
      endDrawBusy();
    }
  }

  // ----------------------------------------------------------------------
  // Resize / scale the current selection (strokes OR nodes)
  // ----------------------------------------------------------------------
  // Screen-space bounding box of the active selection (accounts for a live
  // stroke-resize preview), or null when nothing is selected.
  function selectionScreenBBox() {
    const canvasRect = canvas.getBoundingClientRect();
    const rs = strokeResize;
    let x1 = Infinity, y1 = Infinity, x2 = -Infinity, y2 = -Infinity, any = false;
    if (selectTarget === "nodes" && selectedIds.size) {
      for (const id of selectedIds) {
        const el = nodeEls.get(id);
        if (!el) continue;
        const r = el.getBoundingClientRect();
        const ax1 = r.left - canvasRect.left, ay1 = r.top - canvasRect.top;
        const ax2 = r.right - canvasRect.left, ay2 = r.bottom - canvasRect.top;
        if (ax1 < x1) x1 = ax1; if (ay1 < y1) y1 = ay1;
        if (ax2 > x2) x2 = ax2; if (ay2 > y2) y2 = ay2;
        any = true;
      }
    } else if (selectTarget === "strokes" && selectedStrokeIds.size) {
      for (const id of selectedStrokeIds) {
        const d = STATE.drawings.find((x) => x.id === id);
        if (!d || !d.points || !d.points.length) continue;
        const pad = ((d.width || 2) * (rs ? rs.s : 1) * view.scale) / 2 + 2;
        for (const p of d.points) {
          let wx = p.x, wy = p.y;
          if (rs) { wx = rs.pivot.x + (wx - rs.pivot.x) * rs.s; wy = rs.pivot.y + (wy - rs.pivot.y) * rs.s; }
          const s = worldToScreen(wx, wy);
          if (s.x - pad < x1) x1 = s.x - pad; if (s.y - pad < y1) y1 = s.y - pad;
          if (s.x + pad > x2) x2 = s.x + pad; if (s.y + pad > y2) y2 = s.y + pad;
          any = true;
        }
      }
    }
    if (!any) return null;
    return { x1, y1, x2, y2 };
  }

  // Position the resize box + handles over the selection (hidden while busy).
  function renderResizeBox() {
    const box = $("#resize-box");
    if (!box) return;
    const busy = lasso || drag || pan || stroke || reparentDrag;
    const bb = (mode === "select" && !busy) ? selectionScreenBBox() : null;
    if (!bb || (bb.x2 - bb.x1 < 6 && bb.y2 - bb.y1 < 6)) { box.hidden = true; return; }
    box.hidden = false;
    box.style.left = bb.x1 + "px";
    box.style.top = bb.y1 + "px";
    box.style.width = (bb.x2 - bb.x1) + "px";
    box.style.height = (bb.y2 - bb.y1) + "px";
  }

  function startResize(corner, e) {
    e.preventDefault();
    e.stopPropagation();
    const bb = selectionScreenBBox();
    if (!bb) return;
    const corners = {
      nw: { x: bb.x1, y: bb.y1 }, ne: { x: bb.x2, y: bb.y1 },
      sw: { x: bb.x1, y: bb.y2 }, se: { x: bb.x2, y: bb.y2 },
    };
    const oppOf = { nw: "se", ne: "sw", sw: "ne", se: "nw" };
    const pivotS = corners[oppOf[corner]];
    const grabS = corners[corner];
    const pivotW = screenToWorld(pivotS.x, pivotS.y);
    const grabDist = Math.hypot(grabS.x - pivotS.x, grabS.y - pivotS.y) || 1;
    const origStrokes = new Map();
    const origNodes = new Map();
    if (selectTarget === "strokes") {
      for (const id of selectedStrokeIds) {
        const d = STATE.drawings.find((x) => x.id === id);
        if (d) origStrokes.set(id, { points: d.points.map((p) => ({ ...p })), width: d.width || 2 });
      }
    } else {
      for (const id of selectedIds) {
        const n = STATE.nodes.find((x) => x.id === id);
        if (n) origNodes.set(id, { x: n.x, y: n.y });
      }
    }
    resizing = { corner, pivotS, pivotW, grabDist, origStrokes, origNodes, s: 1 };
    canvas.setPointerCapture?.(e.pointerId);
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp, { once: true });
  }

  function onResizeMove(e) {
    if (!resizing) return;
    const p = eventCanvasPos(e);
    let s = Math.hypot(p.x - resizing.pivotS.x, p.y - resizing.pivotS.y) / resizing.grabDist;
    s = Math.max(0.05, Math.min(s, 20)); // clamp to sane range
    resizing.s = s;
    if (selectTarget === "strokes") {
      strokeResize = { pivot: resizing.pivotW, s };
      drawFx();
    } else {
      for (const [id, orig] of resizing.origNodes) {
        const n = STATE.nodes.find((x) => x.id === id);
        if (!n) continue;
        n.x = Math.round(resizing.pivotW.x + (orig.x - resizing.pivotW.x) * s);
        n.y = Math.round(resizing.pivotW.y + (orig.y - resizing.pivotW.y) * s);
        const el = nodeEls.get(id);
        if (el) { el.style.left = n.x + "px"; el.style.top = n.y + "px"; }
      }
      drawEdges(computeHidden());
    }
    renderResizeBox();
  }

  async function onResizeUp() {
    const rz = resizing;
    resizing = null;
    if (!rz) return;
    drawBusy = true; // hold broadcasts until the scaled geometry is saved
    justMarqueed = true; // keep the selection: skip the click that follows pointerup
    const s = rz.s || 1;
    const changedScale = Math.abs(s - 1) > 0.002;
    try {
      if (selectTarget === "strokes") {
        strokeResize = null;
        if (changedScale) {
          for (const [id, orig] of rz.origStrokes) {
            const newPts = orig.points.map((p) => ({
              ...p,
              x: rz.pivotW.x + (p.x - rz.pivotW.x) * s,
              y: rz.pivotW.y + (p.y - rz.pivotW.y) * s,
            }));
            const newWidth = Math.max(0.5, orig.width * s);
            const d = STATE.drawings.find((x) => x.id === id);
            if (d) { d.points = newPts; d.width = newWidth; }
            await api(`/api/drawings/${id}`, "PATCH", { points: newPts, width: newWidth });
          }
        }
        drawFx();
      } else if (changedScale) {
        for (const [id] of rz.origNodes) {
          const n = STATE.nodes.find((x) => x.id === id);
          if (n) await api(`/api/nodes/${id}`, "PATCH", { x: n.x, y: n.y });
        }
      }
      render(); drawFx();
    } finally {
      endDrawBusy();
    }
  }

  function onNodePointerDown(e, id) {
    if (e.button === 2) return; // right-click is reserved for the edit context menu
    if (e.target.closest("a")) return; // let link clicks through
    const txt = e.target.closest(".node-text");
    if (txt && txt.getAttribute("contenteditable") === "true") return; // editing
    if (e.target.closest(".handle")) return;
    // Space held = pan the camera, even when the press lands on a node (so you
    // can still pan when zoomed in and nodes cover the screen). Don't move it.
    if (spaceDown) { e.stopPropagation(); startPan(e); return; }
    if (mode === "draw") return; // let fx capture
    e.stopPropagation();
    const n = STATE.nodes.find((x) => x.id === id);
    if (!n) return;
    const start = eventCanvasPos(e);
    const isMulti = selectedIds.has(id) && selectedIds.size > 1;
    const origPositions = isMulti
      ? [...selectedIds].map((nid) => { const mn = STATE.nodes.find((x) => x.id === nid); return mn ? { id: nid, x: mn.x, y: mn.y } : null; }).filter(Boolean)
      : [];
    // Node drags move ONLY nodes — strokes are a separate select target now.
    drag = { id, startX: start.x, startY: start.y, origX: n.x, origY: n.y, moved: false, multi: isMulti, origPositions };
    canvas.setPointerCapture?.(e.pointerId);
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp, { once: true });
  }

  // ----------------------------------------------------------------------
  // Canvas pan / draw start
  // ----------------------------------------------------------------------
  // Begin a camera pan from this pointer (middle/right button, or Space held).
  function startPan(e) {
    const p = eventCanvasPos(e);
    pan = { x: p.x, y: p.y, vx: view.x, vy: view.y };
    canvas.classList.add("panning");
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp, { once: true });
  }

  // Cheap per-frame repaint for pan AND zoom: the nodes/images/boxes live inside
  // #world and ride its CSS transform (translate + scale) for free, so we only
  // update the transform and repaint the two screen-space canvases (edges +
  // strokes). This skips the whole per-node DOM reconciliation render() does —
  // that, plus the now reflow-free drawEdges, is what keeps pan/zoom smooth.
  // rAF-throttled so a burst of wheel/pointer events collapses to one repaint.
  let viewportRaf = 0;
  function applyViewport() {
    viewportRaf = 0;
    world.style.transform = `translate(${view.x}px, ${view.y}px) scale(${view.scale})`;
    $("#zoom-label").textContent = Math.round(view.scale * 100) + "%";
    if (typeof updateEraserCursor === "function") updateEraserCursor();
    drawEdges(computeHidden());
    flushFx(); // paint strokes in this same frame (don't lag the edges by one)
    renderResizeBox(); // keep the selection handles glued to the moving content
    scheduleReportViewport(); // tell the server which world-area is on screen
  }
  function scheduleViewport() {
    if (!viewportRaf) viewportRaf = requestAnimationFrame(applyViewport);
  }

  // ---- Current viewport → server ---------------------------------------
  // Report the world-rect the user is currently viewing so server-side
  // auto-placement drops new nodes/images where they can see them, and Claude
  // can read it via get_mindmap. Debounced: only POSTs after the view settles.
  function currentViewport() {
    const r = canvas.getBoundingClientRect();
    const tl = screenToWorld(0, 0);
    const br = screenToWorld(r.width, r.height);
    const c = screenToWorld(r.width / 2, r.height / 2);
    return {
      x: view.x, y: view.y, scale: view.scale,
      cx: c.x, cy: c.y,
      minX: tl.x, minY: tl.y, maxX: br.x, maxY: br.y,
      w: br.x - tl.x, h: br.y - tl.y,
    };
  }
  let reportViewportTimer = 0;
  function reportViewport() {
    reportViewportTimer = 0;
    api("/api/viewport", "POST", currentViewport()).catch(() => {});
  }
  function scheduleReportViewport() {
    if (reportViewportTimer) clearTimeout(reportViewportTimer);
    reportViewportTimer = setTimeout(reportViewport, 350);
    scheduleScreenshot();
  }

  let screenshotTimer = 0;
  function scheduleScreenshot() {
    clearTimeout(screenshotTimer);
    screenshotTimer = setTimeout(captureScreenshot, 2500);
  }
  async function captureScreenshot() {
    if (!window.html2canvas) return;
    try {
      const el = document.getElementById("canvas");
      const cvs = await html2canvas(el, { useCORS: true, scale: 1, logging: false, backgroundColor: "#1a1a2e" });
      const dataUrl = cvs.toDataURL("image/jpeg", 0.85);
      fetch("/api/screenshot", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ dataUrl }) }).catch(() => {});
    } catch (_) {}
  }

  // Full-map capture — triggered by the server (Claude's get_full_map MCP).
  // Temporarily fit ALL nodes into view, snapshot, then restore the user's view
  // so it doesn't disturb where they were looking.
  async function captureFullMap(reqId) {
    if (!window.html2canvas) { fetch("/api/fullmap", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ reqId, error: "no html2canvas" }) }).catch(() => {}); return; }
    const saved = { x: view.x, y: view.y, scale: view.scale };
    try {
      fitView();
      await new Promise((r) => setTimeout(r, 300)); // let transform + edges settle
      const el = document.getElementById("canvas");
      const cvs = await html2canvas(el, { useCORS: true, scale: 1.2, logging: false, backgroundColor: "#1a1a2e" });
      const dataUrl = cvs.toDataURL("image/jpeg", 0.85);
      fetch("/api/fullmap", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ reqId, dataUrl }) }).catch(() => {});
    } catch (e) {
      fetch("/api/fullmap", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ reqId, error: String(e) }) }).catch(() => {});
    } finally {
      view.x = saved.x; view.y = saved.y; view.scale = saved.scale;
      render();
    }
  }
  window.__captureFullMap = captureFullMap;

  canvas.addEventListener("pointerdown", (e) => {
    if (e.target.closest(".node")) return;
    // AI Box draw armed: left-drag traces the region rectangle.
    if (pendingAiBox && e.button === 0 && !spaceDown) {
      if (e.target.closest(".hbox")) { disarmAiBox(); return; }
      startAiBoxDraw(e);
      return;
    }
    if (mode === "draw" && e.button === 0 && !spaceDown) {
      startStroke(e);
      return;
    }
    const wantPan = e.button === 1 || e.button === 2 || spaceDown;
    if (wantPan) {
      startPan(e);
    } else if (mode === "select" && e.button === 0) {
      const p = eventCanvasPos(e);
      if (selectedStrokeIds.size > 0 && selectedIds.size === 0) {
        // stroke-only drag: move selected strokes
        drag = { strokeOnly: true, startX: p.x, startY: p.y, moved: false,
          origStrokePoints: captureStrokePoints() };
      } else {
        // Topics use a rectangle marquee (เหมือนเดิม); strokes keep the freeform
        // lasso. Both store screen-space points so pointInPolygon works for either.
        lasso = { pts: [{ x: p.x, y: p.y }], anchor: { x: p.x, y: p.y }, rect: selectTarget === "nodes" };
      }
      window.addEventListener("pointermove", onPointerMove);
      window.addEventListener("pointerup", onPointerUp, { once: true });
    }
  });

  canvas.addEventListener("click", (e) => {
    if (justMarqueed) { justMarqueed = false; return; }
    if (!e.target.closest(".node") && !e.target.closest(".img-obj") && !e.target.closest(".hbox")) {
      selectedId = null;
      selectedIds = new Set();
      selectedStrokeIds = new Set();
      selectedImgId = null;
      selectedBoxId = null;
      render();
      drawFx();
    }
  });

  // Paste an image from the clipboard (Ctrl+V) anywhere on the page.
  window.addEventListener("paste", (e) => {
    const items = e.clipboardData?.items || [];
    for (const it of items) {
      if (it.type && it.type.startsWith("image/")) {
        const file = it.getAsFile();
        if (file) {
          e.preventDefault();
          fileToImage(file, null); // drop at view center
          toast("วางรูปแล้ว ✓");
          return;
        }
      }
    }
  });

  // Drag-and-drop image files onto the canvas.
  canvas.addEventListener("dragover", (e) => {
    if (e.dataTransfer?.types?.includes("Files")) {
      e.preventDefault();
      e.dataTransfer.dropEffect = "copy";
    }
  });
  canvas.addEventListener("drop", (e) => {
    const files = e.dataTransfer?.files;
    if (files && files.length) {
      e.preventDefault();
      const pt = eventCanvasPos(e);
      for (const f of files) fileToImage(f, pt);
      toast("วางรูปแล้ว ✓");
    }
  });

  canvas.addEventListener("dblclick", async (e) => {
    if (mode !== "select") return;
    // Double-click on existing node → edit it.
    const nodeEl = e.target.closest(".node");
    if (nodeEl) {
      beginEditNode(nodeEl.querySelector(".node-text"));
      return;
    }
    // Double-click on empty canvas → create new node.
    const p = eventCanvasPos(e);
    const w = screenToWorld(p.x, p.y);
    const node = await api("/api/nodes", "POST", { text: "", x: Math.round(w.x), y: Math.round(w.y) });
    if (node) {
      selectedId = node.id;
      setTimeout(() => {
        const el = nodeEls.get(node.id);
        if (el) beginEditNode(el.querySelector(".node-text"));
      }, 60);
    }
  });

  function onPointerMove(e) {
    if (drag) {
      const p = eventCanvasPos(e);
      const dx = (p.x - drag.startX) / view.scale;
      const dy = (p.y - drag.startY) / view.scale;
      if (Math.abs(p.x - drag.startX) + Math.abs(p.y - drag.startY) > 3) drag.moved = true;
      if (drag.strokeOnly) {
        strokeDragOffset = { dx, dy };
        drawFx();
      } else if (drag.multi) {
        for (const orig of drag.origPositions) {
          const mn = STATE.nodes.find((x) => x.id === orig.id);
          if (!mn) continue;
          mn.x = Math.round(orig.x + dx);
          mn.y = Math.round(orig.y + dy);
          const mel = nodeEls.get(mn.id);
          if (mel) { mel.style.left = mn.x + "px"; mel.style.top = mn.y + "px"; mel.classList.add("dragging"); }
        }
        if (drag.origStrokePoints) strokeDragOffset = { dx, dy };
        drawEdges(computeHidden());
        drawFx();
      } else {
        const n = STATE.nodes.find((x) => x.id === drag.id);
        if (n) {
          n.x = Math.round(drag.origX + dx);
          n.y = Math.round(drag.origY + dy);
          const el = nodeEls.get(n.id);
          if (el) {
            el.style.left = n.x + "px";
            el.style.top = n.y + "px";
            el.classList.add("dragging");
          }
          if (drag.origStrokePoints) strokeDragOffset = { dx, dy };
          drawEdges(computeHidden());
          drawFx();
        }
      }
    } else if (lasso) {
      const p = eventCanvasPos(e);
      if (lasso.rect) {
        // rectangle from the anchor to the cursor (4 corners → still a polygon)
        const a = lasso.anchor;
        lasso.pts = [{ x: a.x, y: a.y }, { x: p.x, y: a.y }, { x: p.x, y: p.y }, { x: a.x, y: p.y }];
        drawFx();
      } else {
        const last = lasso.pts[lasso.pts.length - 1];
        // sample only when the pointer has moved a little (keeps the path light)
        if (!last || Math.abs(p.x - last.x) + Math.abs(p.y - last.y) > 2) {
          lasso.pts.push({ x: p.x, y: p.y });
          drawFx();
        }
      }
    } else if (resizing) {
      onResizeMove(e);
    } else if (pan) {
      const p = eventCanvasPos(e);
      view.x = pan.vx + (p.x - pan.x);
      view.y = pan.vy + (p.y - pan.y);
      scheduleViewport();
    } else if (stroke) {
      addStrokePoint(e);
    }
  }

  function onPointerUp() {
    if (drag) {
      const wdx = strokeDragOffset?.dx ?? 0;
      const wdy = strokeDragOffset?.dy ?? 0;
      if (drag.strokeOnly) {
        if (drag.moved && drag.origStrokePoints) commitStrokeMove(drag.origStrokePoints, wdx, wdy);
        else { strokeDragOffset = null; drawFx(); }
      } else if (drag.multi && drag.moved) {
        for (const orig of drag.origPositions) {
          const mn = STATE.nodes.find((x) => x.id === orig.id);
          if (mn) api(`/api/nodes/${orig.id}`, "PATCH", { x: mn.x, y: mn.y });
          const mel = nodeEls.get(orig.id);
          if (mel) mel.classList.remove("dragging");
        }
        if (drag.origStrokePoints) commitStrokeMove(drag.origStrokePoints, wdx, wdy);
        else { strokeDragOffset = null; }
      } else {
        const n = STATE.nodes.find((x) => x.id === drag.id);
        const el = nodeEls.get(drag.id);
        if (el) el.classList.remove("dragging");
        if (n && drag.moved) {
          api(`/api/nodes/${drag.id}`, "PATCH", { x: n.x, y: n.y });
          if (drag.origStrokePoints) commitStrokeMove(drag.origStrokePoints, wdx, wdy);
          else { strokeDragOffset = null; }
        } else { strokeDragOffset = null; }
      }
      drag = null;
    }
    if (lasso) {
      const poly = lasso.pts;
      lasso = null;
      // bounding box of the path — ignore tiny taps (treat as a click/deselect)
      let lminX = Infinity, lminY = Infinity, lmaxX = -Infinity, lmaxY = -Infinity;
      for (const pt of poly) {
        if (pt.x < lminX) lminX = pt.x; if (pt.x > lmaxX) lmaxX = pt.x;
        if (pt.y < lminY) lminY = pt.y; if (pt.y > lmaxY) lmaxY = pt.y;
      }
      if (poly.length >= 3 && (lmaxX - lminX > 6 || lmaxY - lminY > 6)) {
        const hidden = computeHidden();
        const canvasRect = canvas.getBoundingClientRect();
        // Separate features: a lasso grabs ONLY nodes OR ONLY strokes,
        // depending on the active select target (toggle in the toolbar).
        selectedIds = new Set();
        selectedStrokeIds = new Set();
        if (selectTarget === "nodes") {
          for (const n of STATE.nodes) {
            if (hidden.has(n.id)) continue;
            const el = nodeEls.get(n.id);
            let cx, cy;
            if (el) {
              const r = el.getBoundingClientRect();
              cx = (r.left + r.right) / 2 - canvasRect.left;
              cy = (r.top + r.bottom) / 2 - canvasRect.top;
            } else {
              const s = worldToScreen(n.x, n.y); cx = s.x; cy = s.y;
            }
            if (pointInPolygon(cx, cy, poly)) selectedIds.add(n.id);
          }
        } else {
          // a stroke is selected if any of its points falls inside the loop
          for (const d of STATE.drawings) {
            if (!d.points || !d.points.length) continue;
            let hit = false;
            for (const pt of d.points) {
              const s = worldToScreen(pt.x, pt.y);
              if (pointInPolygon(s.x, s.y, poly)) { hit = true; break; }
            }
            if (hit) selectedStrokeIds.add(d.id);
          }
        }
        if (selectedIds.size > 0 || selectedStrokeIds.size > 0) {
          selectedId = null; justMarqueed = true;
        }
      }
      render(); drawFx();
    }
    if (resizing) { onResizeUp(); }
    if (pan) {
      pan = null;
      canvas.classList.remove("panning");
    }
    if (stroke) endStroke();
    renderResizeBox(); // refresh the scale box after any drag/move
    window.removeEventListener("pointermove", onPointerMove);
  }

  // ----------------------------------------------------------------------
  // Drag-to-reparent
  // ----------------------------------------------------------------------
  function nodeAtScreenPoint(sx, sy) {
    for (const [id, el] of nodeEls) {
      const r = el.getBoundingClientRect();
      const cr = canvas.getBoundingClientRect();
      const ex = r.left - cr.left, ey = r.top - cr.top;
      if (sx >= ex && sx <= ex + r.width && sy >= ey && sy <= ey + r.height) return id;
    }
    return null;
  }

  function onReparentMove(e) {
    if (!reparentDrag) return;
    const r = canvas.getBoundingClientRect();
    reparentDrag.ex = e.clientX - r.left;
    reparentDrag.ey = e.clientY - r.top;
    const hit = nodeAtScreenPoint(reparentDrag.ex, reparentDrag.ey);
    const prev = reparentDrag.targetId;
    reparentDrag.targetId = (hit && hit !== reparentDrag.fromId) ? hit : null;
    if (prev !== reparentDrag.targetId) {
      if (prev) nodeEls.get(prev)?.classList.remove("reparent-target");
      if (reparentDrag.targetId) nodeEls.get(reparentDrag.targetId)?.classList.add("reparent-target");
    }
    drawFx();
  }

  function onReparentUp() {
    if (!reparentDrag) return;
    if (reparentDrag.targetId) {
      nodeEls.get(reparentDrag.targetId)?.classList.remove("reparent-target");
      api(`/api/nodes/${reparentDrag.fromId}`, "PATCH", { parentId: reparentDrag.targetId });
    }
    reparentDrag = null;
    drawFx();
    window.removeEventListener("pointermove", onReparentMove);
  }

  // ----------------------------------------------------------------------
  // Zoom (wheel toward cursor)
  // ----------------------------------------------------------------------
  canvas.addEventListener(
    "wheel",
    (e) => {
      e.preventDefault();
      const p = eventCanvasPos(e);
      const before = screenToWorld(p.x, p.y);
      const factor = e.deltaY < 0 ? 1.12 : 1 / 1.12;
      view.scale = Math.min(3, Math.max(0.15, view.scale * factor));
      const after = screenToWorld(p.x, p.y);
      view.x += (after.x - before.x) * view.scale;
      view.y += (after.y - before.y) * view.scale;
      // View math runs per-event (so zoom-toward-cursor stays accurate); the
      // repaint is rAF-throttled and skips node reconciliation like panning.
      scheduleViewport();
    },
    { passive: false }
  );

  canvas.addEventListener("contextmenu", (e) => {
    e.preventDefault();
    const nodeEl = e.target.closest(".node");
    if (nodeEl) { beginEditNode(nodeEl.querySelector(".node-text")); return; }
    if (e.target.closest(".hbox")) return;
    if (mode === "select") showCanvasMenu(e);
  });

  function removeContextMenu() {
    const m = document.querySelector(".ctx-menu");
    if (m) { if (m._closeHandler) document.removeEventListener("pointerdown", m._closeHandler); m.remove(); }
  }

  function showCanvasMenu(e) {
    removeContextMenu();
    const pos = eventCanvasPos(e);
    const wpos = screenToWorld(pos.x, pos.y);
    const menu = document.createElement("div");
    menu.className = "ctx-menu";
    menu.style.cssText = `left:${e.clientX}px;top:${e.clientY}px;`;

    const addHead = (txt) => {
      const head = document.createElement("div");
      head.className = "ctx-head";
      head.textContent = txt;
      menu.appendChild(head);
    };
    const addItem = (txt, onClick) => {
      const item = document.createElement("div");
      item.className = "ctx-item";
      item.textContent = txt;
      item.addEventListener("click", () => { removeContextMenu(); onClick(); });
      menu.appendChild(item);
    };

    // AI Box — arm draw mode; user then drags a rectangle region for Claude.
    addItem("🤖 AI Box — ลากเลือกพื้นที่ให้ AI", () => armAiBoxDraw());

    const others = PROJECTS.filter((p) => p.id !== ACTIVE_ID);
    if (others.length) {
      addHead("สร้าง Portal ไปยัง…");
      others.forEach((p) => {
        addItem("🔀 " + p.title, () => {
          api("/api/boxes", "POST", { kind: "portal", x: Math.round(wpos.x), y: Math.round(wpos.y), w: 200, h: 80, title: p.title, targetProjectId: p.id });
        });
      });
    }

    document.body.appendChild(menu);
    const closeHandler = (ev) => { if (!menu.contains(ev.target)) { removeContextMenu(); } };
    menu._closeHandler = closeHandler;
    setTimeout(() => document.addEventListener("pointerdown", closeHandler), 0);
  }

  // ----------------------------------------------------------------------
  // AI Box — a rectangle region the user drags to scope an AI command.
  // ----------------------------------------------------------------------
  let pendingAiBox = false; // armed: next left-drag draws the region rect
  let aiboxDraw = null;     // active drag: { sx, sy } screen anchor

  function armAiBoxDraw() {
    pendingAiBox = true;
    canvas.classList.add("aibox-arming");
    toast("ลากเมาส์ซ้ายเพื่อวาดกรอบ AI Box 🤖");
  }
  function disarmAiBox() {
    pendingAiBox = false;
    canvas.classList.remove("aibox-arming");
  }

  function startAiBoxDraw(e) {
    const p = eventCanvasPos(e);
    aiboxDraw = { sx: p.x, sy: p.y };
    marqueeEl.style.display = "block";
    marqueeEl.style.left = p.x + "px";
    marqueeEl.style.top = p.y + "px";
    marqueeEl.style.width = "0px";
    marqueeEl.style.height = "0px";
    window.addEventListener("pointermove", onAiBoxDrawMove);
    window.addEventListener("pointerup", onAiBoxDrawUp, { once: true });
  }
  function onAiBoxDrawMove(e) {
    if (!aiboxDraw) return;
    const p = eventCanvasPos(e);
    const l = Math.min(p.x, aiboxDraw.sx), t = Math.min(p.y, aiboxDraw.sy);
    const w = Math.abs(p.x - aiboxDraw.sx), h = Math.abs(p.y - aiboxDraw.sy);
    marqueeEl.style.left = l + "px";
    marqueeEl.style.top = t + "px";
    marqueeEl.style.width = w + "px";
    marqueeEl.style.height = h + "px";
  }
  async function onAiBoxDrawUp(e) {
    window.removeEventListener("pointermove", onAiBoxDrawMove);
    marqueeEl.style.display = "none";
    const d = aiboxDraw;
    aiboxDraw = null;
    disarmAiBox();
    if (!d) return;
    const p = eventCanvasPos(e);
    const a = screenToWorld(Math.min(p.x, d.sx), Math.min(p.y, d.sy));
    const b = screenToWorld(Math.max(p.x, d.sx), Math.max(p.y, d.sy));
    const w = Math.round(b.x - a.x), h = Math.round(b.y - a.y);
    if (w < 24 || h < 24) { toast("กรอบเล็กไป — ลองวาดใหม่"); return; }
    const n = (STATE.boxes || []).filter((x) => x.kind === "aibox").length + 1;
    await api("/api/boxes", "POST", {
      kind: "aibox",
      x: Math.round(a.x), y: Math.round(a.y), w, h,
      title: "AI " + n,
    });
    toast("สร้าง AI Box แล้ว — พูดสั่งงานในกรอบนี้ได้เลย 🎙️");
  }

  // ----------------------------------------------------------------------
  // Freehand stroke
  // ----------------------------------------------------------------------
  function startStroke(e) {
    fxCanvas.setPointerCapture?.(e.pointerId);
    const p = eventCanvasPos(e);
    const w = screenToWorld(p.x, p.y);
    drawBusy = true; // hold off broadcasts until this gesture is saved
    if (eraser) {
      eraseDelete = new Set();
      lastEraseW = w;
      eraseAt(w);
      // keep erasing on move
      stroke = { eraser: true };
      window.addEventListener("pointermove", onEraseMove);
      window.addEventListener("pointerup", onEraseUp, { once: true });
      return;
    }
    stroke = {
      color: $("#pen-color").value,
      width: Number($("#pen-size").value),
      points: [{ x: w.x, y: w.y, p: e.pressure || 0.5 }],
    };
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp, { once: true });
  }
  function addStrokePoint(e) {
    // Pull every sub-sample the browser coalesced into this event so fast pen
    // movement keeps its detail, while the actual paint still happens once per
    // frame (drawFx is rAF-throttled).
    const evs = e.getCoalescedEvents ? e.getCoalescedEvents() : null;
    for (const ev of (evs && evs.length ? evs : [e])) {
      const p = eventCanvasPos(ev);
      const w = screenToWorld(p.x, p.y);
      stroke.points.push({ x: w.x, y: w.y, p: ev.pressure || 0.5 });
    }
    drawFx();
  }
  function endStroke() {
    const s = stroke;
    stroke = null;
    window.removeEventListener("pointermove", onPointerMove);
    if (s && s.points && s.points.length > 0) {
      // Show it immediately (optimistic) so the stroke doesn't blink out while the
      // POST round-trips. Track it as in-flight until a broadcast confirms it, so
      // an out-of-order broadcast can't wipe it in the meantime.
      const tmpId = "tmp-" + tmpCounter++;
      s.id = tmpId;
      STATE.drawings.push(s);
      inflightStrokes.set(tmpId, s);
      drawFx();
      api("/api/drawings", "POST", { color: s.color, width: s.width, points: s.points })
        .then((real) => {
          if (real && real.id) {
            // Adopt the server id (same object) so the confirming broadcast matches
            // and retires it; until then it stays pinned via inflightStrokes.
            inflightStrokes.delete(tmpId);
            s.id = real.id;
            inflightStrokes.set(real.id, s);
          } else {
            // Save failed — drop the optimistic stroke instead of pinning it forever.
            inflightStrokes.delete(tmpId);
            STATE.drawings = STATE.drawings.filter((d) => d !== s);
          }
        })
        .catch(() => {
          inflightStrokes.delete(tmpId);
          STATE.drawings = STATE.drawings.filter((d) => d !== s);
        })
        .finally(endDrawBusy);
    } else {
      endDrawBusy();
    }
  }
  function onEraseMove(e) {
    const p = eventCanvasPos(e);
    const w = screenToWorld(p.x, p.y);
    const thr = Number($("#eraser-size").value) / view.scale;
    // Interpolate between samples so fast drags erase a continuous path, not dots.
    if (lastEraseW) {
      const dist = Math.hypot(w.x - lastEraseW.x, w.y - lastEraseW.y);
      const steps = Math.max(1, Math.ceil(dist / Math.max(thr * 0.5, 0.5)));
      for (let k = 1; k <= steps; k++) {
        const t = k / steps;
        eraseAt({ x: lastEraseW.x + (w.x - lastEraseW.x) * t, y: lastEraseW.y + (w.y - lastEraseW.y) * t });
      }
    } else {
      eraseAt(w);
    }
    lastEraseW = w;
  }
  async function onEraseUp() {
    stroke = null;
    lastEraseW = null;
    window.removeEventListener("pointermove", onEraseMove);
    // Persist the erase: delete touched originals, create the surviving pieces.
    const dels = [...eraseDelete];
    eraseDelete = new Set();
    const news = STATE.drawings.filter((d) => d._new);
    try {
      for (const id of dels) await api(`/api/drawings/${id}`, "DELETE");
      for (const d of news) {
        await api("/api/drawings", "POST", {
          color: d.color,
          width: d.width,
          points: d.points,
        });
      }
    } finally {
      endDrawBusy();
    }
  }

  // Split a polyline by an eraser circle (cx,cy,thr). Walks each segment in small
  // steps so the eraser catches the line BETWEEN stored points too — without that,
  // fast strokes (sparse points) slip past the cursor and "don't erase enough".
  // Survivors keep the original point objects (pressure preserved), so no bloat.
  // Returns null when untouched, [] when fully erased, else surviving point-arrays.
  function erasePolyline(pts, cx, cy, thr, step) {
    if (!pts || !pts.length) return null;
    const inside = (x, y) => Math.hypot(x - cx, y - cy) < thr;
    if (pts.length === 1) return inside(pts[0].x, pts[0].y) ? [] : null;
    let hit = false;
    const out = [];
    let cur = [];
    const flush = () => { if (cur.length) { out.push(cur); cur = []; } };
    const keep = (pt) => { if (inside(pt.x, pt.y)) { hit = true; flush(); } else cur.push(pt); };
    keep(pts[0]);
    for (let i = 1; i < pts.length; i++) {
      const a = pts[i - 1], b = pts[i];
      const n = Math.max(1, Math.ceil(Math.hypot(b.x - a.x, b.y - a.y) / step));
      for (let k = 1; k < n; k++) {
        const t = k / n;
        if (inside(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t)) { hit = true; flush(); }
      }
      keep(b);
    }
    flush();
    return hit ? out : null;
  }

  // Paint-style eraser: split a canvas stroke into the surviving segments instead
  // of deleting the whole thing.
  function splitStrokeByErase(d, w, thr) {
    const pieces = erasePolyline(d.points, w.x, w.y, thr, Math.max(thr * 0.5, 0.5));
    if (pieces === null) return null;
    return pieces.map((s) => ({ color: d.color, width: d.width, points: s }));
  }

  function eraseAt(w) {
    // Eraser radius comes from its own slider (screen px → world units).
    const thr = Number($("#eraser-size").value) / view.scale;
    let changed = false;
    const next = [];
    for (const d of STATE.drawings) {
      if (!d.points) {
        next.push(d);
        continue;
      }
      const pieces = splitStrokeByErase(d, w, thr);
      if (pieces === null) {
        next.push(d);
        continue;
      }
      changed = true;
      // mark a real (server-persisted) stroke for deletion; temp pieces never were saved
      if (d.id != null && !String(d.id).startsWith("tmp-")) eraseDelete.add(d.id);
      for (const pc of pieces) {
        next.push({ ...pc, id: "tmp-" + tmpCounter++, _new: true });
      }
    }
    if (changed) {
      STATE.drawings = next;
      drawFx();
    }
  }

  // Chat panel → extracted to modules/chat.js (setupChat called at bottom of file)

  // ----------------------------------------------------------------------
  // Title
  // ----------------------------------------------------------------------
  const titleInput = $("#map-title");
  function syncTitle() {
    if (document.activeElement !== titleInput && STATE.meta?.title != null) {
      titleInput.value = STATE.meta.title;
    }
  }
  titleInput.addEventListener("change", () => api("/api/meta", "PATCH", { title: titleInput.value }));

  // ----------------------------------------------------------------------
  // Projects
  // ----------------------------------------------------------------------
  const projectSelect = $("#project-select");

  function applyProjects(projects, activeId) {
    const switched = ACTIVE_ID !== null && activeId !== ACTIVE_ID;
    PROJECTS = projects || [];
    ACTIVE_ID = activeId || null;
    renderProjects();
    if (switched) {
      // fresh project loaded — drop any pending optimistic strokes from the old
      // project so they can't be re-pinned onto this one, then frame it.
      inflightStrokes.clear();
      setTimeout(fitView, 60);
    }
  }

  function renderProjects() {
    projectSelect.innerHTML = "";
    for (const p of PROJECTS) {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = p.title || "Untitled";
      if (p.id === ACTIVE_ID) opt.selected = true;
      projectSelect.appendChild(opt);
    }
  }

  projectSelect.addEventListener("change", () => {
    const id = projectSelect.value;
    if (id && id !== ACTIVE_ID) api(`/api/projects/${id}/activate`, "POST");
  });

  $("#btn-new-project").addEventListener("click", async () => {
    const title = prompt("ชื่อโปรเจกต์ใหม่:", "โปรเจกต์ใหม่");
    if (title === null) return;
    const p = await api("/api/projects", "POST", { title: title.trim() || "Untitled" });
    if (p && p.id) api(`/api/projects/${p.id}/activate`, "POST");
  });

  $("#btn-del-project").addEventListener("click", async () => {
    if (PROJECTS.length <= 1) {
      toast("ลบไม่ได้ — ต้องมีอย่างน้อย 1 โปรเจกต์");
      return;
    }
    const cur = PROJECTS.find((p) => p.id === ACTIVE_ID);
    if (!confirm(`ลบโปรเจกต์ "${cur?.title || ""}" ทั้งหมด? (ย้อนกลับไม่ได้)`)) return;
    await api(`/api/projects/${ACTIVE_ID}`, "DELETE");
  });

  // Voice (Thai) + text input → extracted to modules/voice.js (setupVoice called at bottom of file)
  // Chat section add button → extracted to modules/chat.js (setupChat called at bottom of file)

  // ----------------------------------------------------------------------
  // Toolbar
  // ----------------------------------------------------------------------
  function setEraser(on) {
    eraser = on;
    $("#btn-eraser").classList.toggle("active", on);
    $("#tool-pen").classList.toggle("active", !on);
    canvas.classList.toggle("mode-eraser", on);
    updateEraserCursor();
  }
  // Dynamic Photoshop-style ring cursor sized to the eraser radius (screen px).
  function updateEraserCursor() {
    if (!(mode === "draw" && eraser)) {
      canvas.style.cursor = "";
      return;
    }
    // Cap so the cursor image stays within the browser's ~128px limit.
    const r = Math.max(4, Math.min(60, Number($("#eraser-size").value) * view.scale));
    const d = Math.ceil(r * 2) + 2;
    const c = d / 2;
    const svg =
      `<svg xmlns="http://www.w3.org/2000/svg" width="${d}" height="${d}">` +
      `<circle cx="${c}" cy="${c}" r="${r}" fill="none" stroke="black" stroke-width="3"/>` +
      `<circle cx="${c}" cy="${c}" r="${r}" fill="none" stroke="white" stroke-width="1.5"/>` +
      `</svg>`;
    const url = `data:image/svg+xml;base64,${btoa(svg)}`;
    canvas.style.cursor = `url('${url}') ${c} ${c}, cell`;
  }
  function setMode(m) {
    mode = m;
    eraser = false;
    $("#btn-select").classList.toggle("active", m === "select");
    $("#btn-draw").classList.toggle("active", m === "draw");
    $("#btn-eraser").classList.remove("active");
    $("#tool-pen").classList.add("active");
    $("#draw-dock").hidden = m !== "draw";
    fxCanvas.classList.toggle("draw-active", m === "draw");
    canvas.classList.toggle("mode-draw", m === "draw");
    canvas.classList.remove("mode-eraser");
    canvas.style.cursor = "";
  }
  $("#btn-select").addEventListener("click", () => setMode("select"));
  $("#btn-draw").addEventListener("click", () => setMode("draw"));
  // Toggle what the marquee grabs: topics (nodes) vs strokes you drew.
  function setSelectTarget(t) {
    selectTarget = t;
    const btn = $("#btn-sel-target");
    if (btn) {
      btn.textContent = t === "strokes" ? "🎯 เส้นวาด" : "🎯 หัวข้อ";
      btn.classList.toggle("target-strokes", t === "strokes");
    }
    // Separate features: clear whichever kind we're no longer targeting.
    if (t === "strokes") { selectedIds = new Set(); selectedId = null; }
    else { selectedStrokeIds = new Set(); strokeDragOffset = null; }
    render(); drawFx();
  }
  $("#btn-sel-target").addEventListener("click", () => {
    if (mode !== "select") setMode("select");
    setSelectTarget(selectTarget === "nodes" ? "strokes" : "nodes");
  });
  // Resize-box corner handles: grab to scale the selection up/down.
  document.querySelectorAll("#resize-box .rz-handle").forEach((h) => {
    h.addEventListener("pointerdown", (e) => startResize(h.dataset.corner, e));
  });
  // Dock buttons: stop pointerdown so the canvas draw handler doesn't intercept.
  document.querySelectorAll(".dock-tool, .dock-swatch").forEach(el => {
    el.addEventListener("pointerdown", (e) => e.stopPropagation());
  });
  $("#tool-pen").addEventListener("click", () => setEraser(false));
  $("#btn-eraser").addEventListener("click", () => setEraser(!eraser));
  $("#pen-size").addEventListener("input", (e) => {
    $("#pen-size-val").textContent = e.target.value;
  });
  $("#eraser-size").addEventListener("input", (e) => {
    $("#eraser-size-val").textContent = e.target.value;
    updateEraserCursor();
  });
  $("#btn-undo-draw").addEventListener("click", () => {
    const last = STATE.drawings[STATE.drawings.length - 1];
    if (last) api(`/api/drawings/${last.id}`, "DELETE");
  });

  // Undo / redo (whole-map history, served by the backend)
  function updateHistoryButtons(h) {
    $("#btn-undo").disabled = !h.canUndo;
    $("#btn-redo").disabled = !h.canRedo;
  }
  $("#btn-undo").addEventListener("click", () => api("/api/undo", "POST"));
  $("#btn-redo").addEventListener("click", () => api("/api/redo", "POST"));

  $("#btn-add").addEventListener("click", async () => {
    const c = screenToWorld(canvas.clientWidth / 2, canvas.clientHeight / 2);
    const node = await api("/api/nodes", "POST", { text: "", x: Math.round(c.x), y: Math.round(c.y) });
    if (node) {
      selectedId = node.id;
      setTimeout(() => {
        const el = nodeEls.get(node.id);
        if (el) beginEditNode(el.querySelector(".node-text"));
      }, 60);
    }
  });

  $("#btn-fit").addEventListener("click", fitView);
  function fitView() {
    const ns = STATE.nodes;
    if (!ns.length) {
      view.x = canvas.clientWidth / 2;
      view.y = canvas.clientHeight / 2;
      view.scale = 1;
      render();
      return;
    }
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const n of ns) {
      minX = Math.min(minX, n.x);
      minY = Math.min(minY, n.y);
      maxX = Math.max(maxX, n.x + 200);
      maxY = Math.max(maxY, n.y + 60);
    }
    const pad = 80;
    const w = maxX - minX + pad * 2;
    const h = maxY - minY + pad * 2;
    const scale = Math.min(2, Math.max(0.04, Math.min(canvas.clientWidth / w, canvas.clientHeight / h)));
    view.scale = scale;
    view.x = (canvas.clientWidth - (maxX + minX) * scale) / 2;
    view.y = (canvas.clientHeight - (maxY + minY) * scale) / 2;
    render();
  }

  $("#btn-clear").addEventListener("click", () => {
    if (confirm("ล้างมายด์แมปและลายเส้นทั้งหมด?")) api("/api/clear", "POST");
  });

  // ======================================================================
  // Handwriting boxes — a paper-like node you draw inside with a pen.
  // Stroke points are stored NORMALIZED (px / page-width) so they stay
  // correct at any box size or in the fullscreen editor. Page is portrait
  // A4-ish: height = width * PAGE_ASPECT.
  // ======================================================================
  const PAGE_ASPECT = 1.414;
  const BOX_HEADER = 30;
  const RASTER_W = 1200; // resolution used for OCR / sending to Claude

  // Points are normalized: x = fraction of width (0..1), y = fraction of height
  // (0..1). Width and height scale independently so boxes can be any size.
  function strokeToPath(ctx, stroke, sx, sy) {
    const pts = stroke.points || [];
    if (!pts.length) return;
    ctx.strokeStyle = stroke.color || "#111827";
    ctx.lineWidth = Math.max(0.5, (stroke.width || 3) * (sx / 320)); // width ~ relative to a 320px page
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.beginPath();
    ctx.moveTo(pts[0].x * sx, pts[0].y * sy);
    for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x * sx, pts[i].y * sy);
    if (pts.length === 1) ctx.lineTo(pts[0].x * sx + 0.1, pts[0].y * sy + 0.1);
    ctx.stroke();
  }

  // Draw all strokes of a box onto a canvas of the given pixel size (white page).
  function paintBox(canvasEl, strokes, pxW, pxH) {
    canvasEl.width = pxW;
    canvasEl.height = pxH;
    const ctx = canvasEl.getContext("2d");
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, pxW, pxH);
    for (const s of strokes || []) strokeToPath(ctx, s, pxW, pxH);
    return ctx;
  }

  function renderBoxes() {
    const boxes = STATE.boxes || [];
    const present = new Set();
    for (const b of boxes) {
      present.add(b.id);
      let el = boxEls.get(b.id);
      if (!el || el.dataset.kind !== (b.kind || "note")) {
        if (el) { el.remove(); }
        el = createBoxEl(b);
        boxEls.set(b.id, el);
        boxesLayer.appendChild(el);
      }
      el.style.left = b.x + "px";
      el.style.top = b.y + "px";
      el.style.width = b.w + "px";
      el.classList.toggle("selected", b.id === selectedBoxId);
      el.querySelector(".box-title").textContent =
        b.title || (b.kind === "image" ? "คลังรูปภาพ" : b.kind === "portal" ? "Portal" : "บันทึกลายมือ");
      if (b.kind === "portal") {
        el.style.height = (b.h || 80) + "px";
      } else if (b.kind === "aibox") {
        el.style.height = (b.h || 200) + "px";
      } else if (b.kind === "image") {
        el.style.height = (b.h || 240) + "px";
        renderGallery(el, b);
      } else {
        const prev = el.querySelector(".box-preview");
        // only repaint preview if it's not the box currently open in the editor
        if (modalState?.boxId !== b.id) paintBox(prev, b.strokes, b.w, b.h || Math.round(b.w * PAGE_ASPECT));
      }
    }
    for (const [id, el] of boxEls) {
      if (!present.has(id)) {
        el.remove();
        boxEls.delete(id);
      }
    }
  }

  // Thumbnails + captions for an image box; each thumb links out to its URL.
  function renderGallery(el, b) {
    const grid = el.querySelector(".gallery-grid");
    const items = b.items || [];
    grid.innerHTML = "";
    if (!items.length) {
      grid.innerHTML = `<div class="gallery-empty">ยังไม่มีรูป — กด ＋ เพื่อเพิ่ม<br>หรือลากไฟล์รูปมาวางในกล่อง</div>`;
      return;
    }
    items.forEach((it, i) => {
      const cell = document.createElement("div");
      cell.className = "gallery-cell";
      const cap = it.caption ? escapeHtml(it.caption) : "";
      const link = it.url
        ? `<a class="gallery-link" href="${escapeHtml(it.url)}" target="_blank" rel="noopener" title="${escapeHtml(it.url)}">🔗 เปิดเว็บ</a>`
        : "";
      cell.innerHTML =
        `<img src="${escapeHtml(it.src)}" alt="" draggable="false" />
         <div class="gallery-cap">${cap}${link}</div>
         <button class="gallery-del" title="ลบรูปนี้">×</button>`;
      // clicking the image opens the linked page (if any)
      cell.querySelector("img").addEventListener("click", (e) => {
        e.stopPropagation();
        if (it.url) window.open(it.url, "_blank", "noopener");
      });
      // right-click → fullscreen lightbox
      cell.querySelector("img").addEventListener("contextmenu", (e) => {
        e.preventDefault();
        e.stopPropagation();
        openLightbox(it.src);
      });
      cell.querySelector(".gallery-del").addEventListener("pointerdown", (e) => e.stopPropagation());
      cell.querySelector(".gallery-del").addEventListener("click", (e) => {
        e.stopPropagation();
        const next = (b.items || []).slice();
        next.splice(i, 1);
        api(`/api/boxes/${b.id}`, "PATCH", { items: next });
      });
      grid.appendChild(cell);
    });
  }

  // Fullscreen lightbox — click backdrop or press Escape to close.
  function openLightbox(src) {
    const backdrop = document.createElement("div");
    backdrop.className = "lightbox-backdrop";
    backdrop.innerHTML = `<img class="lightbox-img" src="${escapeHtml(src)}" alt="" />`;
    const close = () => backdrop.remove();
    backdrop.addEventListener("click", close);
    backdrop.querySelector(".lightbox-img").addEventListener("click", (e) => e.stopPropagation());
    const onKey = (e) => { if (e.key === "Escape") { close(); window.removeEventListener("keydown", onKey); } };
    window.addEventListener("keydown", onKey);
    document.body.appendChild(backdrop);
  }

  function createBoxEl(b) {
    const el = document.createElement("div");
    el.className =
      "hbox" +
      (b.kind === "image" ? " hbox-image" :
       b.kind === "portal" ? " hbox-portal" :
       b.kind === "aibox" ? " hbox-aibox" : "");
    el.dataset.id = b.id;
    el.dataset.kind = b.kind || "note";

    // AI Box — a translucent region rectangle. Its body lets clicks pass through
    // to the nodes inside; only the header bar and resize handle are interactive.
    if (b.kind === "aibox") {
      el.innerHTML =
        `<div class="box-head">
           <span class="box-title"></span>
           <button class="box-btn b-del" title="ลบกรอบ AI Box">×</button>
         </div>
         <div class="aibox-body"></div>
         <div class="box-resize" title="ปรับขนาด"></div>`;
      el.querySelector(".box-head").addEventListener("pointerdown", (e) => {
        if (mode !== "select") return;
        if (e.target.closest(".box-btn")) return;
        e.stopPropagation();
        selectedBoxId = b.id;
        startBoxMove(e, b.id);
      });
      el.querySelector(".b-del").addEventListener("click", (e) => {
        e.stopPropagation();
        if (confirm("ลบกรอบ AI Box นี้?")) api(`/api/boxes/${b.id}`, "DELETE");
      });
      el.querySelector(".box-resize").addEventListener("pointerdown", (e) => { e.stopPropagation(); startBoxResize(e, b.id); });
      return el;
    }

    if (b.kind === "portal") {
      el.innerHTML =
        `<div class="box-head">
           <span class="box-title"></span>
           <button class="box-btn b-del" title="ลบกล่อง">×</button>
         </div>
         <div class="portal-body">🔀 คลิกเพื่อเปิด</div>`;
      el.querySelector(".box-head").addEventListener("pointerdown", (e) => {
        if (mode !== "select") return;
        if (e.target.closest(".box-btn")) return;
        e.stopPropagation();
        selectedBoxId = b.id;
        startBoxMove(e, b.id);
      });
      el.querySelector(".b-del").addEventListener("click", (e) => {
        e.stopPropagation();
        if (confirm("ลบกล่อง Portal นี้?")) api(`/api/boxes/${b.id}`, "DELETE");
      });
      el.querySelector(".portal-body").addEventListener("click", (e) => {
        e.stopPropagation();
        const box = (STATE.boxes || []).find((x) => x.id === b.id);
        if (box?.targetProjectId) api(`/api/projects/${box.targetProjectId}/activate`, "POST");
      });
      return el;
    }
    const tools =
      b.kind === "image"
        ? `<button class="box-btn b-link" title="โยงไปกล่องอื่น">🔗</button>
           <button class="box-btn b-addimg" title="เพิ่มรูปเข้ากล่อง">＋</button>
           <button class="box-btn b-del" title="ลบกล่อง">×</button>`
        : `<button class="box-btn b-link" title="โยงไปกล่องอื่น">🔗</button>
           <button class="box-btn b-edit" title="ขยาย/เขียน">✏️</button>
           <button class="box-btn b-del" title="ลบกล่อง">×</button>`;
    const bodyHtml =
      b.kind === "image"
        ? `<div class="gallery-grid"></div>`
        : `<canvas class="box-preview"></canvas>`;
    el.innerHTML =
      `<div class="box-head">
         <span class="box-title"></span>
         ${tools}
       </div>
       ${bodyHtml}
       <div class="box-resize" title="ปรับขนาด"></div>`;

    const head = el.querySelector(".box-head");
    head.addEventListener("pointerdown", (e) => {
      if (mode !== "select") return;
      if (e.target.closest(".box-btn")) return;
      e.stopPropagation();
      selectedBoxId = b.id;
      startBoxMove(e, b.id);
    });
    // 🔗 drag-to-connect this box to another box
    el.querySelector(".b-link").addEventListener("pointerdown", (e) => {
      e.stopPropagation();
      e.preventDefault();
      startLinkDrag(e, b.id);
    });
    el.querySelector(".b-del").addEventListener("click", (e) => {
      e.stopPropagation();
      if (confirm("ลบกล่องนี้?")) api(`/api/boxes/${b.id}`, "DELETE");
    });
    if (b.kind === "image") {
      el.querySelector(".b-addimg").addEventListener("click", (e) => { e.stopPropagation(); pickImageForBox(b.id); });
      // drag-drop image files straight into the gallery
      el.addEventListener("dragover", (e) => {
        if (e.dataTransfer?.types?.includes("Files")) { e.preventDefault(); e.stopPropagation(); }
      });
      el.addEventListener("drop", (e) => {
        if (!e.dataTransfer?.files?.length) return;
        e.preventDefault();
        e.stopPropagation();
        for (const f of e.dataTransfer.files) addFileToBox(b.id, f);
      });
    } else {
      el.querySelector(".b-edit").addEventListener("click", (e) => { e.stopPropagation(); openBox(b.id); });
      el.querySelector(".box-preview").addEventListener("dblclick", (e) => { e.stopPropagation(); openBox(b.id); });
    }
    el.querySelector(".box-resize").addEventListener("pointerdown", (e) => { e.stopPropagation(); startBoxResize(e, b.id); });
    return el;
  }

  // ----- Image-box helpers: add an image file/asset as a gallery item -----
  function pickImageForBox(boxId) {
    const inp = document.createElement("input");
    inp.type = "file";
    inp.accept = "image/*";
    inp.multiple = true;
    inp.onchange = () => { for (const f of inp.files) addFileToBox(boxId, f); };
    inp.click();
  }
  async function addFileToBox(boxId, file) {
    if (!file || !file.type.startsWith("image/")) return;
    const dataUrl = await new Promise((res) => {
      const fr = new FileReader();
      fr.onload = () => res(fr.result);
      fr.readAsDataURL(file);
    });
    // upload to /assets so the gallery holds a stable URL, not a huge data URL
    const img = await api("/api/images", "POST", { dataUrl, x: -9999, y: -9999, w: 1, h: 1 });
    if (!img) return;
    await api(`/api/images/${img.id}`, "DELETE"); // we only wanted the saved asset, not a canvas image
    addItemToBox(boxId, { src: img.src, url: "", caption: file.name.replace(/\.[^.]+$/, "") });
  }
  function addItemToBox(boxId, item) {
    const b = (STATE.boxes || []).find((x) => x.id === boxId);
    const items = (b?.items || []).concat([item]);
    return api(`/api/boxes/${boxId}`, "PATCH", { items });
  }

  // ----- Box linking (drag from 🔗 to another box) -----
  let linkDrag = null; // { from, pt:{x,y} screen }
  function startLinkDrag(e, fromId) {
    selectedBoxId = fromId;
    linkDrag = { from: fromId, pt: eventCanvasPos(e) };
    window.addEventListener("pointermove", onLinkDragMove);
    window.addEventListener("pointerup", onLinkDragUp, { once: true });
  }
  function onLinkDragMove(e) {
    if (!linkDrag) return;
    linkDrag.pt = eventCanvasPos(e);
    drawEdges(computeHidden());
  }
  function onLinkDragUp(e) {
    window.removeEventListener("pointermove", onLinkDragMove);
    const ld = linkDrag;
    linkDrag = null;
    if (!ld) return;
    const tgt = document.elementFromPoint(e.clientX, e.clientY)?.closest(".hbox, .node");
    const toId = tgt?.dataset.id;
    if (toId && toId !== ld.from) {
      api("/api/box-links", "POST", { from: ld.from, to: toId });
      toast("โยงแล้ว 🔗");
    }
    render();
  }

  function startBoxMove(e, id) {
    const b = STATE.boxes.find((x) => x.id === id);
    if (!b) return;
    const start = eventCanvasPos(e);
    boxInteract = { id, mode: "move", sx: start.x, sy: start.y, ox: b.x, oy: b.y };
    window.addEventListener("pointermove", onBoxInteract);
    window.addEventListener("pointerup", endBoxInteract, { once: true });
  }
  function startBoxResize(e, id) {
    const b = STATE.boxes.find((x) => x.id === id);
    if (!b) return;
    const start = eventCanvasPos(e);
    boxInteract = { id, mode: "resize", sx: start.x, sy: start.y, ow: b.w, oh: b.h || Math.round(b.w * PAGE_ASPECT) };
    window.addEventListener("pointermove", onBoxInteract);
    window.addEventListener("pointerup", endBoxInteract, { once: true });
  }
  function onBoxInteract(e) {
    if (!boxInteract) return;
    const b = STATE.boxes.find((x) => x.id === boxInteract.id);
    if (!b) return;
    const p = eventCanvasPos(e);
    if (boxInteract.mode === "move") {
      b.x = boxInteract.ox + (p.x - boxInteract.sx) / view.scale;
      b.y = boxInteract.oy + (p.y - boxInteract.sy) / view.scale;
    } else {
      // all box kinds resize freely (width and height independent)
      b.w = Math.max(120, boxInteract.ow + (p.x - boxInteract.sx) / view.scale);
      b.h = Math.max(120, boxInteract.oh + (p.y - boxInteract.sy) / view.scale);
    }
    render();
  }
  function endBoxInteract() {
    window.removeEventListener("pointermove", onBoxInteract);
    if (!boxInteract) return;
    const b = STATE.boxes.find((x) => x.id === boxInteract.id);
    if (b) api(`/api/boxes/${boxInteract.id}`, "PATCH", { x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.w), h: Math.round(b.h) });
    boxInteract = null;
  }

  // ---------------- Fullscreen handwriting editor ----------------
  let modalState = null; // { boxId, strokes, eraser, cur, dirty }
  const bmodal = $("#box-modal");
  const bcanvas = $("#box-canvas");
  const bctx = bcanvas.getContext("2d");

  function openBox(id) {
    const b = STATE.boxes.find((x) => x.id === id);
    if (!b) return;
    modalState = { boxId: id, strokes: JSON.parse(JSON.stringify(b.strokes || [])), eraser: false, cur: null, dirty: false };
    $("#box-modal-title").value = b.title || "";
    $("#box-ocr-result").hidden = true;
    $("#box-eraser").classList.remove("active");
    bmodal.hidden = false; // show first so the stage has a real height
    bmodalSizeCanvas();
    bmodalRedraw();
  }
  function bmodalSizeCanvas() {
    const b = STATE.boxes.find((x) => x.id === modalState.boxId);
    const bw = b ? b.w : 320;
    const bh = b ? (b.h || Math.round(b.w * PAGE_ASPECT)) : 452;
    const aspect = bh / bw; // height / width of THIS box
    const stage = $(".box-modal-stage");
    const availW = stage.clientWidth - 40;
    const availH = stage.clientHeight - 20;
    // fit the box's own aspect ratio inside the stage
    let pxW = availW;
    let pxH = pxW * aspect;
    if (pxH > availH) { pxH = availH; pxW = pxH / aspect; }
    bcanvas.style.width = pxW + "px";
    bcanvas.style.height = pxH + "px";
    bcanvas.width = Math.round(pxW * 2); // crisp on hi-dpi
    bcanvas.height = Math.round(pxH * 2);
  }
  function bmodalRedraw() {
    bctx.fillStyle = "#ffffff";
    bctx.fillRect(0, 0, bcanvas.width, bcanvas.height);
    for (const s of modalState.strokes) strokeToPath(bctx, s, bcanvas.width, bcanvas.height);
  }
  // page-normalized coords from a pointer event over the modal canvas
  function bmodalPt(e) {
    const r = bcanvas.getBoundingClientRect();
    const nx = (e.clientX - r.left) / r.width;  // 0..1 across width
    const ny = (e.clientY - r.top) / r.height;  // 0..1 across height
    return { x: nx, y: ny };
  }
  bcanvas.addEventListener("pointerdown", (e) => {
    bcanvas.setPointerCapture?.(e.pointerId);
    const pt = bmodalPt(e);
    if (modalState.eraser) {
      lastBoxEraseW = pt;
      eraseBoxAt(pt);
      bcanvas.addEventListener("pointermove", onBoxErase);
      window.addEventListener("pointerup", () => { bcanvas.removeEventListener("pointermove", onBoxErase); lastBoxEraseW = null; }, { once: true });
      return;
    }
    modalState.cur = {
      color: $("#box-pen-color").value,
      width: Number($("#box-pen-size").value),
      points: [pt],
    };
    modalState.strokes.push(modalState.cur);
    bcanvas.addEventListener("pointermove", onBoxDraw);
    window.addEventListener("pointerup", onBoxDrawEnd, { once: true });
  });
  function onBoxDraw(e) {
    if (!modalState?.cur) return;
    modalState.cur.points.push(bmodalPt(e));
    bmodalRedraw();
  }
  function onBoxDrawEnd() {
    bcanvas.removeEventListener("pointermove", onBoxDraw);
    if (modalState) { modalState.cur = null; modalState.dirty = true; }
  }
  function eraseBoxAt(pt) {
    const thr = 0.015 + Number($("#box-pen-size").value) / 500; // normalized radius
    const next = [];
    let changed = false;
    for (const s of modalState.strokes) {
      // Split like the canvas eraser instead of deleting the whole stroke, so a
      // partly-touched letter keeps the parts you didn't erase.
      const pieces = erasePolyline(s.points, pt.x, pt.y, thr, Math.max(thr * 0.5, 0.004));
      if (pieces === null) { next.push(s); continue; }
      changed = true;
      for (const p of pieces) next.push({ color: s.color, width: s.width, points: p });
    }
    if (changed) { modalState.strokes = next; modalState.dirty = true; bmodalRedraw(); }
  }
  function onBoxErase(e) {
    const pt = bmodalPt(e);
    const thr = 0.015 + Number($("#box-pen-size").value) / 500;
    // Interpolate so a fast drag erases a continuous path, not spaced-out dots.
    if (lastBoxEraseW) {
      const dist = Math.hypot(pt.x - lastBoxEraseW.x, pt.y - lastBoxEraseW.y);
      const steps = Math.max(1, Math.ceil(dist / Math.max(thr * 0.5, 0.004)));
      for (let k = 1; k <= steps; k++) {
        const t = k / steps;
        eraseBoxAt({ x: lastBoxEraseW.x + (pt.x - lastBoxEraseW.x) * t, y: lastBoxEraseW.y + (pt.y - lastBoxEraseW.y) * t });
      }
    } else {
      eraseBoxAt(pt);
    }
    lastBoxEraseW = pt;
  }

  $("#box-pen-size").addEventListener("input", (e) => {
    $("#box-pen-size-val").textContent = e.target.value;
  });
  $("#box-eraser").addEventListener("click", () => {
    modalState.eraser = !modalState.eraser;
    $("#box-eraser").classList.toggle("active", modalState.eraser);
  });
  $("#box-undo").addEventListener("click", () => {
    if (modalState.strokes.length) { modalState.strokes.pop(); modalState.dirty = true; bmodalRedraw(); }
  });
  $("#box-clear").addEventListener("click", () => {
    if (modalState.strokes.length && confirm("ล้างลายมือทั้งหน้า?")) { modalState.strokes = []; modalState.dirty = true; bmodalRedraw(); }
  });
  async function saveModalBox() {
    if (!modalState) return;
    const title = $("#box-modal-title").value;
    await api(`/api/boxes/${modalState.boxId}`, "PATCH", { strokes: modalState.strokes, title });
    modalState.dirty = false;
  }
  $("#box-close").addEventListener("click", async () => {
    await saveModalBox();
    const id = modalState.boxId;
    modalState = null;
    bmodal.hidden = true;
    const el = boxEls.get(id);
    if (el) { const b = STATE.boxes.find(x => x.id === id); if (b) paintBox(el.querySelector(".box-preview"), b.strokes, b.w, b.h || Math.round(b.w * PAGE_ASPECT)); }
  });

  // Render the current page to a white PNG at OCR resolution (box aspect).
  function rasterizeModal() {
    const b = STATE.boxes.find((x) => x.id === modalState.boxId);
    const aspect = b ? (b.h || Math.round(b.w * PAGE_ASPECT)) / b.w : PAGE_ASPECT;
    const tmp = document.createElement("canvas");
    paintBox(tmp, modalState.strokes, RASTER_W, Math.round(RASTER_W * aspect));
    return tmp.toDataURL("image/png");
  }
  $("#box-send-claude").addEventListener("click", async () => {
    await saveModalBox();
    const dataUrl = rasterizeModal();
    await api(`/api/boxes/${modalState.boxId}/to-claude`, "POST", { dataUrl, note: $("#box-modal-title").value });
    toast("ส่งลายมือให้ Claude แล้ว ✓ — เดี๋ยว Claude อ่านให้");
  });
  $("#box-ocr").addEventListener("click", async () => {
    const out = $("#box-ocr-result");
    out.hidden = false;
    out.textContent = "⏳ กำลังอ่านลายมือ (ไทย+อังกฤษ)… ครั้งแรกอาจโหลดโมเดลสักครู่";
    try {
      const dataUrl = rasterizeModal();
      const { data } = await Tesseract.recognize(dataUrl, "tha+eng");
      const text = (data.text || "").trim();
      out.textContent = text ? "📄 อ่านได้: " + text : "ไม่พบข้อความที่อ่านได้ ลองเขียนให้ชัดขึ้น";
    } catch (err) {
      out.textContent = "OCR ผิดพลาด: " + err.message;
    }
  });

  $("#btn-add-box").addEventListener("click", async () => {
    const c = screenToWorld(canvas.clientWidth / 2, canvas.clientHeight / 2);
    const box = await api("/api/boxes", "POST", { x: Math.round(c.x - 160), y: Math.round(c.y - 100), w: 320 });
    if (box) setTimeout(() => openBox(box.id), 80);
  });

  $("#btn-add-gallery").addEventListener("click", async () => {
    const c = screenToWorld(canvas.clientWidth / 2, canvas.clientHeight / 2);
    const box = await api("/api/boxes", "POST", {
      kind: "image", x: Math.round(c.x - 170), y: Math.round(c.y - 130), w: 340, h: 280, title: "คลังรูปภาพ",
    });
    if (box) { selectedBoxId = box.id; toast("สร้างกล่องรูปภาพแล้ว 🖼️ — กด ＋ เพื่อเพิ่มรูป"); }
  });

  // ----------------------------------------------------------------------
  // Keyboard
  // ----------------------------------------------------------------------
  window.addEventListener("keydown", (e) => {
    // Undo / redo (work even when not typing in a node)
    if ((e.ctrlKey || e.metaKey) && !isTyping(e)) {
      const k = e.key.toLowerCase();
      if (k === "z" && !e.shiftKey) { e.preventDefault(); api("/api/undo", "POST"); return; }
      if ((k === "z" && e.shiftKey) || k === "y") { e.preventDefault(); api("/api/redo", "POST"); return; }
    }
    if (isTyping(e)) return;
    // Tool shortcuts: W = pen (draw), E = eraser. Hold Space = temporary Pan.
    if (e.code === "KeyW") {
      e.preventDefault();
      setMode("draw");
      return;
    }
    if (e.code === "KeyE") {
      // E toggles the eraser: press once to erase (switching into draw mode if
      // needed), press again to drop back to the pen. (W also returns to pen.)
      e.preventDefault();
      if (mode === "draw" && eraser) {
        setEraser(false);
      } else {
        if (mode !== "draw") setMode("draw");
        setEraser(true);
      }
      return;
    }
    if (e.code === "Space") {
      // Hold Space to pan the camera; release to return to the current tool.
      // The pointer handlers already pan whenever spaceDown is set — we just
      // flip the flag here instead of switching tool/mode (so move still works
      // via the select tool, Space no longer selects).
      e.preventDefault();
      if (!spaceDown) {
        spaceDown = true;
        canvas.classList.add("space-pan");
      }
      return;
    }
    if (e.key === "Delete" || e.key === "Backspace") {
      if (selectedIds.size > 0) {
        // multi-selected nodes
        for (const id of selectedIds) api(`/api/nodes/${id}`, "DELETE");
        selectedIds = new Set();
        selectedId = null;
        render();
      } else if (selectedId) {
        api(`/api/nodes/${selectedId}`, "DELETE");
        selectedId = null;
      } else if (selectedStrokeIds.size > 0) {
        // selected drawing strokes
        for (const id of selectedStrokeIds) api(`/api/drawings/${id}`, "DELETE");
        selectedStrokeIds = new Set();
        drawFx();
      } else if (selectedImgId) {
        api(`/api/images/${selectedImgId}`, "DELETE");
        selectedImgId = null;
      } else if (selectedBoxId) {
        api(`/api/boxes/${selectedBoxId}`, "DELETE");
        selectedBoxId = null;
        render();
      }
    }
  });
  // Release the hold-to-pan when Space is let go (or the window loses focus,
  // so a missed keyup can't leave us stuck panning).
  function endSpacePan() {
    if (!spaceDown) return;
    spaceDown = false;
    canvas.classList.remove("space-pan");
  }
  window.addEventListener("keyup", (e) => {
    if (e.code === "Space") endSpacePan();
  });
  window.addEventListener("blur", endSpacePan);
  function isTyping(e) {
    const t = e.target;
    return (
      t.tagName === "INPUT" ||
      t.tagName === "TEXTAREA" ||
      t.getAttribute?.("contenteditable") === "true"
    );
  }

  window.addEventListener("resize", render);

  // ----------------------------------------------------------------------
  // Resizable chat panel
  // ----------------------------------------------------------------------
  (function setupSidebarResize() {
    const sidebar = $("#sidebar");
    const resizer = $("#sidebar-resizer");
    if (!sidebar || !resizer) return;
    const MIN = 220;
    const maxW = () => Math.min(window.innerWidth * 0.75, window.innerWidth - 320);
    const clamp = (w) => Math.max(MIN, Math.min(maxW(), w));

    const saved = parseInt(localStorage.getItem("pn.sidebarWidth"), 10);
    if (saved) sidebar.style.width = clamp(saved) + "px";

    let dragging = false;
    resizer.addEventListener("pointerdown", (e) => {
      dragging = true;
      resizer.setPointerCapture(e.pointerId);
      resizer.classList.add("dragging");
      document.body.classList.add("col-resizing");
      e.preventDefault();
    });
    resizer.addEventListener("pointermove", (e) => {
      if (!dragging) return;
      const w = clamp(e.clientX - sidebar.getBoundingClientRect().left);
      sidebar.style.width = w + "px";
      render();
    });
    const stop = (e) => {
      if (!dragging) return;
      dragging = false;
      resizer.classList.remove("dragging");
      document.body.classList.remove("col-resizing");
      try { resizer.releasePointerCapture(e.pointerId); } catch {}
      localStorage.setItem("pn.sidebarWidth", parseInt(sidebar.style.width, 10) || 340);
      render();
    };
    resizer.addEventListener("pointerup", stop);
    resizer.addEventListener("pointercancel", stop);
    // Double-click the divider to reset to default width.
    resizer.addEventListener("dblclick", () => {
      sidebar.style.width = "340px";
      localStorage.setItem("pn.sidebarWidth", "340");
      render();
    });
  })();

  // ----------------------------------------------------------------------
  // Model switcher
  // ----------------------------------------------------------------------
  (function setupModelSwitcher() {
    const btns = document.querySelectorAll(".model-btn");
    // Fetch current model from settings and mark active button.
    fetch("/api/current-model").then(r => r.json()).then(({ model }) => {
      btns.forEach(b => b.classList.toggle("active", b.dataset.model === model));
    }).catch(() => {});

    btns.forEach(btn => {
      btn.addEventListener("click", async () => {
        const model = btn.dataset.model;
        const res = await fetch("/api/set-model", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ model }),
        });
        if (res.ok) {
          btns.forEach(b => b.classList.toggle("active", b === btn));
          toast(`เปลี่ยนเป็น ${model} แล้ว — มีผลครั้งถัดไปที่เปิด Claude Code ✓`);
        } else {
          toast("เปลี่ยนโมเดลไม่สำเร็จ");
        }
      });
    });
  })();

  // ----------------------------------------------------------------------
  // Boot
  // ----------------------------------------------------------------------
  initNotifications();
  connectWS();
  api("/api/state").then((s) => {
    if (s) {
      applyProjects(s.projects, s.activeId);
      applyState(s);
    }
    fitView();
  });

  function toast(msg) {
    const t = $("#toast");
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(toast._t);
    toast._t = setTimeout(() => t.classList.remove("show"), 3200);
  }

  // ----------------------------------------------------------------------
  // Tags
  // ----------------------------------------------------------------------
  const TAGS = [
    { name: "todo",      color: "#f97316", emoji: "📋" },
    { name: "done",      color: "#22c55e", emoji: "✅" },
    { name: "idea",      color: "#a855f7", emoji: "💡" },
    { name: "important", color: "#ef4444", emoji: "❗" },
    { name: "question",  color: "#3b82f6", emoji: "❓" },
  ];

  let tagPickerNodeId = null;
  const tagPicker = (() => {
    const el = document.createElement("div");
    el.className = "tag-picker";
    el.hidden = true;
    TAGS.forEach((t) => {
      const btn = document.createElement("button");
      btn.className = "tag-picker-item";
      btn.dataset.tag = t.name;
      btn.style.setProperty("--tc", t.color);
      btn.textContent = `${t.emoji} ${t.name}`;
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        if (!tagPickerNodeId) return;
        const node = STATE.nodes.find((n) => n.id === tagPickerNodeId);
        if (!node) return;
        const tags = Array.isArray(node.tags) ? [...node.tags] : [];
        const idx = tags.indexOf(t.name);
        if (idx >= 0) tags.splice(idx, 1); else tags.push(t.name);
        node.tags = tags;
        api(`/api/nodes/${tagPickerNodeId}`, "PATCH", { tags });
        renderTagPicker(tagPickerNodeId);
        render();
      });
      el.appendChild(btn);
    });
    document.body.appendChild(el);
    document.addEventListener("pointerdown", (e) => {
      if (!e.target.closest(".tag-picker") && !e.target.closest(".tag-btn")) {
        el.hidden = true;
        tagPickerNodeId = null;
      }
    });
    return el;
  })();

  function renderTagPicker(nodeId) {
    const node = STATE.nodes.find((n) => n.id === nodeId);
    const tags = node?.tags || [];
    tagPicker.querySelectorAll(".tag-picker-item").forEach((btn) => {
      btn.classList.toggle("active", tags.includes(btn.dataset.tag));
    });
  }

  function openTagPicker(e, nodeId) {
    e.stopPropagation();
    if (tagPickerNodeId === nodeId && !tagPicker.hidden) {
      tagPicker.hidden = true;
      tagPickerNodeId = null;
      return;
    }
    tagPickerNodeId = nodeId;
    renderTagPicker(nodeId);
    const r = e.target.getBoundingClientRect();
    tagPicker.style.left = r.left + "px";
    tagPicker.style.top = r.bottom + 6 + "px";
    tagPicker.hidden = false;
  }

  // ----------------------------------------------------------------------
  // Export (MD/PNG/PDF) + Calendar panel were extracted to
  // modules/export.js & modules/calendar.js — wired at the bottom of this
  // file via setupExport() / setupCalendar(). Do not re-add here (would
  // double-bind the toolbar buttons: calendar toggled twice = stays closed).
  // ----------------------------------------------------------------------

  // -------------------------------------------------------------------------
  // Collapse the left chat panel (ย่อพาเนลซ้าย) — persisted in localStorage
  // -------------------------------------------------------------------------
  const sidebarEl = document.getElementById("sidebar");
  const sidebarResizer = document.getElementById("sidebar-resizer");
  const sidebarExpandBtn = document.getElementById("sidebar-expand");
  function setSidebarCollapsed(collapsed) {
    sidebarEl.classList.toggle("collapsed", collapsed);
    sidebarEl.setAttribute("aria-hidden", String(collapsed));
    if (sidebarResizer) sidebarResizer.style.display = collapsed ? "none" : "";
    if (sidebarExpandBtn) sidebarExpandBtn.hidden = !collapsed;
    try { localStorage.setItem("sidebarCollapsed", collapsed ? "1" : "0"); } catch {}
    // canvases are sized to their container — refit after the layout shift
    setTimeout(() => { try { render(); drawEdges(computeHidden()); drawFx(); } catch {} }, 60);
  }
  document.getElementById("sidebar-collapse")?.addEventListener("click", () => setSidebarCollapsed(true));
  sidebarExpandBtn?.addEventListener("click", () => setSidebarCollapsed(false));
  try { if (localStorage.getItem("sidebarCollapsed") === "1") setSidebarCollapsed(true); } catch {}

  // -------------------------------------------------------------------------
  // Object panel (พาเนล Object ฝั่งขวา) — list every object, delete by hand
  // -------------------------------------------------------------------------
  const objPanel = document.getElementById("obj-panel");
  const objBody = document.getElementById("obj-body");

  function toggleObjPanel(open) {
    const show = open !== undefined ? open : !objPanel.classList.contains("open");
    objPanel.classList.toggle("open", show);
    objPanel.setAttribute("aria-hidden", String(!show));
    document.getElementById("btn-toggle-objects").classList.toggle("active", show);
    if (show) renderObjectPanel();
  }

  function focusObject(kind, id) {
    // center the view on an object so the user sees what a row refers to
    let cx, cy;
    if (kind === "node") { const n = STATE.nodes.find((x) => x.id === id); if (n) { cx = n.x; cy = n.y; } }
    else if (kind === "image") { const im = (STATE.images || []).find((x) => x.id === id); if (im) { cx = im.x + im.w / 2; cy = im.y + im.h / 2; } }
    else { const b = (STATE.boxes || []).find((x) => x.id === id); if (b) { cx = b.x + b.w / 2; cy = b.y + (b.h || 80) / 2; } }
    if (cx === undefined) return;
    const r = canvas.getBoundingClientRect();
    view.x = r.width / 2 - cx * view.scale;
    view.y = r.height / 2 - cy * view.scale;
    render(); drawEdges(computeHidden()); drawFx(); scheduleViewport();
  }

  // window so renderObjectPanel is reachable from render()'s typeof check
  window.renderObjectPanel = renderObjectPanel;
  function renderObjectPanel() {
    if (!objPanel.classList.contains("open")) return;
    const rows = [];
    const esc = (s) => escapeHtml(String(s ?? ""));

    const aiboxes = (STATE.boxes || []).filter((b) => b.kind === "aibox");
    const otherBoxes = (STATE.boxes || []).filter((b) => b.kind !== "aibox");
    const roots = STATE.nodes.filter((n) => !n.parentId);

    const section = (label, count) => `<div class="obj-section">${label} <span class="obj-count">${count}</span></div>`;
    const row = (icon, kind, id, label, sub) =>
      `<div class="obj-row" data-kind="${kind}" data-id="${esc(id)}">
         <span class="obj-icon">${icon}</span>
         <span class="obj-label" title="${esc(label)}">${esc(label) || "<ว่าง>"}${sub ? `<span class="obj-sub">${esc(sub)}</span>` : ""}</span>
         <button class="obj-del" title="ลบ">🗑</button>
       </div>`;

    if (aiboxes.length) {
      rows.push(section("🤖 AI Box", aiboxes.length));
      for (const b of aiboxes) rows.push(row("🤖", "box", b.id, b.title || "AI Box", `${Math.round(b.w)}×${Math.round(b.h)}`));
    }
    rows.push(section("🧠 หัวข้อ (Topics)", STATE.nodes.length));
    if (!STATE.nodes.length) rows.push(`<div class="obj-empty">— ยังไม่มีหัวข้อ —</div>`);
    for (const n of roots) rows.push(row("●", "node", n.id, n.text || "<ว่าง>", null));

    if (otherBoxes.length) {
      rows.push(section("📦 กล่อง (Boxes)", otherBoxes.length));
      for (const b of otherBoxes) {
        const icon = b.kind === "image" ? "🖼️" : b.kind === "portal" ? "🔀" : "📦";
        rows.push(row(icon, "box", b.id, b.title || b.kind, b.kind));
      }
    }
    const imgs = STATE.images || [];
    if (imgs.length) {
      rows.push(section("🌅 รูปลอย (Images)", imgs.length));
      imgs.forEach((im, i) => rows.push(row("🌅", "image", im.id, "รูป #" + (i + 1), `${Math.round(im.w)}×${Math.round(im.h)}`)));
    }
    const draws = STATE.drawings || [];
    rows.push(section("✏️ เส้นวาด (Drawings)", draws.length));

    objBody.innerHTML = rows.join("") || `<div class="obj-empty">ยังไม่มี object</div>`;

    objBody.querySelectorAll(".obj-row").forEach((rowEl) => {
      const kind = rowEl.dataset.kind, id = rowEl.dataset.id;
      rowEl.querySelector(".obj-label").addEventListener("click", () => focusObject(kind, id));
      rowEl.querySelector(".obj-icon").addEventListener("click", () => focusObject(kind, id));
      rowEl.querySelector(".obj-del").addEventListener("click", async (e) => {
        e.stopPropagation();
        if (!confirm("ลบ object นี้?")) return;
        if (kind === "node") await api(`/api/nodes/${id}`, "DELETE");
        else if (kind === "image") await api(`/api/images/${id}`, "DELETE");
        else await api(`/api/boxes/${id}`, "DELETE");
      });
    });
  }

  document.getElementById("btn-toggle-objects").addEventListener("click", () => toggleObjPanel());
  document.getElementById("obj-close").addEventListener("click", () => toggleObjPanel(false));
  document.getElementById("obj-refresh").addEventListener("click", () => renderObjectPanel());

// ----------------------------------------------------------------------
// Module setup — wire extracted sections back with their dependencies
// ----------------------------------------------------------------------
const localActiveSectionRef = { value: localActiveSection };

chatModule = setupChat({ STATE, api, toast, escapeHtml, localActiveSectionRef });

setupVoice({ api, toast, localActiveSectionRef });

setupExport({ STATE, view, canvas, world, toast, render, flushFx });

setupCalendar({ api, toast, escapeHtml });
