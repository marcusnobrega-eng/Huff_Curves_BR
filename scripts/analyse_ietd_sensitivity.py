"""
IETD Sensitivity Analysis
=========================
Evaluates the impact of inter-event time definition (IETD) on:

  Metric 1 — Station-level dominant-quartile stability
  Metric 2 — National and biome-level quartile fraction shift
  Metric 3 — MAE and D_max of empirical Q1 curve vs Huff (1967) reference
  Metric 4 — Event count and duration distribution shift

Reads:
  outputs/station_huff_coefficients.csv          (baseline IETD = 6 h)
  outputs/rainfall_events.csv                    (baseline)
  outputs/sensitivity/ietd_Xh/station_huff_coefficients.csv
  outputs/sensitivity/ietd_Xh/rainfall_events.csv
  outputs/diagnostics/regional/station_results_with_geography.csv
    (for biome join on baseline station set)

Writes:
  outputs/sensitivity/ietd_sensitivity_summary.csv
  outputs/sensitivity/ietd_quartile_stability.csv
  outputs/sensitivity/ietd_curve_metrics.csv
  outputs/sensitivity/ietd_event_stats.csv
"""

from pathlib import Path
import csv, statistics, sys
import numpy as np
import pandas as pd

# ── configuration ──────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
IETD_VALUES = [2, 4, 6, 8, 12]
BASELINE = 6
OUT_DIR = ROOT / "outputs" / "sensitivity"

RESULTS = {
    ietd: (
        ROOT / "outputs" / "station_huff_coefficients.csv"
        if ietd == BASELINE
        else ROOT / "outputs" / "sensitivity" / f"ietd_{ietd}h" / "station_huff_coefficients.csv"
    )
    for ietd in IETD_VALUES
}
EVENTS = {
    ietd: (
        ROOT / "outputs" / "rainfall_events.csv"
        if ietd == BASELINE
        else ROOT / "outputs" / "sensitivity" / f"ietd_{ietd}h" / "rainfall_events.csv"
    )
    for ietd in IETD_VALUES
}
GEO_PATH = ROOT / "outputs" / "diagnostics" / "regional" / "station_results_with_geography.csv"

# ── Huff reference curves ──────────────────────────────────────────────────
HUFF_REFERENCE_COEFFICIENTS = np.array([
    [-0.9633,  3.8869, -7.8950, 10.0890, -8.0108,  3.8936, -0.0032],
    [-39.4360, 125.1800, -146.0400, 73.6040, -13.9360, 1.6243, -0.0068],
    [ 46.5420, -131.5500, 132.6300, -57.3150, 10.7960, -0.1107,  0.0050],
    [-25.2890,  67.5400, -64.9260, 28.0310, -5.2061,  0.8535, -0.0042],
], dtype=float)
HUFF_TAU = np.round(np.arange(0.1, 1.01, 0.1), 10)

def huff_reference(quartile: int, tau: np.ndarray) -> np.ndarray:
    raw = np.polyval(HUFF_REFERENCE_COEFFICIENTS[quartile - 1], tau)
    raw = np.clip(raw, 0.0, 1.0)
    return np.maximum.accumulate(raw)

TAU_GRID = np.round(np.arange(0.0, 1.001, 0.02), 10)


def load_ok(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df[df["status"] == "ok"].copy()


def load_events(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["start", "end"])


def safe_float(v):
    try:
        f = float(v)
        return f if np.isfinite(f) else np.nan
    except (TypeError, ValueError):
        return np.nan


# ══════════════════════════════════════════════════════════════════════════
# METRIC 4 — Event count and duration distribution shift
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "="*68)
print("METRIC 4 — Event count and duration distribution shift")
print("="*68)

evt_rows = []
print(f"\n{'IETD':>6}  {'N_events':>10}  {'N_stations':>11}  "
      f"{'Med_dur_h':>10}  {'Med_vol_mm':>11}  "
      f"{'Q1%':>6}  {'Q2%':>6}  {'Q3%':>6}  {'Q4%':>6}")

for ietd in IETD_VALUES:
    ev = load_events(EVENTS[ietd])
    n = len(ev)
    n_sta = ev["station_id"].nunique()
    med_dur = ev["duration_h"].median()
    med_vol = ev["volume_mm"].median()
    q_pct = {q: 100 * (ev["dominant_event_quartile"] == q).sum() / n
             for q in [1, 2, 3, 4]}
    print(f"  {ietd:>4}h  {n:>10,}  {n_sta:>11,}  "
          f"{med_dur:>10.2f}  {med_vol:>11.1f}  "
          f"{q_pct[1]:>6.1f}  {q_pct[2]:>6.1f}  {q_pct[3]:>6.1f}  {q_pct[4]:>6.1f}")
    evt_rows.append({"ietd_h": ietd, "n_events": n, "n_stations": n_sta,
                     "median_duration_h": med_dur, "median_volume_mm": med_vol,
                     **{f"q{q}_pct": q_pct[q] for q in [1, 2, 3, 4]}})

