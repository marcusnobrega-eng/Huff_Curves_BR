"""
Hydrological impact of the updated Huff curves (SCS-CN screening study).
=======================================================================
For a stratified national sample of small, SCS-eligible HydroBASINS-12
catchments (Cerrado, Caatinga, Mata Atlântica, Pampa), compute the
design-storm hydrograph under (i) the original Huff (1967) Q1 reference
and (ii) the locally derived biome Q1 curve, holding catchment, CN, Tc,
design depth, and duration identical. The only thing that differs is the
temporal pattern, so the change in peak discharge and time-to-peak is
attributable solely to the hyetograph.

Data sources
  catchments : HydroBASINS level 12 (HydroSHEDS)
  soil (HSG) : SoilGrids 250 m clay/sand -> USDA texture -> HSG
  terrain    : Copernicus GLO-90 DEM (windowed COG reads)  -> Tc (Kirpich)
  rainfall   : Xavier gridded Sherman IDF  i = K*T^a/(t+b)^c
  curves     : original Huff (1967) Q1 ; biome Q1 (this study)

Output: outputs/hydro_impact/catchment_impact.csv
        outputs/hydro_impact/design_hydrographs.npz
"""
from pathlib import Path
import os
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.windows import from_bounds

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from huff_curves_br.hydrology import (
    hack_length_km, kirpich_tc_hours, compare_patterns, design_hydrograph)
from huff_curves_br.constants import HUFF_REFERENCE_COEFFICIENTS

os.environ["AWS_NO_SIGN_REQUEST"] = "YES"
os.environ["GDAL_HTTP_TIMEOUT"] = "30"

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "hydro_impact"
OUT.mkdir(parents=True, exist_ok=True)

RNG = np.random.default_rng(42)
N_PER_BIOME = 150
RETURN_PERIOD = 25.0          # years
IA_RATIO = 0.2

# ── soil grids (SoilGrids 0-5 cm, %, 0.02deg) ──────────────────────────────
CLAY = np.load(ROOT / "data/reference/hydro/brazil_clay_005.npy") / 10.0
SAND = np.load(ROOT / "data/reference/hydro/brazil_sand_005.npy") / 10.0
_LONMIN, _LONMAX, _LATMIN, _LATMAX = -74.0, -33.0, -34.5, 6.5
_RES = 0.02

def soil_at(lon, lat):
    j = int((lon - _LONMIN) / _RES)
    i = int((_LATMAX - lat) / _RES)              # row 0 = north
    if 0 <= i < CLAY.shape[0] and 0 <= j < CLAY.shape[1]:
        return float(CLAY[i, j]), float(SAND[i, j])
    return np.nan, np.nan

def hsg_from_texture(clay, sand):
    """USDA-texture-informed hydrologic soil group (A/B/C/D)."""
    if not (np.isfinite(clay) and np.isfinite(sand)):
        return "C"
    if sand >= 70 and clay < 10:
        return "A"
    if clay >= 40:
        return "D"
    if clay >= 27:
        return "C"
    if clay < 18 and sand >= 50:
        return "B"
    return "C" if clay >= 20 else "B"

# CN (AMC II) by biome land-cover archetype x HSG, from NRCS NEH-630 tables
CN_TABLE = {
    "Cerrado":        {"A": 35, "B": 58, "C": 70, "D": 77},   # savanna/woodland, good
    "Caatinga":       {"A": 45, "B": 66, "C": 77, "D": 83},   # semi-arid shrub, fair
    "Mata Atlântica": {"A": 36, "B": 60, "C": 73, "D": 79},   # forest/ag mosaic, good
    "Pampa":          {"A": 39, "B": 61, "C": 74, "D": 80},   # grassland/pasture, good
}

# ── IDF (Xavier Sherman params) ────────────────────────────────────────────
IDF_SRC = ROOT / "idf/XAVIER/RASTER"
_idf = {p: rasterio.open(IDF_SRC / f"IDF_{p}.tif") for p in ["k", "a", "b", "c"]}

def idf_params(lon, lat):
    out = {}
    for p, ds in _idf.items():
        try:
            r, c = ds.index(lon, lat)
            v = ds.read(1)[r, c]
            out[p] = float(v) if np.isfinite(v) else np.nan
        except Exception:
            out[p] = np.nan
    return out

def design_depth_mm(lon, lat, duration_h, T=RETURN_PERIOD):
    pr = idf_params(lon, lat)
    if any(not np.isfinite(v) for v in pr.values()):
        return np.nan
    t_min = duration_h * 60.0
    i = pr["k"] * (T ** pr["a"]) / ((t_min + pr["b"]) ** pr["c"])   # mm/h
    return float(i * duration_h)

# ── DEM (Copernicus GLO-90) windowed read -> relief, slope ────────────────
def cop_tile_url(lat, lon):
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    name = f"Copernicus_DSM_COG_30_{ns}{abs(int(np.floor(lat))):02d}_00_{ew}{abs(int(np.floor(lon))):03d}_00_DEM"
    return f"/vsicurl/https://copernicus-dem-90m.s3.amazonaws.com/{name}/{name}.tif"

def terrain(geom):
    minx, miny, maxx, maxy = geom.bounds
    clat, clon = (miny + maxy) / 2.0, (minx + maxx) / 2.0
    url = cop_tile_url(clat, clon)
    try:
        with rasterio.open(url) as src:
            b = src.bounds
            wx0, wy0 = max(minx, b.left), max(miny, b.bottom)
            wx1, wy1 = min(maxx, b.right), min(maxy, b.top)
            if wx1 <= wx0 or wy1 <= wy0:
                return np.nan, np.nan
            win = from_bounds(wx0, wy0, wx1, wy1, src.transform)
            a = src.read(1, window=win).astype(float)
            a = a[np.isfinite(a) & (a > -1000)]
            if a.size < 10:
                return np.nan, np.nan
            relief = float(np.percentile(a, 95) - np.percentile(a, 5))
            return relief, a.size
    except Exception:
        return np.nan, np.nan

