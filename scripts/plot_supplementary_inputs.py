"""
Supplementary figures for the SCS-CN peak-discharge analysis.
  S1: catchment selection — eligible HydroBASINS-12 by biome + sampled set
  S2: input-data fields — CN, Tc, design depth, soil clay%, 1h/25yr IDF intensity
Saves: outputs/figures/supp_catchments.* and outputs/figures/supp_inputs.*
       (+ manuscript/figures copies)
"""
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

import figstyle as fs
ROOT = fs.ROOT
fs.apply_rcparams(base_size=8)

BRAZIL = [-74, -33, -34.5, 6.5]
BORDER_BIOMES = ["Cerrado", "Caatinga", "Mata Atlântica", "Pampa"]
BCOL = fs.BIOME_COLORS

biomes = gpd.read_file(ROOT/"data/reference/ibge/normalized/biomes.gpkg").to_crs(4326)
brazil = gpd.read_file(ROOT/"data/reference/ibge/normalized/brazil.gpkg").to_crs(4326)
elig = gpd.read_file(ROOT/"data/reference/hydro/eligible_catchments.gpkg")
imp = pd.read_csv(ROOT/"outputs/hydro_impact/catchment_impact.csv")

def base_map(ax, title, panel):
    biomes.boundary.plot(ax=ax, color="#cccccc", lw=0.2, zorder=1)
    brazil.boundary.plot(ax=ax, color="#444444", lw=0.5, zorder=2)
    ax.set_xlim(BRAZIL[0], BRAZIL[1]); ax.set_ylim(BRAZIL[2], BRAZIL[3])
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(f"({panel})  {title}", fontsize=8, fontweight=300, pad=3, loc="left")

# ── S1: catchment selection ───────────────────────────────────────────────
FW = fs.TEXT_WIDTH
fig1, ax = plt.subplots(figsize=(FW*0.62, FW*0.62))
base_map(ax, "SCS-eligible catchments and sampled subset", "")
ax.set_title("")  # single panel, no letter
for b in BORDER_BIOMES:
    sub = elig[elig["biome"] == b]
    sub.plot(ax=ax, color=BCOL[b], alpha=0.45, lw=0, zorder=3, rasterized=True)
ax.scatter(imp["lon"], imp["lat"], s=4, c="black", lw=0, zorder=5,
           label=f"Sampled (n={len(imp)})")
handles = [mpatches.Patch(fc=BCOL[b], alpha=0.6, label=b) for b in BORDER_BIOMES]
handles.append(plt.Line2D([0],[0], marker="o", color="none", markerfacecolor="black",
                          markersize=4, label=f"Sampled (n={len(imp)})"))
ax.legend(handles=handles, loc="lower left", fontsize=6, framealpha=0.9,
          edgecolor="#cccccc", handlelength=1.1, title="Eligible biomes",
          title_fontsize=6)
fs.save(fig1, "supp_catchments")
plt.close(fig1)

# ── S2: input data fields (6 panels) ──────────────────────────────────────
# gridded 1h/25yr IDF intensity from Sherman params
idf = {p: rasterio.open(ROOT/f"idf/XAVIER/RASTER/IDF_{p}.tif") for p in ["k","a","b","c"]}
K = idf["k"].read(1); A = idf["a"].read(1); B = idf["b"].read(1); C = idf["c"].read(1)
nod = idf["k"].nodata
mask = np.isfinite(K) & (K != (nod if nod is not None else -9999)) & (K > 0)
i_1h = np.full_like(K, np.nan)
i_1h[mask] = K[mask] * (25.0**A[mask]) / ((60.0 + B[mask])**C[mask])  # mm/h
idf_extent = [idf["k"].bounds.left, idf["k"].bounds.right,
              idf["k"].bounds.bottom, idf["k"].bounds.top]

# soil clay grid
clay = np.load(ROOT/"data/reference/hydro/brazil_clay_005.npy")/10.0
clay = np.where((clay > 0) & (clay < 100), clay, np.nan)
soil_extent = [-74.0, -33.0, -34.5, 6.5]

fig2 = plt.figure(figsize=(FW, FW*0.62))
gs = GridSpec(2, 3, figure=fig2, wspace=0.10, hspace=0.16,
              left=0.02, right=0.98, top=0.95, bottom=0.04)

def pt_panel(ax, col, title, panel, cmap, label, lo=None, hi=None):
    base_map(ax, title, panel)
    v = imp[col]
    lo = v.quantile(0.02) if lo is None else lo
    hi = v.quantile(0.98) if hi is None else hi
    sc = ax.scatter(imp["lon"], imp["lat"], c=v, cmap=cmap,
                    vmin=lo, vmax=hi, s=5, lw=0.1, edgecolors="white", zorder=4)
    cb = fig2.colorbar(sc, ax=ax, fraction=0.038, pad=0.02, extend="both")
    cb.set_label(label, fontsize=6.5, fontweight=300)
    cb.ax.tick_params(labelsize=5.5, width=0.3); cb.outline.set_linewidth(0.5)

def grid_panel(ax, arr, extent, title, panel, cmap, label, lo, hi):
    base_map(ax, title, panel)
    im = ax.imshow(arr, extent=extent, origin="upper", cmap=cmap,
                   vmin=lo, vmax=hi, zorder=0, interpolation="nearest")
    cb = fig2.colorbar(im, ax=ax, fraction=0.038, pad=0.02, extend="both")
    cb.set_label(label, fontsize=6.5, fontweight=300)
    cb.ax.tick_params(labelsize=5.5, width=0.3); cb.outline.set_linewidth(0.5)

ax1 = fig2.add_subplot(gs[0,0]); pt_panel(ax1, "cn", "Curve number (AMC II)", "a", "viridis", "CN")
ax2 = fig2.add_subplot(gs[0,1]); pt_panel(ax2, "tc_h", "Time of concentration", "b", "cividis", "$T_c$ (h)")
ax3 = fig2.add_subplot(gs[0,2]); pt_panel(ax3, "depth_mm", "Design depth (25-yr, $t=T_c$)", "c", "magma", "P (mm)")
ax4 = fig2.add_subplot(gs[1,0]); pt_panel(ax4, "clay_pct", "Soil clay fraction", "d", "YlOrBr", "clay (%)")
ax5 = fig2.add_subplot(gs[1,1])
grid_panel(ax5, clay, soil_extent, "SoilGrids clay (250 m)", "e", "YlOrBr",
           "clay (%)", np.nanpercentile(clay,2), np.nanpercentile(clay,98))
ax6 = fig2.add_subplot(gs[1,2])
grid_panel(ax6, i_1h, idf_extent, "IDF intensity (1 h, 25-yr)", "f", "magma",
           "i (mm h$^{-1}$)", np.nanpercentile(i_1h,2), np.nanpercentile(i_1h,98))

fs.save(fig2, "supp_inputs")
plt.close(fig2)
print("Supplementary figures written.")
