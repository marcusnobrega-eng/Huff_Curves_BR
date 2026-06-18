"""
Diurnal cycle of event initiation (evidence for convective forcing).
Computes the hour-of-day distribution of event start times, overall and
by dominant quartile, from outputs/rainfall_events.csv.

Note on time zone: ANA telemetric timestamps are used as recorded. The
ABSOLUTE clock hours therefore depend on the network's recording
convention, but the RELATIVE ordering of the quartile peak hours is
invariant to any uniform offset and is the robust result.

Writes: outputs/diagnostics/diurnal_cycle.csv
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ev = pd.read_csv(ROOT / "outputs" / "rainfall_events.csv", parse_dates=["start"])
ev["hour"] = ev["start"].dt.hour
ev["q"] = ev["dominant_event_quartile"]

def shares(h):
    return dict(
        morning=float(h.reindex(range(6, 12)).sum()),
        afternoon=float(h.reindex(range(12, 18)).sum()),
        evening=float(h.reindex(range(18, 24)).sum()),
        night=float(h.reindex(range(0, 6)).sum()),
        peak_hour=int(h.idxmax()),
    )

rows = []
all_h = ev["hour"].value_counts(normalize=True).sort_index() * 100
s = shares(all_h)
rows.append({"group": "all", **s})
print(f"ALL events (n={len(ev):,}): peak {s['peak_hour']:02d}h  "
      f"morning {s['morning']:.1f}%  afternoon {s['afternoon']:.1f}%  "
      f"evening {s['evening']:.1f}%  night {s['night']:.1f}%")

for q in [1, 2, 3, 4]:
    hq = ev.loc[ev["q"] == q, "hour"].value_counts(normalize=True).sort_index() * 100
    s = shares(hq)
    rows.append({"group": f"Q{q}", **s})
    print(f"  Q{q} (n={int((ev['q']==q).sum()):>7,}): peak {s['peak_hour']:02d}h  "
          f"afternoon {s['afternoon']:.1f}%  morning {s['morning']:.1f}%")

out = ROOT / "outputs" / "diagnostics" / "diurnal_cycle.csv"
out.parent.mkdir(parents=True, exist_ok=True)
# also save the full hourly histogram (all + per quartile)
hist = pd.DataFrame({"hour": range(24)})
hist["all_pct"] = [all_h.get(h, 0.0) for h in range(24)]
for q in [1, 2, 3, 4]:
    hq = ev.loc[ev["q"] == q, "hour"].value_counts(normalize=True) * 100
    hist[f"q{q}_pct"] = [hq.get(h, 0.0) for h in range(24)]
hist.to_csv(out, index=False)
pd.DataFrame(rows).to_csv(out.with_name("diurnal_summary.csv"), index=False)
print(f"\nSaved: {out}")
print(f"Saved: {out.with_name('diurnal_summary.csv')}")
