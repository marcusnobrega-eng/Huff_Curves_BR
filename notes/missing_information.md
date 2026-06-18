# Missing Information — Decisions, Action Items, and Unresolved Questions

Updated 2026-06-02 based on author responses. Items marked ✅ are decided. Items marked 🔲 still require action (computation, literature search, or drafting). Items marked ⚠️ require author confirmation before proceeding.

---

## A. General / Pre-draft

| # | Item | Status | Decision / Action |
|---|---|---|---|
| A1 | Author and affiliation | ✅ | Marcus Nobrega Gomes Junior, Stanford University — Department of Earth System Science. |
| A2 | Target journal | ✅ | Journal of Hydrology. |
| A3 | Data archiving | ✅ | Zenodo (post-submission). |
| A4 | Code archiving | ✅ | GitHub release (post-submission). |
| A5 | Conflict of interest | ✅ | None. |
| A6 | LaTeX template | ✅ | Elsevier LaTeX template. |

---

## B. Introduction

| # | Item | Status | Decision / Action |
|---|---|---|---|
| B1 | Research gap | ✅ | Brazil needs Huff curves derived from local sub-daily data rather than the 1967 Illinois curves, which were calibrated on a handful of Midwestern U.S. catchments and may not reflect tropical/subtropical rainfall timing. |
| B2 | Novelty claims | ✅ | All three claims are valid: (1) first national-scale empirical derivation using ANA telemetric data; (2) first quantitative comparison with original Huff (1967) curves; (3) first biome-, state-, and municipality-level polynomial coefficient tables for Brazil. |
| B3 | Citation for Huff (1967) | 🔲 | Retrieve the original paper from the web. Confirm exact title, journal (likely *Water Resources Research*, 1967), volume, pages, DOI. Confirm whether `HUFF_REFERENCE_COEFFICIENTS` in `constants.py` were taken directly from the paper tables or re-fitted by the author from digitized tabular data. |
| B4 | Citations for goodness-of-fit metrics | ✅ | MAE = Wasserstein-1 (Villani, 2003); D_max = Kolmogorov-Smirnov (Massey, 1951); KGE = Gupta et al. (2009). See `notes/methods_justifications.md`. |

---

## C. Study Area and Data

| # | Item | Status | Decision / Action |
|---|---|---|---|
| C1 | Brazil climate/rainfall description | 🔲 | Write a focused study-area section covering: geographic extents, major climate regimes (equatorial Amazon, semi-arid Caatinga, tropical savannah Cerrado, subtropical south), and the six IBGE biomes with their distinct rainfall seasonality patterns. |
| C2 | Timestep choice | ✅ | 15-minute resolution was chosen because: (a) sub-10-minute stations are too sparse to provide national coverage; (b) 60-minute data are too coarse for high-resolution rainfall disaggregation purposes. |
| C3 | Data availability figures | 🔲 | Generate figure(s) showing spatial and temporal availability: map of stations by years of record; histogram of record lengths; possibly a timeline of active stations by year. Source: `station_huff_coefficients.csv` columns `first_timestamp`, `last_timestamp`, `years_span`, `lat`, `lon`. |
| C4 | QC threshold justification | ✅ | ≥4 yr: Bonta & Rao (1988); ≤20% missing: WMO-No.100 (2018) + Marra et al. (2025) BR-SDR. See `notes/methods_justifications.md`. |

---

## D. Methods

