/**
 * modules/export.js
 * Export functions: Markdown, PNG, PDF
 * Receives app internals via dependency injection (setup pattern).
 */
export default function setupExport({ STATE, view, canvas, world, toast, render, flushFx }) {
  // ------------------------------------------------------------------
  // Export Markdown
  // ------------------------------------------------------------------
  function exportMarkdown() {
    const byId = new Map(STATE.nodes.map((n) => [n.id, n]));
    const roots = STATE.nodes.filter((n) => !n.parentId);
    const lines = [`# ${STATE.meta?.title || "Mind Map"}`, ""];
    function walk(node, depth) {
      const prefix = "#".repeat(Math.min(depth + 1, 6));
      const tagStr = (node.tags || []).map((t) => `\`${t}\``).join(" ");
      lines.push(`${prefix} ${node.text}${tagStr ? " " + tagStr : ""}`);
      STATE.nodes
        .filter((n) => n.parentId === node.id)
        .sort((a, b) => a.y - b.y)
        .forEach((child) => walk(child, depth + 1));
    }
    roots.sort((a, b) => a.y - b.y).forEach((r) => walk(r, 1));
    const blob = new Blob([lines.join("\n")], { type: "text/markdown" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${(STATE.meta?.title || "mindmap").replace(/[^a-z0-9ก-๙]+/gi, "_")}.md`;
    a.click();
    URL.revokeObjectURL(a.href);
    toast("ดาวน์โหลด Markdown แล้ว ✓");
  }

  // ------------------------------------------------------------------
  // Capture full board (shared by PNG and PDF)
  // ------------------------------------------------------------------
  async function captureFullBoard(renderScale) {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    const consider = (x, y, w, h) => {
      minX = Math.min(minX, x); minY = Math.min(minY, y);
      maxX = Math.max(maxX, x + w); maxY = Math.max(maxY, y + h);
    };
    STATE.nodes.forEach((n) => consider(n.x, n.y, n.w || 200, n.h || 60));
    (STATE.boxes || []).forEach((b) => consider(b.x, b.y, b.w || 240, b.h || 180));
    (STATE.images || []).forEach((i) => consider(i.x, i.y, i.w || 160, i.h || 160));
    (STATE.drawings || []).forEach((d) => {
      const half = (d.width || 2) / 2 + 4;
      (d.points || []).forEach((p) => consider(p.x - half, p.y - half, half * 2, half * 2));
    });
    if (!isFinite(minX)) { minX = 0; minY = 0; maxX = canvas.clientWidth; maxY = canvas.clientHeight; }
    const pad = 80;
    minX -= pad; minY -= pad; maxX += pad; maxY += pad;
    const fullW = Math.ceil(maxX - minX);
    const fullH = Math.ceil(maxY - minY);

    const htmlEl = document.documentElement;
    const bodyEl = document.body;
    const stageEl = document.getElementById("stage");

    const prevView = { ...view };
    const prevStyle = {
      width: canvas.style.width, height: canvas.style.height,
      overflow: canvas.style.overflow, flex: canvas.style.flex,
    };
    const prevStageOverflow = stageEl.style.overflow;
    const prevHtmlOverflow = htmlEl.style.overflow;
    const prevBodyOverflow = bodyEl.style.overflow;

    view.scale = 1;
    view.x = -minX;
    view.y = -minY;
    htmlEl.style.overflow = "visible";
    bodyEl.style.overflow = "visible";
    stageEl.style.overflow = "visible";
    canvas.style.flex = "0 0 auto";
    canvas.style.overflow = "visible";
    canvas.style.width = fullW + "px";
    canvas.style.height = fullH + "px";
    render();
    flushFx();
    await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));

    try {
      return await html2canvas(canvas, {
        backgroundColor: getComputedStyle(document.body).getPropertyValue("--bg").trim() || "#0f172a",
        width: fullW,
        height: fullH,
        windowWidth: Math.max(fullW, window.innerWidth),
        windowHeight: Math.max(fullH, window.innerHeight),
        scale: renderScale,
        useCORS: true,
        logging: false,
      });
    } finally {
      stageEl.style.overflow = prevStageOverflow;
      htmlEl.style.overflow = prevHtmlOverflow;
      bodyEl.style.overflow = prevBodyOverflow;
      Object.assign(view, prevView);
      canvas.style.flex = prevStyle.flex;
      canvas.style.width = prevStyle.width;
      canvas.style.height = prevStyle.height;
      canvas.style.overflow = prevStyle.overflow;
      render();
    }
  }

  // ------------------------------------------------------------------
  // Export PNG
  // ------------------------------------------------------------------
  async function exportPng() {
    if (typeof html2canvas !== "function") {
      toast("html2canvas ยังโหลดไม่เสร็จ ลองอีกครั้ง");
      return;
    }
    toast("กำลัง render PNG ทั้งหน้า…");
    try {
      const cvs = await captureFullBoard(2);
      const a = document.createElement("a");
      a.href = cvs.toDataURL("image/png");
      a.download = `${(STATE.meta?.title || "mindmap").replace(/[^a-z0-9ก-๙]+/gi, "_")}.png`;
      a.click();
      toast("ดาวน์โหลด PNG แล้ว ✓ (ทั้งหน้า)");
    } catch (err) {
      toast("Export PNG ไม่สำเร็จ: " + err.message);
    }
  }

  // ------------------------------------------------------------------
  // Export PDF
  // ------------------------------------------------------------------
  async function exportPdf() {
    if (typeof html2canvas !== "function") {
      toast("html2canvas ยังโหลดไม่เสร็จ ลองอีกครั้ง");
      return;
    }
    if (typeof window.jspdf === "undefined") {
      toast("jsPDF ยังโหลดไม่เสร็จ ลองอีกครั้ง");
      return;
    }
    toast("กำลัง render PDF ความละเอียดสูง…");
    try {
      const rect = canvas.getBoundingClientRect();
      const probeW = Math.max(rect.width, 800);
      const probeH = Math.max(rect.height, 600);
      let scale = Math.min(3, Math.max(1.5, 4096 / Math.max(probeW, probeH)));
      const cvs = await captureFullBoard(scale);
      const maxPixels = 60_000_000;
      let finalCanvas = cvs;
      if (cvs.width * cvs.height > maxPixels) {
        const shrink = Math.sqrt(maxPixels / (cvs.width * cvs.height));
        const sc = document.createElement("canvas");
        sc.width = Math.round(cvs.width * shrink);
        sc.height = Math.round(cvs.height * shrink);
        sc.getContext("2d").drawImage(cvs, 0, 0, sc.width, sc.height);
        finalCanvas = sc;
      }
      const { jsPDF } = window.jspdf;
      const pdf = new jsPDF({
        orientation: finalCanvas.width >= finalCanvas.height ? "landscape" : "portrait",
        unit: "px",
        format: [finalCanvas.width, finalCanvas.height],
      });
      pdf.addImage(finalCanvas.toDataURL("image/png"), "PNG", 0, 0, finalCanvas.width, finalCanvas.height);
      pdf.save(`${(STATE.meta?.title || "mindmap").replace(/[^a-z0-9ก-๙]+/gi, "_")}.pdf`);
      toast("ดาวน์โหลด PDF แล้ว ✓ (ทั้งหน้า ความละเอียดสูง)");
    } catch (err) {
      toast("Export PDF ไม่สำเร็จ: " + err.message);
    }
  }

  // ------------------------------------------------------------------
  // Wire up buttons
  // ------------------------------------------------------------------
  document.getElementById("btn-export-md").addEventListener("click", exportMarkdown);
  document.getElementById("btn-export-png").addEventListener("click", exportPng);
  document.getElementById("btn-export-pdf").addEventListener("click", exportPdf);
}