# ── Huff CDF callables ─────────────────────────────────────────────────────
def make_cdf(coeffs):
    coeffs = np.asarray(coeffs, dtype=float)
    def cdf(tau):
        tau = np.asarray(tau, dtype=float)
        v = np.polyval(coeffs, tau)
        v = np.clip(v, 0.0, 1.0)
        v = np.maximum.accumulate(v) if v.ndim else v
        if v.ndim:
            v[0], v[-1] = 0.0, 1.0
        return v
    return cdf

HUFF_REF_Q1 = make_cdf(HUFF_REFERENCE_COEFFICIENTS[0])

biome_coef = pd.read_csv(ROOT / "outputs/diagnostics/regional/biome_huff_coefficients.csv")
BIOME_Q1 = {}
for _, row in biome_coef.iterrows():
    c = [row[f"q1_coef_{i}"] for i in range(1, 9)]
    if all(np.isfinite(c)):
        BIOME_Q1[row["biome_name"]] = make_cdf(c)

# ── sample catchments ──────────────────────────────────────────────────────
cat = gpd.read_file(ROOT / "data/reference/hydro/eligible_catchments.gpkg")
sample = []
for b in ["Cerrado", "Caatinga", "Mata Atlântica", "Pampa"]:
    sub = cat[cat["biome"] == b]
    idx = RNG.choice(sub.index.to_numpy(), size=min(N_PER_BIOME, len(sub)), replace=False)
    sample.append(sub.loc[idx])
sample = pd.concat(sample)
sample = gpd.GeoDataFrame(sample, geometry="geometry", crs=cat.crs).reset_index(drop=True)
print(f"Sampled {len(sample)} catchments; computing impact...")

rows = []
hydrographs = {}
for k, c in sample.iterrows():
    geom = c.geometry
    area = float(c["SUB_AREA"])
    lon, lat = geom.representative_point().x, geom.representative_point().y
    biome = c["biome"]
    if biome not in BIOME_Q1:
        continue

    relief, npix = terrain(geom)
    if not np.isfinite(relief) or relief <= 0:
        continue
    L_km = hack_length_km(area)
    L_m = L_km * 1000.0
    slope = max(relief / L_m, 1e-3)
    tc = kirpich_tc_hours(L_m, slope)
    tc = float(np.clip(tc, 0.1, 24.0))

    clay, sand = soil_at(lon, lat)
    hsg = hsg_from_texture(clay, sand)
    cn = CN_TABLE[biome][hsg]

    depth = design_depth_mm(lon, lat, tc)
    if not np.isfinite(depth) or depth <= 0:
        continue

    res = compare_patterns(depth, tc, HUFF_REF_Q1, BIOME_Q1[biome],
                           cn=cn, tc_hours=tc, area_km2=area, ia_ratio=IA_RATIO)
    hybas_id = int(c["HYBAS_ID"])
    rows.append({
        "hybas_id": hybas_id, "biome": biome, "lon": lon, "lat": lat,
        "area_km2": area, "relief_m": relief, "slope": slope, "tc_h": tc,
        "clay_pct": clay, "sand_pct": sand, "hsg": hsg, "cn": cn,
        "depth_mm": depth, **res,
    })
    # store time/discharge arrays for both reference and local curves
    _ref = design_hydrograph(depth, tc, HUFF_REF_Q1,    cn=cn, tc_hours=tc, area_km2=area, ia_ratio=IA_RATIO)
    _loc = design_hydrograph(depth, tc, BIOME_Q1[biome], cn=cn, tc_hours=tc, area_km2=area, ia_ratio=IA_RATIO)
    hydrographs[hybas_id] = {
        "t_ref":   _ref.time_hours,        "q_ref":   _ref.discharge_m3s,
        "t_local": _loc.time_hours,        "q_local": _loc.discharge_m3s,
    }
    if (k + 1) % 100 == 0:
        print(f"  {k+1}/{len(sample)} processed ({len(rows)} valid)")

df = pd.DataFrame(rows)
df.to_csv(OUT / "catchment_impact.csv", index=False)
print(f"\nWrote {OUT/'catchment_impact.csv'}  ({len(df)} catchments)")

# save per-catchment design hydrographs (ragged arrays -> object npz)
npz_data = {}
for hid, arrs in hydrographs.items():
    for key, arr in arrs.items():
        npz_data[f"{hid}__{key}"] = arr
np.savez_compressed(OUT / "design_hydrographs.npz", **npz_data)
print(f"Wrote {OUT/'design_hydrographs.npz'}  ({len(hydrographs)} catchments)")
print("\n=== Δ peak discharge (updated vs original Huff), % ===")
print(df.groupby("biome")["d_qp_pct"].describe()[["count", "mean", "50%", "min", "max"]].round(2))
print("\n=== Δ time-to-peak (h) ===")
print(df.groupby("biome")["d_tp_h"].describe()[["mean", "50%"]].round(3))
print(f"\nNATIONAL median Δpeak = {df['d_qp_pct'].median():.2f}%  "
      f"(IQR {df['d_qp_pct'].quantile(.25):.2f} to {df['d_qp_pct'].quantile(.75):.2f})")
print(f"NATIONAL median Δtp   = {df['d_tp_h'].median():.3f} h")
