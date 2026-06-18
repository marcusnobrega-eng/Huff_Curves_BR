"""
Figure: Diurnal cycle of event initiation by dominant quartile.
  (a) Hour-of-day distribution of event start times (all + Q1..Q4 lines)
  (b) Modal start hour and morning-start fraction by quartile (the
      timezone-invariant monotonic gradient)

Uses shared style (Helvetica Neue Light + Okabe-Ito quartile colours).
Saves: outputs/figures/diurnal_cycle.{pdf,svg,png}  (+ manuscript copy)
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import figstyle as fs

ROOT = fs.ROOT
fs.apply_rcparams(base_size=8)

hist = pd.read_csv(ROOT / "outputs" / "diagnostics" / "diurnal_cycle.csv")
summ = pd.read_csv(ROOT / "outputs" / "diagnostics" / "diurnal_summary.csv")

QCOL = fs.QUARTILE_COLORS           # 1..4 -> Okabe-Ito
hours = hist["hour"].to_numpy()

FW = fs.TEXT_WIDTH
fig, (axA, axB) = plt.subplots(
    1, 2, figsize=(FW, FW * 0.42),
    gridspec_kw=dict(width_ratios=[1.55, 1.0], wspace=0.28))

# ── (a) hour-of-day distribution ──────────────────────────────────────────
# shade afternoon window 12-18h
axA.axvspan(12, 18, color="#f2efe6", zorder=0)
axA.text(15, axA.get_ylim()[1], "", )  # placeholder

axA.plot(hours, hist["all_pct"], color="#444444", lw=1.8, zorder=5,
         label="All events")
for q in [1, 2, 3, 4]:
    axA.plot(hours, hist[f"q{q}_pct"], color=QCOL[q], lw=1.2, zorder=4,
             label=f"Q{q}")

axA.set_xlim(0, 23)
axA.set_xticks([0, 3, 6, 9, 12, 15, 18, 21])
axA.set_xlabel("Hour of day at event start (ANA recording time)")
axA.set_ylabel("Share of events (%)")
axA.set_title("(a)  Diurnal cycle of event initiation",
              fontsize=9, fontweight=300, pad=4, loc="left")
axA.grid(axis="y", lw=0.3, color="#e6e6e6", zorder=1)
axA.spines[["top", "right"]].set_visible(False)
axA.spines[["left", "bottom"]].set_linewidth(0.4)
axA.tick_params(width=0.4)
# afternoon annotation
ymax = axA.get_ylim()[1]
axA.text(15, ymax * 0.97, "afternoon\n12–18 h", ha="center", va="top",
         fontsize=6.0, color="#8a7f55", fontweight=300, linespacing=1.2)
axA.legend(ncol=1, fontsize=6.5, framealpha=0.9, edgecolor="#cccccc",
           loc="upper left", handlelength=1.3, labelspacing=0.3)

# ── (b) modal start hour + morning fraction by quartile ───────────────────
q_order = ["Q1", "Q2", "Q3", "Q4"]
peak = [int(summ.loc[summ.group == q, "peak_hour"].iloc[0]) for q in q_order]
morn = [float(summ.loc[summ.group == q, "morning"].iloc[0]) for q in q_order]
xq = np.arange(4)
bar_cols = [QCOL[i] for i in [1, 2, 3, 4]]

# left axis: modal start hour (bars)
bars = axB.bar(xq, peak, width=0.62, color=bar_cols, edgecolor="black",
               linewidth=0.3, alpha=0.9, zorder=3)
axB.set_ylim(12, 17)
axB.set_yticks([12, 13, 14, 15, 16, 17])
axB.set_ylabel("Modal start hour")
axB.set_xticks(xq)
axB.set_xticklabels(q_order)
axB.set_xlabel("Dominant quartile")
axB.set_title("(b)  Timing gradient across quartiles",
              fontsize=9, fontweight=300, pad=4, loc="left")
axB.spines[["top"]].set_visible(False)
axB.spines[["left", "bottom", "right"]].set_linewidth(0.4)
axB.tick_params(width=0.4)
for x, p in zip(xq, peak):
    axB.text(x, p + 0.08, f"{p:02d}h", ha="center", va="bottom",
             fontsize=6.5, fontweight=300)

# right axis: morning-start fraction (line + markers)
axB2 = axB.twinx()
axB2.plot(xq, morn, color="#222222", lw=1.3, marker="o", ms=5,
          markerfacecolor="white", markeredgecolor="#222222",
          markeredgewidth=1.0, zorder=6)
axB2.set_ylabel("Morning starts, 06–12 h (%)")
axB2.set_ylim(10, 28)
axB2.spines[["top"]].set_visible(False)
axB2.spines[["left", "bottom", "right"]].set_linewidth(0.4)
axB2.tick_params(width=0.4)
for x, m in zip(xq, morn):
    axB2.text(x + 0.04, m + 0.5, f"{m:.1f}%", ha="left", va="bottom",
              fontsize=6.0, color="#222222")

axB2.legend(handles=[
    Line2D([0], [0], color="#888888", lw=4, alpha=0.8, label="Modal start hour (left)"),
    Line2D([0], [0], color="#222222", lw=1.3, marker="o", ms=4,
           markerfacecolor="white", label="Morning starts (right)"),
], fontsize=6.0, framealpha=0.9, edgecolor="#cccccc", loc="upper left",
   handlelength=1.6, labelspacing=0.3)

fs.save(fig, "diurnal_cycle")
plt.close(fig)
print("Diurnal figure written.")
