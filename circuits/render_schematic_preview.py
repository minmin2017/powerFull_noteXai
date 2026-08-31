import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, FancyArrowPatch

fig, ax = plt.subplots(figsize=(6, 5))
ax.set_xlim(-1, 6)
ax.set_ylim(-1, 6)
ax.set_aspect("equal")
ax.axis("off")

# Source B1 (circle) on the left, vertical
src_x, src_top, src_bot = 0, 4.2, 1.2
ax.add_patch(Circle((src_x, (src_top + src_bot) / 2), 0.8, fill=False, lw=2, color="#1f77b4"))
ax.plot([src_x, src_x], [src_top, src_top + 0.6], color="black", lw=1.5)
ax.plot([src_x, src_x], [src_bot, src_bot - 0.6], color="black", lw=1.5)
ax.text(src_x - 1.3, (src_top + src_bot) / 2, "B1\nv(t)", ha="center", va="center", fontsize=10, color="#1f77b4")
ax.text(src_x, (src_top + src_bot) / 2 + 0.25, "+", ha="center", fontsize=12)
ax.text(src_x, (src_top + src_bot) / 2 - 0.35, "\u2212", ha="center", fontsize=12)

top_y, bot_y = src_top + 0.6, src_bot - 0.6
right_x = 4.5

# top wire
ax.plot([src_x, right_x], [top_y, top_y], color="black", lw=1.5)
# bottom wire
ax.plot([src_x, right_x], [bot_y, bot_y], color="black", lw=1.5)

# R1 resistor (rectangle) on the right, top half
r_top, r_bot = top_y, 3.0
ax.plot([right_x, right_x], [top_y, r_top], color="black", lw=1.5)
ax.add_patch(Rectangle((right_x - 0.35, r_bot), 0.7, r_top - r_bot, fill=False, lw=2, color="#d62728"))
ax.text(right_x + 0.9, (r_top + r_bot) / 2, "R1\n5\u03a9", ha="center", va="center", fontsize=10, color="#d62728")

# wire between R1 and L1
mid_y = r_bot
l_top = mid_y
l_bot = 1.8
ax.plot([right_x, right_x], [mid_y, l_top], color="black", lw=1.5)

# L1 inductor (loops, approximated by rectangle)
ax.add_patch(Rectangle((right_x - 0.35, l_bot), 0.7, l_top - l_bot, fill=False, lw=2, color="#2ca02c", hatch="~~~"))
ax.text(right_x + 0.9, (l_top + l_bot) / 2, "L1\n15 mH", ha="center", va="center", fontsize=10, color="#2ca02c")

# wire down to bottom rail
ax.plot([right_x, right_x], [l_bot, bot_y], color="black", lw=1.5)

# ground symbol at B1 negative terminal
gnd_x, gnd_y = src_x, bot_y
ax.plot([gnd_x - 0.25, gnd_x + 0.25], [gnd_y - 0.15, gnd_y - 0.15], color="black", lw=1.5)
ax.plot([gnd_x - 0.15, gnd_x + 0.15], [gnd_y - 0.28, gnd_y - 0.28], color="black", lw=1.5)
ax.plot([gnd_x - 0.05, gnd_x + 0.05], [gnd_y - 0.41, gnd_y - 0.41], color="black", lw=1.5)

# current arrow label
ax.annotate("", xy=(right_x - 1.1, top_y + 0.35), xytext=(right_x - 1.9, top_y + 0.35),
            arrowprops=dict(arrowstyle="->", lw=1.5))
ax.text((right_x - 1.5), top_y + 0.55, "i(t)", ha="center", fontsize=10)

ax.set_title("Exercise 12 schematic (as wired in exercise12_schematic.asc)\nv(t) = 10 + 20cos(2\u03c060t\u221225\u00b0) + 30cos(4\u03c060t+20\u00b0) V", fontsize=10)

out = r"C:\Users\wicha\Desktop\powerfull_note\circuits\exercise12_schematic_preview.png"
fig.tight_layout()
fig.savefig(out, dpi=150)
print("saved:", out)
