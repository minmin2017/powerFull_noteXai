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
  let eraseDelete = new Set(); // server ids of strokes touched during an erase drag
  let tmpCounter = 0; // temp ids for stroke pieces created while erasing

  const $ = (s) => document.querySelector(s);
  const canvas = $("#canvas");
  const world = $("#world");
  const nodesLayer = $("#nodes");
  const imagesLayer = $("#images");
  const edgesCanvas = $("#edges");
  const fxCanvas = $("#fx");
  const ectx = edgesCanvas.getContext("2d");
  const fctx = fxCanvas.getContext("2d");
  const nodeEls = new Map();
  const imgEls = new Map();
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
        if (msg.type === "state") {
          if (msg.projects) applyProjects(msg.projects, msg.activeId);
          applyState(msg.state);
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
    STATE = s;
    renderChat();
    syncTitle();
    render();
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
      // text (skip while editing to avoid caret jumps)
      const txt = el.querySelector(".node-text");
      if (document.activeElement !== txt && txt.textContent !== n.text) txt.textContent = n.text;
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

  function createNodeEl(n) {
    const el = document.createElement("div");
    el.className = "node";
    el.dataset.id = n.id;
    el.innerHTML = `<div class="node-text"></div><button class="handle add-child" title="เพิ่มหัวข้อย่อย">+</button><button class="handle del-node" title="ลบหัวข้อนี้ (และหัวข้อย่อย)">×</button>`;
    const txt = el.querySelector(".node-text");

    el.addEventListener("pointerdown", (e) => onNodePointerDown(e, n.id));
    el.addEventListener("click", (e) => {
      e.stopPropagation();
      selectedId = n.id;
      render();
    });

    txt.addEventListener("dblclick", (e) => {
      e.stopPropagation();
      txt.setAttribute("contenteditable", "true");
      txt.focus();
      document.getSelection().selectAllChildren(txt);
    });
    txt.addEventListener("blur", () => {
      txt.removeAttribute("contenteditable");
      const node = STATE.nodes.find((x) => x.id === n.id);
      const val = txt.textContent.trim();
      if (node && val !== node.text) {
        node.text = val;
        api(`/api/nodes/${n.id}`, "PATCH", { text: val });
      }
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
          if (cel) {
            const t = cel.querySelector(".node-text");
            t.setAttribute("contenteditable", "true");
            t.focus();
          }
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
    if (!e.target.closest(".node") && !e.target.closest(".img-obj")) {
      selectedId = null;
      selectedImgId = null;
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
    if (e.target.closest(".node")) return;
    if (mode !== "select") return;
    const p = eventCanvasPos(e);
    const w = screenToWorld(p.x, p.y);
    const node = await api("/api/nodes", "POST", { text: "", x: Math.round(w.x), y: Math.round(w.y) });
    if (node) {
      selectedId = node.id;
      setTimeout(() => {
        const el = nodeEls.get(node.id);
        if (el) {
          const t = el.querySelector(".node-text");
          t.setAttribute("contenteditable", "true");
          t.focus();
        }
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

  canvas.addEventListener("contextmenu", (e) => e.preventDefault());

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
  function renderChat() {
    const box = $("#chat");
    const msgs = STATE.chat || [];
    if (!msgs.length) {
      box.innerHTML =
        '<div class="chat-empty">ยังไม่มีข้อความ<br>เมื่อ Claude ใช้เครื่องมือ <code>say_to_user</code><br>ข้อความจะมาโผล่ที่นี่ ✨</div>';
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

  function setupVoice() {
    if (!SR) {
      $("#voice-status").textContent = "เบราว์เซอร์นี้ไม่รองรับการพูด — ใช้ Chrome หรือ Edge";
      $("#mic-btn").disabled = true;
      $("#mic-btn").style.opacity = 0.4;
      return;
    }
    recog = new SR();
    recog.lang = "th-TH";
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
    try {
      recog.start();
    } catch {}
    $("#mic-btn").classList.add("listening");
    $("#voice-status").textContent = "กำลังฟัง… พูดได้เลย (กดอีกครั้งเพื่อหยุด)";
  }

  function stopListening() {
    listening = false;
    try {
      recog.stop();
    } catch {}
    $("#mic-btn").classList.remove("listening");
    $("#voice-status").textContent = "กดไมค์เพื่อพูดภาษาไทย";
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

  async function submitUserInput(text) {
    // Show it in chat and queue it for Claude Code to drain via get_inbox.
    await api("/api/chat", "POST", { role: "user", text });
    await api("/api/inbox", "POST", { text });
    await api("/api/voice", "POST", { text }); // keep legacy get_voice_input working
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

  $("#btn-add").addEventListener("click", async () => {
    const c = screenToWorld(canvas.clientWidth / 2, canvas.clientHeight / 2);
    const node = await api("/api/nodes", "POST", { text: "", x: Math.round(c.x), y: Math.round(c.y) });
    if (node) {
      selectedId = node.id;
      setTimeout(() => {
        const el = nodeEls.get(node.id);
        if (el) {
          const t = el.querySelector(".node-text");
          t.setAttribute("contenteditable", "true");
          t.focus();
        }
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

  // ----------------------------------------------------------------------
  // Keyboard
  // ----------------------------------------------------------------------
  window.addEventListener("keydown", (e) => {
    if (e.code === "Space" && !isTyping(e)) {
      spaceDown = true;
      canvas.classList.add("panning");
    }
    if ((e.key === "Delete" || e.key === "Backspace") && !isTyping(e)) {
      if (selectedId) {
        api(`/api/nodes/${selectedId}`, "DELETE");
        selectedId = null;
      } else if (selectedImgId) {
        api(`/api/images/${selectedImgId}`, "DELETE");
        selectedImgId = null;
      }
    }
  });
  window.addEventListener("keyup", (e) => {
    if (e.code === "Space") {
      spaceDown = false;
      if (!pan) canvas.classList.remove("panning");
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
