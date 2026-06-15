/* Powerfull Note — frontend
 * Mind map (nodes + edges), freehand pen layer, pan/zoom, Thai voice,
 * live sync with the server over WebSocket, and a Claude chat panel.
 */
(() => {
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
  let drag = null; // node drag
  let pan = null; // canvas pan
  let stroke = null; // active freehand stroke
  let spaceDown = false;
  let serverBootId = null; // detect server restarts for live reload
  let eraseDelete = new Set(); // server ids of strokes touched during an erase drag
  let tmpCounter = 0; // temp ids for stroke pieces created while erasing
  let localActiveSection = "main"; // mirrors activeSection but updates immediately on tab click

  const $ = (s) => document.querySelector(s);
  const canvas = $("#canvas");
  const world = $("#world");
  const nodesLayer = $("#nodes");
  const imagesLayer = $("#images");
  const boxesLayer = $("#boxes");
  const edgesCanvas = $("#edges");
  const fxCanvas = $("#fx");
  const ectx = edgesCanvas.getContext("2d");
  const fctx = fxCanvas.getContext("2d");
  const nodeEls = new Map();
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
    // Preserve a node we're actively dragging so the broadcast doesn't snap it.
    if (drag) {
      const local = STATE.nodes.find((n) => n.id === drag.id);
      const incoming = s.nodes.find((n) => n.id === drag.id);
      if (local && incoming) {
        incoming.x = local.x;
        incoming.y = local.y;
      }
    }
    maybeNotifyClaude(s);
    STATE = s;
    renderChat();
    syncTitle();
    render();
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

  // ----------------------------------------------------------------------
  // Hidden set (collapsed subtrees)
  // ----------------------------------------------------------------------
  function computeHidden() {
    const byId = new Map(STATE.nodes.map((n) => [n.id, n]));
    const hidden = new Set();
    for (const n of STATE.nodes) {
      let p = n.parentId ? byId.get(n.parentId) : null;
      while (p) {
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
      el.classList.toggle("selected", n.id === selectedId);
      el.style.borderColor = n.color || "var(--accent)";
      // text (skip while editing to avoid caret jumps); URLs become links
      const txt = el.querySelector(".node-text");
      if (document.activeElement !== txt) setNodeText(txt, n.text);
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
    drawEdges(hidden);
    drawFx();
  }

  // Linkify URLs in node text. While editing we show the raw text so the user
  // can edit the URL; otherwise URLs render as clickable links.
  const URL_RE = /(https?:\/\/[^\s<]+)/g;
  function escapeHtml(s) {
    return s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
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
    el.innerHTML = `<div class="node-text"></div><button class="handle add-child" title="เพิ่มหัวข้อย่อย">+</button><button class="handle del-node" title="ลบหัวข้อนี้ (และหัวข้อย่อย)">×</button>`;
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
    if (!it) return;
    const im = imgById(it.id);
    if (im) {
      api(`/api/images/${it.id}`, "PATCH", { x: im.x, y: im.y, w: im.w, h: im.h, rotation: im.rotation });
    }
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
    const rect = (id) => {
      const el = nodeEls.get(id);
      if (!el || el.style.display === "none") return null;
      const b = el.getBoundingClientRect();
      return {
        l: b.left - r.left,
        t: b.top - r.top,
        cx: b.left - r.left + b.width / 2,
        cy: b.top - r.top + b.height / 2,
        w: b.width,
        h: b.height,
      };
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
      ectx.strokeStyle = (STATE.nodes.find((x) => x.id === n.id)?.color) || "#6366f1";
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
      const el = boxEls.get(id);
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

  // freehand drawings + active stroke (screen space, above nodes)
  function drawFx() {
    const r = canvas.getBoundingClientRect();
    sizeCanvas(fxCanvas, fctx, r);
    fctx.clearRect(0, 0, r.width, r.height);
    const all = STATE.drawings.slice();
    if (stroke) all.push(stroke);
    for (const d of all) drawStroke(d);
  }

  function drawStroke(d) {
    if (!d.points || d.points.length < 1) return;
    fctx.strokeStyle = d.color;
    fctx.lineCap = "round";
    fctx.lineJoin = "round";
    const pts = d.points.map((p) => {
      const s = worldToScreen(p.x, p.y);
      return { x: s.x, y: s.y, p: p.p ?? 0.5 };
    });
    if (pts.length === 1) {
      fctx.beginPath();
      fctx.arc(pts[0].x, pts[0].y, (d.width * view.scale) / 2, 0, Math.PI * 2);
      fctx.fillStyle = d.color;
      fctx.fill();
      return;
    }
    for (let i = 1; i < pts.length; i++) {
      const a = pts[i - 1];
      const b = pts[i];
      fctx.beginPath();
      fctx.moveTo(a.x, a.y);
      fctx.lineTo(b.x, b.y);
      fctx.lineWidth = Math.max(0.6, d.width * view.scale * (0.35 + 1.3 * b.p));
      fctx.stroke();
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
  function onNodePointerDown(e, id) {
    if (e.button === 2) return; // right-click is reserved for the edit context menu
    if (e.target.closest("a")) return; // let link clicks through
    const txt = e.target.closest(".node-text");
    if (txt && txt.getAttribute("contenteditable") === "true") return; // editing
    if (e.target.closest(".handle")) return;
    if (mode === "draw") return; // let fx capture
    e.stopPropagation();
    const n = STATE.nodes.find((x) => x.id === id);
    if (!n) return;
    const start = eventCanvasPos(e);
    drag = { id, startX: start.x, startY: start.y, origX: n.x, origY: n.y, moved: false };
    canvas.setPointerCapture?.(e.pointerId);
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp, { once: true });
  }

  // ----------------------------------------------------------------------
  // Canvas pan / draw start
  // ----------------------------------------------------------------------
  canvas.addEventListener("pointerdown", (e) => {
    if (e.target.closest(".node")) return;
    const wantPan = e.button === 1 || e.button === 2 || spaceDown || (mode === "select" && e.button === 0);
    if (mode === "draw" && e.button === 0 && !spaceDown) {
      startStroke(e);
      return;
    }
    if (wantPan) {
      const p = eventCanvasPos(e);
      pan = { x: p.x, y: p.y, vx: view.x, vy: view.y };
      canvas.classList.add("panning");
      window.addEventListener("pointermove", onPointerMove);
      window.addEventListener("pointerup", onPointerUp, { once: true });
    }
  });

  canvas.addEventListener("click", (e) => {
    if (!e.target.closest(".node") && !e.target.closest(".img-obj") && !e.target.closest(".hbox")) {
      selectedId = null;
      selectedImgId = null;
      selectedBoxId = null;
      render();
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
        drawEdges(computeHidden());
        drawFx();
      }
    } else if (pan) {
      const p = eventCanvasPos(e);
      view.x = pan.vx + (p.x - pan.x);
      view.y = pan.vy + (p.y - pan.y);
      render();
    } else if (stroke) {
      addStrokePoint(e);
    }
  }

  function onPointerUp() {
    if (drag) {
      const n = STATE.nodes.find((x) => x.id === drag.id);
      const el = nodeEls.get(drag.id);
      if (el) el.classList.remove("dragging");
      if (n && drag.moved) api(`/api/nodes/${drag.id}`, "PATCH", { x: n.x, y: n.y });
      drag = null;
    }
    if (pan) {
      pan = null;
      canvas.classList.remove("panning");
    }
    if (stroke) endStroke();
    window.removeEventListener("pointermove", onPointerMove);
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
      render();
    },
    { passive: false }
  );

  canvas.addEventListener("contextmenu", (e) => {
    e.preventDefault();
    // Right-click an existing node → edit its text inline.
    const nodeEl = e.target.closest(".node");
    if (nodeEl) beginEditNode(nodeEl.querySelector(".node-text"));
  });

  // ----------------------------------------------------------------------
  // Freehand stroke
  // ----------------------------------------------------------------------
  function startStroke(e) {
    fxCanvas.setPointerCapture?.(e.pointerId);
    const p = eventCanvasPos(e);
    const w = screenToWorld(p.x, p.y);
    if (eraser) {
      eraseDelete = new Set();
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
    const p = eventCanvasPos(e);
    const w = screenToWorld(p.x, p.y);
    stroke.points.push({ x: w.x, y: w.y, p: e.pressure || 0.5 });
    drawFx();
  }
  function endStroke() {
    const s = stroke;
    stroke = null;
    if (s && s.points && s.points.length > 0) api("/api/drawings", "POST", s);
    window.removeEventListener("pointermove", onPointerMove);
  }
  function onEraseMove(e) {
    const p = eventCanvasPos(e);
    eraseAt(screenToWorld(p.x, p.y));
  }
  async function onEraseUp() {
    stroke = null;
    window.removeEventListener("pointermove", onEraseMove);
    // Persist the erase: delete touched originals, create the surviving pieces.
    const dels = [...eraseDelete];
    eraseDelete = new Set();
    const news = STATE.drawings.filter((d) => d._new);
    for (const id of dels) await api(`/api/drawings/${id}`, "DELETE");
    for (const d of news) {
      await api("/api/drawings", "POST", {
        color: d.color,
        width: d.width,
        points: d.points,
      });
    }
  }

  // Paint-style eraser: remove only the points under the cursor and split the
  // stroke into the surviving segments, instead of deleting the whole stroke.
  function splitStrokeByErase(d, w, thr) {
    let hit = false;
    const segments = [];
    let cur = [];
    for (const pt of d.points) {
      if (Math.hypot(pt.x - w.x, pt.y - w.y) < thr) {
        hit = true;
        if (cur.length) {
          segments.push(cur);
          cur = [];
        }
      } else {
        cur.push(pt);
      }
    }
    if (cur.length) segments.push(cur);
    if (!hit) return null;
    return segments
      .filter((s) => s.length > 0)
      .map((s) => ({ color: d.color, width: d.width, points: s }));
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

  // ----------------------------------------------------------------------
  // Chat panel
  // ----------------------------------------------------------------------
  function renderChatTabs() {
    const list = $("#chat-tab-list");
    if (!list) return;
    const sections = STATE.chatSections && STATE.chatSections.length
      ? STATE.chatSections
      : [{ id: "main", name: "แชทหลัก" }];
    const active = STATE.activeSection || sections[0].id;
    localActiveSection = active;
    list.innerHTML = "";
    for (const sec of sections) {
      const tab = document.createElement("div");
      tab.className = "chat-tab" + (sec.id === active ? " active" : "");
      tab.dataset.id = sec.id;
      const label = document.createElement("span");
      label.className = "chat-tab-name";
      label.textContent = sec.name || "แชท";
      tab.appendChild(label);
      // switch section on click
      tab.addEventListener("click", () => {
        localActiveSection = sec.id; // update immediately so next submit uses correct section
        if (sec.id !== (STATE.activeSection || "main")) api(`/api/chat-sections/${sec.id}/activate`, "POST");
      });
      // double-click to rename
      label.addEventListener("dblclick", (e) => {
        e.stopPropagation();
        const name = prompt("เปลี่ยนชื่อแชท:", sec.name || "");
        if (name && name.trim()) api(`/api/chat-sections/${sec.id}`, "PATCH", { name: name.trim() });
      });
      if (sections.length > 1) {
        const del = document.createElement("button");
        del.className = "chat-tab-del";
        del.textContent = "×";
        del.title = "ลบแชทนี้ (พร้อมข้อความข้างใน)";
        del.addEventListener("click", (e) => {
          e.stopPropagation();
          if (confirm(`ลบแชท "${sec.name}" และข้อความทั้งหมดในนั้น?`)) api(`/api/chat-sections/${sec.id}`, "DELETE");
        });
        tab.appendChild(del);
      }
      list.appendChild(tab);
    }
  }

  function renderChat() {
    renderChatTabs();
    const box = $("#chat");
    const active = STATE.activeSection || "main";
    const msgs = (STATE.chat || []).filter((m) => (m.section || "main") === active);
    if (!msgs.length) {
      box.innerHTML =
        '<div class="chat-empty">ยังไม่มีข้อความในแชทนี้<br>เมื่อ Claude ใช้เครื่องมือ <code>say_to_user</code><br>ข้อความจะมาโผล่ที่นี่ ✨</div>';
      return;
    }
    const atBottom = box.scrollHeight - box.scrollTop - box.clientHeight < 60;
    box.innerHTML = "";
    for (const m of msgs) {
      const el = document.createElement("div");
      el.className = "msg " + (m.role || "claude");
      const t = new Date(m.ts).toLocaleTimeString("th-TH", { hour: "2-digit", minute: "2-digit" });
      // Turn literal backslash-n (and \r\n) into real line breaks; .msg uses white-space: pre-wrap.
      const body = escapeHtml(m.text).replace(/\\r\\n|\\n|\\r/g, "\n");
      el.innerHTML = `${body}<span class="ts">${t}</span>`;
      box.appendChild(el);
    }
    if (atBottom) box.scrollTop = box.scrollHeight;
  }
  function escapeHtml(s) {
    return String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  }

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
      // fresh project loaded — frame it once the new nodes render
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

  // ----------------------------------------------------------------------
  // Voice (Thai) + text input
  // ----------------------------------------------------------------------
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recog = null;
  let listening = false;
  let finalBuf = "";

  // Mic language: a two-state toggle (ไทย ↔ EN), persisted.
  const langToggle = $("#voice-lang");
  let currentLang = localStorage.getItem("pn.voiceLang") || "th-TH";
  function voiceLang() { return currentLang; }
  function isThai() { return currentLang.startsWith("th"); }
  function applyLang() {
    const th = isThai();
    if (langToggle) langToggle.classList.toggle("en", !th);
    if (recog) recog.lang = currentLang;
    $("#mic-btn").title = th ? "พูดภาษาไทย (th-TH)" : "Speak English (en-US)";
    if (!listening) $("#voice-status").textContent = th ? "กดไมค์เพื่อพูดภาษาไทย" : "Tap the mic to speak English";
  }
  if (langToggle) {
    applyLang();
    langToggle.addEventListener("click", () => {
      currentLang = isThai() ? "en-US" : "th-TH";
      localStorage.setItem("pn.voiceLang", currentLang);
      applyLang();
    });
  }

  function setupVoice() {
    if (!SR) {
      $("#voice-status").textContent = "เบราว์เซอร์นี้ไม่รองรับการพูด — ใช้ Chrome หรือ Edge";
      $("#mic-btn").disabled = true;
      $("#mic-btn").style.opacity = 0.4;
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
      $("#voice-interim").textContent = interim;
    };
    recog.onerror = (e) => {
      $("#voice-status").textContent = "ข้อผิดพลาดเสียง: " + e.error;
    };
    recog.onend = () => {
      if (listening) {
        // user still wants to listen (Chrome auto-stops); restart
        try {
          recog.start();
        } catch {}
      }
    };
  }

  function startListening() {
    if (!recog) return;
    finalBuf = "";
    listening = true;
    recog.lang = voiceLang(); // honor the latest language choice
    try {
      recog.start();
    } catch {}
    $("#mic-btn").classList.add("listening");
    $("#voice-status").textContent = isThai()
      ? "กำลังฟัง… พูดได้เลย (กดอีกครั้งเพื่อหยุด)"
      : "Listening… speak now (tap again to stop)";
  }

  function stopListening() {
    listening = false;
    try {
      recog.stop();
    } catch {}
    $("#mic-btn").classList.remove("listening");
    $("#voice-status").textContent = isThai() ? "กดไมค์เพื่อพูดภาษาไทย" : "Tap the mic to speak English";
    const text = (finalBuf + " " + $("#voice-interim").textContent).trim();
    $("#voice-interim").textContent = "";
    if (text) submitUserInput(text);
  }

  $("#mic-btn").addEventListener("click", () => (listening ? stopListening() : startListening()));

  const textInput = $("#text-input");
  function sendFromInput() {
    const v = textInput.value.trim();
    if (!v) return;
    submitUserInput(v);
    textInput.value = "";
  }
  textInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendFromInput();
  });
  $("#send-btn").addEventListener("click", sendFromInput);

  // New chat section (tab)
  $("#chat-tab-add").addEventListener("click", async () => {
    const name = prompt("ชื่อแชทใหม่:", "แชทใหม่");
    if (name === null) return;
    await api("/api/chat-sections", "POST", { name: name.trim() || "แชทใหม่" });
  });

  async function submitUserInput(text) {
    const section = localActiveSection || "main";
    await api("/api/chat", "POST", { role: "user", text, section });
    await api("/api/inbox", "POST", { text, section });
    await api("/api/voice", "POST", { text });
    toast("ส่งเข้า Claude แล้ว ✓ — ให้ Claude เรียก get_inbox เพื่อรับ");
  }

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
    const scale = Math.min(2, Math.max(0.2, Math.min(canvas.clientWidth / w, canvas.clientHeight / h)));
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
        b.title || (b.kind === "image" ? "คลังรูปภาพ" : "บันทึกลายมือ");
      if (b.kind === "image") {
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

  function createBoxEl(b) {
    const el = document.createElement("div");
    el.className = "hbox" + (b.kind === "image" ? " hbox-image" : "");
    el.dataset.id = b.id;
    el.dataset.kind = b.kind || "note";
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
    const tgt = document.elementFromPoint(e.clientX, e.clientY)?.closest(".hbox");
    const toId = tgt?.dataset.id;
    if (toId && toId !== ld.from) {
      api("/api/box-links", "POST", { from: ld.from, to: toId });
      toast("โยงกล่องแล้ว 🔗");
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
      // free resize: width and height independent
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
      eraseBoxAt(pt);
      bcanvas.addEventListener("pointermove", onBoxErase);
      window.addEventListener("pointerup", () => bcanvas.removeEventListener("pointermove", onBoxErase), { once: true });
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
    const before = modalState.strokes.length;
    modalState.strokes = modalState.strokes.filter((s) =>
      !(s.points || []).some((p) => Math.hypot(p.x - pt.x, p.y - pt.y) < thr)
    );
    if (modalState.strokes.length !== before) { modalState.dirty = true; bmodalRedraw(); }
  }
  function onBoxErase(e) { eraseBoxAt(bmodalPt(e)); }

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
    if (el) { const b = STATE.boxes.find(x => x.id === id); if (b) paintBox(el.querySelector(".box-preview"), b.strokes, b.w); }
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
    // Tool shortcuts: W = pen (draw), Space = select/move
    if (e.code === "KeyW") {
      e.preventDefault();
      setMode("draw");
      return;
    }
    if (e.code === "Space") {
      e.preventDefault();
      setMode("select");
      return;
    }
    if (e.key === "Delete" || e.key === "Backspace") {
      if (selectedId) {
        api(`/api/nodes/${selectedId}`, "DELETE");
        selectedId = null;
      } else if (selectedImgId) {
        api(`/api/images/${selectedImgId}`, "DELETE");
        selectedImgId = null;
      }
    }
  });
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
  setupVoice();
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
})();
