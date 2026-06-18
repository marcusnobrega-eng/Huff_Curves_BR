# F4 — Limitations (draft for Discussion section)
Generated 2026-06-02.

---

## Suggested draft text

The following limitations should be acknowledged in the Discussion. These are ordered from most to least consequential.

---

### 1. Spatial coverage gaps

The ANA telemetric network is unevenly distributed across Brazil. Station density is highest in the Southeast and South (Mata Atlântica, Pampa) and lowest in the Amazon interior (western Pará, Amazonas, Roraima, Acre) and the semi-arid Caatinga (central and northern Piauí, Maranhão, Ceará). Of the 3,164 stations in the catalogue, only 1,045 (33.0%) passed quality control, primarily because 65.9% of stations had >20% missing observations. The resulting spatial bias means that:
- The Amazônia biome is represented by 132 stations concentrated on the southern and eastern periphery (arc of deforestation), not the deep interior.
- The Caatinga is represented by only 49 stations — the sparsest coverage relative to biome area.
- Biome-level curves for Pantanal (n=5) should be treated as indicative only.

**Suggested text:**
> "The spatial distribution of accepted stations reflects the uneven density of the ANA telemetric network, with sparser coverage in the Amazon interior and semi-arid northeast. Results for the Pantanal biome (n = 5 stations) and several individual states should be interpreted cautiously."

---

### 2. Mixed temporal resolution

Of the 1,045 accepted stations, 51.8% operate at 60-minute resolution, while only 35.5% operate at the target 15-minute resolution. This is a consequence of the ANA telemetric network's operational history: 60-minute stations are more numerous, older, and have longer complete records. While the dominant quartile classification is robust across timestep classes (Q1: 97.8% at 15 min, 92.8% at 60 min), the 60-minute stations cannot resolve rainfall patterns shorter than one hour. Events shorter than four records (4 hours at 60 min) are excluded by the minimum record filter, which may under-represent the most intense short-duration convective events that are especially relevant to Q1 classification.

**Suggested text:**
> "More than half of accepted stations (51.8%) record at 60-minute intervals rather than the target 15-minute resolution. At this timestep, events shorter than four hours are excluded. The dominant Q1 classification is consistent across all resolution classes, but quantile curves at 60-minute stations represent somewhat longer events on average."

---

### 3. Single data source

All data derive from the ANA Hidroweb telemetric network (DadosHidrometeorologicos endpoint). No cross-validation against INMET automatic weather stations, CEMADEN sub-hourly gauges, or radar-derived estimates was performed. Different gauge networks may yield different missing-data patterns, temporal resolution distributions, and spatial coverage — all of which could affect the subset of stations passing quality control and the resulting curve shapes.

**Suggested text:**
> "Huff curves were derived exclusively from ANA telemetric gauges. Cross-validation against the INMET or CEMADEN networks, or against radar precipitation estimates, was beyond the scope of this study but is recommended to assess sensitivity to gauge network choice."

---

### 4. Stationary record (no trend analysis)

Records span 2010–2025. No attempt was made to assess temporal non-stationarity in storm temporal patterns — i.e., whether the dominant quartile or curve shape has changed over time due to climate variability or long-term change. Given evidence for intensification of extreme rainfall events in southeastern Brazil (e.g., Marengo et al., 2021), this is a relevant limitation for long-term design applications.

**Suggested text:**
> "The derived curves represent the 2010–2025 climatological period. Temporal trends in storm temporal structure were not examined; users applying these curves to design horizons beyond this period should consider potential non-stationarity."

---

### 5. Fixed IETD applied uniformly

A single IETD = 6 h was applied to all stations regardless of biome or climate regime. There is evidence that the optimal IETD varies by climate (Restrepo-Posada & Eagleson, 1982; Dunkerley, 2008). In the semi-arid Caatinga, longer inter-event times are common; in the wetter Amazon, shorter dry spells may separate distinct convective cells. The sensitivity analysis (Section X) shows that the main finding (Q1 dominance) is robust to IETD choice, but absolute event counts and minor quartile fractions do vary.

**Suggested text:**
> "A uniform IETD of 6 h was applied nationally. The IETD sensitivity analysis (Supplementary Figure S1) confirms that the Q1 classification is robust (84.7% of stations stable across all tested values), but the optimal IETD may vary by climate region. Future work should explore region-specific IETD calibration."

---

### 6. Municipality-level curves: mostly unreliable

Of 694 municipalities with at least one accepted station, only 19 (2.7%) have ≥5 stations — the minimum recommended for a reliable regional curve. Municipality-level polynomial coefficients are provided as supplementary data but should be used only for the 19 reliable municipalities and with caution for the others.

**Suggested text:**
> "Municipality-level polynomial coefficients are provided in Supplementary Table SX. However, 97.3% of municipalities are represented by fewer than 5 stations (the recommended minimum for stable percentile estimation); these curves carry substantial uncertainty and are intended only as preliminary estimates for engineering planning purposes, not as calibrated design values."
