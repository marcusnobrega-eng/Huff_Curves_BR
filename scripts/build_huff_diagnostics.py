#!/usr/bin/env python3
"""Build diagnostic maps and regional Huff coefficient GIS products."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import geopandas as gpd

from huff_curves_br.geodata import download_ibge_reference_layers, ibge_reference_paths
from huff_curves_br.maps import plot_region_choropleth, plot_station_diagnostic_panel, plot_station_maps
from huff_curves_br.regional import build_regional_products


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create Huff diagnostics, regional coefficients, and GIS outputs.")
    parser.add_argument(
        "--station-results",
        type=Path,
        default=ROOT / "outputs" / "station_huff_coefficients.csv",
        help="Station-level Huff coefficient CSV.",
    )
    parser.add_argument(
        "--curves",
        type=Path,
        default=ROOT / "outputs" / "huff_curves_long.csv",
        help="Long-form station Huff curve CSV.",
    )
    parser.add_argument(
        "--reference-dir",
        type=Path,
        default=ROOT / "data" / "reference" / "ibge",
        help="IBGE reference-layer cache directory.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "diagnostics",
        help="Diagnostics and regional output directory.",
    )
    parser.add_argument("--overwrite-reference", action="store_true", help="Redownload and rebuild IBGE layers.")
    parser.add_argument(
        "--quality",
        default="intermediaria",
        choices=["minima", "intermediaria", "maxima"],
        help="IBGE malhas simplification quality.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    paths = ibge_reference_paths(args.reference_dir)
    if args.overwrite_reference or not all(path.exists() for path in paths.values()):
        paths = download_ibge_reference_layers(args.reference_dir, quality=args.quality, overwrite=args.overwrite_reference)

    map_dir = args.output_dir / "figures"
    map_dir.mkdir(parents=True, exist_ok=True)
    station_maps = plot_station_maps(
        args.station_results,
        map_dir,
        boundary_path=paths["brazil"],
        biomes_path=paths["biomes"],
    )
    panel = plot_station_diagnostic_panel(
        args.station_results,
        map_dir / "station_diagnostic_panel.png",
        boundary_path=paths["brazil"],
        biomes_path=paths["biomes"],
    )
    print(f"Wrote diagnostic panel: {panel}")
    for name, path in station_maps.items():
        print(f"Wrote station map {name}: {path}")

    regional_dir = args.output_dir / "regional"
    regional_outputs = build_regional_products(
        args.station_results,
        args.curves,
        reference_dir=args.reference_dir,
        output_dir=regional_dir,
    )
    for name, path in regional_outputs.items():
        print(f"Wrote {name}: {path}")

    for scope in ["state", "municipality", "biome"]:
        gpkg = regional_outputs.get(f"{scope}_gpkg")
        if gpkg is None:
            continue
        gdf = gpd.read_file(gpkg)
        plot_region_choropleth(
            gdf,
            "dominant_quartile",
            map_dir / f"{scope}_dominant_quartile.png",
            title=f"{scope.title()} Dominant Quartile",
            categorical=True,
        )
        plot_region_choropleth(
            gdf,
            "median_kge_mean",
            map_dir / f"{scope}_median_kge.png",
            title=f"{scope.title()} Median Station KGE",
            cmap="magma",
        )
        plot_region_choropleth(
            gdf,
            "n_events",
            map_dir / f"{scope}_event_count.png",
            title=f"{scope.title()} Events Used",
            cmap="cividis",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
