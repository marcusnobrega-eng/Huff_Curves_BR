"""
Publication-quality station maps
=================================
Generates three figures saved as PDF, SVG and PNG:

  Figure 4  (map_dominant_quartile.pdf/.svg)
    Single-panel Brazil map — stations coloured by dominant quartile.
    Non-OK stations shown as small grey markers for spatial context.

  Figure 5  (map_mae_dmax.pdf/.svg)
    Two-panel map:
      (a) Q1 MAE — departure of empirical Q1 curve from Huff (1967)
      (b) Mean D_max across Q1–Q4

  Figure 6  (map_record_length.pdf/.svg)
    Single-panel — stations coloured by years of record (data-availability map).

Design spec
  Width  : 190 mm (double-column Elsevier)
  Font   : DejaVu Sans
  Projection: PlateCarrée (EPSG:4326) — suitable for Brazil's extent
  Biome boundaries overlaid in light grey for geographic context
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import matplotlib.colors as mcolors
import matplotlib.cm as cm
import geopandas as gpd

# ── paths ───────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "outputs" / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RESULTS_PATH = ROOT / "outputs" / "station_huff_coefficients.csv"
BRAZIL_PATH  = ROOT / "data" / "reference" / "ibge" / "normalized" / "brazil.gpkg"
BIOMES_PATH  = ROOT / "data" / "reference" / "ibge" / "normalized" / "biomes.gpkg"
STATES_PATH  = ROOT / "data" / "reference" / "ibge" / "normalized" / "states.gpkg"

# ── style constants ──────────────────────────────────────────────────────────
MM      = 1 / 25.4
FW      = 190 * MM
QCOL    = {1: "#1f77b4", 2: "#2ca02c", 3: "#ff7f0e", 4: "#d62728"}
QLBL    = {1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"}
TICK_FS = 8; LABEL_FS = 9; PANEL_FS = 9; LEGEND_FS = 7.5; ANNOT_FS = 7

# Brazil approximate bounds (with padding)
LON_MIN, LON_MAX = -74.5, -28.5
LAT_MIN, LAT_MAX = -34.5,   5.5
ASPECT = (LON_MAX - LON_MIN) / (LAT_MAX - LAT_MIN)  # ≈ 1.18

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": TICK_FS,
    "axes.labelsize": LABEL_FS,
    "axes.titlesize": PANEL_FS,
    "xtick.labelsize": TICK_FS,
    "ytick.labelsize": TICK_FS,
    "legend.fontsize": LEGEND_FS,
    "axes.linewidth": 0.5,
    "figure.dpi": 200,
    "savefig.dpi": 300,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
})

# ── load data ────────────────────────────────────────────────────────────────
print("Loading station data …")
df = pd.read_csv(RESULTS_PATH)
ok = df[df["status"] == "ok"].copy()
not_ok = df[df["status"] != "ok"].copy()

# numeric coerce
for col in ["lat", "lon", "dominant_quartile", "q1_mae", "q1_d_max",
            "mae_mean", "d_max_mean", "years_span"]:
    df[col]     = pd.to_numeric(df[col],     errors="coerce")
    if col in ok.columns:
        ok[col] = pd.to_numeric(ok[col],     errors="coerce")

print("Loading geographic layers …")
brazil = gpd.read_file(BRAZIL_PATH)
biomes = gpd.read_file(BIOMES_PATH)
states = gpd.read_file(STATES_PATH)

# ── helper: draw base map ────────────────────────────────────────────────────
def base_map(ax, show_states=False):
    brazil.plot(ax=ax, facecolor="none", edgecolor="#222222",
                linewidth=0.7, zorder=3)
    biomes.plot(ax=ax, facecolor="none", edgecolor="#aaaaaa",
                linewidth=0.35, zorder=2)
    if show_states:
        states.plot(ax=ax, facecolor="none", edgecolor="#888888",
                    linewidth=0.3, zorder=2)
    ax.set_xlim(LON_MIN, LON_MAX)
    ax.set_ylim(LAT_MIN, LAT_MAX)
    ax.set_facecolor("#e8f4fd")
    ax.set_aspect("equal")
    ax.set_xlabel("Longitude (°)", fontsize=LABEL_FS)
    ax.set_ylabel("Latitude (°)",  fontsize=LABEL_FS)
    ax.tick_params(labelsize=TICK_FS)


def save(fig, stem: Path):
    for ext in ("pdf", "svg", "png"):
        dpi = 150 if ext == "png" else None
        kw  = dict(bbox_inches="tight")
        if dpi: kw["dpi"] = dpi
        fig.savefig(str(stem) + f".{ext}", format=ext, **kw)
    print(f"  → {stem}.pdf / .svg / .png")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 4 — Dominant quartile map
# ══════════════════════════════════════════════════════════════════════════════
print("\nBuilding Figure 4 — dominant quartile map …")

fig4, ax4 = plt.subplots(1, 1, figsize=(FW, FW / ASPECT * 1.05),
                          constrained_layout=True)
base_map(ax4, show_states=True)

# non-OK stations (context dots — skipped or no-events)
mask_non = not_ok["lat"].notna() & not_ok["lon"].notna()
ax4.scatter(not_ok.loc[mask_non, "lon"], not_ok.loc[mask_non, "lat"],
            s=2, c="#cccccc", alpha=0.35, lw=0, zorder=4,
            rasterized=True)

# OK stations by dominant quartile — larger dots, drawn last
counts = {}
for q in [1, 2, 3, 4]:
    sub = ok[ok["dominant_quartile"] == q]
    counts[q] = len(sub)
    ax4.scatter(sub["lon"], sub["lat"],
                s=11, c=QCOL[q], alpha=0.9, lw=0.2,
                edgecolors="white", zorder=5, rasterized=True)

# legend — quartiles + non-OK + biome boundary line
legend_handles = [
    mpatches.Patch(color=QCOL[q],
                   label=f"{QLBL[q]}  (n = {counts[q]:,})")
    for q in [1, 2, 3, 4]
]
legend_handles += [
    mpatches.Patch(color="#cccccc",
                   label=f"Not used  (n = {len(not_ok):,})"),
    Line2D([0], [0], color="#aaaaaa", lw=0.8,
           label="Biome boundary"),
]
ax4.legend(handles=legend_handles, loc="lower left", framealpha=0.92,
           edgecolor="#aaaaaa", fontsize=LEGEND_FS, markerscale=1.0,
           title="Dominant quartile", title_fontsize=LEGEND_FS)

ax4.set_title("(a)  Dominant Huff quartile per station",
              fontsize=PANEL_FS, fontweight="bold", pad=4)

save(fig4, OUT_DIR / "map_dominant_quartile")
plt.close(fig4)


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 5 — MAE and D_max maps (two panels side by side)
# ══════════════════════════════════════════════════════════════════════════════
print("Building Figure 5 — MAE and D_max maps …")

panel_h = FW / ASPECT * 1.05

fig5, (ax5a, ax5b) = plt.subplots(1, 2, figsize=(FW, panel_h),
                                   constrained_layout=True)

for ax, col, label, panel_tag in [
    (ax5a, "q1_mae",    "Q1 MAE",       "(a)"),
    (ax5b, "d_max_mean","Mean D_max",   "(b)"),
]:
    base_map(ax, show_states=False)

    sub = ok.dropna(subset=[col])
    vmin = sub[col].quantile(0.02)
    vmax = sub[col].quantile(0.98)

    sc = ax.scatter(sub["lon"], sub["lat"],
                    c=sub[col], cmap="plasma_r",
                    vmin=vmin, vmax=vmax,
                    s=7, alpha=0.85, lw=0.1,
                    edgecolors="none", zorder=5, rasterized=True)

    cb = fig5.colorbar(sc, ax=ax, orientation="horizontal",
                       pad=0.04, fraction=0.035, aspect=30)
    cb.set_label(label, fontsize=LABEL_FS - 0.5)
    cb.ax.tick_params(labelsize=TICK_FS - 1)

    ax.set_title(f"{panel_tag}  {label} vs Huff (1967)",
                 fontsize=PANEL_FS, fontweight="bold", pad=4)

    # annotate median
    median_val = sub[col].median()
    ax.text(0.98, 0.98, f"median = {median_val:.3f}",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=ANNOT_FS, color="#222222",
            bbox=dict(boxstyle="round,pad=0.3", fc="white",
                      ec="#aaaaaa", alpha=0.85))

save(fig5, OUT_DIR / "map_mae_dmax")
plt.close(fig5)


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 6 — Record length (data availability) map
# ══════════════════════════════════════════════════════════════════════════════
print("Building Figure 6 — record length map …")

fig6, ax6 = plt.subplots(1, 1, figsize=(FW, panel_h),
                          constrained_layout=True)
base_map(ax6, show_states=True)

# all stations with coordinates, coloured by years_span
all_sta = df.dropna(subset=["lat", "lon", "years_span"])
vmin6   = all_sta["years_span"].quantile(0.02)
vmax6   = all_sta["years_span"].quantile(0.98)

sc6 = ax6.scatter(all_sta["lon"], all_sta["lat"],
                  c=all_sta["years_span"], cmap="YlGnBu",
                  vmin=vmin6, vmax=vmax6,
                  s=5, alpha=0.80, lw=0, zorder=5, rasterized=True)

cb6 = fig6.colorbar(sc6, ax=ax6, orientation="horizontal",
                    pad=0.04, fraction=0.035, aspect=30)
cb6.set_label("Record length (years)", fontsize=LABEL_FS - 0.5)
cb6.ax.tick_params(labelsize=TICK_FS - 1)

ax6.set_title("(a)  Station record length",
              fontsize=PANEL_FS, fontweight="bold", pad=4)

# station count annotation
ax6.text(0.98, 0.98,
         f"n = {len(all_sta):,} stations\nMedian = {all_sta['years_span'].median():.1f} yr",
         transform=ax6.transAxes, ha="right", va="top",
         fontsize=ANNOT_FS, color="#222222",
         bbox=dict(boxstyle="round,pad=0.3", fc="white",
                   ec="#aaaaaa", alpha=0.85))

save(fig6, OUT_DIR / "map_record_length")
plt.close(fig6)

print("\nAll maps written to outputs/figures/")
