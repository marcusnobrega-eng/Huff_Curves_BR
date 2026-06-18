"""
Figure: per-station quartile composition of the event population.
Four maps (Q1%, Q2%, Q3%, Q4%) of the fraction of each station's events
falling in each quartile, with a shared colourbar and a bottom-left
inset bar chart giving the per-biome median for that quartile.
Same visual language as the per-quartile MAE/D_max figure.

Saves: outputs/figures/map_quartile_percent.{pdf,svg,png} (+ manuscript)
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
    ok[f"q{q}_percent_events"] = pd.to_numeric(ok[f"q{q}_percent_events"], errors="coerce")

geo = pd.read_csv(ROOT/"outputs"/"diagnostics"/"regional"/"station_results_with_geography.csv")
geo["station_id"] = geo["station_id"].astype(str).str.replace(r"\.0$", "", regex=True)
ok["station_id"] = ok["station_id"].astype(str).str.replace(r"\.0$", "", regex=True)
ok = ok.merge(geo[["station_id", "biome_name"]], on="station_id", how="left")

try:
    import geopandas as gpd
    biomes = gpd.read_file(ROOT/"data"/"reference"/"ibge"/"normalized"/"biomes.gpkg").to_crs(4326)
    brazil = gpd.read_file(ROOT/"data"/"reference"/"ibge"/"normalized"/"brazil.gpkg").to_crs(4326)
    HAS_GEO = True
except Exception:
    HAS_GEO = False

# shared colour scale across the four quartiles (2nd-98th pct of pooled %)
pooled = pd.concat([ok[f"q{q}_percent_events"] for q in [1, 2, 3, 4]]).dropna()
LO, HI = float(pooled.quantile(0.02)), float(pooled.quantile(0.98))
norm = mcolors.Normalize(vmin=LO, vmax=HI, clip=True)
CMAP = "magma"

def biome_medians(q):
    return [float(ok.loc[ok["biome_name"] == b, f"q{q}_percent_events"].median())
            for b in BIOME_ORDER]

FW = fs.TEXT_WIDTH
fig = plt.figure(figsize=(FW, FW * 0.40))
gs = GridSpec(1, 5, figure=fig, width_ratios=[1, 1, 1, 1, 0.03],
              wspace=0.07, left=0.02, right=0.945, top=0.90, bottom=0.14)

panel_idx = iter("abcd")
for c, q in enumerate([1, 2, 3, 4]):
    ax = fig.add_subplot(gs[0, c])
    if HAS_GEO:
        biomes.boundary.plot(ax=ax, color="#bbbbbb", lw=0.25, zorder=2)
        brazil.boundary.plot(ax=ax, color="#444444", lw=0.45, zorder=3)
    ax.scatter(ok["lon"], ok["lat"], c=ok[f"q{q}_percent_events"],
               cmap=CMAP, norm=norm, s=3.0, lw=0.0, zorder=4, rasterized=True)
    ax.set_xlim(BRAZIL[0], BRAZIL[1]); ax.set_ylim(BRAZIL[2], BRAZIL[3])
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(f"({next(panel_idx)})  Q{q}", fontsize=8,
                 fontweight=300, pad=3, loc="left")

    # ── inset: per-biome median %, bottom-left (own scale, ymax labelled) ─
    inax = ax.inset_axes([0.015, 0.05, 0.345, 0.26])
    vals = biome_medians(q)
    vmax = float(np.nanmax(vals))
    xb = np.arange(len(BIOME_ORDER))
    inax.bar(xb, vals, width=0.82,
             color=[BCOL[b] for b in BIOME_ORDER],
             edgecolor="black", linewidth=0.2)
    inax.set_xticks([])
    inax.set_ylim(0, vmax * 1.12)
    inax.set_xlim(-0.7, len(BIOME_ORDER) - 0.3)
    inax.set_yticks([vmax])
    inax.set_yticklabels([f"{vmax:.0f}%"], fontsize=4.6, color="#333333")
    inax.tick_params(axis="y", length=1.3, width=0.3, pad=1.0, colors="#555555")
    for name, sp in inax.spines.items():
        if name == "left":
            sp.set_linewidth(0.3); sp.set_color("#777777")
        else:
            sp.set_visible(False)
    inax.patch.set_visible(False)

# shared colourbar (extended ends; thin; thicker outline)
cax = fig.add_subplot(gs[0, 4])
cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=CMAP),
                  cax=cax, extend="both")
cb.set_label("Share of station events (%)", fontsize=7.5, fontweight=300)
cb.ax.tick_params(labelsize=6.0, width=0.4)
cb.outline.set_linewidth(0.78)
cb.outline.set_edgecolor("#222222")

# shared biome legend
handles = [mpatches.Patch(fc=BCOL[b], ec="black", lw=0.2, label=b)
           for b in BIOME_ORDER]
fig.legend(handles=handles, ncol=6, loc="lower center",
           bbox_to_anchor=(0.5, 0.005), fontsize=6.5, frameon=False,
           handlelength=1.1, handletextpad=0.4, columnspacing=1.0,
           title="Inset bars — per-biome median share", title_fontsize=6.5)

fs.save(fig, "map_quartile_percent")
plt.close(fig)
print("Quartile-percent composition figure written.")
