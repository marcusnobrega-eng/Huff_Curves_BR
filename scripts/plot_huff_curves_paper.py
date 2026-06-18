"""
Publication-quality Huff curve figures
=======================================
Generates two main figures saved as PDF and SVG:

  Figure 1 (huff_curves_national.pdf/.svg)
    2 × 2 panel grid — Q1, Q2, Q3, Q4 at national scale
    Each panel: empirical median (thick line) + inter-station p10/p90 band
                + Huff (1967) reference (dashed)

  Figure 2 (huff_curves_biome_Q1.pdf/.svg)
    2 × 3 panel grid — all 6 IBGE biomes, Q1 only
    Each panel: empirical median + inter-station band + Huff (1967) reference

Design spec
  Width  : 190 mm (double-column Elsevier)
  Height : auto
  Font   : DejaVu Sans (ships with matplotlib; substitute for Arial in LaTeX)
  Sizes  : 8 pt ticks, 9 pt axis labels, 9 pt panel labels (bold), 8 pt legend
  Colours:
    Q1 → #1f77b4  (blue)
    Q2 → #2ca02c  (green)
    Q3 → #ff7f0e  (orange)
    Q4 → #d62728  (red)
    Huff reference → black, dashed
    Band fill → same hue, alpha 0.15
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

# ── paths ──────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "outputs" / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CURVES_PATH  = ROOT / "outputs" / "huff_curves_long.csv"
GEO_PATH     = ROOT / "outputs" / "diagnostics" / "regional" / "station_results_with_geography.csv"
BIOME_CURVES = ROOT / "outputs" / "diagnostics" / "regional" / "biome_huff_curves_long.csv"

# ── Huff (1967) reference ───────────────────────────────────────────────────
HUFF_COEFFS = np.array([
    [-0.9633,  3.8869,  -7.8950, 10.0890, -8.0108,  3.8936, -0.0032],
    [-39.4360, 125.1800,-146.0400,73.6040,-13.9360,  1.6243, -0.0068],
    [ 46.5420,-131.5500, 132.6300,-57.3150,10.7960, -0.1107,  0.0050],
    [-25.2890,  67.5400, -64.9260,28.0310, -5.2061,  0.8535, -0.0042],
], dtype=float)

TAU_REF = np.linspace(0.0, 1.0, 200)

def huff_ref(q: int) -> np.ndarray:
    """Evaluate and sanitize Huff (1967) reference curve for quartile q (1-based)."""
    raw = np.polyval(HUFF_COEFFS[q - 1], TAU_REF)
    raw = np.clip(raw, 0.0, 1.0)
    raw = np.maximum.accumulate(raw)
    raw[0]  = 0.0
    raw[-1] = 1.0
    return raw

# ── style constants ─────────────────────────────────────────────────────────
MM   = 1 / 25.4          # inches per mm
FW   = 190 * MM          # full Elsevier double-column width
QCOL = {1: "#1f77b4", 2: "#2ca02c", 3: "#ff7f0e", 4: "#d62728"}
QLBL = {1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"}
HUFF_COLOR   = "black"
HUFF_LS      = "--"
HUFF_LW      = 1.0
EMP_LW       = 1.6
BAND_ALPHA   = 0.15
TICK_FS      = 8
LABEL_FS     = 9
PANEL_FS     = 9
LEGEND_FS    = 7.5

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": TICK_FS,
    "axes.labelsize": LABEL_FS,
    "axes.titlesize": PANEL_FS,
    "xtick.labelsize": TICK_FS,
    "ytick.labelsize": TICK_FS,
    "legend.fontsize": LEGEND_FS,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "grid.linewidth": 0.4,
    "grid.color": "#cccccc",
    "figure.dpi": 200,
    "savefig.dpi": 300,
    "pdf.fonttype": 42,      # embeds fonts as TrueType → compatible with Elsevier
    "svg.fonttype": "none",  # keeps text as text in SVG
})

# ── load data ───────────────────────────────────────────────────────────────
print("Loading station curves …")
curves = pd.read_csv(CURVES_PATH)
curves["station_id"] = curves["station_id"].astype(str).str.replace(r"\.0$", "", regex=True)
curves["quartile"]   = pd.to_numeric(curves["quartile"], errors="coerce").astype("Int64")
curves["tau"]        = pd.to_numeric(curves["tau"], errors="coerce")
curves["median"]     = pd.to_numeric(curves["median"], errors="coerce")

print("Loading geography …")
geo = pd.read_csv(GEO_PATH)
geo["station_id"] = geo["station_id"].astype(str).str.replace(r"\.0$", "", regex=True)
biome_map = geo.set_index("station_id")["biome_name"].to_dict()
curves["biome"] = curves["station_id"].map(biome_map)

BIOME_ORDER = [
    "Amazônia", "Caatinga", "Cerrado",
    "Mata Atlântica", "Pampa", "Pantanal",
]
BIOME_LABEL = {
    "Amazônia":      "Amazônia\n(n = {n})",
    "Caatinga":      "Caatinga\n(n = {n})",
    "Cerrado":       "Cerrado\n(n = {n})",
    "Mata Atlântica":"Mata Atlântica\n(n = {n})",
    "Pampa":         "Pampa\n(n = {n})",
    "Pantanal":      "Pantanal\n(n = {n})",
}

# ── helper: national band ───────────────────────────────────────────────────
def national_band(q: int):
    """Return (tau, median, p10, p90) arrays at national level for quartile q."""
    sub = curves[curves["quartile"] == q].copy()
    grp = sub.groupby("tau")["median"]
    tau    = np.array(sorted(grp.groups.keys()), dtype=float)
    median = grp.median().loc[tau].to_numpy()
    p10    = grp.quantile(0.10).loc[tau].to_numpy()
    p90    = grp.quantile(0.90).loc[tau].to_numpy()
    return tau, median, p10, p90

def biome_band(biome: str, q: int):
    """Return (tau, median, p10, p90) for one biome + quartile."""
    sub = curves[(curves["biome"] == biome) & (curves["quartile"] == q)].copy()
    if sub.empty:
        return None, None, None, None
    grp    = sub.groupby("tau")["median"]
    tau    = np.array(sorted(grp.groups.keys()), dtype=float)
    median = grp.median().loc[tau].to_numpy()
    p10    = grp.quantile(0.10).loc[tau].to_numpy()
    p90    = grp.quantile(0.90).loc[tau].to_numpy()
    n_sta  = sub["station_id"].nunique()
    return tau, median, p10, p90, n_sta

# ── helper: draw one panel ──────────────────────────────────────────────────
def draw_panel(ax, tau, median, p10, p90, q, ref_tau=TAU_REF, show_xlabel=True,
               show_ylabel=True, n_sta=None, title=None):
    color = QCOL[q]
    # reference first (behind)
    ax.plot(ref_tau, huff_ref(q), color=HUFF_COLOR, ls=HUFF_LS, lw=HUFF_LW,
            zorder=2, label="Huff (1967)")
    # band
    ax.fill_between(tau, p10, p90, color=color, alpha=BAND_ALPHA, zorder=3)
    # median
    ax.plot(tau, median, color=color, lw=EMP_LW, zorder=4,
            label=f"{QLBL[q]} empirical")
    # 1:1 diagonal (light)
    ax.plot([0, 1], [0, 1], color="#aaaaaa", lw=0.5, ls=":", zorder=1)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.grid(True, zorder=0)
    if show_xlabel:
        ax.set_xlabel("Normalised storm time, τ")
    if show_ylabel:
        ax.set_ylabel("Cumulative rainfall fraction, F(τ)")
    if title:
        ax.set_title(title, fontsize=PANEL_FS, fontweight="bold", pad=3)

    # station count annotation
    if n_sta is not None:
        ax.text(0.04, 0.96, f"n = {n_sta:,}", transform=ax.transAxes,
                ha="left", va="top", fontsize=7, color="#444444")
    return ax

# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 1 — National curves, all four quartiles (2 × 2 grid)
# ══════════════════════════════════════════════════════════════════════════════
print("Building Figure 1 — national Huff curves …")

fig1, axes1 = plt.subplots(
    2, 2,
    figsize=(FW, FW * 0.9),
    sharex=True, sharey=True,
    constrained_layout=True,
)
panel_labels = ["(a)", "(b)", "(c)", "(d)"]
positions    = [(0,0),(0,1),(1,0),(1,1)]

n_national = curves["station_id"].nunique()

for idx, q in enumerate([1, 2, 3, 4]):
    r, c = positions[idx]
    ax   = axes1[r][c]
    tau, med, p10, p90 = national_band(q)
    draw_panel(
        ax, tau, med, p10, p90, q,
        show_xlabel=(r == 1),
        show_ylabel=(c == 0),
        title=f"{panel_labels[idx]}  {QLBL[q]}",
    )
    ax.text(0.04, 0.96, f"n = {n_national:,}", transform=ax.transAxes,
            ha="left", va="top", fontsize=7, color="#444444")

# shared legend — placed in panel (a) Q1, colours match that panel
legend_elements = [
    Line2D([0], [0], color="#555555",   lw=EMP_LW, label="Empirical median"),
    mpatches.Patch(color="#555555",     alpha=BAND_ALPHA+0.15, label="P10–P90 inter-station range"),
    Line2D([0], [0], color=HUFF_COLOR,  lw=HUFF_LW, ls=HUFF_LS, label="Huff (1967) reference"),
]
axes1[0][0].legend(handles=legend_elements, loc="lower right", framealpha=0.92,
                   edgecolor="#aaaaaa")

for ax in axes1.flat:
    ax.set_xticklabels([f"{v:.2f}".rstrip("0").rstrip(".") if v not in (0,1) else str(int(v))
                        for v in [0, 0.25, 0.5, 0.75, 1.0]])

stem1 = OUT_DIR / "huff_curves_national"
fig1.savefig(str(stem1) + ".pdf", format="pdf", bbox_inches="tight")
fig1.savefig(str(stem1) + ".svg", format="svg", bbox_inches="tight")
fig1.savefig(str(stem1) + ".png", format="png", dpi=150, bbox_inches="tight")
plt.close(fig1)
print(f"  → {stem1}.pdf / .svg")

# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 2 — Biome Q1 curves (2 × 3 grid)
# ══════════════════════════════════════════════════════════════════════════════
print("Building Figure 2 — biome Q1 curves …")

fig2, axes2 = plt.subplots(
    2, 3,
    figsize=(FW, FW * 0.72),
    sharex=True, sharey=True,
    constrained_layout=True,
)
biome_panel_labels = ["(a)", "(b)", "(c)", "(d)", "(e)", "(f)"]
biome_positions    = [(0,0),(0,1),(0,2),(1,0),(1,1),(1,2)]
q1_color = QCOL[1]

for idx, biome in enumerate(BIOME_ORDER):
    r, c   = biome_positions[idx]
    ax     = axes2[r][c]
    result = biome_band(biome, 1)
    tau, med, p10, p90, n_sta = result if len(result) == 5 else (*result, None)

    if tau is None:
        ax.text(0.5, 0.5, "No data", ha="center", va="center",
                transform=ax.transAxes, fontsize=8, color="grey")
        ax.set_title(f"{biome_panel_labels[idx]}  {biome}", fontsize=PANEL_FS,
                     fontweight="bold", pad=3)
        continue

    # reference
    ax.plot(TAU_REF, huff_ref(1), color=HUFF_COLOR, ls=HUFF_LS, lw=HUFF_LW, zorder=2)
    # band
    ax.fill_between(tau, p10, p90, color=q1_color, alpha=BAND_ALPHA, zorder=3)
    # median
    ax.plot(tau, med, color=q1_color, lw=EMP_LW, zorder=4)
    # 1:1 diagonal
    ax.plot([0, 1], [0, 1], color="#aaaaaa", lw=0.5, ls=":", zorder=1)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.grid(True, zorder=0)

    # MAE annotation
    ref_at_tau = np.interp(tau, TAU_REF, huff_ref(1))
    finite = np.isfinite(med) & np.isfinite(ref_at_tau)
    mae = np.mean(np.abs(med[finite] - ref_at_tau[finite])) if finite.sum() > 1 else np.nan
    ann = f"n = {n_sta:,}\nMAE = {mae:.3f}"
    ax.text(0.04, 0.96, ann, transform=ax.transAxes,
            ha="left", va="top", fontsize=6.5, color="#444444",
            linespacing=1.4)

    if r == 1:
        ax.set_xlabel("Normalised storm time, τ")
    if c == 0:
        ax.set_ylabel("Cumulative rainfall fraction, F(τ)")

    ax.set_title(f"{biome_panel_labels[idx]}  {biome}", fontsize=PANEL_FS,
                 fontweight="bold", pad=3)

# shared legend on top-right panel
legend_elements2 = [
    Line2D([0], [0], color=q1_color,    lw=EMP_LW, label="Q1 empirical median"),
    mpatches.Patch(color=q1_color,      alpha=BAND_ALPHA+0.1, label="P10–P90 inter-station range"),
    Line2D([0], [0], color=HUFF_COLOR,  lw=HUFF_LW, ls=HUFF_LS, label="Huff (1967) Q1 reference"),
]
axes2[0][2].legend(handles=legend_elements2, loc="lower right", framealpha=0.9,
                   edgecolor="#aaaaaa")

stem2 = OUT_DIR / "huff_curves_biome_Q1"
fig2.savefig(str(stem2) + ".pdf", format="pdf", bbox_inches="tight")
fig2.savefig(str(stem2) + ".svg", format="svg", bbox_inches="tight")
fig2.savefig(str(stem2) + ".png", format="png", dpi=150, bbox_inches="tight")
plt.close(fig2)
print(f"  → {stem2}.pdf / .svg")

# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 3 — All biomes × all quartiles (4 × 6 supplementary grid)
# ══════════════════════════════════════════════════════════════════════════════
print("Building Figure 3 — all biomes × all quartiles (supplementary) …")

fig3, axes3 = plt.subplots(
    4, 6,
    figsize=(FW * 1.4, FW * 1.0),   # wider for supplementary — can be A4 width
    sharex=True, sharey=True,
    constrained_layout=True,
)

row_labels = {1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"}
alpha_idx  = "abcdefghijklmnopqrstuvwx"

for qi, q in enumerate([1, 2, 3, 4]):
    for bi, biome in enumerate(BIOME_ORDER):
        ax     = axes3[qi][bi]
        result = biome_band(biome, q)
        tau, med, p10, p90, n_sta = result if len(result) == 5 else (*result, None)
        color  = QCOL[q]

        ax.plot(TAU_REF, huff_ref(q), color=HUFF_COLOR, ls=HUFF_LS, lw=0.8, zorder=2)

        if tau is not None and med is not None:
            ax.fill_between(tau, p10, p90, color=color, alpha=BAND_ALPHA, zorder=3)
            ax.plot(tau, med, color=color, lw=1.2, zorder=4)
            # MAE
            ref_at = np.interp(tau, TAU_REF, huff_ref(q))
            finite = np.isfinite(med) & np.isfinite(ref_at)
            mae = np.mean(np.abs(med[finite] - ref_at[finite])) if finite.sum() > 1 else np.nan
            ax.text(0.05, 0.94, f"MAE={mae:.3f}", transform=ax.transAxes,
                    ha="left", va="top", fontsize=5.5, color="#444444")
            if n_sta is not None:
                ax.text(0.95, 0.05, f"n={n_sta}", transform=ax.transAxes,
                        ha="right", va="bottom", fontsize=5.5, color="#444444")

        ax.plot([0,1],[0,1], color="#bbbbbb", lw=0.4, ls=":", zorder=1)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.set_xticks([0, 0.5, 1.0]); ax.set_yticks([0, 0.5, 1.0])
        ax.grid(True, zorder=0)

        panel_letter = alpha_idx[qi * 6 + bi]
        ax.set_title(f"({panel_letter})", fontsize=6.5, fontweight="bold", pad=2)

        if qi == 0:
            short_name = biome.split()[0]  # "Amazônia", "Caatinga" etc.
            ax.text(0.5, 1.18, short_name, transform=ax.transAxes,
                    ha="center", va="bottom", fontsize=7, fontweight="bold")
        if bi == 0:
            ax.set_ylabel(f"{row_labels[q]}\nF(τ)", fontsize=7)
        if qi == 3:
            ax.set_xlabel("τ", fontsize=7)

stem3 = OUT_DIR / "huff_curves_all_biomes_quartiles"
fig3.savefig(str(stem3) + ".pdf", format="pdf", bbox_inches="tight")
fig3.savefig(str(stem3) + ".svg", format="svg", bbox_inches="tight")
fig3.savefig(str(stem3) + ".png", format="png", dpi=100, bbox_inches="tight")
plt.close(fig3)
print(f"  → {stem3}.pdf / .svg")

print("\nAll figures written to outputs/figures/")
