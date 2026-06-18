# Paper Asset Map

Maps each manuscript section to the project files that support it.
All file paths are relative to the repository root.

---

## Introduction

**Needed:** Background on Huff curves (original 1967 Illinois study), their use in Brazilian hydrology and urban drainage design, and the motivation for a Brazil-wide empirical derivation.

**What exists in the project:**
- `src/huff_curves_br/constants.py` — embeds the 7th-degree polynomial coefficients for the original Huff Q1–Q4 reference curves, sourced from the 1967 Huff publication. These are the baseline against which all empirical curves are compared.
- `README.md` — brief scope statement; confirms the workflow's objective.

**What must be written:**
- Literature review and research gap statement (no draft or notes exist).
- Statement of objectives (not documented beyond the README).

---

## Study Area and Data

### Study area narrative
**What exists:**
- `Stations_Info.csv` — 3,164 stations with latitude, longitude, and drainage area (km²), covering all Brazilian states and biomes.
- `data/reference/ibge/normalized/` — `biomes.gpkg`, `states.gpkg`, `municipalities.gpkg`, `brazil.gpkg` for national coverage description.
- `outputs/diagnostics/regional/station_results_with_geography.csv` — each station linked to state, region, and biome.

**What must be written:**
- Geographic description of Brazil (area, climate zones, rainfall regimes by region).
- Narrative linking the biome/state breakdown to the station network.

### Data source
**What exists:**
- `src/huff_curves_br/ana.py` — documents the ANA telemetric endpoint (`DadosHidrometeorologicos`), 90-day chunked downloads, and retry logic.
- `src/huff_curves_br/constants.py` — default date range: 2014-01-01 to 2024-12-31.
- `web/huff_viewer/data/analytics.json` — reports: 3,164 stations processed, 2,049 passing quality control, median record length 10.84 years.

**Quantitative summary for the paper:**
- Total stations in catalog: 3,164
- Stations with valid outputs ("ok"): 2,049 (64.7%)
- Stations rejected by quality control: 137 (4.3%)
- Stations with no events extracted: 939 (29.7%)
- Stations with no ANA data: 33 (1.0%)
- Stations with download errors: 6 (0.2%)
- Timestep resolutions present: 1, 5, 10, 15, 16, 30, 60 min (15 min dominant)
- Record lengths (ok stations): 4.1–16.0 years; median 10.8 years

### Station map figure
**Available:** `outputs/maps/map_event_count.png` (event count per station — useful to show spatial coverage). `outputs/diagnostics/figures/station_diagnostic_panel.png` (6-panel diagnostic map).

---

## Methods

### Data acquisition and quality control
**What exists:**
- `src/huff_curves_br/ana.py` — download from ANA SOAP endpoint.
- `src/huff_curves_br/series.py` — timestep inference (median of pairwise differences), series regularization (left-join onto regular time grid), intensity cap (default 300 mm/h), negative value removal, full-zero-year detection.
- `src/huff_curves_br/constants.py` — QC thresholds:
  - `DEFAULT_MAX_MISSING_FRACTION = 0.20` (≤20% missing)
  - `DEFAULT_MIN_YEARS = 4.0` (≥4 years of record)
  - `DEFAULT_MAX_INTENSITY_MM_H = 300.0` (QC cap)

### Event extraction
**What exists:**
- `src/huff_curves_br/events.py` — IETD-based dry-gap splitting, with post-split filters:
  - `DEFAULT_IETD_HOURS = 6.0` (inter-event time definition)
  - `DEFAULT_MIN_EVENT_DEPTH_MM = 1.0`
  - `DEFAULT_MIN_EVENT_RECORDS = 4`
  - `DEFAULT_MAX_EVENT_DURATION_HOURS = 96.0`
- ANA `Chuva` field is treated as interval rainfall depth (mm), not intensity. See README data-convention note.

### Huff curve derivation
**What exists:**
- `src/huff_curves_br/huff.py`:
  - `event_cumulative_curve()` — normalizes event timestamps to τ ∈ [0,1] and computes cumulative rainfall fraction F(τ).
  - `assign_huff_quartile()` — assigns each event to Q1–Q4 by the time quartile containing the most rainfall.
  - `_fit_quartile()` — interpolates each event curve onto a τ grid (step 0.02), stacks them, computes percentile envelopes (p10–p90), fits a 7th-degree polynomial to the median curve (p50).
  - `sanitize_cdf()` — clips to [0,1] and enforces monotonicity.
- `src/huff_curves_br/constants.py`:
  - `HUFF_FIT_DEGREE = 7`
  - `HUFF_INTERP_STEP = 0.02`
  - `HUFF_PERCENTILE_LEVELS = (10, 20, ..., 90)`

### Comparison with original Huff curves
**What exists:**
- `src/huff_curves_br/constants.py` — `HUFF_REFERENCE_COEFFICIENTS`: 4×7 array of polynomial coefficients for original Huff Q1–Q4 (evaluated on `HUFF_REFERENCE_TAU = 0.1, 0.2, ..., 1.0`).
- `src/huff_curves_br/metrics.py` — `fitness_metrics()` computes KGE, NSE, IA, PBIAS, RMSE, MAE, R² between empirical fitted curve and original Huff reference curve at τ = 0.1–1.0.