| # | Item | Status | Decision / Action |
|---|---|---|---|
| D1 | IETD = 6 h justification | ✅ | Three lines: (1) Restrepo-Posada & Eagleson (1982), Bonta & Rao (1988), Dunkerley (2008), Huff (1967) all use 6h; (2) event count peaks at 6h; (3) MAE vs Huff ref increases monotonically beyond 6h. See `notes/methods_justifications.md`. |
| D2 | Minimum event depth | ✅ | Changed to **12.7 mm (0.5 inches)** — replicates Huff (1967) storm-selection criterion exactly. `DEFAULT_MIN_EVENT_DEPTH_MM` updated in `constants.py`. All results must be recomputed (see H5). |
| D3 | Quartile assignment method citation | ✅ | Cite Huff (1967) for the quartile-of-peak-depth assignment method. |
| D4 | 7th-degree polynomial justification | ✅ | Same degree as Huff (1967); R² > 0.99 at all scales confirms fit quality. Note that reference coefficients are author-fitted to digitised Huff curves (not from the 1967 paper directly). See `notes/methods_justifications.md`. |
| D5 | Variable timestep handling | ✅ | The paper will state that 15-minute resolution was the target; stations at other resolutions (1, 5, 10, 16, 30, 60 min) are processed with their native timestep but the analysis is designed around the 15-minute standard for the reasons in C2. |
| D6 | Low-event-count flagging | ✅ | Regional curves with fewer than a defined minimum number of contributing stations (TBD — suggest ≥5 or ≥10) will be flagged as unreliable in both tables and figures. The specific threshold must be chosen and documented. |
| D7 | IETD sensitivity analysis | ✅ | Complete. Five IETD values (2, 4, 6, 8, 12 h) tested across all 4 metrics. 84.7% station stability; 96–97% agreement with ±2 h bracket. MAE minimised at short IETD. Results in `outputs/sensitivity/` and `notes/ietd_sensitivity.md`. Sensitivity figure still needed (G3). |

---

## E. Results

| # | Item | Status | Decision / Action |
|---|---|---|---|
| E1 | Pipeline processing summary table | ✅ | ok=1,045 (33.0%), skipped_quality=2,086 (65.9%, of which 93.1% failed missing-data filter), skipped=33 (1.0%). Timestep mix: 15 min=35.5%, 30 min=12.7%, 60 min=51.8%. See `notes/table_captions_E6.md` Table 1. |
| E2 | Event characteristic statistics | ✅ | Complete. Full breakdown by quartile: volume, duration, avg/max intensity. Results in `notes/event_statistics.md`. |
| E3 | Seasonal breakdown | ✅ | Complete. Monthly and seasonal (DJF/MAM/JJA/SON) breakdown by quartile. Key finding: JJA Q1 fraction drops to 33.6% vs ~45% in other seasons. Results in `notes/event_statistics.md`. |
| E4 | Publication-quality figures | ✅ | Six figures generated as PDF + SVG + PNG in `outputs/figures/` via `scripts/plot_huff_curves_paper.py` and `scripts/plot_maps_paper.py`. See figure inventory below. |
| E5 | Figure captions | ✅ | Drafted for Figures 1–5 (main) + S1–S2 (supplementary). See `notes/figure_captions_E5.md`. |
| E6 | Table captions | ✅ | Drafted for Tables 1–4 (main) + S1–S2 (supplementary). See `notes/table_captions_E6.md`. |
| E7 | Coefficient uncertainty / confidence intervals | ✅ | Bootstrap A (over stations, B=2000): national Q1 95% CI mean width = 0.006 (very tight). Bootstrap B (over events, analytical SE of median): station-level CI width at τ=0.50 median=0.065. Updated figures include bootstrap CI band. CSVs in `outputs/bootstrap/`. Scripts: `scripts/bootstrap_uncertainty.py`. |

---

## F. Discussion

| # | Item | Status | Decision / Action |
|---|---|---|---|
| F1 | Prior Brazilian Huff studies | ✅ | Complete. Full lit-review in `notes/literature_review_F1.md`. Gap confirmed: no national-scale peer-reviewed study. Key prior work: Florianópolis 2021 (3,212 events, Q1=37.6%), SC Mountain Region 2021 (1,697 events, Q1=46.7%), BR-SDR dataset (2025). ⚠️ Florianópolis full citation still unconfirmed. |
| F2 | Q1 dominance hypothesis | ✅ | Mechanism established: thermally-driven deep convection → afternoon peak → rapid instability release → front-loaded mass curve. JJA dip to 33.6% explained by frontal/stratiform winter rainfall. Biome breakdown explained. Key refs: Zipser et al. (2006); Marengo et al. (2012); Diurnal cycle Brazil (2024). Timestep robustness confirmed (Q1: 97.8% at 15 min, 92.8% at 60 min). See `notes/q1_dominance_mechanism_F2.md`. |
| F3 | Goodness-of-fit metric choice | ✅ | **MAE** (mean absolute CDF deviation = Wasserstein-1 distance; units: rainfall fraction) and **D_max** (maximum absolute CDF deviation = KS statistic; units: rainfall fraction) are the primary metrics. KGE retained in output for reference but not reported as a primary result. Both metrics implemented in `metrics.py` and exported at station and regional level. Discuss in paper: what D_max threshold constitutes acceptable agreement? When does the empirical curve fail to track the Huff shape? |
| F4 | Limitations | ✅ | Six limitations drafted: (1) spatial coverage gaps, (2) mixed 60/15 min resolution, (3) single data source, (4) no trend analysis, (5) uniform IETD, (6) municipality curves mostly unreliable. See `notes/limitations_F4.md`. |

