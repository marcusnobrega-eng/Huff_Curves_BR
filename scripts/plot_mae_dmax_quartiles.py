"""
Figure 6: per-quartile goodness-of-fit maps (MAE and D_max, Q1-Q4).
  Row 1: MAE   for Q1..Q4   (shared, extended colourbar)
  Row 2: D_max for Q1..Q4   (shared, extended colourbar)
Each map: Brazil + biome boundaries only (no states), stations coloured
by that quartile's metric, with a small inset bar chart (bottom-right)
giving the per-biome median.

Saves: outputs/figures/map_mae_dmax_quartiles.{pdf,svg,png} (+ manuscript)
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

import figstyle as fs

ROOT = fs.ROOT
fs.apply_rcparams(base_size=8)

BRAZIL = [-74, -33, -34.5, 6.5]
BIOME_ORDER = fs.BIOME_ORDER
BCOL = fs.BIOME_COLORS

# ── data + biome mapping ──────────────────────────────────────────────────
df = pd.read_csv(ROOT / "outputs" / "station_huff_coefficients.csv")
ok = df[df["status"] == "ok"].copy()
ok["lon"] = pd.to_numeric(ok["lon"], errors="coerce")
ok["lat"] = pd.to_numeric(ok["lat"], errors="coerce")
ok = ok.dropna(subset=["lon", "lat"])
for q in [1, 2, 3, 4]:
    ok[f"q{q}_mae"]   = pd.to_numeric(ok[f"q{q}_mae"],   errors="coerce")
    ok[f"q{q}_d_max"] = pd.to_numeric(ok[f"q{q}_d_max"], errors="coerce")

geo = pd.read_csv(ROOT/"outputs"/"diagnostics"/"regional"/"station_results_with_geography.csv")
geo["station_id"] = geo["station_id"].astype(str).str.replace(r"\.0$", "", regex=True)
ok["station_id"] = ok["station_id"].astype(str).str.replace(r"\.0$", "", regex=True)
ok = ok.merge(geo[["station_id", "biome_name"]], on="station_id", how="left")

# ── boundaries (biomes + Brazil only) ─────────────────────────────────────
try:
    import geopandas as gpd
    biomes = gpd.read_file(ROOT/"data"/"reference"/"ibge"/"normalized"/"biomes.gpkg").to_crs(4326)
    brazil = gpd.read_file(ROOT/"data"/"reference"/"ibge"/"normalized"/"brazil.gpkg").to_crs(4326)
    HAS_GEO = True
except Exception:
    HAS_GEO = False

def limits(prefix):
    allv = pd.concat([ok[f"q{q}_{prefix}"] for q in [1, 2, 3, 4]]).dropna()
    return float(allv.quantile(0.02)), float(allv.quantile(0.98))

def biome_medians(prefix, q):
    """Median metric per biome (fixed order); NaN where absent."""
    return [float(ok.loc[ok["biome_name"] == b, f"q{q}_{prefix}"].median())
            for b in BIOME_ORDER]

CMAP = "magma"
FW = fs.TEXT_WIDTH
fig = plt.figure(figsize=(FW, FW * 0.66))
# thin colourbar column (half previous width: 0.06 -> 0.03)
gs = GridSpec(2, 5, figure=fig, width_ratios=[1, 1, 1, 1, 0.03],
              wspace=0.08, hspace=0.10,
              left=0.05, right=0.945, top=0.965, bottom=0.10)

rows = [("mae",   "MAE",               *limits("mae")),
        ("d_max", r"$D_\mathrm{max}$", *limits("d_max"))]
panel_idx = iter("abcdefgh")

for r, (prefix, rlabel, lo, hi) in enumerate(rows):
    norm = mcolors.Normalize(vmin=lo, vmax=hi, clip=True)
    # row-wide inset y-limit so the per-biome bars are comparable across quartiles
    row_bmax = np.nanmax([np.nanmax(biome_medians(prefix, q)) for q in [1, 2, 3, 4]])

    for c, q in enumerate([1, 2, 3, 4]):
        ax = fig.add_subplot(gs[r, c])
        if HAS_GEO:
            biomes.boundary.plot(ax=ax, color="#bbbbbb", lw=0.25, zorder=2)
            brazil.boundary.plot(ax=ax, color="#444444", lw=0.45, zorder=3)
        ax.scatter(ok["lon"], ok["lat"], c=ok[f"q{q}_{prefix}"],
                   cmap=CMAP, norm=norm, s=3.0, lw=0.0, zorder=4,
                   rasterized=True)
        ax.set_xlim(BRAZIL[0], BRAZIL[1]); ax.set_ylim(BRAZIL[2], BRAZIL[3])
        ax.set_aspect("equal")
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():     # no panel border
            s.set_visible(False)

        ax.set_title(f"({next(panel_idx)})  Q{q}", fontsize=8,
                     fontweight=300, pad=3, loc="left")
        if c == 0:
            ax.set_ylabel(rlabel, fontsize=9, fontweight=300)

        # ── inset: per-biome median bar chart (bottom-left, over empty SW) ─
        inax = ax.inset_axes([0.015, 0.05, 0.345, 0.26])
        vals = biome_medians(prefix, q)
        xb = np.arange(len(BIOME_ORDER))
        inax.bar(xb, vals, width=0.82,
                 color=[BCOL[b] for b in BIOME_ORDER],
                 edgecolor="black", linewidth=0.2)
        inax.set_xticks([])
        inax.set_ylim(0, row_bmax * 1.12)
        inax.set_xlim(-0.7, len(BIOME_ORDER) - 0.3)
        # show the y-axis maximum as a single labelled tick
        inax.set_yticks([row_bmax])
        inax.set_yticklabels([f"{row_bmax:.3f}"], fontsize=4.6, color="#333333")
        inax.tick_params(axis="y", length=1.3, width=0.3, pad=1.0,
                         colors="#555555")
        for name, sp in inax.spines.items():
            if name == "left":
                sp.set_linewidth(0.3); sp.set_color("#777777")
            else:
                sp.set_visible(False)
        inax.patch.set_visible(False)    # transparent (sits over empty area)

    # ── shared, extended, thin colourbar with thicker outline ─────────────
    cax = fig.add_subplot(gs[r, 4])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=CMAP),
                      cax=cax, extend="both")
    cb.set_label(rlabel, fontsize=7.5, fontweight=300)
    cb.ax.tick_params(labelsize=6.0, width=0.4)
    cb.outline.set_linewidth(0.78)      # +30% over previous 0.6
    cb.outline.set_edgecolor("#222222")

# ── shared biome legend (maps the inset-bar colours) ──────────────────────
handles = [mpatches.Patch(fc=BCOL[b], ec="black", lw=0.2, label=b)
           for b in BIOME_ORDER]
fig.legend(handles=handles, ncol=6, loc="lower center",
           bbox_to_anchor=(0.5, 0.005), fontsize=6.5, frameon=False,
           handlelength=1.1, handletextpad=0.4, columnspacing=1.0,
           title="Inset bars — per-biome median", title_fontsize=6.5)

fs.save(fig, "map_mae_dmax_quartiles")
plt.close(fig)
print("Per-quartile MAE/D_max figure (with biome insets) written.")
