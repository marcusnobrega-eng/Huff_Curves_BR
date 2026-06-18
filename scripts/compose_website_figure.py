"""
Compose the website panels into one manuscript figure:
  (a) full interface overview  (large, top, full width)
  (b) Normalized Huff curves
  (c) Design-storm hyetograph
  (d) Event-quartile composition and statistics
  (e) Polynomial coefficient table
Saves: outputs/figures/website_viewer.{pdf,png}  (+ manuscript copy)
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import glob
import matplotlib.font_manager as fm
for _t in glob.glob(str(Path(__file__).resolve().parent.parent/"assets"/"fonts"/"*.ttf")):
    fm.fontManager.addfont(_t)
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.gridspec import GridSpec

ROOT = Path(__file__).resolve().parent.parent
FIG  = ROOT / "outputs" / "figures"

plt.rcParams.update({
    "font.family": "Helvetica Neue", "font.weight": 300,
    "pdf.fonttype": 42, "svg.fonttype": "none",
})

overview   = mpimg.imread(FIG / "web_overview.png")
curves     = mpimg.imread(FIG / "web_curves.png")
hyeto      = mpimg.imread(FIG / "web_hyetograph.png")
donut      = mpimg.imread(FIG / "web_quartile_donut.png")
poly       = mpimg.imread(FIG / "web_polynomial.png")

MM = 1/25.4
FW = 190 * MM
fig = plt.figure(figsize=(FW, FW * 1.16))
# 3 rows: overview spans row 0; 2x2 grid in rows 1-2
gs = GridSpec(3, 2, figure=fig,
              height_ratios=[1.30, 1.0, 1.0],
              hspace=0.16, wspace=0.06,
              left=0.012, right=0.988, top=0.965, bottom=0.012)

def panel(ax, img, label, title):
    ax.imshow(img)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(f"{label}  {title}", fontsize=8, fontweight=300,
                 loc="left", pad=3, color="#111111")

ax_a = fig.add_subplot(gs[0, :])
panel(ax_a, overview, "(a)",
      "Huff Curves BR Atlas — interactive interface")

ax_b = fig.add_subplot(gs[1, 0]); panel(ax_b, curves, "(b)", "Normalised Huff curves")
ax_c = fig.add_subplot(gs[1, 1]); panel(ax_c, hyeto,  "(c)", "Design-storm hyetograph")
ax_d = fig.add_subplot(gs[2, 0]); panel(ax_d, donut,  "(d)", "Event-quartile composition")
ax_e = fig.add_subplot(gs[2, 1]); panel(ax_e, poly,   "(e)", "Polynomial coefficients")

for ext in ("pdf", "png"):
    fig.savefig(FIG / f"website_viewer.{ext}", dpi=300, bbox_inches="tight")
import shutil
shutil.copy(str(FIG / "website_viewer.pdf"),
            str(ROOT / "manuscript" / "figures" / "website_viewer.pdf"))
plt.close(fig)
print("Composite website figure written.")
