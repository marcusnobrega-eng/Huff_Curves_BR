"""
Figure: hydrological impact — 3-row × 3-col map layout with biome insets.

Row 1  (response variables):
  (a) Δ peak discharge (%)       updated vs. original Huff Q1
  (b) Δ time-to-peak (h)         negative = earlier peak
  (c) Δ hydrograph duration (h)  time to Q < 1 % of peak
Row 2  (catchment / forcing descriptors):
  (d) SCS curve number CN
  (e) Time of concentration Tc (h)
  (f) 25-year design rainfall intensity (mm h⁻¹)
Row 3  (catchment physical properties):
  (g) Runoff coefficient RC
  (h) Catchment area (km²)
  (i) Soil clay content (%)

Each panel: scatter map + thin narrow colorbar + biome boxplot inset
            (upper-left corner, no zero-line).
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.gridspec import GridSpec

import figstyle as fs

ROOT = fs.ROOT
fs.apply_rcparams(base_size=8)

df = pd.read_csv(ROOT / "outputs" / "hydro_impact" / "catchment_impact.csv")
df["intensity_mm_h"] = df["depth_mm"] / df["tc_h"]

BORDER_BIOMES = ["Cerrado", "Caatinga", "Mata Atlântica", "Pampa"]
BCOL = fs.BIOME_COLORS

try:
    import geopandas as gpd
    biomes = gpd.read_file(ROOT / "data/reference/ibge/normalized/biomes.gpkg").to_crs(4326)
    brazil = gpd.read_file(ROOT / "data/reference/ibge/normalized/brazil.gpkg").to_crs(4326)
    HAS_GEO = True
except Exception:
    HAS_GEO = False

FW = fs.TEXT_WIDTH
fig = plt.figure(figsize=(FW, FW * 1.22))
gs = GridSpec(3, 3, figure=fig,
              hspace=0.18, wspace=0.08,
              left=0.01, right=0.99, top=0.97, bottom=0.03)

# ── panel specs: (col, cmap, norm_type, cb_label, letter, title) ──────────────
panels = [
    # Row 1 — response variables
    ("d_qp_pct",       "RdBu_r",  "div",
     "Δ$Q_p$ (%)",          "(a)", "Δ peak discharge (%)"),
    ("d_tp_h",         "RdBu_r",  "div",
     "Δ$t_p$ (h)",          "(b)", "Δ time-to-peak (h)"),
    ("d_duration_h",   "RdBu",    "div",
     "Δ$T_d$ (h)",          "(c)", "Δ hydrograph duration (h)"),
    # Row 2 — catchment / forcing descriptors
    ("cn",             "YlOrRd",  "seq",
     "CN",                  "(d)", "Curve number (CN)"),
    ("tc_h",           "viridis", "seq",
     "$T_c$ (h)",           "(e)", "Time of concentration $T_c$ (h)"),
    ("intensity_mm_h", "YlOrBr",  "seq",
     "mm h$^{-1}$",         "(f)", "Design rainfall intensity (mm h$^{-1}$)"),
    # Row 3 — catchment physical properties
    ("rc",             "YlOrBr",  "seq",
     "RC (–)",              "(g)", "Runoff coefficient RC"),
    ("area_km2",       "viridis", "seq",
     "km$^2$",              "(h)", "Catchment area (km$^2$)"),
    ("clay_pct",       "YlOrRd",  "seq",
     "Clay (%)",            "(i)", "Soil clay content (%)"),
]


def make_norm(col, ntype):
    vals = df[col].dropna()
    if ntype == "div":
        vmax = float(np.nanpercentile(np.abs(vals), 98))
        return mcolors.TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax)
    return mcolors.Normalize(vmin=float(np.nanpercentile(vals, 2)),
                             vmax=float(np.nanpercentile(vals, 98)))


def biome_inset(ax_main, col):
    """Small biome boxplot, positioned in the lower-left at 80 % height."""
    # x0=0.01, y0=0.13 (raised), width=0.38, height=0.23 (80 % of original 0.29)
    ax_i = ax_main.inset_axes([0.01, 0.13, 0.38, 0.23])
    data = [df.loc[df["biome"] == b, col].dropna().values for b in BORDER_BIOMES]
    bp = ax_i.boxplot(
        data, vert=True, widths=0.56, patch_artist=True,
        showfliers=False,
        medianprops=dict(color="black", lw=0.8),
        whiskerprops=dict(lw=0.4, color="#555555"),
        capprops=dict(lw=0.4, color="#555555"),
        boxprops=dict(lw=0.3),
    )
    for patch, b in zip(bp["boxes"], BORDER_BIOMES):
        patch.set_facecolor(BCOL[b])
        patch.set_alpha(0.90)
    ax_i.set_xticks(range(1, 5))
    ax_i.set_xticklabels(["Ce", "Ca", "MA", "Pa"], fontsize=4.5)
    ax_i.tick_params(width=0.3, labelsize=4.5, pad=1, length=2)
    ax_i.spines[["top", "right"]].set_visible(False)
    ax_i.spines[["left", "bottom"]].set_linewidth(0.3)
    ax_i.grid(axis="y", lw=0.2, color="#e0e0e0", zorder=0)
    ax_i.set_facecolor("white")
    ax_i.patch.set_alpha(0.88)


for idx, (col, cmap, ntype, cb_lbl, letter, title) in enumerate(panels):
    row, c = divmod(idx, 3)
    ax = fig.add_subplot(gs[row, c])

    if HAS_GEO:
        biomes.boundary.plot(ax=ax, color="#cccccc", lw=0.2, zorder=2)
        brazil.boundary.plot(ax=ax, color="#444444", lw=0.45, zorder=3)

    norm = make_norm(col, ntype)
    sc = ax.scatter(df["lon"], df["lat"], c=df[col], cmap=cmap,
                    norm=norm, s=5, lw=0.12, edgecolors="black", zorder=4)

    ax.set_xlim(-74, -33)
    ax.set_ylim(-34.5, 6.5)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)

    ax.set_title(f"{letter}  {title}", fontsize=7, fontweight=300,
                 pad=2, loc="left")

    # half width (shrink 0.41), double thickness (fraction 0.076),
    # double outline linewidth (0.90)
    cb = fig.colorbar(sc, ax=ax, orientation="horizontal",
                      fraction=0.076, pad=0.01, shrink=0.41, extend="both")
    cb.set_label(cb_lbl, fontsize=6, fontweight=300, labelpad=1)
    cb.ax.tick_params(labelsize=5.0, width=0.35, length=2)
    cb.outline.set_linewidth(0.90)

    biome_inset(ax, col)


fs.save(fig, "hydro_impact")
plt.close(fig)
print("Hydrological impact figure written.")