pd.DataFrame(evt_rows).to_csv(OUT_DIR / "ietd_event_stats.csv", index=False)
print(f"\n  → Saved: outputs/sensitivity/ietd_event_stats.csv")


# ══════════════════════════════════════════════════════════════════════════
# METRIC 1 — Station-level dominant-quartile stability
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "="*68)
print("METRIC 1 — Station-level dominant-quartile stability")
print("="*68)

# Build per-station dominant-quartile table across all IETD values
all_dfs = {}
for ietd in IETD_VALUES:
    ok = load_ok(RESULTS[ietd])
    ok["station_id"] = ok["station_id"].astype(str).str.replace(r"\.0$", "", regex=True)
    all_dfs[ietd] = ok.set_index("station_id")["dominant_quartile"].rename(f"q_{ietd}h")

stability_df = pd.concat(all_dfs.values(), axis=1)
stability_df.index.name = "station_id"

# Baseline OK stations only
baseline_ok = load_ok(RESULTS[BASELINE])
baseline_ok["station_id"] = baseline_ok["station_id"].astype(str).str.replace(r"\.0$", "", regex=True)
baseline_ids = set(baseline_ok["station_id"])
stab = stability_df.loc[stability_df.index.isin(baseline_ids)].copy()

# For each station, how many IETD values agree with the baseline quartile?
baseline_col = f"q_{BASELINE}h"
stab["baseline_q"] = stab[baseline_col]
other_cols = [f"q_{i}h" for i in IETD_VALUES if i != BASELINE]
stab["n_agree"] = stab[other_cols].apply(
    lambda row: (row == stab.loc[row.name, "baseline_col"]
                 if False else
                 sum(row[c] == stab.loc[row.name, "baseline_q"] for c in other_cols)),
    axis=1,
)
stab["fully_stable"] = stab["n_agree"] == len(other_cols)
stab["has_data_all"] = stab[other_cols].notna().all(axis=1)

n_baseline = len(stab)
n_stable = stab["fully_stable"].sum()
n_has_data = stab["has_data_all"].sum()

print(f"\n  Baseline OK stations:                 {n_baseline:>5,}")
print(f"  Stations with data at all IETD values: {n_has_data:>5,}")
print(f"  Fully stable (same Q at all IETD):     {n_stable:>5,}  ({100*n_stable/n_baseline:.1f}%)")

# Per IETD: % agreement with baseline
print(f"\n  Agreement with baseline (IETD={BASELINE}h) per IETD value:")
print(f"  {'IETD':>6}  {'N with data':>12}  {'N agree':>9}  {'% agree':>8}")
agree_rows = []
for ietd in IETD_VALUES:
    if ietd == BASELINE:
        continue
    col = f"q_{ietd}h"
    has = stab[col].notna() & stab["baseline_q"].notna()
    agree = (stab.loc[has, col] == stab.loc[has, "baseline_q"]).sum()
    n_has = has.sum()
    pct = 100 * agree / n_has if n_has > 0 else np.nan
    print(f"  {ietd:>4}h  {n_has:>12,}  {agree:>9,}  {pct:>8.1f}%")
    agree_rows.append({"ietd_h": ietd, "n_with_data": int(n_has),
                       "n_agree_with_baseline": int(agree), "pct_agree": pct})

# Quartile breakdown per IETD for stations in baseline OK set
print(f"\n  Dominant quartile distribution (baseline OK stations only):")
print(f"  {'IETD':>6}  {'Q1':>6}  {'Q2':>6}  {'Q3':>6}  {'Q4':>6}  {'NaN':>6}")
for ietd in IETD_VALUES:
    col = f"q_{ietd}h"
    vc = stab[col].value_counts(dropna=False)
    q1 = int(vc.get(1.0, vc.get(1, 0)))
    q2 = int(vc.get(2.0, vc.get(2, 0)))
    q3 = int(vc.get(3.0, vc.get(3, 0)))
    q4 = int(vc.get(4.0, vc.get(4, 0)))
    nan = int(stab[col].isna().sum())
    print(f"  {ietd:>4}h  {q1:>6,}  {q2:>6,}  {q3:>6,}  {q4:>6,}  {nan:>6,}")

stab.to_csv(OUT_DIR / "ietd_quartile_stability.csv")
pd.DataFrame(agree_rows).to_csv(OUT_DIR / "ietd_quartile_agreement.csv", index=False)
print(f"\n  → Saved: outputs/sensitivity/ietd_quartile_stability.csv")
print(f"  → Saved: outputs/sensitivity/ietd_quartile_agreement.csv")


# ══════════════════════════════════════════════════════════════════════════
# METRIC 3 — MAE and D_max of empirical Q1–Q4 curves vs Huff (1967)
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "="*68)
print("METRIC 3 — MAE and D_max of empirical curves vs Huff (1967)")
print("="*68)

# Load huff_curves_long for each IETD
def load_curves(ietd: int) -> pd.DataFrame:
    if ietd == BASELINE:
        p = ROOT / "outputs" / "huff_curves_long.csv"
    else:
        p = ROOT / "outputs" / "sensitivity" / f"ietd_{ietd}h" / "huff_curves_long.csv"
    return pd.read_csv(p)

