#!/usr/bin/env python3
"""Generate map outputs from a station_huff_coefficients.csv file."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from huff_curves_br.maps import plot_station_maps


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plot station-level empirical Huff maps.")
    parser.add_argument(
        "--results",
        type=Path,
        default=ROOT / "outputs" / "station_huff_coefficients.csv",
        help="Station results CSV from run_huff_pipeline.py.",
    )
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "maps", help="Map output directory.")
    parser.add_argument("--brazil-boundary", type=Path, default=None, help="Optional Brazil boundary layer.")
    parser.add_argument("--biomes", type=Path, default=None, help="Optional Brazil biomes layer.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    paths = plot_station_maps(args.results, args.output_dir, boundary_path=args.brazil_boundary, biomes_path=args.biomes)
    for name, path in paths.items():
        print(f"Wrote {name} map: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
