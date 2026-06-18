# Event Statistics — E2 & E3
Generated 2026-06-02 from `outputs/rainfall_events.csv` (290,164 events, 1,045 stations, 2010–2025).

---

## E2 — Event characteristics by quartile

|  | Q1 | Q2 | Q3 | Q4 | ALL |
|---|---|---|---|---|---|
| N events | 126,565 | 70,396 | 55,132 | 38,071 | 290,164 |
| % of events | 43.6 | 24.3 | 19.0 | 13.1 | 100.0 |

### Volume (mm)
| Statistic | Q1 | Q2 | Q3 | Q4 | ALL |
|---|---|---|---|---|---|
| Mean | 38.9 | 46.7 | 46.9 | 72.6 | 46.7 |
| Median | 26.0 | 27.6 | 27.8 | 27.0 | 26.8 |
| Std | 70.1 | 114.3 | 127.7 | 213.6 | 120.5 |
| P25 | 18.0 | 18.8 | 18.8 | 18.0 | 18.2 |
| P75 | 40.8 | 44.0 | 45.0 | 49.6 | 43.2 |

### Duration (h)
| Statistic | Q1 | Q2 | Q3 | Q4 | ALL |
|---|---|---|---|---|---|
| Mean | 12.49 | 14.26 | 15.63 | 16.96 | 14.10 |
| Median | 9.00 | 10.50 | 12.00 | 13.00 | 10.00 |
| Std | 11.35 | 13.03 | 12.96 | 13.24 | 12.45 |
| P25 | 5.50 | 5.75 | 7.25 | 8.00 | 6.00 |
| P75 | 15.00 | 18.00 | 19.00 | 22.00 | 17.25 |

### Average intensity (mm/h)
| Statistic | Q1 | Q2 | Q3 | Q4 | ALL |
|---|---|---|---|---|---|
| Mean | 4.46 | 4.88 | 3.97 | 4.65 | 4.50 |
| Median | 3.06 | 2.94 | 2.53 | 2.39 | 2.82 |
| P25 | 1.82 | 1.67 | 1.54 | 1.45 | 1.66 |
| P75 | 5.29 | 5.36 | 4.26 | 4.32 | 5.00 |

### Maximum intensity (mm/h)
| Statistic | Q1 | Q2 | Q3 | Q4 | ALL |
|---|---|---|---|---|---|
| Mean | 28.3 | 23.7 | 22.1 | 23.9 | 25.4 |
| Median | 20.4 | 16.0 | 15.0 | 16.0 | 17.6 |
| P25 | 11.4 | 9.0 | 8.5 | 8.8 | 9.8 |
| P75 | 36.8 | 30.4 | 28.0 | 30.4 | 32.8 |
| P95 | (see code) | | | | |

---

## E3 — Seasonal breakdown

### Event counts by season
| Season | Q1 | Q2 | Q3 | Q4 | Total |
|---|---|---|---|---|---|
| DJF (summer) | 51,179 | 26,072 | 20,697 | 14,852 | 112,800 |
| MAM (autumn) | 31,524 | 17,362 | 13,116 | 9,511 | 71,513 |
| JJA (winter) | 10,568 | 8,755 | 7,223 | 4,934 | 31,480 |
| SON (spring) | 33,294 | 18,207 | 14,096 | 8,774 | 74,371 |

### Quartile fraction (%) within each season
| Season | Q1 % | Q2 % | Q3 % | Q4 % |
|---|---|---|---|---|
| DJF | 45.4 | 23.1 | 18.3 | 13.2 |
| MAM | 44.1 | 24.3 | 18.3 | 13.3 |
| JJA | **33.6** | 27.8 | 22.9 | 15.7 |
| SON | 44.8 | 24.5 | 19.0 | 11.8 |

### Monthly breakdown (event totals and quartile %)
| Month | N events | Q1 % | Q2 % | Q3 % | Q4 % |
|---|---|---|---|---|---|
| Jan | 38,279 | 45.3 | 22.8 | 18.5 | 13.3 |
| Feb | 34,495 | 45.5 | 23.2 | 18.1 | 13.2 |
| Mar | 33,222 | 46.6 | 23.0 | 17.3 | 13.1 |
| Apr | 22,092 | 44.3 | 24.3 | 18.2 | 13.2 |
| May | 16,199 | 38.6 | 27.0 | 20.6 | 13.8 |
| Jun | 12,478 | 33.9 | 26.6 | 23.5 | 15.9 |
| Jul | 8,382 | 34.1 | 28.0 | 22.7 | 15.3 |
| Aug | 10,620 | 32.7 | 29.1 | 22.4 | 15.7 |
| Sep | 13,559 | 40.4 | 25.3 | 21.5 | 12.9 |
| Oct | 27,282 | 45.8 | 24.9 | 18.2 | 11.1 |
| Nov | 33,530 | 45.7 | 23.8 | 18.6 | 11.9 |
| Dec | 40,026 | 45.3 | 23.3 | 18.4 | 13.0 |

---

## Key interpretive notes

### E2 findings
- **Q1 is shortest and most intense:** median duration 9 h vs 13 h for Q4; median peak intensity 20.4 mm/h vs 15–16 mm/h for Q2–Q4. Consistent with rapid convective cells that release most rainfall early.
- **Q4 has the highest mean volume (72.6 mm) but similar median (27 mm):** extreme right skew driven by a small number of very large events (frontal or orographic systems). The high std (213.6 mm) flags this.
- **Median volumes are similar across quartiles (~26–28 mm):** quartile assignment captures timing, not primarily depth.
- **Q1 average intensity is highest (mean 4.46 mm/h):** short duration + concentrated early rainfall → higher intensity.

### E3 findings
- **DJF dominates event occurrence (38.9% of all events):** austral summer convective activity drives event frequency nationally.
- **JJA has the lowest Q1 fraction (33.6% vs ~44–46% in other seasons):** in austral winter, fewer front-loaded events and relatively more Q2–Q4 patterns — consistent with frontal/stratiform rainfall in southern Brazil.
- **Q1 fraction is lowest in Jun–Aug (32–34%):** months with maximum frontal activity in the subtropics.
- **Mar has the highest Q1 fraction (46.6%):** late-summer convective peak, particularly in Cerrado and Mata Atlântica.
- **This seasonal signal should be explored biome by biome** — the Amazon wet season peaks differently from the SACZ-dominated southeast.

---

## Diurnal cycle of event initiation (added — supports Q1 mechanism)
Source: `scripts/analyse_diurnal_cycle.py` → `outputs/diagnostics/diurnal_cycle.csv`.
Hour = `start` timestamp hour, ANA recording-time convention (absolute
clock uncertain; relative ordering across quartiles is timezone-invariant).

| Group | Modal start hour | Afternoon 12–18h | Morning 06–12h |
|---|---|---|---|
| All (290,164) | 15h | 35.3% | 18.6% |
| Q1 | **16h** | 36.5% | **14.1%** |
| Q2 | 15h | 34.4% | 20.5% |
| Q3 | 14h | 34.3% | 22.5% |
| Q4 | **13h** | 34.0% | **24.3%** |

**Robust (timezone-independent) result:** modal start hour and morning-share
both vary monotonically Q1→Q4. Q1 storms peak latest (16h) and are least
likely to start in the morning (14.1%); Q4 peak earliest (13h), most morning
starts (24.3%). This is internal evidence that front-loaded storms are the
most direct expression of afternoon convective forcing.
