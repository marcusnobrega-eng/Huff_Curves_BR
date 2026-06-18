# Design-hydrograph impact analysis (SCS-CN) — added

Quantifies the engineering impact of replacing original Huff (1967) Q1
with the locally derived biome Q1 curve, via a controlled experiment:
only the temporal pattern changes; catchment/CN/Tc/depth/duration fixed.

## Pipeline (`scripts/run_hydro_impact.py`)
- Catchments: HydroBASINS L12 → eligible filter (area 5–250 km²;
  biomes Cerrado/Caatinga/Mata Atlântica/Pampa; Amazônia+Pantanal
  excluded — saturation-excess/wetland, SCS invalid). 30,866 eligible;
  sample 150/biome = 600; 579 valid after data screening.
- Soil/CN: SoilGrids 250 m clay/sand → HSG → CN(biome×HSG), NRCS AMC II.
- Terrain/Tc: Copernicus GLO-90 DEM (windowed) → relief; L=Hack(area);
  S=relief/L; Tc=Kirpich, clipped [0.1,24] h.
- Rainfall: Xavier Sherman IDF i=K·T^a/(t+b)^c, T=25 yr, t=Tc.
- Engine (`src/huff_curves_br/hydrology.py`): SCS-CN losses (Ia=0.2S),
  SCS dimensionless UH (peak factor 484), convolution → outlet Q(t).
- Compare original Huff Q1 vs biome Q1 → ΔQp (%), Δtp (h).

## Result (`outputs/hydro_impact/catchment_impact.csv`, n=579)
National median **ΔQp = +7.7%** (IQR 6.2–9.5); updated > original at
EVERY catchment (Illinois reference under-predicts peak).

| Biome | median ΔQp | median Δtp |
|---|---|---|
| Cerrado | +11.2% | −0.58 h (earlier) |
| Caatinga | +9.3% | −0.56 h |
| Mata Atlântica | +6.7% | ~0 |
| Pampa | +5.1% | +0.38 h (later) |

Gradient mirrors convective→frontal and the MAE-vs-Huff gradient:
largest underestimation where climate departs most from Illinois.
Tight within-biome spread (despite real CN/Tc/depth variation) ⇒
result governed by curve shape.

## Manuscript
- Methods §3.8 "Design-hydrograph sensitivity experiment"
- Results §4.6 "Impact on design peak discharge"
- Figure 9 (`hydro_impact`): map of ΔQp + boxplots ΔQp, Δtp by biome
- Discussion (Practical implications), Limitations (SCS scope),
  Abstract, Conclusions, Highlights, Data availability all updated
- 7 new refs: Lehner2013, Poggio2021, CopernicusDEM, Xavier2016,
  Kirpich1940, NRCS2004, TR55_1986

## Caveats (stated in paper)
- Screening study, NOT calibrated flood model. Relative comparison;
  absolute peaks not validated. Not national (excludes Amazon/Pantanal).
- Xavier2016 IDF citation needs verification before submission.
