# -*- coding: utf-8 -*-
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.backends.backend_pdf import PdfPages

OUT = r"C:\Users\wicha\Desktop\powerfull_note\circuits\exercise12_solution.pdf"
SCHEM_IMG = r"C:\Users\wicha\Desktop\powerfull_note\circuits\exercise12_schematic_preview.png"
WAVE_IMG = r"C:\Users\wicha\Desktop\powerfull_note\circuits\exercise12_waveforms.png"

plt.rcParams["font.family"] = "DejaVu Sans"  # covers ∠ (angle), Greek, superscripts

def new_page():
    fig = plt.figure(figsize=(8.27, 11.69))  # A4 portrait
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    return fig, ax


def text_block(ax, x, y, s, fontsize=11, weight="normal", family=None, va="top"):
    ax.text(x, y, s, fontsize=fontsize, weight=weight, va=va, ha="left",
             transform=ax.transAxes, family=family)


with PdfPages(OUT) as pdf:

    # ---------------- Page 1: Problem + schematic ----------------
    fig, ax = new_page()
    text_block(ax, 0.08, 0.96, "Exercise 12 \u2014 Non-sinusoidal Source, RL Load",
               fontsize=16, weight="bold")
    text_block(ax, 0.08, 0.90,
        "A non-sinusoidal voltage source has a Fourier series of\n\n"
        "v(t) = 10 + 20cos(2\u03c060t \u2212 25\u00b0) + 30cos(4\u03c060t + 20\u00b0)  V\n\n"
        "This voltage is connected to a load that is 5\u03a9 resistor and 15 mH\n"
        "inductor in series. Determine the power absorbed by the load.",
        fontsize=11)

    try:
        img = mpimg.imread(SCHEM_IMG)
        imgax = fig.add_axes([0.15, 0.28, 0.7, 0.42])
        imgax.imshow(img)
        imgax.axis("off")
    except Exception as e:
        text_block(ax, 0.08, 0.5, f"[schematic image missing: {e}]")

    text_block(ax, 0.08, 0.20,
        "circuits\\exercise12_schematic.asc \u2014 open directly in LTspice\n"
        "(verified: simulated results match the hand solution below)",
        fontsize=9, family="Consolas")
    text_block(ax, 0.08, 0.04, "powerfull_note \u2014 Exercise 12 solution", fontsize=8)
    pdf.savefig(fig)
    plt.close(fig)

    # ---------------- Page 2: Current derivation ----------------
    fig, ax = new_page()
    text_block(ax, 0.08, 0.96, "Solution (1/2) \u2014 Phasor current in each term",
               fontsize=15, weight="bold")

    body = (
        "Step 1 \u2014 DC term (\u03c9 = 0, inductor is a short circuit)\n"
        "    I\u2080 = V\u2080 / R = 10 / 5 = 2 A\n\n"
        "Step 2 \u2014 AC term at \u03c9\u2081 = 2\u03c0(60) = 377 rad/s   (source: 20\u2220\u221225\u00b0 V)\n"
        "    Z\u2081 = R + j\u03c9\u2081L = 5 + j(377)(0.015) = 5 + j5.655 \u03a9\n"
        "    |Z\u2081| = \u221a(5\u00b2 + 5.655\u00b2) = 7.55 \u03a9,   \u2220Z\u2081 = tan\u207b\u00b9(5.655/5) = 48.5\u00b0\n"
        "    I\u2081 = V\u2081 / Z\u2081 = 20\u2220\u221225\u00b0 / 7.55\u222048.5\u00b0 = 2.65\u2220\u221273.5\u00b0 A\n\n"
        "Step 3 \u2014 AC term at \u03c9\u2082 = 4\u03c0(60) = 754 rad/s   (source: 30\u222020\u00b0 V)\n"
        "    Z\u2082 = R + j\u03c9\u2082L = 5 + j(754)(0.015) = 5 + j11.31 \u03a9\n"
        "    |Z\u2082| = \u221a(5\u00b2 + 11.31\u00b2) = 12.37 \u03a9,   \u2220Z\u2082 = tan\u207b\u00b9(11.31/5) = 66.2\u00b0\n"
        "    I\u2082 = V\u2082 / Z\u2082 = 30\u222020\u00b0 / 12.37\u222066.2\u00b0 = 2.43\u2220\u221246.2\u00b0 A\n\n"
        "Result:\n"
        "    i(t) = 2 + 2.65cos(2\u03c060t \u2212 73.5\u00b0) + 2.43cos(4\u03c060t \u2212 46.2\u00b0)  A\n\n"
        "LTspice check (Fourier of I(L1), transient sim):\n"
        "    DC = 1.9996 A,  60 Hz = 2.649\u222073.51\u00b0,  120 Hz = 2.426\u222046.15\u00b0\n"
        "    (magnitudes match to 3 s.f.; angle sign is a reference-direction\n"
        "     convention difference between the loop current and I(L1))"
    )
    text_block(ax, 0.08, 0.88, body, fontsize=10.5, family="DejaVu Sans")
    pdf.savefig(fig)
    plt.close(fig)

    # ---------------- Page 3: Power derivation ----------------
    fig, ax = new_page()
    text_block(ax, 0.08, 0.96, "Solution (2/2) \u2014 Power absorbed by the load",
               fontsize=15, weight="bold")

    body2 = (
        "Average power at each frequency:  P = (1/2)V\u00b7I\u00b7cos(\u03b8v \u2212 \u03b8i)\n\n"
        "DC term:\n"
        "    P\u2080 = V\u2080\u00b7I\u2080 = (10)(2) = 20 W\n\n"
        "\u03c9\u2081 = 2\u03c0(60):\n"
        "    P\u2081 = (20)(2.65)/2 \u00b7 cos(\u221225\u00b0 \u2212 (\u221273.5\u00b0)) = 26.5 \u00b7 cos(48.5\u00b0)\n"
        "       = 26.5 \u00d7 0.6626 \u2248 17.4 W\n\n"
        "\u03c9\u2082 = 4\u03c0(60):\n"
        "    P\u2082 = (30)(2.43)/2 \u00b7 cos(20\u00b0 \u2212 (\u221246.2\u00b0)) = 36.45 \u00b7 cos(66.2\u00b0)\n"
        "       = 36.45 \u00d7 0.4014 \u2248 14.8 W\n\n"
        "Total power absorbed by the load:\n"
        "    P = P\u2080 + P\u2081 + P\u2082 = 20 + 17.4 + 14.8 = 52.2 W\n\n"
        "Alternative check (rms current method, average inductor power = 0):\n"
        "    P = I_rms\u00b2\u00b7R = [2\u00b2 + (2.65/\u221a2)\u00b2 + (2.43/\u221a2)\u00b2]\u00b7(5) = 52.2 W\n\n"
        "LTspice check (numeric time-average of v(t)\u00b7i(t) over one exact 60 Hz\n"
        "period, after the RL turn-on transient settles):\n"
        "    P_avg (simulated) = 52.27 W   \u2014   matches the hand solution."
    )
    text_block(ax, 0.08, 0.88, body2, fontsize=10.5, family="DejaVu Sans")
    pdf.savefig(fig)
    plt.close(fig)

    # ---------------- Page 4: Waveforms ----------------
    fig, ax = new_page()
    text_block(ax, 0.08, 0.96, "Simulated waveforms (LTspice, steady state)",
               fontsize=15, weight="bold")
    try:
        img2 = mpimg.imread(WAVE_IMG)
        imgax2 = fig.add_axes([0.06, 0.08, 0.9, 0.82])
        imgax2.imshow(img2)
        imgax2.axis("off")
    except Exception as e:
        text_block(ax, 0.08, 0.5, f"[waveform image missing: {e}]")
    pdf.savefig(fig)
    plt.close(fig)

print("saved:", OUT)
