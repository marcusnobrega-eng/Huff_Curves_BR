#!/usr/bin/env python3
"""Build compact static assets for the Huff curve web viewer."""

import argparse
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


BASE_COLUMNS = [
    "station_id",
    "lat",
    "lon",
    "area_km2",
    "status",
    "status_reason",
    "n_events",
    "dt_min",
    "n_observations",
    "missing_fraction",
    "years_span",
    "first_timestamp",
    "last_timestamp",
    "has_full_zero_year",
    "max_daily_mm",
    "dominant_quartile",
    "kge_mean",
    "mae_mean",
    "d_max_mean",
]

GEOGRAPHY_COLUMNS = [
    "municipality_code",
    "municipality_name",
    "state_code",
    "state_abbrev",
    "state_name",
    "region_code",
    "region_abbrev",
    "region_name",
    "biome_name",
]

EVENT_SUMMARY_COLUMNS = [
    "event_volume_median_mm",
    "event_volume_p90_mm",
    "event_duration_median_h",
    "event_duration_p90_h",
    "event_peak_intensity_p95_mm_h",
]


def station_id_series(series):
    return series.astype(str).str.replace(r"\.0$", "", regex=True)


def finite_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def clean_scalar(value, digits=6):
    if value is None:
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return round(value, digits)
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if pd.isna(value):
        return None
    return value


def clean_array(values, digits=5):
    cleaned = []
    for value in values:
        number = finite_number(value)
        cleaned.append(round(number, digits) if number is not None else None)
    return cleaned


def read_station_table(outputs_dir):
    station_path = outputs_dir / "station_huff_coefficients.csv"
    if not station_path.exists():
        raise FileNotFoundError("Missing {}".format(station_path))

    stations = pd.read_csv(station_path, dtype={"station_id": str})
    stations["station_id"] = station_id_series(stations["station_id"])

    geo_path = outputs_dir / "diagnostics" / "regional" / "station_results_with_geography.csv"
    if geo_path.exists():
        geo_usecols = ["station_id"] + GEOGRAPHY_COLUMNS
        geo = pd.read_csv(geo_path, dtype={"station_id": str}, usecols=lambda c: c in geo_usecols)
        geo["station_id"] = station_id_series(geo["station_id"])
        geo = geo.drop_duplicates(subset=["station_id"])
        keep_geo_cols = [c for c in geo.columns if c != "station_id"]
        stations = stations.drop(columns=[c for c in keep_geo_cols if c in stations.columns], errors="ignore")
        stations = stations.merge(geo, on="station_id", how="left")

    events_path = outputs_dir / "rainfall_events.csv"
    if events_path.exists():
        usecols = [
            "station_id",
            "duration_h",
            "volume_mm",
            "maximum_intensity_mm_h",
        ]
        events = pd.read_csv(events_path, dtype={"station_id": str}, usecols=usecols)
        events["station_id"] = station_id_series(events["station_id"])
        summary = (
            events.groupby("station_id")
            .agg(
                event_volume_median_mm=("volume_mm", "median"),
                event_volume_p90_mm=("volume_mm", lambda x: x.quantile(0.9)),
                event_duration_median_h=("duration_h", "median"),
                event_duration_p90_h=("duration_h", lambda x: x.quantile(0.9)),
                event_peak_intensity_p95_mm_h=("maximum_intensity_mm_h", lambda x: x.quantile(0.95)),
            )
            .reset_index()
        )
        stations = stations.merge(summary, on="station_id", how="left")

    return stations


def curve_payload(group):
    payload = {"station_id": str(group["station_id"].iloc[0]), "quartiles": {}}
    for quartile, qgroup in group.groupby("quartile"):
        qgroup = qgroup.sort_values("tau")
        qkey = str(int(quartile))
        payload["quartiles"][qkey] = {
            "tau": clean_array(qgroup["tau"].tolist(), digits=4),
            "median": clean_array(qgroup["median"].tolist(), digits=5),
            "p10": clean_array(qgroup["p10"].tolist(), digits=5) if "p10" in qgroup else [],
            "p50": clean_array(qgroup["p50"].tolist(), digits=5) if "p50" in qgroup else [],
            "p90": clean_array(qgroup["p90"].tolist(), digits=5) if "p90" in qgroup else [],
        }
    return payload


