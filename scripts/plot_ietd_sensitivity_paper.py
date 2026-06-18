"""
Publication-quality IETD sensitivity figure           (G3)
===========================================================
Single figure with 4 panels (2 × 2):

  (a) Event count and median duration vs IETD
  (b) Event-level quartile fraction (%) vs IETD
  (c) Station-level Q1 fraction (%) vs IETD — national + biomes
  (d) Curve-fit quality vs IETD — MAE and D_max for Q1–Q4

Baseline IETD = 6 h marked with a vertical dashed line on every panel.

Output: outputs/figures/ietd_sensitivity.pdf / .svg / .png
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches

ROOT    = Path(__file__).resolve().parent.parent
SENS    = ROOT / "outputs" / "sensitivity"
FIG_DIR = ROOT / "outputs" / "figures"

# ── load data ────────────────────────────────────────────────────────────────
evt    = pd.read_csv(SENS / "ietd_event_stats.csv")
curv   = pd.read_csv(SENS / "ietd_curve_metrics.csv")
summ   = pd.read_csv(SENS / "ietd_sensitivity_summary.csv")
agree  = pd.read_csv(SENS / "ietd_quartile_agreement.csv")

IETD_VALS = sorted(evt["ietd_h"].unique())
BASELINE  = 6

# ── style ────────────────────────────────────────────────────────────────────
MM = 1/25.4; FW = 190*MM
QCOL = {1:"#1f77b4", 2:"#2ca02c", 3:"#ff7f0e", 4:"#d62728"}
QLBL = {1:"Q1", 2:"Q2", 3:"Q3", 4:"Q4"}

BIOME_COLOR = {
    "Amazônia":      "#1b7837",
    "Caatinga":      "#d8b365",
    "Cerrado":       "#f6e8c3",   # too light → use a stronger shade
    "Mata Atlântica":"#762a83",
    "Pampa":         "#74add1",
    "Pantanal":      "#4d9221",
}
# use more distinguishable biome colours
BIOME_COLOR = {
    "Amazônia":      "#2166ac",
    "Caatinga":      "#e08214",
    "Cerrado":       "#8073ac",
    "Mata Atlântica":"#d6604d",
    "Pampa":         "#35978f",
    "Pantanal":      "#000000",
}
BIOME_LS = {
    "Amazônia":      "-",
    "Caatinga":      "--",
    "Cerrado":       "-.",
    "Mata Atlântica":":",
    "Pampa":         (0,(3,1,1,1)),
    "Pantanal":      (0,(5,2)),
}
BIOME_MARKER = {
    "Amazônia":"o","Caatinga":"s","Cerrado":"^",
    "Mata Atlântica":"D","Pampa":"v","Pantanal":"*",
}

plt.rcParams.update({
    "font.family":"sans-serif","font.size":8,
    "axes.labelsize":9,"axes.titlesize":9,
    "xtick.labelsize":8,"ytick.labelsize":8,
    "legend.fontsize":7,"axes.linewidth":0.6,
    "grid.linewidth":0.35,"grid.color":"#dddddd",
    "figure.dpi":200,"savefig.dpi":300,
    "pdf.fonttype":42,"svg.fonttype":"none",
})

BASELINE_KW = dict(color="#555555", ls="--", lw=0.8, zorder=0, alpha=0.7)

fig, axes = plt.subplots(2, 2, figsize=(FW, FW*0.88), constrained_layout=True)
(ax_a, ax_b), (ax_c, ax_d) = axes

x = np.array(IETD_VALS)

# ── Panel (a): event count + median duration ─────────────────────────────────
ax_a2 = ax_a.twinx()

color_cnt = "#1f77b4"
color_dur = "#d62728"

lns1 = ax_a.plot(x, evt["n_events"]/1000, color=color_cnt, lw=1.5,
                 marker="o", ms=5, zorder=3, label="Event count (×10³)")
lns2 = ax_a2.plot(x, evt["median_duration_h"], color=color_dur, lw=1.5,
                  marker="s", ms=5, ls="--", zorder=3, label="Median duration (h)")

ax_a.axvline(BASELINE, **BASELINE_KW)
ax_a.set_xlabel("IETD (h)")
ax_a.set_ylabel("Event count (×10³)", color=color_cnt)
ax_a2.set_ylabel("Median event duration (h)", color=color_dur)
ax_a.tick_params(axis="y", colors=color_cnt)
ax_a2.tick_params(axis="y", colors=color_dur)
ax_a.yaxis.set_major_formatter(mticker.FormatStrFormatter("%d"))
ax_a.set_xticks(x)
ax_a.set_ylim(250, 300)
ax_a.grid(True, axis="x")
ax_a.set_title("(a)  Events vs IETD", fontweight="bold", pad=3)

# combined legend
lns = lns1 + lns2
ax_a.legend(lns, [l.get_label() for l in lns], loc="lower center",
            framealpha=0.9, edgecolor="#aaaaaa")
ax_a.annotate("baseline", xy=(BASELINE, ax_a.get_ylim()[0]),
              xytext=(BASELINE+0.3, 252), fontsize=6.5, color="#555555")

# ── Panel (b): event-level quartile fraction ─────────────────────────────────
for q in [1,2,3,4]:
    col = f"q{q}_pct"
    ax_b.plot(x, evt[col], color=QCOL[q], lw=1.5, marker="o", ms=5,
              label=QLBL[q], zorder=3)

ax_b.axvline(BASELINE, **BASELINE_KW)
ax_b.set_xlabel("IETD (h)")
ax_b.set_ylabel("Event fraction (%)")
ax_b.set_xticks(x)
ax_b.set_ylim(0, 55)
ax_b.grid(True, axis="x")
ax_b.set_title("(b)  Event-level quartile fraction vs IETD", fontweight="bold", pad=3)
ax_b.legend(loc="upper right", framealpha=0.9, edgecolor="#aaaaaa",
            ncol=2, columnspacing=0.8)

# ── Panel (c): station Q1 fraction — national + biomes ─────────────────────
nat = summ[summ["scope"]=="national"].sort_values("ietd_h")
ax_c.plot(nat["ietd_h"], nat["q1_pct"], color="#222222", lw=2.0,
          marker="D", ms=6, zorder=4, label="National", clip_on=False)

biome_order = ["Amazônia","Caatinga","Cerrado","Mata Atlântica","Pampa","Pantanal"]
for biome in biome_order:
    sub = summ[(summ["scope"]=="biome") & (summ["region"]==biome)].sort_values("ietd_h")
    if sub.empty:
        continue
    ax_c.plot(sub["ietd_h"], sub["q1_pct"],
              color=BIOME_COLOR[biome], lw=1.2,
              ls=BIOME_LS[biome],
              marker=BIOME_MARKER[biome], ms=4.5,
              zorder=3, label=biome)

ax_c.axvline(BASELINE, **BASELINE_KW)
ax_c.set_xlabel("IETD (h)")
ax_c.set_ylabel("Q1-dominant stations (%)")
ax_c.set_xticks(x)
ax_c.set_ylim(60, 102)
ax_c.grid(True, axis="x")
ax_c.set_title("(c)  Station Q1 fraction vs IETD", fontweight="bold", pad=3)
ax_c.legend(loc="lower right", framealpha=0.9, edgecolor="#aaaaaa",
            fontsize=6.5, ncol=2, columnspacing=0.5, handlelength=2)

# ── Panel (d): MAE and D_max for Q1–Q4 ──────────────────────────────────────
ax_d2 = ax_d.twinx()

for q in [1,2,3,4]:
    sub = curv[curv["quartile"]==q].sort_values("ietd_h")
    ax_d.plot(sub["ietd_h"], sub["mae"], color=QCOL[q], lw=1.4,
              marker="o", ms=4.5, ls="-", zorder=3)
    ax_d2.plot(sub["ietd_h"], sub["d_max"], color=QCOL[q], lw=1.0,
               marker="s", ms=4, ls="--", zorder=3, alpha=0.8)

ax_d.axvline(BASELINE, **BASELINE_KW)
ax_d.set_xlabel("IETD (h)")
ax_d.set_ylabel("MAE (–––)", color="#333333")
ax_d2.set_ylabel("D_max (– –)", color="#333333")
ax_d.set_xticks(x)
ax_d.grid(True, axis="x")
ax_d.set_title("(d)  Curve-fit quality vs IETD", fontweight="bold", pad=3)

# legend: quartile colours + line style for MAE vs Dmax
q_handles = [Line2D([0],[0], color=QCOL[q], lw=1.4, label=QLBL[q])
             for q in [1,2,3,4]]
style_handles = [
    Line2D([0],[0], color="#555555", lw=1.4, ls="-",  label="MAE"),
    Line2D([0],[0], color="#555555", lw=1.0, ls="--", label="D_max"),
]
ax_d.legend(handles=q_handles+style_handles, loc="upper left",
            framealpha=0.9, edgecolor="#aaaaaa", fontsize=6.5,
            ncol=2, columnspacing=0.6)

# ── save ─────────────────────────────────────────────────────────────────────
stem = FIG_DIR / "ietd_sensitivity"
for ext, dpi in [("pdf",None),("svg",None),("png",150)]:
    kw = dict(bbox_inches="tight")
    if dpi: kw["dpi"] = dpi
    fig.savefig(str(stem)+f".{ext}", format=ext, **kw)
    print(f"  → {stem}.{ext}")

plt.close(fig)
print("Done.")
