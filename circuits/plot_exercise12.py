from spicelib import RawRead
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

raw = RawRead(r"C:\Users\wicha\Desktop\powerfull_note\circuits\exercise12_non_sinusoidal.raw")

t = np.array(raw.get_trace("time").get_wave(), dtype=float)
v = np.array(raw.get_trace("V(vin)").get_wave(), dtype=float)
i = np.array(raw.get_trace("I(L1)").get_wave(), dtype=float)
p = v * i

# show 2 periods of 60Hz AFTER the RL turn-on transient has settled
# (tau = L/R = 3ms; starting at t=20ms is >6 tau so only the periodic
# steady-state waveform remains, matching the phasor-based textbook solution)
win_start, win_len = 0.02, 0.0334
mask = (t >= win_start) & (t <= win_start + win_len)
t2 = (t[mask] - win_start)
v2, i2, p2 = v[mask], i[mask], p[mask]

# true average power: integrate over an EXACT number of 60Hz periods
# after the RL transient (tau = L/R = 3ms) has died out, else a partial-period
# window biases the mean (verified: 20-50ms window alone gives ~40.6W, not 52.2W)
T60 = 1 / 60
settle = 0.02
period_mask = (t >= settle) & (t <= settle + T60)
avg_p = np.trapezoid(p[period_mask], t[period_mask]) / T60

fig, axes = plt.subplots(3, 1, figsize=(9, 9), sharex=True)

axes[0].plot(t2 * 1000, v2, color="#1f77b4")
axes[0].set_ylabel("v(t) [V]")
axes[0].set_title("Source voltage v(t)")
axes[0].grid(True, alpha=0.3)

axes[1].plot(t2 * 1000, i2, color="#d62728")
axes[1].set_ylabel("i(t) [A]")
axes[1].set_title("Load current i(t)")
axes[1].grid(True, alpha=0.3)

axes[2].plot(t2 * 1000, p2, color="#2ca02c")
axes[2].axhline(avg_p, color="black", linestyle="--", linewidth=1,
                 label=f"avg P = {avg_p:.1f} W")
axes[2].set_ylabel("p(t) [W]")
axes[2].set_xlabel("time [ms]")
axes[2].set_title("Instantaneous power absorbed by load")
axes[2].legend(loc="upper right")
axes[2].grid(True, alpha=0.3)

fig.suptitle("Exercise 12 - Non-sinusoidal source, R=5\u03a9 + L=15mH series load", y=1.0)
fig.tight_layout()
out_path = r"C:\Users\wicha\Desktop\powerfull_note\circuits\exercise12_waveforms.png"
fig.savefig(out_path, dpi=150)
print("saved:", out_path)
print("average power (numeric):", avg_p)
