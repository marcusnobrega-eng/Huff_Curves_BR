"""
Publication-quality map figures (PDF + SVG)
============================================
  Figure 3 — map_dominant_quartile   (station dominant quartile)
  Figure 4 — map_mae_dmax            (MAE and D_max spatial distribution)
  Figure 5 — map_record_length       (data availability)

Saves all outputs under outputs/figures/.
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
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from matplotlib.colors import BoundaryNorm, ListedColormap
import matplotlib.cm as cm

ROOT    = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "outputs" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# ── data ───────────────────────────────────────────────────────────────────
ok  = pd.read_csv(ROOT/"outputs"/"station_huff_coefficients.csv")
ok  = ok[ok["status"]=="ok"].copy()
all_sta = pd.read_csv(ROOT/"outputs"/"station_huff_coefficients.csv")

geo_path = ROOT/"outputs"/"diagnostics"/"regional"/"station_results_with_geography.csv"
geo = pd.read_csv(geo_path)
geo["station_id"] = geo["station_id"].astype(str).str.replace(r"\.0$","",regex=True)
ok["station_id"]  = ok["station_id"].astype(str).str.replace(r"\.0$","",regex=True)

ok = ok.merge(geo[["station_id","biome_name"]], on="station_id", how="left")
ok["dominant_quartile"] = pd.to_numeric(ok["dominant_quartile"], errors="coerce")
ok["mae_mean"]  = pd.to_numeric(ok["mae_mean"],  errors="coerce")
ok["d_max_mean"]= pd.to_numeric(ok["d_max_mean"],errors="coerce")
ok["years_span"]= pd.to_numeric(ok["years_span"],errors="coerce")

# rejected / skipped stations
rej = all_sta[all_sta["status"]!="ok"].copy()
rej["lat"] = pd.to_numeric(rej["lat"], errors="coerce")
rej["lon"] = pd.to_numeric(rej["lon"], errors="coerce")
rej = rej.dropna(subset=["lat","lon"])

# ── try to load biome / state boundary shapefiles ─────────────────────────
try:
    import geopandas as gpd
    biome_gdf = gpd.read_file(
        ROOT/"data"/"reference"/"ibge"/"normalized"/"biomes.gpkg").to_crs(4326)
    state_gdf = gpd.read_file(
        ROOT/"data"/"reference"/"ibge"/"normalized"/"states.gpkg").to_crs(4326)
    HAS_GEO = True
except Exception:
    HAS_GEO = False
    print("  geopandas not available or shapefiles not found — maps without borders")

# ── style ──────────────────────────────────────────────────────────────────
MM = 1/25.4; FW = 190*MM
plt.rcParams.update({
    "font.family":"Helvetica Neue","font.weight":300,"font.size":8,
    "axes.labelsize":9,"axes.titlesize":9,
    "xtick.labelsize":7,"ytick.labelsize":7,
    "axes.linewidth":0.5,
    "figure.dpi":200,"savefig.dpi":300,
    "pdf.fonttype":42,"svg.fonttype":"none",
})

BRAZIL_EXTENT = [-74, -28, -34, 6]   # [lon_min, lon_max, lat_min, lat_max]

def set_map_ax(ax, title, panel_label=""):
    ax.set_xlim(BRAZIL_EXTENT[0], BRAZIL_EXTENT[1])
    ax.set_ylim(BRAZIL_EXTENT[2], BRAZIL_EXTENT[3])
    ax.set_aspect("equal")
    ax.set_xlabel("Longitude (°)")
    ax.set_ylabel("Latitude (°)")
    # no lat/long gridlines
    prefix = f"{panel_label}  " if panel_label else ""
    ax.set_title(f"{prefix}{title}", fontweight=300, pad=3, fontsize=9, loc="left")

def draw_borders(ax):
    if HAS_GEO:
        biome_gdf.boundary.plot(ax=ax, color="#888888", lw=0.4, zorder=2)
        state_gdf.boundary.plot(ax=ax, color="#444444", lw=0.6, zorder=3)

def save_fig(fig, stem):
    for ext, dpi in [("pdf",None),("svg",None),("png",150)]:
        kw = dict(bbox_inches="tight")
        if dpi: kw["dpi"] = dpi
        fig.savefig(str(stem)+f".{ext}", format=ext, **kw)
    print(f"  → {stem}.pdf / .svg / .png")

# ══════════════════════════════════════════════════════════════════════════
# Figure 3 — Dominant quartile map
# ══════════════════════════════════════════════════════════════════════════
# distinct, vivid categorical colours for the four quartiles
QCOL = {1:"#1b9e77", 2:"#7570b3", 3:"#e6ab02", 4:"#d95f02"}
QLBL = {1:"Q1 (n=986)", 2:"Q2 (n=21)", 3:"Q3 (n=9)", 4:"Q4 (n=29)"}

fig3, ax3 = plt.subplots(1, 1, figsize=(FW*0.6, FW*0.65), constrained_layout=True)
draw_borders(ax3)

# rejected stations (grey background)
ax3.scatter(rej["lon"], rej["lat"], c="#cccccc", s=4, lw=0, zorder=2,
            label=f"Excluded (n={len(rej):,})", rasterized=True)

# OK stations coloured by dominant quartile
for q in [1,2,3,4]:
    sub = ok[ok["dominant_quartile"]==q]
    ax3.scatter(sub["lon"], sub["lat"], c=QCOL[q], s=9, lw=0.2, edgecolors="white",
                zorder=4, rasterized=True)

set_map_ax(ax3, "Dominant Huff quartile")

# legend
patches = [mpatches.Patch(fc="#cccccc", label=f"Excluded (n={len(rej):,})")]
patches += [mpatches.Patch(fc=QCOL[q], label=QLBL[q]) for q in [1,2,3,4]]
ax3.legend(handles=patches, loc="lower left", fontsize=7,
           framealpha=0.92, edgecolor="#aaaaaa", handlelength=1)

save_fig(fig3, FIG_DIR/"map_dominant_quartile")
plt.close(fig3)

# ══════════════════════════════════════════════════════════════════════════
# Figure 4 — MAE and D_max maps  (two-panel)
# ══════════════════════════════════════════════════════════════════════════
fig4, axes4 = plt.subplots(1, 2, figsize=(FW, FW*0.55), constrained_layout=True)

# disp = display label with mathtext so 'max' renders as a subscript
for ax, col, disp, panel, cmap_name in [
    (axes4[0], "mae_mean",   r"MAE",            "(a)", "magma"),
    (axes4[1], "d_max_mean", r"$D_\mathrm{max}$", "(b)", "magma"),
]:
    draw_borders(ax)
    vals = ok[col].dropna()
    vmin = vals.quantile(0.02)
    vmax = vals.quantile(0.98)

    sc = ax.scatter(ok["lon"], ok["lat"],
                    c=ok[col], cmap=cmap_name,
                    vmin=vmin, vmax=vmax,
                    s=10, lw=0.2, edgecolors="white",
                    zorder=4, rasterized=True)
    cb = plt.colorbar(sc, ax=ax, fraction=0.022, pad=0.02)
    cb.set_label(disp, fontsize=8)
    cb.ax.tick_params(labelsize=7, width=0.4)
    cb.outline.set_linewidth(0.9)
    cb.outline.set_edgecolor("#222222")

    med = vals.median()
    ax.text(0.03, 0.04, f"Median = {med:.3f}", transform=ax.transAxes,
            fontsize=7, color="#222222",
            bbox=dict(fc="white", ec="#cccccc", alpha=0.8, pad=2))

    set_map_ax(ax, f"Q1 {disp} vs Huff (1967)", panel)

save_fig(fig4, FIG_DIR/"map_mae_dmax")
plt.close(fig4)

# ══════════════════════════════════════════════════════════════════════════
# Figure 5 — Data availability (record length)
# ══════════════════════════════════════════════════════════════════════════
all_sta["lat"] = pd.to_numeric(all_sta["lat"], errors="coerce")
all_sta["lon"] = pd.to_numeric(all_sta["lon"], errors="coerce")
all_sta["years_span"] = pd.to_numeric(all_sta["years_span"], errors="coerce")
has_data = all_sta.dropna(subset=["lat","lon","years_span"])

fig5, axes5 = plt.subplots(1, 2, figsize=(FW, FW*0.55), constrained_layout=True)

# left: record length map
ax = axes5[0]
draw_borders(ax)
sc = ax.scatter(has_data["lon"], has_data["lat"],
                c=has_data["years_span"], cmap="viridis_r",
                vmin=0, vmax=16,
                s=5, lw=0, zorder=4, rasterized=True)
cb = plt.colorbar(sc, ax=ax, fraction=0.022, pad=0.02)
cb.set_label("Record length (yr)", fontsize=8)
cb.ax.tick_params(labelsize=7, width=0.4)
cb.outline.set_linewidth(0.9)
cb.outline.set_edgecolor("#222222")
set_map_ax(ax, "Station record length", "(a)")
ax.text(0.03,0.04, f"n = {len(has_data):,}\nMedian = {has_data['years_span'].median():.1f} yr",
        transform=ax.transAxes, fontsize=7,
        bbox=dict(fc="white", ec="#cccccc", alpha=0.8, pad=2))

# right: histogram of record lengths
ax2 = axes5[1]
bins = np.arange(0, 17, 1)
n_ok  = ok["years_span"].dropna()
n_all = has_data["years_span"]

ax2.hist(n_all, bins=bins, color="#cccccc", edgecolor="#888888",
         lw=0.5, zorder=2, label=f"All stations (n={len(n_all):,})")
ax2.hist(n_ok,  bins=bins, color="#1f77b4", edgecolor="#1f77b4",
         lw=0.5, zorder=3, alpha=0.75, label=f"OK stations (n={len(n_ok):,})")
ax2.axvline(4, color="#d62728", lw=1.0, ls="--", label="4-yr QC threshold")
ax2.set_xlabel("Record length (years)")
ax2.set_ylabel("Number of stations")
ax2.set_title("(b)  Record length distribution", fontweight=300, pad=3, fontsize=9)
ax2.legend(fontsize=7, framealpha=0.92, edgecolor="#aaaaaa")
ax2.grid(True, lw=0.3, color="#dddddd", zorder=0)

save_fig(fig5, FIG_DIR/"map_record_length")
plt.close(fig5)

print("All publication maps done.")
