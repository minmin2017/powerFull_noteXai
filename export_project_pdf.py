import urllib.request
import json
import os
from PIL import Image, ImageDraw, ImageFont

def export_canvas_to_pdf():
    # 1. Fetch current active project state
    res = urllib.request.urlopen("http://localhost:4321/api/state")
    state = json.loads(res.read().decode("utf-8"))

    drawings = state.get("drawings", [])
    images = state.get("images", [])
    nodes = state.get("nodes", [])
    project_title = state.get("meta", {}).get("title", "Project")

    print(f"Exporting '{project_title}' with {len(drawings)} drawings, {len(images)} images, {len(nodes)} nodes...")

    # 2. Compute bounding box
    min_x, max_x = 999999, -999999
    min_y, max_y = 999999, -999999

    for d in drawings:
        for p in d.get("points", []):
            min_x = min(min_x, p["x"])
            max_x = max(max_x, p["x"])
            min_y = min(min_y, p["y"])
            max_y = max(max_y, p["y"])

    for img in images:
        x, y, w, h = img.get("x", 0), img.get("y", 0), img.get("w", 300), img.get("h", 200)
        min_x = min(min_x, x)
        max_x = max(max_x, x + w)
        min_y = min(min_y, y)
        max_y = max(max_y, y + h)

    for n in nodes:
        x, y = n.get("x", 0), n.get("y", 0)
        min_x = min(min_x, x - 100)
        max_x = max(max_x, x + 300)
        min_y = min(min_y, y - 50)
        max_y = max(max_y, y + 100)

    # Padding
    padding = 60
    min_x -= padding
    min_y -= padding
    max_x += padding
    max_y += padding

    width = int(max_x - min_x)
    height = int(max_y - min_y)

    print(f"Canvas size: {width} x {height} px")

    # 3. Create high-res Image Canvas
    canvas = Image.new("RGB", (width, height), (18, 18, 24)) # Dark obsidian background
    draw = ImageDraw.Draw(canvas)

    # Helper coordinate transform
    def tx(x): return int(x - min_x)
    def ty(y): return int(y - min_y)

    # 4. Render Images
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for img_meta in images:
        src = img_meta.get("src", "")
        if src.startswith("/assets/"):
            rel_path = src.lstrip("/")
            local_img_path = os.path.join(base_dir, "data", rel_path.replace("/", os.sep))
            if os.path.exists(local_img_path):
                try:
                    img_obj = Image.open(local_img_path).convert("RGBA")
                    w_px = int(img_meta.get("w", img_obj.width))
                    h_px = int(img_meta.get("h", img_obj.height))
                    img_resized = img_obj.resize((w_px, h_px), Image.Resampling.LANCZOS)
                    pos_x = tx(img_meta.get("x", 0))
                    pos_y = ty(img_meta.get("y", 0))
                    canvas.paste(img_resized, (pos_x, pos_y), img_resized)
                except Exception as e:
                    print(f"Failed rendering image {src}: {e}")

    # 5. Render Drawings (Handwriting strokes)
    for d in drawings:
        color_hex = d.get("color", "#ffffff")
        stroke_w = int(d.get("width", 3))
        pts = d.get("points", [])
        if len(pts) > 1:
            line_pts = [(tx(p["x"]), ty(p["y"])) for p in pts]
            draw.line(line_pts, fill=color_hex, width=stroke_w)

    # 6. Render Text Nodes
    for n in nodes:
        text = n.get("text", "")
        if text:
            nx = tx(n.get("x", 0))
            ny = ty(n.get("y", 0))
            draw.rectangle([nx, ny, nx + 250, ny + 50], fill=(30, 30, 45), outline=(99, 102, 241), width=2)
            draw.text((nx + 10, ny + 15), text, fill="#ffffff")

    # 7. Save as PDF
    pdf_path = os.path.join(base_dir, "Ray_Dalio_Project_Full_Canvas.pdf")
    canvas.save(pdf_path, "PDF", resolution=100.0)
    print(f"Successfully exported PDF to: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    export_canvas_to_pdf()
