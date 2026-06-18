"""
Capture website panels for the manuscript figure (Playwright).
Produces:
  outputs/figures/web_overview.png      — full interface
  outputs/figures/web_curves.png        — Normalized Huff curves
  outputs/figures/web_hyetograph.png    — Design-storm hyetograph
  outputs/figures/web_quartile.png      — Event quartiles + statistics
  outputs/figures/web_polynomial.png    — Polynomial coefficients
"""
from pathlib import Path
import time
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT / "outputs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
URL  = "http://localhost:8765/web/huff_viewer/index.html"
STATION = "14100000"   # Manacapuru, AM — rich record, all quartiles populated

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1000},
                                device_scale_factor=2)
        page.goto(URL, wait_until="networkidle")
        time.sleep(2.5)
        # select a representative station
        page.evaluate(f"selectStation('{STATION}', true)")
        time.sleep(3.0)   # let Chart.js animations settle

        # (a) full-interface overview (viewport)
        page.screenshot(path=str(OUT / "web_overview.png"))
        print("  overview ✓")

        # helper: screenshot the section element that contains a given selector
        def shot(container_selector, fname, pad=0):
            el = page.locator(container_selector).first
            el.scroll_into_view_if_needed()
            time.sleep(0.8)
            el.screenshot(path=str(OUT / fname))
            print(f"  {fname} ✓")

        # (b) Normalized Huff curves — the section wrapping #curveChart
        shot("section.chart-section:has(#curveChart)", "web_curves.png")
        # (c) Design-storm hyetograph
        shot("section.storm-section", "web_hyetograph.png")
        # (d) Event quartiles donut
        shot("section.chart-section:has(#eventBreakdownChart)", "web_quartile_donut.png")
        #     Quartile statistics table
        shot("section.table-section:has(#quartileTable)", "web_quartile_table.png")
        # (e) Polynomial coefficients
        shot("details.coefficients-panel", "web_polynomial.png")

        browser.close()

if __name__ == "__main__":
    run()
