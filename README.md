# Huff Curves BR

Python workflow to download ANA sub-daily rainfall data, extract rainfall events, compute empirical Huff curves, compare them with the original Huff curves, and export station-level coefficient tables and maps.

## Current Scope

The repository now keeps only the pieces needed for:

1. Downloading/caching ANA telemetric rainfall data.
2. Cleaning and regularizing sub-daily rainfall series.
3. Extracting rainfall events with an inter-event dry period.
4. Computing empirical Huff curves and quartile-specific polynomial coefficients.
5. Comparing empirical curves with original Huff curves using KGE and other metrics.
6. Exporting CSV tables, diagnostic figures, maps, and regional GIS products.

All old MATLAB disaggregation-coefficient scripts, generated rasters, parity tables, and unrelated outputs were removed.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

For shapefile/biome map overlays and regional GIS exports:

```bash
pip install -e ".[dev,geo]"
```

On HPC systems that only provide Python 3.6, use the legacy setuptools path and keep pip/setuptools on Python-3.6-compatible releases:

```bash
python3.6 -m pip install "pip<22" "setuptools<60" wheel
python3.6 -m pip install -e .

# Include this extra when you need IBGE joins, shapefiles, GeoPackages, and maps:
python3.6 -m pip install -e ".[geo]"
```

## Run

Process all stations in `Stations_Info.csv` and download ANA data:

```bash
python scripts/run_huff_pipeline.py --make-maps
```

Quick test on the first station:

```bash
python scripts/run_huff_pipeline.py --limit 1 --make-maps
```

Full-catalog integration test for a bounded one-year period:

```bash
python scripts/run_huff_pipeline.py \
  --start-date 2020-01-01 \
  --end-date 2020-12-31 \
  --min-years 0 \
  --max-missing-fraction 1 \
  --workers 4 \
  --retries 5 \
  --retry-sleep-seconds 10 \
  --make-maps
```

Process cached ANA files only:

```bash
python scripts/run_huff_pipeline.py --no-download
```

Relax quality filters while exploring:

```bash
python scripts/run_huff_pipeline.py --limit 5 --min-years 0 --max-missing-fraction 1
```

## Outputs

The main pipeline writes:

- `outputs/station_huff_coefficients.csv`: one row per station with status, diagnostics, dominant quartile, KGE, and quartile coefficients.
- `outputs/rainfall_events.csv`: one row per extracted event with volume, duration, intensity, and event quartile.
- `outputs/huff_curves_long.csv`: long-form empirical percentile curves by station, quartile, and normalized time.
- `outputs/maps/map_dominant_quartile.png`: dominant quartile map.
- `outputs/maps/map_kge_mean.png`: mean KGE map.
- `outputs/maps/map_event_count.png`: rainfall event count map.

## Diagnostics And Regional Products

Download and normalize official IBGE layers:

```bash
python scripts/prepare_ibge_reference_layers.py
```

Build diagnostic maps and state, municipality, and biome median-Huff products from existing station outputs:

```bash
python scripts/build_huff_diagnostics.py
```

The diagnostics script uses the station-level median Huff curves (`median`, equivalent to `p50`) to create representative regional curves and polynomial coefficients. It writes:

- `outputs/diagnostics/figures/station_diagnostic_panel.png`: dominant quartile, intensity, event count, years, KGE, and missingness panel.
- `outputs/diagnostics/regional/station_results_with_geography.csv`: station results joined to municipality, state, region, and biome.
- `outputs/diagnostics/regional/state_huff_coefficients.csv`
- `outputs/diagnostics/regional/municipality_huff_coefficients.csv`
- `outputs/diagnostics/regional/biome_huff_coefficients.csv`
- Matching `.gpkg` files with full field names for QGIS.
- Matching shapefile folders for compatibility with older GIS workflows.
- Long-form regional median curves: `state_huff_curves_long.csv`, `municipality_huff_curves_long.csv`, and `biome_huff_curves_long.csv`.

## Important Data Convention

ANA `Chuva` is treated as interval rainfall depth in millimeters (`rainfall_mm`). Event intensity fields are derived from that depth and the inferred timestep:

```text
intensity_mm_h = rainfall_mm * 60 / timestep_minutes
```

This matters for event volumes and Huff cumulative rainfall fractions.

## Optional Custom Reference Layers

Maps work without shapefiles, and `build_huff_diagnostics.py` downloads official IBGE layers automatically. To use custom layers instead, download them into `data/reference` and pass them to the map step:

```bash
python scripts/download_reference_layers.py \
  --url "https://example.org/current_layer.zip" \
  --output data/reference/current_layer.zip \
  --extract-to data/reference/current_layer

python scripts/run_huff_pipeline.py \
  --make-maps \
  --brazil-boundary data/reference/brazil_boundary/layer.shp \
  --biomes data/reference/biomes/layer.shp
```

Use the same map script to regenerate maps from an existing CSV:

```bash
python scripts/plot_huff_maps.py \
  --results outputs/station_huff_coefficients.csv \
  --brazil-boundary data/reference/brazil_boundary/layer.shp \
  --biomes data/reference/biomes/layer.shp
```

## Tests

```bash
pytest
```

## Package Layout

- `src/huff_curves_br/ana.py`: ANA downloader and cache helpers.
- `src/huff_curves_br/series.py`: rainfall cleaning, timestep inference, diagnostics.
- `src/huff_curves_br/events.py`: rainfall event extraction.
- `src/huff_curves_br/huff.py`: empirical Huff curves, coefficients, and metrics.
- `src/huff_curves_br/pipeline.py`: end-to-end station workflow and CSV exports.
- `src/huff_curves_br/geodata.py`: official IBGE reference layers and station spatial joins.
- `src/huff_curves_br/regional.py`: state, municipality, and biome median-Huff aggregation and GIS exports.
- `src/huff_curves_br/maps.py`: optional map outputs.
- `src/huff_curves_br/reference.py`: generic reference-layer downloader.
