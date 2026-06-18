"""
Shared figure style for the Huff Curves BR manuscript
=====================================================
Single source of truth for fonts, colours, and save helpers so every
figure in the paper is visually consistent.

Palette: Okabe–Ito colourblind-safe categorical palette — the de-facto
standard for scientific publishing (recommended by the colour-palette
guidance at simplifiedsciencepublishing.com). Sequential data uses the
perceptually-uniform 'cividis' / 'viridis' maps.

Font: Helvetica Neue Light (weight 300), extracted to assets/fonts/.
"""

from pathlib import Path
import glob
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

ROOT     = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "assets" / "fonts"
FIG_DIR  = ROOT / "outputs" / "figures"
MANU_FIG = ROOT / "manuscript" / "figures"

# ── register Helvetica Neue Light ─────────────────────────────────────────
for _ttf in glob.glob(str(FONT_DIR / "*.ttf")):
    try:
        fm.fontManager.addfont(_ttf)
    except Exception:
        pass

# ── Okabe–Ito colourblind-safe categorical palette ────────────────────────
OKABE_ITO = {
    "black":   "#000000",
    "orange":  "#E69F00",
    "skyblue": "#56B4E9",
    "green":   "#009E73",
    "yellow":  "#F0E442",
    "blue":    "#0072B2",
    "vermil":  "#D55E00",
    "purple":  "#CC79A7",
}

# Quartile colours (Q1–Q4) — distinct, ordered, colourblind-safe
QUARTILE_COLORS = {
    1: OKABE_ITO["blue"],     # Q1 — front-loaded (primary result)
    2: OKABE_ITO["green"],    # Q2
    3: OKABE_ITO["orange"],   # Q3
    4: OKABE_ITO["vermil"],   # Q4
}
QUARTILE_LABELS = {1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"}

# Biome colours — assigned from the Okabe–Ito palette
BIOME_COLORS = {
    "Amazônia":       OKABE_ITO["green"],
    "Caatinga":       OKABE_ITO["orange"],
    "Cerrado":        OKABE_ITO["yellow"],
    "Mata Atlântica": OKABE_ITO["blue"],
    "Pampa":          OKABE_ITO["skyblue"],
    "Pantanal":       OKABE_ITO["purple"],
}
BIOME_ORDER = ["Amazônia", "Caatinga", "Cerrado",
               "Mata Atlântica", "Pampa", "Pantanal"]

# Sequential maps for continuous fields
SEQ_CMAP_RECORD = "cividis"     # record length (Fig 1) — colourblind-safe
SEQ_CMAP_METRIC = "magma"       # MAE / D_max (Fig 5)
SEQ_CMAP_RECMAP = "magma"       # standalone record-length map (Fig 5 alt)

# Pale, low-saturation biome fills for use as MAP BACKGROUND context.
# (Distinct from the saturated BIOME_COLORS used in line plots / legends.)
BIOME_FILL = {
    "Amazônia":       "#D8F0E6",
    "Caatinga":       "#F5E7C2",
    "Cerrado":        "#EFE8A6",
    "Mata Atlântica": "#DDEBF7",
    "Pampa":          "#D7E5EF",
    "Pantanal":       "#F0DDE8",
}
BIOME_BORDER = "#4A4A4A"        # grey35

# Distinct categorical colours for the four dominant quartiles (Fig 4 map)
QUARTILE_MAP_COLORS = {
    1: "#1b9e77",   # teal-green
    2: "#7570b3",   # indigo
    3: "#e6ab02",   # gold
    4: "#d95f02",   # burnt orange
}

# Neutral greys
GREY_EXCLUDED = "#000000"       # excluded stations (black, high visibility)
GREY_GRID     = "#e6e6e6"
GREY_REF      = "#000000"       # Huff reference line

# ── matplotlib rcParams ───────────────────────────────────────────────────
def apply_rcparams(base_size: int = 8):
    plt.rcParams.update({
        "font.family":       "Helvetica Neue",
        "font.weight":       300,
        "font.size":         base_size,
        "axes.labelsize":    base_size + 1,
        "axes.titlesize":    base_size + 1,
        "axes.titleweight":  300,
        "axes.labelweight":  300,
        "xtick.labelsize":   base_size - 0.5,
        "ytick.labelsize":   base_size - 0.5,
        "legend.fontsize":   base_size - 0.5,
        "axes.linewidth":    0.5,
        "xtick.major.width": 0.4,
        "ytick.major.width": 0.4,
        "grid.linewidth":    0.4,
        "grid.color":        GREY_GRID,
        "figure.dpi":        150,
        "savefig.dpi":       300,
        "pdf.fonttype":      42,
        "svg.fonttype":      "none",
    })

# Elsevier single-column / full text width in inches
MM = 1 / 25.4
TEXT_WIDTH = 190 * MM

# ── thicker colourbar outline helper ──────────────────────────────────────
def style_colorbar(cb, label="", thin=True, thick_outline=True):
    """Apply thinner width + thicker outline contour to a colourbar."""
    cb.set_label(label, fontsize=7.5, fontweight=300, labelpad=3)
    cb.ax.tick_params(labelsize=6.5, width=0.4)
    if thick_outline:
        cb.outline.set_linewidth(0.9)   # double the usual ~0.45
        cb.outline.set_edgecolor("#222222")
    else:
        cb.outline.set_linewidth(0.45)
    return cb

# ── unified save helper (PDF + SVG + PNG, and copy PDF to manuscript) ──────
def save(fig, name: str, copy_to_manuscript: bool = True):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    stem = FIG_DIR / name
    for ext, dpi in [("pdf", None), ("svg", None), ("png", 150)]:
        kw = dict(bbox_inches="tight")
        if dpi:
            kw["dpi"] = dpi
        fig.savefig(f"{stem}.{ext}", format=ext, **kw)
    if copy_to_manuscript:
        import shutil
        MANU_FIG.mkdir(parents=True, exist_ok=True)
        shutil.copy(f"{stem}.pdf", str(MANU_FIG / f"{name}.pdf"))
    print(f"  → {name}.pdf / .svg / .png"
          + ("  (+manuscript)" if copy_to_manuscript else ""))
