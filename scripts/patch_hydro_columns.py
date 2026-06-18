"""
Patch catchment_impact.csv with the columns added after the initial run:
  rc            — runoff coefficient (= runoff_mm / depth_mm)
  duration_ref_h, duration_local_h, d_duration_h
                — hydrograph duration (time to Q < 1 % of peak)

All catchment inputs (depth_mm, tc_h, cn, area_km2, biome) are already
in the CSV, so this avoids re-downloading any DEM/IDF/soil data.
"""
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from huff_curves_br.hydrology import design_hydrograph, _hydrograph_duration_hours
from huff_curves_br.constants import HUFF_REFERENCE_COEFFICIENTS

# ── rebuild Huff CDF callables ──────────────────────────────────────────────
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

IA_RATIO = 0.2
OUT = ROOT / "outputs" / "hydro_impact"

df = pd.read_csv(OUT / "catchment_impact.csv")
print(f"Loaded {len(df)} catchments.")

rc_vals, dur_ref, dur_loc, d_dur = [], [], [], []

for _, row in df.iterrows():
    biome = row["biome"]
    depth = row["depth_mm"]
    tc    = row["tc_h"]
    cn    = row["cn"]
    area  = row["area_km2"]

    rc_vals.append(row["runoff_mm"] / depth if depth > 0 else np.nan)

    if biome not in BIOME_Q1 or not all(np.isfinite([depth, tc, cn, area])):
        dur_ref.append(np.nan); dur_loc.append(np.nan); d_dur.append(np.nan)
        continue

    ref = design_hydrograph(depth, tc, HUFF_REF_Q1,
                            cn=cn, tc_hours=tc, area_km2=area, ia_ratio=IA_RATIO)
    loc = design_hydrograph(depth, tc, BIOME_Q1[biome],
                            cn=cn, tc_hours=tc, area_km2=area, ia_ratio=IA_RATIO)
    dr = _hydrograph_duration_hours(ref)
    dl = _hydrograph_duration_hours(loc)
    dur_ref.append(dr); dur_loc.append(dl); d_dur.append(dl - dr)

df["rc"]               = rc_vals
df["duration_ref_h"]   = dur_ref
df["duration_local_h"] = dur_loc
df["d_duration_h"]     = d_dur

df.to_csv(OUT / "catchment_impact.csv", index=False)
print(f"Patched CSV written ({len(df)} rows).")
print(df[["rc", "duration_ref_h", "duration_local_h", "d_duration_h"]].describe().round(3))
