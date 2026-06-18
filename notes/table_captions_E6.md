# E6 — Table Captions (draft)
Generated 2026-06-02.

---

## Table 1 — Pipeline processing summary (E1)

**Caption:**
Summary of the ANA telemetric station processing pipeline. The catalogue comprised 3,164 stations; 3,131 had locally cached data. Quality filters require: (i) ≥4 years of record span, (ii) ≤20% missing observations after regularisation to the native timestep, and (iii) absence of a near-complete calendar year with exactly zero valid rainfall. The dominant quality-control failure was high missing fraction (>20%), affecting 93.1% of rejected stations. Of the 1,045 accepted stations, 371 (35.5%) operated at 15-min resolution, 133 (12.7%) at 30 min, and 541 (51.8%) at 60 min.

| Outcome | N | % | Description |
|---|---|---|---|
| OK — curves fitted | 1,045 | 33.0 | Passed all QC; empirical Huff curves and polynomial coefficients derived |
| Skipped — quality | 2,086 | 65.9 | Failed ≥1 quality filter (93.1% too many missing; 1.9% full-zero year; 1.5% insufficient years) |
| Skipped — no data | 33 | 1.0 | No cached ANA data available |
| **Total** | **3,164** | **100.0** | |

---

## Table 2 — Event characteristics by dominant quartile

**Caption:**
Summary statistics of the 290,164 qualifying rainfall events by dominant quartile assignment. A minimum storm total of 12.7 mm (0.5 in) and a 6-hour inter-event time definition (IETD) were applied, following Huff (1967). Statistics shown: number of events, percentage of total, and median (with interquartile range in parentheses) of storm volume, duration, average intensity, and maximum intensity. P25 and P75 refer to the 25th and 75th percentiles across events.

| | Q1 | Q2 | Q3 | Q4 | All |
|---|---|---|---|---|---|
| N events | 126,565 | 70,396 | 55,132 | 38,071 | 290,164 |
| % of events | 43.6 | 24.3 | 19.0 | 13.1 | 100.0 |
| Volume (mm) — median (IQR) | 26.0 (18.0–40.8) | 27.6 (18.8–44.0) | 27.8 (18.8–45.0) | 27.0 (18.0–49.6) | 26.8 (18.2–43.2) |
| Duration (h) — median (IQR) | 9.0 (5.5–15.0) | 10.5 (5.8–18.0) | 12.0 (7.3–19.0) | 13.0 (8.0–22.0) | 10.0 (6.0–17.3) |
| Avg intensity (mm/h) — median | 3.06 | 2.94 | 2.53 | 2.39 | 2.82 |
| Max intensity (mm/h) — median | 20.4 | 16.0 | 15.0 | 16.0 | 17.6 |

---

## Table 3 — Station-level Huff curve metrics by biome

**Caption:**
Summary of empirical Huff curve characteristics for the 1,045 accepted stations, aggregated by IBGE biome. MAE = mean absolute error of the biome median Q1 curve relative to the Huff (1967) Q1 reference; D_max = maximum absolute deviation (Kolmogorov–Smirnov statistic). Dominant quartile (Q1 for all biomes) is confirmed by the percentage of biome stations classified as Q1-dominant. Bootstrap 95% confidence intervals on the biome MAE are given in parentheses (B = 2,000 resamples over stations).

| Biome | n stations | n events | Median record (yr) | Q1 % | Q1 MAE (95% CI) | Q1 D_max |
|---|---|---|---|---|---|---|
| Amazônia | 132 | 50,299 | — | 99.2 | 0.063 | 0.121 |
| Caatinga | 49 | 6,491 | — | 98.0 | 0.059 | 0.112 |
| Cerrado | 348 | 85,521 | — | 99.7 | 0.060 | 0.114 |
| Mata Atlântica | 488 | 141,356 | — | 88.7 | 0.028 | 0.042 |
| Pampa | 23 | 4,913 | — | 95.7 | 0.019 | 0.062 |
| Pantanal | 5 | 1,584 | — | 100.0 | 0.058ᵃ | 0.115ᵃ |
| **National** | **1,045** | **290,164** | **10.6** | **94.4** | **0.045** | **0.097** |

ᵃ Pantanal result based on n = 5 stations; interpret with caution.

*Note: Fill in median record length from station_results_with_geography.csv by biome before submission.*

---

## Table 4 — IETD sensitivity summary

**Caption:**
Sensitivity of key results to the inter-event time definition (IETD). The baseline (IETD = 6 h) is shown in bold. 'Q1 station %' is the fraction of the 1,045 baseline-OK stations classified as Q1-dominant. 'Agreement' is the percentage of stations retaining the same dominant quartile as the baseline. MAE is computed for the national Q1 median empirical curve relative to the Huff (1967) reference. All runs used minimum storm total 12.7 mm.

| IETD (h) | Events | Med. duration (h) | Q1 station % | Agreement with 6 h | Q1 MAE |
|---|---|---|---|---|---|
| 2 | 269,768 | 6.5 | 84.8 | 88.1% | 0.032 |
| 4 | 285,737 | 8.3 | 92.4 | 96.3% | 0.040 |
| **6** | **290,164** | **10.0** | **94.4** | **—** | **0.045** |
| 8 | 289,615 | 12.3 | 96.5 | 97.1% | 0.050 |
| 12 | 279,484 | 18.0 | 98.5 | 95.7% | 0.057 |

---

## Table S1 (Supplementary) — Polynomial coefficients by biome (Q1)

**Caption:**
7th-degree polynomial coefficients for the Q1 median Huff curve at national and biome level, fitted to the biome median empirical curve (see Methods). Coefficients are ordered for `numpy.polyval` (highest degree first). Bootstrap 95% confidence intervals (B = 2,000) on each coefficient are provided in Supplementary Table S2.

*[Table content: extract directly from biome_huff_coefficients.csv, columns q1_coef_1 through q1_coef_8.]*

---

## Table S2 (Supplementary) — State-level Q1 characteristics

**Caption:**
Q1 Huff curve characteristics for all 27 Brazilian states with at least one accepted station. Columns as in Table 3.

*[Table content: extract from state_huff_coefficients.csv.]*
