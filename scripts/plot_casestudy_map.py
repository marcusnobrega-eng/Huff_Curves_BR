"""
Figure 1 — Study area: ANA station network and data availability
================================================================
Two-panel publication figure:
  (a) Brazil map (geographic lat/long axes), biome fills (Okabe-Ito
      palette + legend), state boundaries, stations coloured by record
      length, with an inset colourbar inside panel (a). No basemap.
  (b) Record-length histogram.

Uses shared style: scripts/figstyle.py  (Helvetica Neue Light + palette)
Saves: outputs/figures/casestudy_dem.{pdf,svg,png}  (+ manuscript copy)
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import geopandas as gpd
from matplotlib.gridspec import GridSpec

import figstyle as fs

ROOT = fs.ROOT
fs.apply_rcparams(base_size=8)

CRS_GEO = "EPSG:4326"

# ── boundaries (geographic) ───────────────────────────────────────────────
biome_gdf = gpd.read_file(
    ROOT/"data"/"reference"/"ibge"/"normalized"/"biomes.gpkg").to_crs(CRS_GEO)
state_gdf = gpd.read_file(
    ROOT/"data"/"reference"/"ibge"/"normalized"/"states.gpkg").to_crs(CRS_GEO)
brazil = gpd.read_file(
    ROOT/"data"/"reference"/"ibge"/"normalized"/"brazil.gpkg").to_crs(CRS_GEO)

biome_col = next((c for c in ["biome_name", "nome", "name", "NM_BIOMA"]
                  if c in biome_gdf.columns), None)

# ── station data ──────────────────────────────────────────────────────────
df = pd.read_csv(ROOT/"outputs"/"station_huff_coefficients.csv")
for c in ["lat", "lon", "years_span"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
df = df.dropna(subset=["lat", "lon"])
ok  = df[df["status"] == "ok"].copy()
rej = df[df["status"] != "ok"].copy()

STA_CMAP = plt.get_cmap(fs.SEQ_CMAP_RECORD)   # cividis (colourblind-safe)
# clip=True squishes out-of-bounds values to the [4, 16] limits
STA_NORM = mcolors.Normalize(vmin=4, vmax=16, clip=True)

# ── layout: map | histogram ───────────────────────────────────────────────
FW = fs.TEXT_WIDTH
fig = plt.figure(figsize=(FW, FW * 0.52))
gs = GridSpec(1, 2, figure=fig, width_ratios=[1.7, 1.0],
              wspace=0.22, left=0.06, right=0.985, top=0.94, bottom=0.12)
ax_map  = fig.add_subplot(gs[0, 0])
ax_hist = fig.add_subplot(gs[0, 1])

# ════════════════════════════════════════════════════════════════════════════
# (a) MAP
# Visual hierarchy: pale biome context (back) → excluded (faint) →
#                   accepted stations with white halo + black outline (front)
# ════════════════════════════════════════════════════════════════════════════
# 1. biome fills — pale, low-saturation, transparent background context
if biome_col:
    for biome, grp in biome_gdf.groupby(biome_col):
        grp.plot(ax=ax_map, color=fs.BIOME_FILL.get(biome, "#eeeeee"),
                 linewidth=0, alpha=0.45, zorder=1)
else:
    biome_gdf.plot(ax=ax_map, color="#eeeeee", linewidth=0, alpha=0.45, zorder=1)

# 2. biome borders — thin grey35
biome_gdf.boundary.plot(ax=ax_map, color=fs.BIOME_BORDER, linewidth=0.15,
                        zorder=2, alpha=0.45)
# state + national outline (kept subtle, structural only)
state_gdf.boundary.plot(ax=ax_map, color="#9a9a9a", linewidth=0.3, zorder=3, alpha=0.7)
brazil.boundary.plot(ax=ax_map, color="#555555", linewidth=0.6, zorder=4)

# 3. excluded stations — faint, small, de-emphasised
ax_map.scatter(rej["lon"], rej["lat"], c="#666666", s=1.6, lw=0,
               zorder=5, alpha=0.32, rasterized=True)

# 4. accepted stations — WHITE HALO underneath, then point on top
#    halo: slightly larger pure-white marker
ax_map.scatter(ok["lon"], ok["lat"], c="white", s=22, lw=0,
               zorder=6, rasterized=True)
#    point: shape-21 equivalent — fill mapped to record length, thin black edge
sc = ax_map.scatter(ok["lon"], ok["lat"], c=ok["years_span"].values,
                    cmap=STA_CMAP, norm=STA_NORM, s=12,
                    edgecolors="black", linewidths=0.2, alpha=0.95,
                    zorder=7, rasterized=True)

# geographic axes
ax_map.set_xlim(-74, -33)
ax_map.set_ylim(-34.5, 6.5)
ax_map.set_aspect("equal")
ax_map.set_xlabel("Longitude (°)", fontweight=300)
ax_map.set_ylabel("Latitude (°)", fontweight=300)
ax_map.set_xticks([-70, -60, -50, -40])
ax_map.set_yticks([-30, -20, -10, 0])
ax_map.tick_params(width=0.4, labelsize=7)
ax_map.set_xticklabels(["70°W", "60°W", "50°W", "40°W"])
ax_map.set_yticklabels(["30°S", "20°S", "10°S", "0°"])
for s in ax_map.spines.values():
    s.set_linewidth(0.5)
ax_map.set_title("(a)  ANA telemetric network — data availability",
                 fontsize=9, fontweight=300, pad=4, loc="left")

# ── inset colourbar inside panel (a): half width, thick outline ───────────
# native ax.inset_axes (robust with bbox_inches="tight")
# [x0, y0, width, height] in axes-relative coords; width 0.022 = thin
cax = ax_map.inset_axes([0.90, 0.30, 0.022, 0.40])
cb = fig.colorbar(plt.cm.ScalarMappable(norm=STA_NORM, cmap=STA_CMAP),
                  cax=cax, orientation="vertical")
fs.style_colorbar(cb, label="Record length (yr)",
                  thin=True, thick_outline=True)
cb.set_ticks([4, 8, 12, 16])
cax.yaxis.set_label_position("left")
cax.yaxis.set_ticks_position("left")

# ── biome legend (pale fills match the map background) ────────────────────
biome_patches = [
    mpatches.Patch(fc=fs.BIOME_FILL[b], ec=fs.BIOME_BORDER, lw=0.3, label=b)
    for b in fs.BIOME_ORDER
]
biome_patches.append(
    mpatches.Patch(fc="#666666", ec="none", alpha=0.5,
                   label=f"Excl. ({len(rej):,})")
)
ax_map.legend(handles=biome_patches, loc="lower left", fontsize=6.0,
              framealpha=0.9, edgecolor="#cccccc", handlelength=1.1,
              handletextpad=0.5, borderpad=0.6, labelspacing=0.3,
              title="Biome / status", title_fontsize=6.0)

# ── scale bar (lower-right, geographic) ───────────────────────────────────
# 500 km ≈ 4.5° lon at ~20°S (cos20° ≈ 0.94, 1°≈111km → 500/104≈4.8°)
bar_deg = 500.0 / (111.0 * np.cos(np.radians(20)))
x1 = -34.5
x0 = x1 - bar_deg
y0 = -32.5
ax_map.plot([x0, x1], [y0, y0], color="#111111", lw=1.2,
            solid_capstyle="butt", zorder=7)
for xv in [x0, x1]:
    ax_map.plot([xv, xv], [y0 - 0.5, y0 + 0.5], color="#111111", lw=0.8, zorder=7)
ax_map.text((x0 + x1) / 2, y0 - 1.0, "500 km", ha="center", va="top",
            fontsize=6.5, color="#111111", fontweight=300)

# ════════════════════════════════════════════════════════════════════════════
# (b) HISTOGRAM
# ════════════════════════════════════════════════════════════════════════════
bins     = np.arange(0, 17.5, 1)
all_span = df["years_span"].dropna()
ok_span  = ok["years_span"].dropna()

ax_hist.hist(all_span, bins=bins, color="#B8B8B8", edgecolor="#9a9a9a",
             lw=0.4, zorder=2, label=f"All  (n = {len(all_span):,})")
ax_hist.hist(ok_span, bins=bins, color="#1A80BB",
             edgecolor="white", lw=0.3, alpha=0.95, zorder=3,
             label=f"Accepted  (n = {len(ok_span):,})")
ax_hist.axvline(4, color="#A00000", lw=1.1, ls="--", zorder=4,
                label="QC min.  (4 yr)")

ax_hist.set_xlabel("Record length (years)", fontweight=300)
ax_hist.set_ylabel("Number of stations", fontweight=300)
ax_hist.set_title("(b)  Record length distribution",
                  fontsize=9, fontweight=300, pad=4, loc="left")
ax_hist.legend(fontsize=6.5, framealpha=0.9, edgecolor="#cccccc",
               loc="upper right", handlelength=1.2, borderpad=0.6,
               labelspacing=0.35)
ax_hist.grid(axis="y", lw=0.3, color="#e6e6e6", zorder=0)
ax_hist.set_xlim(0, 17)
ax_hist.spines[["top", "right"]].set_visible(False)
ax_hist.spines[["left", "bottom"]].set_linewidth(0.4)
ax_hist.tick_params(width=0.4)
ax_hist.text(0.97, 0.74, f"Median (accepted):\n{ok_span.median():.1f} yr",
             transform=ax_hist.transAxes, ha="right", va="top",
             fontsize=6.5, fontweight=300, color="#333333",
             bbox=dict(fc="white", ec="#cccccc", alpha=0.85, pad=2, lw=0.4))

fs.save(fig, "casestudy_dem")
plt.close(fig)
print("Done.")
