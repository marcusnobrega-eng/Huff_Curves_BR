"""End-to-end processing pipeline for ANA rainfall and empirical Huff curves."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from .ana import AnaDownloadConfig, download_station, load_station_cache, save_station_cache
from .constants import (
    DEFAULT_END_DATE,
    DEFAULT_IETD_HOURS,
    DEFAULT_MAX_EVENT_DURATION_HOURS,
    DEFAULT_MAX_INTENSITY_MM_H,
    DEFAULT_MAX_MISSING_FRACTION,
    DEFAULT_MIN_EVENT_DEPTH_MM,
    DEFAULT_MIN_EVENT_RECORDS,
    DEFAULT_MIN_YEARS,
    DEFAULT_START_DATE,
)
from .events import RainfallEvent, extract_events
from .huff import (
    HuffResult,
    assign_huff_quartile,
    compute_huff_result,
    event_cumulative_curve,
    flatten_huff_result,
)
from .series import SeriesDiagnostics, clean_rainfall_values, diagnostics, infer_timestep_minutes, regularize_series
from .stations import load_station_catalog, station_record

Downloader = Callable[[str, str, str, AnaDownloadConfig | None], pd.DataFrame]
ProgressCallback = Callable[[str], None]


@dataclass(frozen=True)
class PipelineConfig:
    station_catalog_path: Path = Path("Stations_Info.csv")
    raw_dir: Path = Path("data/raw")
    output_dir: Path = Path("outputs")
    start_date: str = DEFAULT_START_DATE
    end_date: str = DEFAULT_END_DATE
    limit: int | None = None
    refresh_cache: bool = False
    allow_download: bool = True
    min_years: float = DEFAULT_MIN_YEARS
    max_missing_fraction: float = DEFAULT_MAX_MISSING_FRACTION
    max_intensity_mm_h: float = DEFAULT_MAX_INTENSITY_MM_H
    ietd_hours: float = DEFAULT_IETD_HOURS
    min_event_depth_mm: float = DEFAULT_MIN_EVENT_DEPTH_MM
    min_event_records: int = DEFAULT_MIN_EVENT_RECORDS
    max_event_duration_hours: float = DEFAULT_MAX_EVENT_DURATION_HOURS
    workers: int = 1


@dataclass(frozen=True)
class StationPipelineResult:
    station_id: str
    status: str
    reason: str
    row: dict[str, object]
    events: list[RainfallEvent]
    huff_result: HuffResult | None


@dataclass(frozen=True)
class PipelineOutputs:
    station_results_path: Path
    event_table_path: Path
    curve_table_path: Path
    station_results: pd.DataFrame
    event_table: pd.DataFrame
    curve_table: pd.DataFrame


def _diagnostics_row(diag: SeriesDiagnostics | None) -> dict[str, object]:
    if diag is None:
        return {
            "dt_min": np.nan,
            "n_observations": 0,
            "missing_fraction": np.nan,
            "years_span": np.nan,
            "first_timestamp": None,
            "last_timestamp": None,
            "has_full_zero_year": False,
            "max_daily_mm": np.nan,
        }

    return {
        "dt_min": diag.timestep_min,
        "n_observations": diag.n_observations,
        "missing_fraction": diag.missing_fraction,
        "years_span": diag.years_span,
        "first_timestamp": diag.first_timestamp,
        "last_timestamp": diag.last_timestamp,
        "has_full_zero_year": diag.has_full_zero_year,
        "max_daily_mm": diag.max_daily_mm,
    }


def _base_station_row(
    station: dict[str, object],
    status: str,
    reason: str,
    diag: SeriesDiagnostics | None,
    n_events: int = 0,
) -> dict[str, object]:
    row: dict[str, object] = {
        "station_id": station["station_id"],
        "lat": station["lat"],
        "lon": station["lon"],
        "area_km2": station.get("area_km2"),
        "status": status,
        "status_reason": reason,
        "n_events": n_events,
    }
    row.update(_diagnostics_row(diag))
    return row


def _quality_reasons(diag: SeriesDiagnostics, config: PipelineConfig) -> list[str]:
    reasons: list[str] = []
    if not np.isfinite(diag.timestep_min) or diag.timestep_min <= 0:
        reasons.append("invalid_timestep")
    if np.isfinite(config.min_years) and diag.years_span < config.min_years:
        reasons.append("insufficient_years")
    if np.isfinite(config.max_missing_fraction) and diag.missing_fraction > config.max_missing_fraction:
        reasons.append("too_many_missing_records")
    if diag.has_full_zero_year:
        reasons.append("full_zero_calendar_year")
    return reasons


def _empty_raw() -> pd.DataFrame:
    return pd.DataFrame(columns=["station_id", "datetime", "rainfall_mm", "stage_m", "flow_m3_s"])


def _load_or_download_station(
    station_id: str,
    config: PipelineConfig,
    ana_config: AnaDownloadConfig | None,
    downloader: Downloader,
) -> pd.DataFrame:
    cached = _empty_raw() if config.refresh_cache else load_station_cache(config.raw_dir, station_id)
    if not cached.empty:
        return cached

    if not config.allow_download:
        return cached

    downloaded = downloader(station_id, config.start_date, config.end_date, ana_config)
    if not downloaded.empty:
        save_station_cache(downloaded, config.raw_dir, station_id)
    return downloaded


def process_station(
    station: dict[str, object] | pd.Series,
    config: PipelineConfig,
    ana_config: AnaDownloadConfig | None = None,
    downloader: Downloader = download_station,
) -> StationPipelineResult:
    """Process one station through download/cache, QC, event extraction, and Huff fitting."""
    if isinstance(station, pd.Series):
        station_dict = station_record(station)
    else:
        station_dict = station
    station_id = str(station_dict["station_id"])

    try:
        raw = _load_or_download_station(station_id, config, ana_config, downloader)
    except Exception as exc:
        reason = f"download_error:{type(exc).__name__}:{str(exc)[:300]}"
        row = _base_station_row(station_dict, "error", reason, None)
        return StationPipelineResult(station_id, "error", reason, row, [], None)
    if raw.empty:
        reason = "no_cached_or_downloaded_data" if not config.allow_download else "no_ana_data"
        row = _base_station_row(station_dict, "skipped", reason, None)
        return StationPipelineResult(station_id, "skipped", reason, row, [], None)

    timestep_min = infer_timestep_minutes(raw["datetime"])
    regular = regularize_series(raw, timestep_min=timestep_min if np.isfinite(timestep_min) else None)
    regular = clean_rainfall_values(regular, max_intensity_mm_h=config.max_intensity_mm_h)
    diag = diagnostics(regular, timestep_min=timestep_min if np.isfinite(timestep_min) else None)

    reasons = _quality_reasons(diag, config)
    if reasons:
        reason = ",".join(reasons)
        row = _base_station_row(station_dict, "skipped_quality", reason, diag)
        return StationPipelineResult(station_id, "skipped_quality", reason, row, [], None)

    events = extract_events(
        regular,
        timestep_min=diag.timestep_min,
        ietd_hours=config.ietd_hours,
        min_event_depth_mm=config.min_event_depth_mm,
        min_records=config.min_event_records,
        max_event_duration_hours=config.max_event_duration_hours,
    )
    if not events:
        reason = "no_valid_rainfall_events"
        row = _base_station_row(station_dict, "no_events", reason, diag)
        return StationPipelineResult(station_id, "no_events", reason, row, [], None)

    huff = compute_huff_result(
        station_id=station_id,
        lat=float(station_dict["lat"]),
        lon=float(station_dict["lon"]),
        timestep_min=diag.timestep_min,
        events=events,
    )
    row = _base_station_row(station_dict, "ok", "", diag, n_events=len(events))
    row.update(flatten_huff_result(huff))
    return StationPipelineResult(station_id, "ok", "", row, events, huff)


def event_rows(station_id: str, events: list[RainfallEvent]) -> list[dict[str, object]]:
    """Convert extracted events into a flat CSV-friendly table."""
    rows: list[dict[str, object]] = []
    for idx, event in enumerate(events, start=1):
        tau, cumulative = event_cumulative_curve(event)
        quartile = assign_huff_quartile(tau, cumulative) if tau.size else None
        rows.append(
            {
                "station_id": station_id,
                "event_id": idx,
                "start": event.start,
                "end": event.end,
                "duration_h": event.duration_hours,
                "volume_mm": event.volume_mm,
                "average_intensity_mm_h": event.average_intensity_mm_h,
                "maximum_intensity_mm_h": event.maximum_intensity_mm_h,
                "dominant_event_quartile": quartile,
                "n_records": int(event.rainfall_mm.size),
            }
        )
    return rows


def curve_rows(result: HuffResult | None) -> list[dict[str, object]]:
    """Convert station Huff curves into long-form CSV rows."""
    if result is None:
        return []

    rows: list[dict[str, object]] = []
    for quartile, q_result in result.quartiles.items():
        for i, tau in enumerate(q_result.tau_grid):
            row: dict[str, object] = {
                "station_id": result.station_id,
                "lat": result.lat,
                "lon": result.lon,
                "quartile": quartile,
                "tau": float(tau),
                "median": float(q_result.median_curve[i]) if np.isfinite(q_result.median_curve[i]) else np.nan,
            }
            for level, curve in q_result.percentile_curves.items():
                value = curve[i]
                row[f"p{level}"] = float(value) if np.isfinite(value) else np.nan
            rows.append(row)
    return rows


def run_pipeline(
    config: PipelineConfig,
    ana_config: AnaDownloadConfig | None = None,
    downloader: Downloader = download_station,
    progress: ProgressCallback | None = None,
) -> PipelineOutputs:
    """Run the full station catalog workflow and write CSV outputs."""
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stations = load_station_catalog(config.station_catalog_path, limit=config.limit)

    station_rows: list[dict[str, object]] = []
    all_event_rows: list[dict[str, object]] = []
    all_curve_rows: list[dict[str, object]] = []
    station_records = [station_record(row) for _, row in stations.iterrows()]

    def collect_result(idx: int, result: StationPipelineResult) -> None:
        station_rows.append(result.row)
        all_event_rows.extend(event_rows(result.station_id, result.events))
        all_curve_rows.extend(curve_rows(result.huff_result))
        if progress is not None:
            suffix = f": {result.reason}" if result.reason else ""
            progress(f"[{idx + 1}/{len(station_records)}] {result.station_id} {result.status}{suffix}")

    workers = max(1, int(config.workers))
    if workers == 1:
        for idx, station in enumerate(station_records):
            if progress is not None:
                progress(f"[{idx + 1}/{len(station_records)}] processing station {station['station_id']}")
            result = process_station(station, config, ana_config=ana_config, downloader=downloader)
            collect_result(idx, result)
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(process_station, station, config, ana_config, downloader): idx
                for idx, station in enumerate(station_records)
            }
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    result = future.result()
                except Exception as exc:
                    station = station_records[idx]
                    station_id = str(station["station_id"])
                    reason = f"pipeline_error:{type(exc).__name__}:{str(exc)[:300]}"
                    row = _base_station_row(station, "error", reason, None)
                    result = StationPipelineResult(station_id, "error", reason, row, [], None)
                collect_result(idx, result)

    station_results = pd.DataFrame(station_rows)
    event_table = pd.DataFrame(all_event_rows)
    curve_table = pd.DataFrame(all_curve_rows)

    station_results_path = output_dir / "station_huff_coefficients.csv"
    event_table_path = output_dir / "rainfall_events.csv"
    curve_table_path = output_dir / "huff_curves_long.csv"

    station_results.to_csv(station_results_path, index=False)
    event_table.to_csv(event_table_path, index=False)
    curve_table.to_csv(curve_table_path, index=False)

    return PipelineOutputs(
        station_results_path=station_results_path,
        event_table_path=event_table_path,
        curve_table_path=curve_table_path,
        station_results=station_results,
        event_table=event_table,
        curve_table=curve_table,
    )
