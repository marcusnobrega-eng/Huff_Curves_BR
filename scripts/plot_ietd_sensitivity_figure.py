"""
IETD Sensitivity Figure (G3)
=============================
Four-panel publication figure for the supplementary material.
  (a) Event count + median duration vs IETD
  (b) Event-level quartile fraction vs IETD
  (c) Station Q1 fraction nationally and by biome vs IETD
  (d) MAE and D_max of empirical Q1–Q4 curves vs Huff (1967) reference

Saves: outputs/figures/ietd_sensitivity.pdf / .svg / .png
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")

import glob as _glob, os as _os
from pathlib import Path as _Path
for _f in _glob.glob(str(_Path(__file__).resolve().parent.parent / "assets" / "fonts" / "*.ttf")):
    import matplotlib.font_manager as _fm; _fm.fontManager.addfont(_f)
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT    = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "outputs" / "figures"
BOOT    = ROOT / "outputs" / "sensitivity"

# ── load sensitivity tables ────────────────────────────────────────────────
evt   = pd.read_csv(BOOT / "ietd_event_stats.csv")
summ  = pd.read_csv(BOOT / "ietd_sensitivity_summary.csv")
curve = pd.read_csv(BOOT / "ietd_curve_metrics.csv")

IETD  = [2, 4, 6, 8, 12]
BASE  = 6

# ── style ──────────────────────────────────────────────────────────────────
MM = 1/25.4; FW = 190*MM
plt.rcParams.update({
    "font.family":"Helvetica Neue","font.weight":300,"font.size":8,
    "axes.labelsize":9,"axes.titlesize":9,
    "xtick.labelsize":8,"ytick.labelsize":8,
    "legend.fontsize":7.5,"axes.linewidth":0.6,
    "grid.linewidth":0.4,"grid.color":"#cccccc",
    "figure.dpi":200,"savefig.dpi":300,
    "pdf.fonttype":42,"svg.fonttype":"none",
})

QCOL = {1:"#0072B2", 2:"#009E73", 3:"#E69F00", 4:"#D55E00"}  # Okabe-Ito
BIOME_COLS = {
    "Amazônia":       "#009E73",
    "Caatinga":       "#E69F00",
    "Cerrado":        "#F0E442",
    "Mata Atlântica": "#0072B2",
    "Pampa":          "#56B4E9",
    "Pantanal":       "#CC79A7",
}
BASE_LW   = 1.5
THIN_LW   = 1.0
BASE_VLINE_KW = dict(x=BASE, color="#555555", ls="--", lw=0.8, alpha=0.7)

fig, axes = plt.subplots(2, 2, figsize=(FW, FW*0.85), constrained_layout=True)
panel_labels = ["(a)", "(b)", "(c)", "(d)"]

# ── (a) Event count + median duration ─────────────────────────────────────
ax = axes[0][0]
ax2 = ax.twinx()

color_n   = "#0072B2"   # Okabe-Ito blue (markers only)
color_dur = "#D55E00"   # Okabe-Ito vermillion (markers only)

ax.plot(evt["ietd_h"], evt["n_events"]/1000, "o-",
        color=color_n, lw=BASE_LW, ms=5, zorder=3)
ax2.plot(evt["ietd_h"], evt["median_duration_h"], "s--",
         color=color_dur, lw=THIN_LW, ms=4, zorder=3)

ax.axvline(**BASE_VLINE_KW)
ax.set_xlabel("IETD (h)")
# y-axis labels and ticks kept black; series distinguished by legend
ax.set_ylabel("Events (×1,000)")
ax2.set_ylabel("Median duration (h)")
ax.set_xticks(IETD)
ax.grid(True, zorder=0)
ax.set_title(f"{panel_labels[0]}  Event count and duration", fontweight=300, pad=3)

leg = [Line2D([0],[0], color=color_n, lw=BASE_LW, marker="o", ms=5,
              label="Events (×1,000)"),
       Line2D([0],[0], color=color_dur, lw=THIN_LW, ls="--", marker="s", ms=4,
              label="Median duration (h)")]
ax.legend(handles=leg, loc="upper right", framealpha=0.9, edgecolor="#aaaaaa")

# ── (b) Event-level quartile fraction ─────────────────────────────────────
ax = axes[0][1]
for q in [1,2,3,4]:
    ax.plot(evt["ietd_h"], evt[f"q{q}_pct"], "o-",
            color=QCOL[q], lw=BASE_LW, ms=5, label=f"Q{q}", zorder=3)

ax.axvline(**BASE_VLINE_KW)
ax.set_xlabel("IETD (h)")
ax.set_ylabel("Event-level quartile fraction (%)")
ax.set_xticks(IETD)
ax.grid(True, zorder=0)
ax.set_title(f"{panel_labels[1]}  Quartile fraction (events)", fontweight=300, pad=3)
ax.legend(ncol=2, framealpha=0.9, edgecolor="#aaaaaa", loc="center right")

# ── (c) Station Q1 fraction nationally + by biome ─────────────────────────
ax = axes[1][0]

# national
nat = summ[summ["scope"] == "national"].sort_values("ietd_h")
ax.plot(nat["ietd_h"], nat["q1_pct"], "k-o",
        lw=2.0, ms=6, zorder=5, label="National")

# biomes
for biome, col in BIOME_COLS.items():
    sub = summ[(summ["scope"]=="biome") & (summ["region"]==biome)].sort_values("ietd_h")
    if sub.empty:
        continue
    ax.plot(sub["ietd_h"], sub["q1_pct"], "o--",
            color=col, lw=THIN_LW, ms=4, alpha=0.85,
            label=biome.replace("Mata Atlântica","Mata Atl."))

ax.axvline(**BASE_VLINE_KW)
ax.set_xlabel("IETD (h)")
ax.set_ylabel("Stations with dominant Q1 (%)")
ax.set_xticks(IETD)
ax.set_ylim(60, 102)
ax.grid(True, zorder=0)
ax.set_title(f"{panel_labels[2]}  Q1 station fraction", fontweight=300, pad=3)
ax.legend(ncol=2, fontsize=6.5, framealpha=0.9, edgecolor="#aaaaaa",
          loc="lower right")

# ── (d) MAE and D_max by quartile ─────────────────────────────────────────
ax = axes[1][1]

for q in [1,2,3,4]:
    sub = curve[curve["quartile"]==q].sort_values("ietd_h")
    ax.plot(sub["ietd_h"], sub["mae"], "o-",
            color=QCOL[q], lw=BASE_LW, ms=5,
            label=f"Q{q} MAE", zorder=3)
    ax.plot(sub["ietd_h"], sub["d_max"], "s--",
            color=QCOL[q], lw=THIN_LW, ms=4, alpha=0.7,
            label=f"Q{q} D_max", zorder=2)

ax.axvline(**BASE_VLINE_KW)
ax.set_xlabel("IETD (h)")
ax.set_ylabel("Curve metric vs Huff (1967) reference")
ax.set_xticks(IETD)
ax.grid(True, zorder=0)
ax.set_title(f"{panel_labels[3]}  MAE and D_max vs Huff (1967)", fontweight=300, pad=3)

# compact legend: one row per quartile, solid=MAE, dashed=D_max
leg2 = []
for q in [1,2,3,4]:
    leg2.append(Line2D([0],[0], color=QCOL[q], lw=BASE_LW, marker="o", ms=4,
                       label=f"Q{q} MAE"))
    leg2.append(Line2D([0],[0], color=QCOL[q], lw=THIN_LW, ls="--", marker="s", ms=3,
                       label=f"Q{q} D_max", alpha=0.8))
ax.legend(handles=leg2, ncol=2, fontsize=6.5, framealpha=0.9,
          edgecolor="#aaaaaa", loc="upper left")

# baseline annotation on all panels
for ax_row in axes:
    for ax_ in ax_row:
        ax_.text(BASE+0.1, ax_.get_ylim()[0] +
                 0.03*(ax_.get_ylim()[1]-ax_.get_ylim()[0]),
                 "baseline\n6 h", fontsize=6, color="#555555", va="bottom")

def save_fig(fig, stem):
    for ext, dpi in [("pdf",None),("svg",None),("png",150)]:
        kw = dict(bbox_inches="tight")
        if dpi: kw["dpi"] = dpi
        fig.savefig(str(stem)+f".{ext}", format=ext, **kw)
    print(f"  → {stem}.pdf / .svg / .png")

save_fig(fig, FIG_DIR / "ietd_sensitivity")
plt.close(fig)
print("IETD sensitivity figure done.")
