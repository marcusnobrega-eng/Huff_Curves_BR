"""
Figure: Data-availability map with SRTM DEM hillshade background    (C3)
=========================================================================
Downloads SRTM tiles via srtm.py, assembles a DEM grid for Brazil,
computes a hillshade, then overlays the station data-availability layer.

Saves: outputs/figures/casestudy_dem.pdf / .svg / .png
       manuscript/figures/casestudy_dem.pdf
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm
from matplotlib.colors import LightSource
import matplotlib.patches as mpatches
import geopandas as gpd
import srtm

# ── paths ─────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "outputs" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# ── Brazil extent ─────────────────────────────────────────────────────────
LON_MIN, LON_MAX = -74.0, -28.0
LAT_MIN, LAT_MAX = -34.5,   5.5

# ── DEM grid parameters ───────────────────────────────────────────────────
# 0.05° spacing ≈ 5.5 km — fine for a country-scale figure
RES   = 0.05
lons  = np.arange(LON_MIN, LON_MAX + RES, RES)
lats  = np.arange(LAT_MAX, LAT_MIN - RES, -RES)   # north → south
NLAT, NLON = len(lats), len(lons)
print(f"DEM grid: {NLAT} × {NLON} = {NLAT*NLON:,} points "
      f"(spacing {RES}°)")

# ── download / assemble SRTM elevation ────────────────────────────────────
cache_path = ROOT / "data" / "reference" / "dem" / "brazil_dem.npy"
cache_path.parent.mkdir(parents=True, exist_ok=True)

if cache_path.exists():
    print("Loading cached DEM …")
    elev = np.load(str(cache_path))
else:
    print("Downloading SRTM tiles — this takes a few minutes …")
    srtm_data = srtm.get_data()
    elev = np.full((NLAT, NLON), np.nan, dtype=np.float32)

    total = NLAT * NLON
    step  = max(1, total // 20)
    done  = 0

    for i, lat in enumerate(lats):
        for j, lon in enumerate(lons):
            e = srtm_data.get_elevation(lat, lon)
            if e is not None:
                elev[i, j] = e
            done += 1
            if done % step == 0:
                print(f"  {100*done/total:.0f}% …", flush=True)

    # fill small gaps with nearest-valid
    from scipy.ndimage import generic_filter
    def fill_nan(arr):
        center = arr[len(arr)//2]
        if not np.isnan(center):
            return center
        valid = arr[~np.isnan(arr)]
        return valid.mean() if valid.size else 0.0
    for _ in range(3):
        mask = np.isnan(elev)
        if not mask.any():
            break
        elev = generic_filter(elev, fill_nan, size=3,
                              mode='nearest').astype(np.float32)
    elev = np.where(np.isnan(elev), 0.0, elev)

    np.save(str(cache_path), elev)
    print("DEM cached.")

print(f"Elevation range: {elev.min():.0f} m – {elev.max():.0f} m")

# ── hillshade ─────────────────────────────────────────────────────────────
ls = LightSource(azdeg=315, altdeg=40)
hs = ls.hillshade(elev, vert_exag=6, dx=RES*111_000, dy=RES*111_000)
# blend hillshade with elevation for tinted effect
norm_elev = (np.clip(elev, 0, 3000) / 3000.0)

# ── load boundaries ───────────────────────────────────────────────────────
biome_gdf = gpd.read_file(
    ROOT/"data"/"reference"/"ibge"/"normalized"/"biomes.gpkg").to_crs(4326)
state_gdf = gpd.read_file(
    ROOT/"data"/"reference"/"ibge"/"normalized"/"states.gpkg").to_crs(4326)

# ── station data ──────────────────────────────────────────────────────────
df = pd.read_csv(ROOT/"outputs"/"station_huff_coefficients.csv")
df["lat"]        = pd.to_numeric(df["lat"],        errors="coerce")
df["lon"]        = pd.to_numeric(df["lon"],        errors="coerce")
df["years_span"] = pd.to_numeric(df["years_span"], errors="coerce")
df = df.dropna(subset=["lat","lon"])

ok  = df[df["status"] == "ok"]
rej = df[df["status"] != "ok"]

# ── style ─────────────────────────────────────────────────────────────────
MM = 1/25.4; FW = 190*MM
plt.rcParams.update({
    "font.family":"sans-serif","font.size":8,
    "axes.labelsize":9,"axes.titlesize":10,
    "xtick.labelsize":7,"ytick.labelsize":7,
    "legend.fontsize":7,"axes.linewidth":0.6,
    "figure.dpi":200,"savefig.dpi":300,
    "pdf.fonttype":42,"svg.fonttype":"none",
})

fig, axes = plt.subplots(1, 2, figsize=(FW, FW*0.55),
                          gridspec_kw=dict(width_ratios=[1.7, 1]),
                          constrained_layout=True)

# ── LEFT PANEL: DEM hillshade + stations ─────────────────────────────────
ax = axes[0]
extent = [LON_MIN, LON_MAX, LAT_MIN, LAT_MAX]

# Base: blended hillshade + hypsometric tint
cmap_topo = plt.cm.terrain
rgba = cmap_topo(norm_elev * 0.6 + 0.15)[:, :, :3]
blended = hs[..., np.newaxis] * 0.5 + rgba * 0.5
blended = np.clip(blended, 0, 1)

ax.imshow(blended, extent=extent, origin="upper",
          aspect="equal", zorder=1)

# Boundaries
biome_gdf.boundary.plot(ax=ax, color="#555555", lw=0.35, zorder=2, alpha=0.7)
state_gdf.boundary.plot(ax=ax, color="#111111", lw=0.55, zorder=3, alpha=0.8)

# Rejected stations (small grey)
ax.scatter(rej["lon"], rej["lat"],
           c="#cccccc", s=1.5, lw=0, zorder=4, alpha=0.5,
           rasterized=True, label=f"Excluded (n={len(rej):,})")

# OK stations — coloured by years of record
cmap_sta = plt.cm.plasma_r
norm_sta = mcolors.Normalize(vmin=4, vmax=16)
sc = ax.scatter(ok["lon"], ok["lat"],
                c=ok["years_span"], cmap=cmap_sta, norm=norm_sta,
                s=7, lw=0.2, edgecolors="white",
                zorder=5, rasterized=True,
                label=f"Accepted (n={len(ok):,})")

cb = plt.colorbar(sc, ax=ax, fraction=0.03, pad=0.02, aspect=25)
cb.set_label("Record length (yr)", fontsize=8)
cb.ax.tick_params(labelsize=7)

ax.set_xlim(LON_MIN, LON_MAX)
ax.set_ylim(LAT_MIN, LAT_MAX)
ax.set_aspect("equal")
ax.set_xlabel("Longitude (°)", fontsize=9)
ax.set_ylabel("Latitude (°)", fontsize=9)
ax.set_title("(a)  ANA telemetric stations and record length",
             fontweight="bold", pad=4)

# Legend
leg_patches = [
    mpatches.Patch(fc="#cccccc", ec="#999999", label=f"Excluded stations (n={len(rej):,})"),
    mpatches.Patch(fc=cmap_sta(norm_sta(10)), label=f"Accepted stations (n={len(ok):,})"),
]
ax.legend(handles=leg_patches, loc="lower left", fontsize=6.5,
          framealpha=0.88, edgecolor="#aaaaaa", handlelength=1)

# Annotations: biome labels (centroid)
biome_labels = {
    "Amazônia":      (-62, -3),
    "Cerrado":       (-49, -13),
    "Caatinga":      (-39, -10),
    "Mata Atlântica":(-43, -22),
    "Pampa":         (-52, -30),
    "Pantanal":      (-57, -18),
}
for name, (x, y) in biome_labels.items():
    short = name.replace("Mata Atlântica", "Mata\nAtlântica")
    ax.text(x, y, short, fontsize=5.5, color="#111111",
            ha="center", va="center", zorder=6,
            bbox=dict(fc="white", alpha=0.55, ec="none", pad=0.8))

# ── RIGHT PANEL: histogram of record lengths ──────────────────────────────
ax2 = axes[1]
bins = np.arange(0, 17.5, 1)
all_span = df["years_span"].dropna()
ok_span  = ok["years_span"].dropna()

ax2.hist(all_span, bins=bins, color="#cccccc", edgecolor="#999999",
         lw=0.4, zorder=2, label=f"All stations\n(n={len(all_span):,})")
ax2.hist(ok_span,  bins=bins, color=cmap_sta(0.55), edgecolor="white",
         lw=0.3, alpha=0.85, zorder=3,
         label=f"Accepted stations\n(n={len(ok_span):,})")
ax2.axvline(4, color="#d62728", lw=1.2, ls="--",
            zorder=4, label="QC threshold\n(4-yr minimum)")

ax2.set_xlabel("Record length (years)", fontsize=9)
ax2.set_ylabel("Number of stations",    fontsize=9)
ax2.set_title("(b)  Record length distribution",
              fontweight="bold", pad=4)
ax2.legend(fontsize=6.5, framealpha=0.9, edgecolor="#aaaaaa",
           loc="upper left")
ax2.grid(True, lw=0.3, color="#dddddd", zorder=0)
ax2.set_xlim(0, 17)
med_ok = ok_span.median()
ax2.text(0.97, 0.97,
         f"Median (accepted): {med_ok:.1f} yr\nMedian (all):      {all_span.median():.1f} yr",
         transform=ax2.transAxes, ha="right", va="top",
         fontsize=6.5, color="#222222",
         bbox=dict(fc="white", ec="#cccccc", alpha=0.85, pad=2))

# ── save ──────────────────────────────────────────────────────────────────
def save(fig, stem):
    for ext, dpi in [("pdf",None),("svg",None),("png",150)]:
        kw = dict(bbox_inches="tight")
        if dpi: kw["dpi"] = dpi
        fig.savefig(str(stem)+f".{ext}", format=ext, **kw)
    print(f"  → {stem}.pdf / .svg / .png")

save(fig, FIG_DIR/"casestudy_dem")

# also copy to manuscript/figures/
import shutil
(ROOT/"manuscript"/"figures").mkdir(parents=True, exist_ok=True)
shutil.copy(str(FIG_DIR/"casestudy_dem.pdf"),
            str(ROOT/"manuscript"/"figures"/"casestudy_dem.pdf"))

plt.close(fig)
print("Done.")
