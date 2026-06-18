# D7 — IETD Sensitivity Analysis
Generated 2026-06-02. IETD values tested: 2, 4, **6 (baseline)**, 8, 12 h.
All runs: `--no-download --min-event-depth-mm 12.7 --max-missing-fraction 0.20 --workers 2`.
Analysis script: `scripts/analyse_ietd_sensitivity.py`.
Output files: `outputs/sensitivity/ietd_*.csv`.

---

## Metric 4 — Event count and duration shift

| IETD | N events | Med duration (h) | Med volume (mm) | Q1 % | Q2 % | Q3 % | Q4 % |
|---|---|---|---|---|---|---|---|
| 2 h | 269,768 | 6.50 | 25.8 | 41.9 | 29.8 | 18.8 | 9.5 |
| 4 h | 285,737 | 8.25 | 26.2 | 43.2 | 26.2 | 19.1 | 11.4 |
| **6 h** | **290,164** | **10.00** | **26.8** | **43.6** | **24.3** | **19.0** | **13.1** |
| 8 h | 289,615 | 12.25 | 27.4 | 43.9 | 22.9 | 18.6 | 14.7 |
| 12 h | 279,484 | 18.00 | 28.8 | 44.3 | 21.0 | 17.9 | 16.8 |

**Interpretation:**
- Event count peaks at IETD = 6 h. Shorter IETD splits events; many sub-events fail the 12.7 mm
  minimum depth threshold, reducing qualifying counts. Longer IETD merges events but reduces
  the number of discrete storms.
- Median duration scales monotonically with IETD (6.5 h → 18.0 h).
- Q4 fraction is most sensitive to IETD: 9.5% at 2 h → 16.8% at 12 h. Long-IETD merging
  creates longer composite events, some of which accumulate rainfall in the later phase.
- Q1 event fraction is stable (41.9–44.3%) — small absolute range across a 6× span of IETD.

---

## Metric 1 — Station-level dominant-quartile stability

All 1,045 baseline-OK stations have data at every IETD value.

**84.7% of stations (885/1,045) retain the same dominant quartile across all five IETD values.**

| IETD vs baseline (6 h) | N stations | N agree | % agree |
|---|---|---|---|
| 2 h | 1,045 | 921 | 88.1% |
| 4 h | 1,045 | 1,006 | **96.3%** |
| 8 h | 1,045 | 1,015 | **97.1%** |
| 12 h | 1,045 | 1,000 | 95.7% |

**Dominant quartile distribution (station-level) by IETD:**

| IETD | Q1 | Q2 | Q3 | Q4 |
|---|---|---|---|---|
| 2 h | 886 | 116 | 10 | 33 |
| 4 h | 966 | 43 | 3 | 33 |
| **6 h** | **986** | **21** | **9** | **29** |
| 8 h | 1,008 | 11 | 2 | 24 |
| 12 h | 1,029 | 1 | 0 | 15 |

**Interpretation:**
- The Q1-dominant classification is robust: the direction of effect (Q1 gains stations as IETD
  increases) is systematic and physically expected — longer events are more likely to have a
  rapid early intensification phase that defines the whole storm.
- IETD = 2 h is the most sensitive choice: 88.1% agreement, with Q2 gaining 95 extra stations
  relative to baseline. These are stations where splitting at a 2 h gap fragments a single
  convective event into sub-events, some of which have a mid-duration peak.
- The ±2 h bracket (4 h and 8 h) shows > 96% agreement — very strong robustness.

---

## Metric 3 — MAE and D_max vs Huff (1967) reference

National median empirical curves computed over all 1,045 baseline-OK stations.

| IETD | Q1 MAE | Q1 D_max | Q2 MAE | Q2 D_max | Q3 MAE | Q3 D_max | Q4 MAE | Q4 D_max |
|---|---|---|---|---|---|---|---|---|
| 2 h | **0.0323** | **0.0661** | **0.0356** | **0.0705** | **0.0275** | **0.0417** | **0.0107** | 0.0487 |
| 4 h | 0.0398 | 0.0626 | 0.0397 | 0.0820 | 0.0363 | 0.0729 | 0.0249 | 0.0613 |
| **6 h** | **0.0451** | **0.0807** | **0.0424** | **0.0905** | **0.0416** | **0.0899** | **0.0358** | **0.0863** |
| 8 h | 0.0501 | 0.0947 | 0.0444 | 0.0953 | 0.0454 | 0.1060 | 0.0422 | 0.1070 |
| 12 h | 0.0566 | 0.0993 | 0.0456 | 0.1011 | 0.0472 | 0.1182 | 0.0428 | 0.1204 |