### Regional aggregation
**What exists:**
- `src/huff_curves_br/geodata.py` — spatial join: station point → municipality, state, region, biome using IBGE GeoPackages.
- `src/huff_curves_br/regional.py` — for each geographic unit, takes the median (p50) station-level curves across all "ok" stations, fits a 7th-degree polynomial, computes metrics.

---

## Results

### Station-level results table
**Available:**
- `outputs/station_huff_coefficients.csv` — 3,164 rows; columns include dominant_quartile, n_events, years_span, missing_fraction, kge_mean, and per-quartile coefficients and metrics.

**Key numbers already computed:**
- KGE mean: min 0.210, median 0.914, max 0.976 (ok stations)
- Events per station: 1–2,206; median 551
- Dominant quartile breakdown: Q1 = 1,994 stations (97.3%); Q2 = 9; Q3 = 5; Q4 = 41
- Event quartile breakdown: Q1 = 548,194 (47.0%); Q2 = 233,443 (20.0%); Q3 = 188,701 (16.2%); Q4 = 196,462 (16.8%)

### Dominant quartile map
**Available:** `outputs/maps/map_dominant_quartile.png`, `outputs/diagnostics/figures/map_dominant_quartile.png`

### KGE map
**Available:** `outputs/maps/map_kge_mean.png`, `outputs/diagnostics/figures/map_kge_mean.png`

### Biome-level results
**Available:** `outputs/diagnostics/regional/biome_huff_coefficients.csv`

| Biome | N stations | N events | Dominant Q | Median KGE |
|---|---|---|---|---|
| Amazônia | 280 | 21,689 | Q1 | 0.860 |
| Caatinga | 106 | 5,200 | Q1 | 0.856 |
| Cerrado | 546 | 28,410 | Q1 | 0.876 |
| Mata Atlântica | 903 | 51,037 | Q1 | 0.902 |
| Pampa | 48 | 2,139 | Q1 | 0.904 |
| Pantanal | 12 | 472 | Q1 | 0.865 |

Polynomial coefficients for all biomes and all quartiles are in `biome_huff_coefficients.csv` (ready for table).

**Figures:** `outputs/diagnostics/figures/biome_dominant_quartile.png`, `biome_event_count.png`, `biome_median_kge.png`

### State-level results
**Available:** `outputs/diagnostics/regional/state_huff_coefficients.csv` (27 states), matching shapefile and GeoPackage.

**Figures:** `outputs/diagnostics/figures/state_dominant_quartile.png`, `state_event_count.png`, `state_median_kge.png`

---

## Discussion

**What the data supports (no text exists yet):**
- Near-universal dominance of Q1 in Brazil (early-peaking rainfall events) across all biomes and regions — contrast with the continental United States where Q1–Q4 all appear.
- Biome-level KGE differences (Mata Atlântica/Pampa ≈ 0.90 vs. Amazônia/Caatinga ≈ 0.86) suggesting poorer fit of original Huff curves in equatorial and semi-arid regions.
- Station density and record-length limitations (29.7% of stations produced no events, often in arid northeast or data-sparse regions).
- IETD sensitivity: fixed at 6 h following standard practice — no sensitivity analysis in the current codebase.
- Comparison with any prior Brazilian Huff curve studies: not yet addressed.

---

## Figures Summary

| Figure file | Candidate paper figure |
|---|---|
| `outputs/maps/map_dominant_quartile.png` | Map of dominant quartile — main results figure |
| `outputs/maps/map_kge_mean.png` | Map of KGE — model performance figure |
| `outputs/maps/map_event_count.png` | Map of event count — data coverage figure |
| `outputs/diagnostics/figures/station_diagnostic_panel.png` | 6-panel diagnostic figure (supplementary or methods) |
| `outputs/diagnostics/figures/biome_*` | Biome-level bar charts |
| `outputs/diagnostics/figures/state_*` | State-level bar charts |

All existing figures are PNG. Journal-quality vector figures (PDF/SVG) do not yet exist.

---

## Tables Summary

| Content | Source file |
|---|---|
| Station processing summary (status counts) | `outputs/station_huff_coefficients.csv` — compute from `status` column |
| Biome-level Huff coefficients | `outputs/diagnostics/regional/biome_huff_coefficients.csv` |
| State-level Huff coefficients | `outputs/diagnostics/regional/state_huff_coefficients.csv` |
| Default pipeline parameters | `src/huff_curves_br/constants.py` |
| Original Huff reference coefficients | `src/huff_curves_br/constants.py` → `HUFF_REFERENCE_COEFFICIENTS` |

---

## References

**What is embedded in the code (not yet formatted):**
- Huff (1967) — original Illinois Huff curve publication (implied by `HUFF_REFERENCE_COEFFICIENTS`; exact citation not documented in the repository).
- ANA telemetric service — endpoint in `constants.py`.
- IBGE biomes 2025 shapefile — URL in `constants.py`.
- KGE metric — Gupta et al. (2009); NSE — Nash & Sutcliffe (1970); IA — Willmott (1981) — implied by metric names but not cited in code.

No bibliography file (BibTeX, RIS, etc.) exists in the repository.