curve_rows = []
print(f"\n  National median curve metrics (all baseline-OK stations pooled):")
print(f"  {'IETD':>6}  {'Q':>3}  {'MAE':>8}  {'D_max':>8}  {'N_stations':>11}")

for ietd in IETD_VALUES:
    curves = load_curves(ietd)
    curves["station_id"] = curves["station_id"].astype(str).str.replace(r"\.0$", "", regex=True)

    # Restrict to baseline OK station set for comparability
    curves = curves[curves["station_id"].isin(baseline_ids)]

    for q in [1, 2, 3, 4]:
        sub = curves[curves["quartile"] == q].copy()
        if sub.empty:
            continue
        # National median curve: median across stations at each tau
        national = (sub.groupby("tau")["median"]
                    .median()
                    .reset_index()
                    .sort_values("tau"))
        tau_vals = national["tau"].to_numpy()
        emp_vals = national["median"].to_numpy()

        # Interpolate to HUFF_TAU for comparison
        ref = huff_reference(q, HUFF_TAU)
        emp_at_ref = np.interp(HUFF_TAU, tau_vals, emp_vals)

        finite = np.isfinite(emp_at_ref) & np.isfinite(ref)
        if finite.sum() < 2:
            mae, d_max = np.nan, np.nan
        else:
            residuals = emp_at_ref[finite] - ref[finite]
            mae   = float(np.mean(np.abs(residuals)))
            d_max = float(np.max(np.abs(residuals)))

        n_sta = sub["station_id"].nunique()
        print(f"  {ietd:>4}h  {q:>3}  {mae:>8.4f}  {d_max:>8.4f}  {n_sta:>11,}")
        curve_rows.append({
            "ietd_h": ietd, "quartile": q,
            "n_stations": n_sta, "mae": mae, "d_max": d_max,
        })

pd.DataFrame(curve_rows).to_csv(OUT_DIR / "ietd_curve_metrics.csv", index=False)
print(f"\n  → Saved: outputs/sensitivity/ietd_curve_metrics.csv")


# ══════════════════════════════════════════════════════════════════════════
# METRIC 2 — National and biome-level quartile fraction shift
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "="*68)
print("METRIC 2 — National & biome-level quartile fraction shift")
print("="*68)

# Load biome mapping from baseline geography file
geo = pd.read_csv(GEO_PATH)
geo["station_id"] = geo["station_id"].astype(str).str.replace(r"\.0$", "", regex=True)
biome_map = geo.set_index("station_id")["biome_name"].to_dict()

summary_rows = []
print(f"\n  National level — dominant quartile fractions (OK stations only):")
print(f"  {'IETD':>6}  {'N_ok':>7}  {'Q1%':>7}  {'Q2%':>7}  {'Q3%':>7}  {'Q4%':>7}")

for ietd in IETD_VALUES:
    ok = load_ok(RESULTS[ietd])
    n = len(ok)
    dq = ok["dominant_quartile"].value_counts(normalize=True) * 100
    q_pct = {q: float(dq.get(float(q), dq.get(q, 0.0))) for q in [1, 2, 3, 4]}
    print(f"  {ietd:>4}h  {n:>7,}  {q_pct[1]:>7.1f}  {q_pct[2]:>7.1f}  "
          f"{q_pct[3]:>7.1f}  {q_pct[4]:>7.1f}")
    row = {"ietd_h": ietd, "scope": "national", "region": "Brazil",
           "n_ok": n, **{f"q{q}_pct": q_pct[q] for q in [1, 2, 3, 4]}}
    summary_rows.append(row)

print(f"\n  Biome level — Q1 fraction (%) by IETD:")
biomes = sorted(b for b in set(biome_map.values()) if isinstance(b, str))
header = f"  {'Biome':<22}" + "".join(f"  {i}h" for i in IETD_VALUES)
print(header)

for biome in biomes:
    biome_stations = {sid for sid, b in biome_map.items() if b == biome}
    line = f"  {biome:<22}"
    for ietd in IETD_VALUES:
        ok = load_ok(RESULTS[ietd])
        ok["station_id"] = ok["station_id"].astype(str).str.replace(r"\.0$", "", regex=True)
        sub = ok[ok["station_id"].isin(biome_stations)]
        if len(sub) == 0:
            line += f"  {'—':>4}"
            continue
        q1_pct = 100 * (sub["dominant_quartile"].isin([1, 1.0])).mean()
        line += f" {q1_pct:>5.1f}"
        summary_rows.append({
            "ietd_h": ietd, "scope": "biome", "region": biome,
            "n_ok": len(sub), "q1_pct": q1_pct,
        })
    print(line)

pd.DataFrame(summary_rows).to_csv(OUT_DIR / "ietd_sensitivity_summary.csv", index=False)
print(f"\n  → Saved: outputs/sensitivity/ietd_sensitivity_summary.csv")

print("\n" + "="*68)
print("IETD sensitivity analysis complete.")
print("="*68)