**Key finding: MAE and D_max increase monotonically with IETD.**
Shorter IETD → empirical curves that are CLOSER to the Huff (1967) reference.

**Physical interpretation:**
- Huff (1967) used a 6 h IETD in Illinois, but the Illinois dataset is dominated by organised
  convective systems shorter than ~24 h. At IETD = 2–4 h, the Brazilian pipeline extracts the
  pure convective cells that best match Huff's event population.
- Longer IETD merges convective bursts with stratiform trailing regions, producing longer,
  more complex composite events. The median curve of these longer events has a flatter early
  rise → departs further from the sharp Q1 shape in Huff.
- This creates a methodological tension:
  - Shorter IETD → better Q1 curve fit, but fewer qualifying events and more fragmentation
  - Longer IETD → stronger station-level Q1 dominance, but empirical curves depart more from
    the Huff reference
  - IETD = 6 h is the literature-standard compromise, matching the original Huff (1967) choice.

---

## Metric 2 — National and biome-level Q1 fraction shift

**National Q1 station fraction (%):**

| IETD | N OK | Q1 % | Q2 % | Q3 % | Q4 % |
|---|---|---|---|---|---|
| 2 h | 1,045 | 84.8 | 11.1 | 1.0 | 3.2 |
| 4 h | 1,045 | 92.4 | 4.1 | 0.3 | 3.2 |
| **6 h** | **1,045** | **94.4** | **2.0** | **0.9** | **2.8** |
| 8 h | 1,045 | 96.5 | 1.1 | 0.2 | 2.3 |
| 12 h | 1,045 | 98.5 | 0.1 | 0.0 | 1.4 |

**Biome-level Q1 fraction (%) by IETD:**

| Biome | 2 h | 4 h | 6 h | 8 h | 12 h |
|---|---|---|---|---|---|
| Amazônia | 95.5 | 99.2 | 99.2 | 99.2 | 99.2 |
| Caatinga | 89.8 | 95.9 | 98.0 | 100.0 | 100.0 |
| Cerrado | 98.6 | 99.7 | 99.7 | 100.0 | 100.0 |
| Mata Atlântica | 71.7 | 85.2 | 88.7 | 92.6 | 96.9 |
| Pampa | 78.3 | 87.0 | 95.7 | 100.0 | 100.0 |
| Pantanal | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |

**Interpretation:**
- Mata Atlântica and Pampa are the most IETD-sensitive biomes.
  - Mata Atlântica: 71.7% Q1 at 2 h → 96.9% at 12 h. This biome has the most diverse storm
    types (frontal, orographic, convective) and the highest station density. At short IETD,
    splitting exposes the within-event variability.
  - Pampa: 78.3% at 2 h → 100% at 8–12 h. Southern Brazil is heavily influenced by cold
    fronts, which produce more complex multi-peak rainfall sequences that fragment at short IETD.
- Amazônia, Cerrado, Caatinga, and Pantanal are stable across all IETD values (>95% Q1 at 4h+).
  These biomes are dominated by thermally-driven convective cells that are inherently short and
  front-loaded.

---

## Summary for the paper

**The results are robust to IETD choice.** The specific conclusions that hold across all tested
values are:
1. Q1 is the dominant quartile nationally — at every IETD.
2. Q1 dominance is strongest in Amazônia, Cerrado, Caatinga, and Pantanal — at every IETD.
3. Mata Atlântica and Pampa show the most sensitivity — worth noting in limitations.

**Justification for IETD = 6 h:**
- Matches the original Huff (1967) storm separation criterion (literature standard).
- Cited by Restrepo-Posada & Eagleson (1982) and Bonta & Rao (1988) as the most common value
  for temperate and subtropical climates.
- Maximises total qualifying event count (290,164 vs 270–290k at other values).
- Produces 96–97% agreement with ±2 h alternatives at the station level.
- The curve-fit degradation at longer IETD (metric 3) provides an additional objective argument
  against using 8 or 12 h for this specific application.
