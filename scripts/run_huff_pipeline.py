#!/usr/bin/env python3
"""Run the ANA download, rainfall-event, and empirical Huff curve pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from huff_curves_br.ana import AnaDownloadConfig
from huff_curves_br.constants import (
    ANA_ENDPOINT,
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
from huff_curves_br.maps import plot_station_maps
from huff_curves_br.pipeline import PipelineConfig, run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download ANA sub-daily rainfall data and compute empirical Huff curves."
    )
    parser.add_argument("--stations", type=Path, default=ROOT / "Stations_Info.csv", help="Station catalog CSV.")
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "raw", help="Raw ANA cache directory.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs", help="Output directory.")
    parser.add_argument("--start-date", default=DEFAULT_START_DATE, help="Inclusive ANA start date, YYYY-MM-DD.")
    parser.add_argument("--end-date", default=DEFAULT_END_DATE, help="Inclusive ANA end date, YYYY-MM-DD.")
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N stations.")
    parser.add_argument("--no-download", action="store_true", help="Use cached ANA CSV files only.")
    parser.add_argument("--refresh-cache", action="store_true", help="Force new ANA downloads even when cache exists.")
    parser.add_argument("--endpoint", default=ANA_ENDPOINT, help="ANA DadosHidrometeorologicos endpoint.")
    parser.add_argument("--chunk-days", type=int, default=90, help="Days per ANA request chunk.")
    parser.add_argument("--timeout-seconds", type=int, default=60, help="ANA request timeout.")
    parser.add_argument("--retries", type=int, default=3, help="ANA request retries per chunk.")
    parser.add_argument(
        "--retry-sleep-seconds",
        type=float,
        default=3.0,
        help="Base sleep between ANA retries; 429 responses use quadratic backoff from this value.",
    )
    parser.add_argument("--min-years", type=float, default=DEFAULT_MIN_YEARS, help="Minimum station record span.")
    parser.add_argument(
        "--max-missing-fraction",
        type=float,
        default=DEFAULT_MAX_MISSING_FRACTION,
        help="Maximum allowed missing fraction after regularization.",
    )
    parser.add_argument(
        "--max-intensity-mm-h",
        type=float,
        default=DEFAULT_MAX_INTENSITY_MM_H,
        help="QC threshold for derived interval intensity.",
    )
    parser.add_argument("--ietd-hours", type=float, default=DEFAULT_IETD_HOURS, help="Dry gap separating events.")
    parser.add_argument(
        "--min-event-depth-mm",
        type=float,
        default=DEFAULT_MIN_EVENT_DEPTH_MM,
        help="Minimum rainfall volume per event.",
    )
    parser.add_argument(
        "--min-event-records",
        type=int,
        default=DEFAULT_MIN_EVENT_RECORDS,
        help="Minimum number of records per event.",
    )
    parser.add_argument(
        "--max-event-duration-hours",
        type=float,
        default=DEFAULT_MAX_EVENT_DURATION_HOURS,
        help="Maximum event duration kept for Huff analysis.",
    )
    parser.add_argument("--workers", type=int, default=1, help="Parallel station workers for ANA/cache processing.")
    parser.add_argument("--make-maps", action="store_true", help="Generate standard station maps after CSV outputs.")
    parser.add_argument("--brazil-boundary", type=Path, default=None, help="Optional Brazil boundary layer.")
    parser.add_argument("--biomes", type=Path, default=None, help="Optional Brazil biomes layer.")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    pipeline_config = PipelineConfig(
        station_catalog_path=args.stations,
        raw_dir=args.raw_dir,
        output_dir=args.output_dir,
        start_date=args.start_date,
        end_date=args.end_date,
        limit=args.limit,
        refresh_cache=args.refresh_cache,
        allow_download=not args.no_download,
        min_years=args.min_years,
        max_missing_fraction=args.max_missing_fraction,
        max_intensity_mm_h=args.max_intensity_mm_h,
        ietd_hours=args.ietd_hours,
        min_event_depth_mm=args.min_event_depth_mm,
        min_event_records=args.min_event_records,
        max_event_duration_hours=args.max_event_duration_hours,
        workers=args.workers,
    )
    ana_config = AnaDownloadConfig(
        endpoint=args.endpoint,
        timeout_seconds=args.timeout_seconds,
        chunk_days=args.chunk_days,
        retries=args.retries,
        retry_sleep_seconds=args.retry_sleep_seconds,
    )

    outputs = run_pipeline(pipeline_config, ana_config=ana_config, progress=lambda msg: print(msg, flush=True))
    print(f"Wrote station coefficients: {outputs.station_results_path}", flush=True)
    print(f"Wrote rainfall events: {outputs.event_table_path}", flush=True)
    print(f"Wrote long-form Huff curves: {outputs.curve_table_path}", flush=True)

    if args.make_maps:
        map_paths = plot_station_maps(
            outputs.station_results,
            args.output_dir / "maps",
            boundary_path=args.brazil_boundary,
            biomes_path=args.biomes,
        )
        for name, path in map_paths.items():
            print(f"Wrote {name} map: {path}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