---

## G. Supplementary Material

| # | Item | Status | Decision / Action |
|---|---|---|---|
| G1 | Full station-level table | ✅ | Exists as `outputs/station_huff_coefficients.csv` (1,045 OK stations, all coefficients and metrics). Submit as supplementary data file. |
| G2 | Municipality-level table | ✅ | `outputs/diagnostics/regional/municipality_huff_coefficients.csv` updated with `reliable` flag (≥5 stations). Only 19/694 municipalities reliable. Flagged in limitations. |
| G3 | IETD sensitivity figures | ✅ | 2×2 figure: (a) event count+duration, (b) event quartile fraction, (c) station Q1 fraction by biome, (d) MAE+D_max vs Huff reference. Script: `scripts/plot_ietd_sensitivity_paper.py`. Output: `outputs/figures/ietd_sensitivity.pdf/.svg/.png`. |
| G4 | Web viewer | 🔲 | Plan URL for the deployed web viewer (currently local only). If hosted, include as supplementary resource or data-availability link. |

---

## H. Unresolved Technical Questions

| # | Question | Status |
|---|---|---|
| H1 | Are `HUFF_REFERENCE_COEFFICIENTS` from Huff (1967) directly, or re-fitted by the author? | ✅ | Author-fitted 7th-degree polynomial to digitised Huff (1967) median curves. RMSE < 0.025 at all quartiles. Must be stated in Methods. |
| H2 | What is the mechanistic driver of Q1 dominance? | ✅ | Thermally-driven deep convection; frontal/stratiform systems explain JJA dip and Mata Atlântica/Pampa sensitivity. See `notes/q1_dominance_mechanism_F2.md`. |
| H3 | Minimum event depth | ✅ | 12.7 mm (0.5 in). Pipeline rerun complete. |
| H4 | Low-station-count flag for municipality curves | ✅ | ≥5 stations threshold applied; 19/694 municipalities reliable. |
| H5 | IETD sensitivity runs | ✅ | Complete (2, 4, 6, 8, 12 h — all 4 metrics). See `notes/ietd_sensitivity.md`. |

---

## Remaining before manuscript drafting

| Item | Status | Notes |
|---|---|---|
| Publication figures (PDF/SVG) | ✅ | National + biome Huff panels with bootstrap CI generated. IETD sensitivity figure → in progress. Maps → in progress. |
| Bootstrap uncertainty (E7) | ✅ | Station-level CI (approx.) + regional bootstrap (B=2000) done. `outputs/bootstrap/`. |
| E2/E3 event statistics | ✅ | See `notes/event_statistics.md`. |
| D7 IETD sensitivity | ✅ | See `notes/ietd_sensitivity.md`. |
| F1 lit search | ✅ | Brazilian Huff studies found; SC Mountain Region, Florianópolis, São Carlos. |
| F2 Q1 mechanism | ✅ | See `notes/q1_dominance_mechanism_F2.md`. |
| Figure captions | ✅ | See `notes/figure_captions_E5.md`. |
| Table captions | ✅ | See `notes/table_captions_E6.md`. |
| Limitations | ✅ | See `notes/limitations_F4.md`. |
| Methods justifications | ✅ | See `notes/methods_justifications.md`. |
| **C1 Study-area text** | 🔲 | Draft for manuscript — Brazilian rainfall climatology. |
| **IETD figure (G3)** | 🔲 | Data ready; figure script needed. |
| **Remaining maps (PDF/SVG)** | 🔲 | MAE/D_max map, record-length/data-availability map. |
