"""Convert branding/min_icon.png into branding/icon.ico for the desktop shortcut.

Usage: python tools/make_icon.py
"""
import os
import sys

from PIL import Image

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(WORKSPACE, "branding", "min_icon.png")
DST = os.path.join(WORKSPACE, "branding", "icon.ico")

def main():
    if not os.path.exists(SRC):
        print(f"Error: {SRC} not found. Generate/save the icon image there first.")
        sys.exit(1)
    img = Image.open(SRC).convert("RGBA")
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(DST, format="ICO", sizes=sizes)
    print(f"Wrote {DST}")

if __name__ == "__main__":
    main()
