# Overleaf Upload Instructions

## Files to upload

| File | Upload to |
|---|---|
| `main.tex` | root of project |
| `references.bib` | root of project |
| `figures/huff_curves_national_bootstrap.pdf` | `figures/` subfolder |
| `figures/huff_curves_biome_Q1_bootstrap.pdf` | `figures/` subfolder |
| `figures/map_dominant_quartile.pdf` | `figures/` subfolder |
| `figures/map_mae_dmax.pdf` | `figures/` subfolder |
| `figures/map_record_length.pdf` | `figures/` subfolder |
| `figures/ietd_sensitivity.pdf` | `figures/` subfolder |

## Template setup

1. Create a new Overleaf project from the template:
   https://www.overleaf.com/latex/templates/elseviers-cas-latex-single-column-template/rsnbvrmnptyq

2. Delete the default `sample.tex` and upload `main.tex` as the main file.

3. Upload `references.bib` and all PDF figures.

4. The compiler should be set to **pdfLaTeX**.

5. You need the `cas-sc.cls` file — it comes with the template automatically
   when you create from the Overleaf link above.

## Packages required (all standard on Overleaf)

- natbib
- graphicx
- amsmath
- booktabs
- array
- multirow
- siunitx
- hyperref
- xcolor
- lineno
- setspace

## Before submission

- [ ] Replace ORCID placeholder (0000-0000-0000-0000)
- [ ] Replace Zenodo DOI placeholder (XXXXXXX)
- [ ] Replace GitHub URL placeholder (XXXXXXX)
- [ ] Verify Marra et al. (2025) page numbers
- [ ] Remove `\linenumbers` command for final PDF
- [ ] Add Figure S2 (all biomes × all quartiles) if required
- [ ] Fill in any empty supplementary table shells

---

## Supplementary Material (added)

`supplementary.tex` — standalone document compiled separately (shares
`references.bib`). Upload alongside `main.tex`. Compile: pdfLaTeX →
BibTeX → pdfLaTeX × 2. Output: 6 pages.

Contents:
- S1 Purpose/design of the SCS-CN experiment
- S2 Input datasets (Table S1) + Fig S2 (`supp_inputs.pdf`)
- S3 Catchment selection (Tables S2/S3) + Fig S1 (`supp_catchments.pdf`)
- S4 Full mathematical description (Sherman IDF, Hack, Kirpich, SCS-CN,
  SCS unit hydrograph, convolution, ΔQp/Δtp) — Eqs. S1–S9
- S5 Per-catchment results pointer

Additional figures to upload to `figures/`:
- `supp_inputs.pdf`, `supp_catchments.pdf`, `hydro_impact.pdf`,
  `map_quartile_percent.pdf`, `diurnal_cycle.pdf`

Reminder: verify the Xavier (2016) IDF citation — the gridded
Sherman-IDF product may warrant its own reference.
