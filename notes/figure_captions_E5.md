# E5 — Figure Captions (draft)
Generated 2026-06-02. For Elsevier Journal of Hydrology submission.
All figure files are in `outputs/figures/`. Use the `_bootstrap` versions for Figures 1 and 2.

---

## Figure 1 — huff_curves_national_bootstrap.pdf

**Caption:**
National empirical Huff curves for Brazil derived from 1,045 rain gauge stations (290,164 rainfall events, 2010–2025). Each panel shows one quartile (Q1–Q4, labelled a–d). The solid coloured line is the national median empirical curve; the light shaded band is the P10–P90 inter-station range reflecting natural storm-to-storm variability; the darker shaded band is the bootstrap 95% confidence interval on the national median (B = 2,000 resamples over stations). The dashed black line is the original Huff (1967) reference curve for that quartile, derived from 261 storms recorded in Illinois, USA. All curves are normalised: τ is the fraction of total storm time elapsed and F(τ) is the fraction of total storm depth accumulated by time τ. The dotted diagonal represents a uniform temporal distribution (F = τ).

---

## Figure 2 — huff_curves_biome_Q1_bootstrap.pdf

**Caption:**
Q1 (first-quartile dominant) empirical Huff curves by IBGE biome. Layout as in Figure 1: solid line = biome median; light band = P10–P90 inter-station range; dark band = bootstrap 95% CI on the biome median (B = 2,000 resamples). Dashed black line: Huff (1967) Q1 reference. Station count (n) and mean absolute error (MAE) relative to the Huff (1967) reference are annotated in each panel. The Pantanal (f) result is indicative only (n = 5).

---

## Figure 3 — map_dominant_quartile.pdf

**Caption:**
Spatial distribution of the dominant Huff quartile across 1,045 Brazilian rain gauge stations. The dominant quartile is defined as the quartile receiving the greatest cumulative rainfall depth, following Huff (1967). Coloured circles denote the quartile assignment; grey dots (n = 2,119) are stations excluded from the analysis (failed quality control or no qualifying events). Light grey lines indicate IBGE biome boundaries; dark grey lines show state boundaries. Coordinate reference system: EPSG:4326.

---

## Figure 4 — map_mae_dmax.pdf

**Caption:**
Spatial distribution of goodness-of-fit metrics comparing empirical Q1 Huff curves to the Huff (1967) Illinois reference. (a) Mean absolute error (MAE) of the Q1 empirical median curve; (b) mean maximum absolute deviation (D_max, equivalent to the Kolmogorov–Smirnov statistic) averaged across all four quartiles. Lower values (brighter yellow) indicate better agreement with the reference. Median values are annotated in each panel. Stations are coloured from the 2nd to 98th percentile of each metric to suppress outlier influence on the colour scale.

---

## Figure 5 — map_record_length.pdf

**Caption:**
Data availability: record length (years) for all 3,131 stations with cached data in the ANA telemetric network. Stations are shown regardless of quality-control outcome. Colour encodes years of continuous or intermittent record from the first to last available timestamp. Biome and state boundaries are overlaid in grey. Station counts and median record length are annotated.

---

## Figure S1 (Supplementary) — ietd_sensitivity.pdf

**Caption:**
Sensitivity of the results to the choice of inter-event time definition (IETD). (a) Total qualifying event count (solid, left axis) and median event duration (dashed, right axis) as functions of IETD. (b) Event-level quartile fraction (%) for Q1–Q4 as a function of IETD. (c) Fraction of stations with Q1 as the dominant quartile, shown nationally (thick black line) and for each IBGE biome. (d) Curve-fit quality — MAE (solid lines) and D_max (dashed lines) of the empirical Q1–Q4 median curves relative to the Huff (1967) reference, as a function of IETD. In all panels, the vertical dashed grey line marks the baseline IETD = 6 h used in the main analysis. All comparisons restrict the station set to the 1,045 stations used in the baseline run.

---

## Figure S2 (Supplementary) — huff_curves_all_biomes_quartiles.pdf

**Caption:**
Empirical Huff curves for all combinations of IBGE biome (columns: Amazônia, Caatinga, Cerrado, Mata Atlântica, Pampa, Pantanal) and quartile (rows: Q1–Q4). Layout as in Figure 2. Station count (n) and MAE relative to the Huff (1967) reference (dashed) are annotated in each panel. Panels with n < 5 should be interpreted with caution.