def write_curves(outputs_dir, data_dir):
    curves_path = outputs_dir / "huff_curves_long.csv"
    curves_dir = data_dir / "curves"
    if curves_dir.exists():
        shutil.rmtree(str(curves_dir))
    curves_dir.mkdir(parents=True, exist_ok=True)

    if not curves_path.exists():
        return set()

    usecols = ["station_id", "quartile", "tau", "median", "p10", "p50", "p90"]
    curves = pd.read_csv(curves_path, dtype={"station_id": str}, usecols=lambda c: c in usecols)
    curves["station_id"] = station_id_series(curves["station_id"])
    curves["quartile"] = pd.to_numeric(curves["quartile"], errors="coerce")
    curves = curves.dropna(subset=["station_id", "quartile"])

    written = set()
    for station_id, group in curves.groupby("station_id", sort=False):
        payload = curve_payload(group)
        path = curves_dir / "{}.json".format(station_id)
        path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        written.add(str(station_id))
    return written


def quartile_record(row, quartile):
    prefix = "q{}".format(quartile)
    coeffs = []
    for idx in range(1, 9):
        coeffs.append(clean_scalar(row.get("{}_coef_{}".format(prefix, idx)), digits=8))
    return {
        "n_events": clean_scalar(row.get("{}_n_events".format(prefix)), digits=3),
        "percent_events": clean_scalar(row.get("{}_percent_events".format(prefix)), digits=3),
        "avg_volume_mm": clean_scalar(row.get("{}_avg_volume_mm".format(prefix)), digits=3),
        "std_volume_mm": clean_scalar(row.get("{}_std_volume_mm".format(prefix)), digits=3),
        "avg_duration_h": clean_scalar(row.get("{}_avg_duration_h".format(prefix)), digits=3),
        "std_duration_h": clean_scalar(row.get("{}_std_duration_h".format(prefix)), digits=3),
        "max_intensity_mm_h": clean_scalar(row.get("{}_max_intensity_mm_h".format(prefix)), digits=3),
        "kge": clean_scalar(row.get("{}_kge".format(prefix)), digits=4),
        "r2": clean_scalar(row.get("{}_r2".format(prefix)), digits=4),
        "rmse": clean_scalar(row.get("{}_rmse".format(prefix)), digits=4),
        "mae": clean_scalar(row.get("{}_mae".format(prefix)), digits=4),
        "coefficients": coeffs,
    }


def station_record(row, curve_station_ids):
    station_id = str(row["station_id"])
    record = {}
    for col in BASE_COLUMNS + GEOGRAPHY_COLUMNS + EVENT_SUMMARY_COLUMNS:
        if col in row.index:
            record[col] = clean_scalar(row.get(col), digits=6)

    dominant = finite_number(row.get("dominant_quartile"))
    record["dominant_quartile"] = int(dominant) if dominant is not None else None
    record["station_id"] = station_id
    record["curve_path"] = "data/curves/{}.json".format(station_id) if station_id in curve_station_ids else None
    record["quartiles"] = {}
    for quartile in range(1, 5):
        record["quartiles"][str(quartile)] = quartile_record(row, quartile)
    return record


def histogram(values, bins):
    numeric = pd.to_numeric(values, errors="coerce").dropna().to_numpy(dtype=float)
    if numeric.size == 0:
        counts = [0] * (len(bins) - 1)
    else:
        counts = np.histogram(numeric, bins=bins)[0].astype(int).tolist()
    labels = []
    for left, right in zip(bins[:-1], bins[1:]):
        if right == bins[-1]:
            labels.append("{}+".format(int(left)))
        else:
            labels.append("{}-{}".format(int(left), int(right)))
    return {"labels": labels, "counts": counts}


def summarize_group(df, group_col, label_col=None, limit=None):
    if group_col not in df.columns:
        return []
    ok = df[df["status"].eq("ok")].copy()
    ok = ok.dropna(subset=[group_col])
    rows = []
    for key, group in ok.groupby(group_col, dropna=False):
        if label_col and label_col in group.columns:
            label = group[label_col].dropna().astype(str).iloc[0] if not group[label_col].dropna().empty else str(key)
        else:
            label = str(key)
        q_counts = {}
        for q in range(1, 5):
            q_counts[str(q)] = int(pd.to_numeric(group.get("q{}_n_events".format(q), 0), errors="coerce").fillna(0).sum())
        dominant = max(q_counts, key=q_counts.get) if sum(q_counts.values()) else None
        rows.append(
            {
                "id": clean_scalar(key),
                "name": label,
                "n_stations": int(group["station_id"].nunique()),
                "n_events": int(pd.to_numeric(group["n_events"], errors="coerce").fillna(0).sum()),
                "median_years_span": clean_scalar(pd.to_numeric(group["years_span"], errors="coerce").median(), digits=2),
                "median_kge_mean": clean_scalar(pd.to_numeric(group["kge_mean"], errors="coerce").median(), digits=3),
                "median_mae_mean": clean_scalar(pd.to_numeric(group.get("mae_mean", pd.Series(dtype=float)), errors="coerce").median(), digits=4),
                "dominant_quartile": int(dominant) if dominant is not None else None,
            }
        )
    rows = sorted(rows, key=lambda item: item["n_events"], reverse=True)
    return rows[:limit] if limit else rows


