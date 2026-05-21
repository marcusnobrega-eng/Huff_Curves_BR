"""Regional empirical Huff curve aggregation and GIS exports."""

from __future__ import annotations

import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from .constants import HUFF_FIT_DEGREE, HUFF_REFERENCE_TAU
from .geodata import _require_geopandas, enrich_station_geography, load_ibge_reference_layers
from .huff import original_huff_curves, sanitize_cdf
from .metrics import MetricResult, fitness_metrics


def _as_station_id(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace(r"\.0$", "", regex=True)


def _fit_curve(tau: np.ndarray, curve: np.ndarray, quartile: int) -> tuple[np.ndarray, MetricResult]:
    finite = np.isfinite(tau) & np.isfinite(curve)
    if finite.sum() < HUFF_FIT_DEGREE + 1:
        return np.full(HUFF_FIT_DEGREE + 1, np.nan), MetricResult(*(float("nan"),) * 7, n_valid=0)
    coeffs = np.polyfit(tau[finite], curve[finite], HUFF_FIT_DEGREE)
    fitted_reference_tau = sanitize_cdf(np.polyval(coeffs, HUFF_REFERENCE_TAU), force_endpoints=False)
    reference = original_huff_curves(HUFF_REFERENCE_TAU)[quartile - 1]
    return coeffs, fitness_metrics(fitted_reference_tau, reference)


def _metric_prefix(row: dict[str, object], prefix: str, coeffs: np.ndarray, metrics: MetricResult) -> None:
    row[f"{prefix}_kge"] = metrics.kge
    row[f"{prefix}_r2"] = metrics.r2
    row[f"{prefix}_rmse"] = metrics.rmse
    row[f"{prefix}_mae"] = metrics.mae
    for i, coef in enumerate(coeffs, start=1):
        row[f"{prefix}_coef_{i}"] = float(coef)


def _dominant_quartile(row: pd.Series) -> int | None:
    counts = np.array([row.get(f"q{q}_n_events", 0) for q in range(1, 5)], dtype=float)
    counts = np.where(np.isfinite(counts), counts, 0.0)
    return int(np.argmax(counts) + 1) if counts.sum() > 0 else None


def _intensity_columns(df: pd.DataFrame) -> list[str]:
    return [f"q{q}_max_intensity_mm_h" for q in range(1, 5) if f"q{q}_max_intensity_mm_h" in df.columns]


def _station_summary(
    stations: pd.DataFrame,
    region_id_col: str,
    region_name_col: str,
    extra_cols: list[str],
) -> pd.DataFrame:
    ok = stations[stations["status"].eq("ok")].copy()
    ok = ok.dropna(subset=[region_id_col])
    ok["station_id"] = _as_station_id(ok["station_id"])
    ok[region_id_col] = ok[region_id_col].astype(str).str.replace(r"\.0$", "", regex=True)

    intensity_cols = _intensity_columns(ok)
    if intensity_cols:
        ok["station_max_intensity_mm_h"] = ok[intensity_cols].max(axis=1, skipna=True)
    else:
        ok["station_max_intensity_mm_h"] = np.nan

    group_cols = list(dict.fromkeys([region_id_col, region_name_col] + [c for c in extra_cols if c in ok.columns]))
    rows = []
    for keys, group in ok.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = {col: value for col, value in zip(group_cols, keys)}
        row["n_stations"] = int(group["station_id"].nunique())
        row["n_events"] = int(pd.to_numeric(group["n_events"], errors="coerce").fillna(0).sum())
        row["median_years_span"] = float(pd.to_numeric(group["years_span"], errors="coerce").median())
        row["median_kge_mean"] = float(pd.to_numeric(group["kge_mean"], errors="coerce").median())
        row["median_missing_fraction"] = float(pd.to_numeric(group["missing_fraction"], errors="coerce").median())
        row["median_max_intensity_mm_h"] = float(pd.to_numeric(group["station_max_intensity_mm_h"], errors="coerce").median())
        row["max_event_intensity_mm_h"] = float(pd.to_numeric(group["station_max_intensity_mm_h"], errors="coerce").max())
        for q in range(1, 5):
            q_col = f"q{q}_n_events"
            if q_col in group.columns:
                row[q_col] = int(pd.to_numeric(group[q_col], errors="coerce").fillna(0).sum())
            else:
                row[q_col] = 0
        row["dominant_quartile"] = _dominant_quartile(pd.Series(row))
        rows.append(row)
    return pd.DataFrame(rows)


def regional_median_curves(
    stations: pd.DataFrame,
    curves: str | Path | pd.DataFrame,
    region_id_col: str,
    region_name_col: str,
    extra_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Aggregate station median Huff curves to regional median curves."""
    extra_cols = extra_cols or []
    station_cols = list(dict.fromkeys(["station_id", region_id_col, region_name_col] + [c for c in extra_cols if c in stations.columns]))
    station_regions = stations[stations["status"].eq("ok")][station_cols].dropna(subset=[region_id_col]).copy()
    station_regions["station_id"] = _as_station_id(station_regions["station_id"])
    station_regions[region_id_col] = station_regions[region_id_col].astype(str).str.replace(r"\.0$", "", regex=True)

    curve_table = pd.read_csv(curves) if not isinstance(curves, pd.DataFrame) else curves.copy()
    curve_table["station_id"] = _as_station_id(curve_table["station_id"])
    curve_table["quartile"] = pd.to_numeric(curve_table["quartile"], errors="coerce").astype("Int64")
    curve_table["tau"] = pd.to_numeric(curve_table["tau"], errors="coerce")
    curve_table["median"] = pd.to_numeric(curve_table["median"], errors="coerce")
    curve_table = curve_table.dropna(subset=["quartile", "tau", "median"])

    merged = curve_table.merge(station_regions, on="station_id", how="inner")
    group_cols = list(dict.fromkeys([region_id_col, region_name_col] + [c for c in extra_cols if c in merged.columns] + ["quartile", "tau"]))
    out = (
        merged.groupby(group_cols, dropna=False)
        .agg(
            median=("median", "median"),
            n_curve_stations=("station_id", "nunique"),
        )
        .reset_index()
    )
    return out


def regional_huff_coefficients(
    stations,
    curves: str | Path | pd.DataFrame,
    region_id_col: str,
    region_name_col: str,
    scope: str,
    extra_cols: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute regional median Huff curves and polynomial coefficients."""
    extra_cols = extra_cols or []
    station_df = pd.DataFrame(stations.drop(columns="geometry", errors="ignore")).copy()
    summary = _station_summary(station_df, region_id_col, region_name_col, extra_cols)
    curves_long = regional_median_curves(station_df, curves, region_id_col, region_name_col, extra_cols)

    coeff_rows = []
    for _, summary_row in summary.iterrows():
        row = summary_row.to_dict()
        row["scope"] = scope
        for q in range(1, 5):
            subset = curves_long[
                (curves_long[region_id_col].astype(str) == str(summary_row[region_id_col]))
                & (curves_long["quartile"].astype(int) == q)
            ].sort_values("tau")
            row[f"q{q}_n_curve_stations"] = int(subset["n_curve_stations"].max()) if not subset.empty else 0
            coeffs, metrics = _fit_curve(subset["tau"].to_numpy(float), subset["median"].to_numpy(float), q)
            _metric_prefix(row, f"q{q}", coeffs, metrics)
        coeff_rows.append(row)

    coeffs = pd.DataFrame(coeff_rows)
    sort_cols = [region_id_col]
    if sort_cols[0] in coeffs.columns:
        coeffs = coeffs.sort_values(sort_cols).reset_index(drop=True)
    return coeffs, curves_long


def _safe_shapefile_columns(columns: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    used: set[str] = set()
    replacements = {
        "municipality_code": "mun_code",
        "municipality_name": "mun_name",
        "state_code": "uf_code",
        "state_abbrev": "uf",
        "state_name": "uf_name",
        "biome_name": "biome",
        "dominant_quartile": "dom_q",
        "n_stations": "n_sta",
        "n_events": "n_evt",
        "median_years_span": "med_yrs",
        "median_kge_mean": "med_kge",
        "median_missing_fraction": "med_miss",
        "median_max_intensity_mm_h": "med_int",
        "max_event_intensity_mm_h": "max_int",
    }
    for col in columns:
        if col == "geometry":
            continue
        candidate = replacements.get(col)
        if candidate is None:
            candidate = re.sub(r"[^A-Za-z0-9_]+", "_", col)
            candidate = candidate.replace("_n_events", "_evt")
            candidate = candidate.replace("_n_curve_stations", "_sta")
            candidate = candidate.replace("_coef_", "_c")
            candidate = candidate.replace("_quartile", "_q")
            candidate = candidate[:10]
        base = candidate[:10]
        candidate = base
        i = 1
        while candidate.lower() in used:
            suffix = str(i)
            candidate = f"{base[: 10 - len(suffix)]}{suffix}"
            i += 1
        used.add(candidate.lower())
        mapping[col] = candidate
    return mapping


def export_region_products(
    coefficients: pd.DataFrame,
    geometries,
    region_id_col: str,
    output_dir: str | Path,
    basename: str,
) -> dict[str, Path]:
    """Export regional coefficients to CSV, GeoPackage, and Shapefile."""
    gpd = _require_geopandas()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / f"{basename}_huff_coefficients.csv"
    gpkg_path = output_dir / f"{basename}_huff_coefficients.gpkg"
    shp_dir = output_dir / f"{basename}_huff_coefficients_shp"
    shp_path = shp_dir / f"{basename}_huff_coefficients.shp"

    coefficients.to_csv(csv_path, index=False)

    regions = geometries.copy()
    regions[region_id_col] = regions[region_id_col].astype(str).str.replace(r"\.0$", "", regex=True)
    coeffs = coefficients.copy()
    coeffs[region_id_col] = coeffs[region_id_col].astype(str).str.replace(r"\.0$", "", regex=True)
    merged = regions.merge(coeffs, on=region_id_col, how="inner")
    merged = gpd.GeoDataFrame(merged, geometry="geometry", crs=regions.crs).to_crs(4326)
    merged.to_file(gpkg_path, driver="GPKG")

    shp_dir.mkdir(parents=True, exist_ok=True)
    shp = merged.rename(columns=_safe_shapefile_columns(list(merged.columns)))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        shp.to_file(shp_path, driver="ESRI Shapefile", encoding="UTF-8")

    return {"csv": csv_path, "gpkg": gpkg_path, "shapefile": shp_path}


def build_regional_products(
    station_results: str | Path | pd.DataFrame,
    curves: str | Path | pd.DataFrame,
    reference_dir: str | Path = "data/reference/ibge",
    output_dir: str | Path = "outputs/regional",
) -> dict[str, Path]:
    """Create state, municipality, and biome median-Huff coefficient products."""
    layers = load_ibge_reference_layers(reference_dir)
    stations = enrich_station_geography(
        station_results,
        municipalities=layers["municipalities"],
        states=layers["states"],
        biomes=layers["biomes"],
    )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    station_csv = output_dir / "station_results_with_geography.csv"
    station_gpkg = output_dir / "station_results_with_geography.gpkg"
    stations.drop(columns="geometry").to_csv(station_csv, index=False)
    stations.to_file(station_gpkg, driver="GPKG")

    outputs = {"station_geography_csv": station_csv, "station_geography_gpkg": station_gpkg}

    state_coeffs, state_curves = regional_huff_coefficients(
        stations,
        curves,
        region_id_col="state_code",
        region_name_col="state_name",
        scope="state",
        extra_cols=["state_abbrev", "region_name"],
    )
    state_curves_path = output_dir / "state_huff_curves_long.csv"
    state_curves.to_csv(state_curves_path, index=False)
    outputs["state_curves_csv"] = state_curves_path
    outputs.update({f"state_{k}": v for k, v in export_region_products(
        state_coeffs,
        layers["states"],
        "state_code",
        output_dir,
        "state",
    ).items()})

    city_coeffs, city_curves = regional_huff_coefficients(
        stations,
        curves,
        region_id_col="municipality_code",
        region_name_col="municipality_name",
        scope="municipality",
        extra_cols=["state_abbrev", "state_name", "region_name", "biome_name"],
    )
    city_curves_path = output_dir / "municipality_huff_curves_long.csv"
    city_curves.to_csv(city_curves_path, index=False)
    outputs["municipality_curves_csv"] = city_curves_path
    outputs.update({f"municipality_{k}": v for k, v in export_region_products(
        city_coeffs,
        layers["municipalities"],
        "municipality_code",
        output_dir,
        "municipality",
    ).items()})

    biome_coeffs, biome_curves = regional_huff_coefficients(
        stations,
        curves,
        region_id_col="biome_name",
        region_name_col="biome_name",
        scope="biome",
    )
    biome_curves_path = output_dir / "biome_huff_curves_long.csv"
    biome_curves.to_csv(biome_curves_path, index=False)
    outputs["biome_curves_csv"] = biome_curves_path
    outputs.update({f"biome_{k}": v for k, v in export_region_products(
        biome_coeffs,
        layers["biomes"],
        "biome_name",
        output_dir,
        "biome",
    ).items()})

    return outputs