def build_analytics(stations):
    ok = stations[stations["status"].eq("ok")].copy()
    status_counts = stations["status"].fillna("unknown").value_counts().to_dict()
    quartile_counts = ok["dominant_quartile"].dropna().astype(int).value_counts().sort_index().to_dict()
    event_total = int(pd.to_numeric(ok["n_events"], errors="coerce").fillna(0).sum())
    total_q_events = {}
    for q in range(1, 5):
        total_q_events[str(q)] = int(pd.to_numeric(ok.get("q{}_n_events".format(q), 0), errors="coerce").fillna(0).sum())

    return {
        "generated_at": utc_stamp(),
        "totals": {
            "stations": int(len(stations)),
            "ok_stations": int(len(ok)),
            "events": event_total,
            "median_years_span": clean_scalar(pd.to_numeric(ok["years_span"], errors="coerce").median(), digits=2),
            "median_kge_mean": clean_scalar(pd.to_numeric(ok["kge_mean"], errors="coerce").median(), digits=3),
            "median_mae_mean": clean_scalar(pd.to_numeric(ok.get("mae_mean", pd.Series(dtype=float)), errors="coerce").median(), digits=4),
            "median_missing_fraction": clean_scalar(pd.to_numeric(ok["missing_fraction"], errors="coerce").median(), digits=4),
        },
        "status_counts": {str(k): int(v) for k, v in status_counts.items()},
        "dominant_quartile_counts": {str(k): int(v) for k, v in quartile_counts.items()},
        "event_quartile_counts": total_q_events,
        "years_histogram": histogram(ok["years_span"], [0, 1, 2, 4, 6, 8, 10, 12, 14, 16, 20]),
        "event_histogram": histogram(ok["n_events"], [0, 10, 50, 100, 250, 500, 750, 1000, 1500, 2000, 2500]),
        "kge_histogram": histogram(ok["kge_mean"], [0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.01]),
        "mae_histogram": histogram(ok.get("mae_mean", pd.Series(dtype=float)), [0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.15]),
        "by_state": summarize_group(stations, "state_abbrev", "state_name"),
        "by_biome": summarize_group(stations, "biome_name", "biome_name"),
        "by_municipality": summarize_group(stations, "municipality_code", "municipality_name", limit=40),
    }


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def write_bootstrap(path, manifest, analytics, stations, curves_dir, curve_station_ids):
    curves = {}
    for station_id in sorted(curve_station_ids):
        curve_path = curves_dir / "{}.json".format(station_id)
        if curve_path.exists():
            curves[str(station_id)] = json.loads(curve_path.read_text(encoding="utf-8"))

    payload = {
        "manifest": manifest,
        "analytics": analytics,
        "stations": stations,
        "curves": curves,
    }
    text = "window.HUFF_BOOTSTRAP="
    text += json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    text += ";\n"
    path.write_text(text, encoding="utf-8")


def utc_stamp():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_assets(outputs_dir, web_dir):
    data_dir = web_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    stations = read_station_table(outputs_dir)
    curve_station_ids = write_curves(outputs_dir, data_dir)
    station_payload = [station_record(row, curve_station_ids) for _, row in stations.iterrows()]
    analytics = build_analytics(stations)
    manifest = {
        "generated_at": utc_stamp(),
        "station_count": len(station_payload),
        "curve_station_count": len(curve_station_ids),
        "source_outputs_dir": str(outputs_dir),
    }

    write_json(data_dir / "stations.json", station_payload)
    write_json(data_dir / "analytics.json", analytics)
    write_json(data_dir / "manifest.json", manifest)
    write_bootstrap(data_dir / "bootstrap.js", manifest, analytics, station_payload, data_dir / "curves", curve_station_ids)
    return manifest


def build_parser():
    parser = argparse.ArgumentParser(description="Create compact web assets from Huff pipeline outputs.")
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"), help="Pipeline output directory.")
    parser.add_argument("--web-dir", type=Path, default=Path("web") / "huff_viewer", help="Web viewer directory.")
    return parser


def main():
    args = build_parser().parse_args()
    manifest = build_assets(args.outputs_dir, args.web_dir)
    print("Wrote web assets for {station_count} stations and {curve_station_count} curve sets.".format(**manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
