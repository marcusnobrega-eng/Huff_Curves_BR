import numpy as np
import pandas as pd

from huff_curves_br.events import extract_events


def test_extract_events_uses_interval_depths_and_dry_gap():
    times = pd.date_range("2020-01-01", periods=80, freq="15min")
    rainfall = np.zeros(len(times), dtype=float)
    rainfall[1:5] = [1.0, 2.0, 1.0, 1.0]
    rainfall[40:44] = [0.5, 1.0, 1.0, 0.5]
    df = pd.DataFrame({"datetime": times, "rainfall_mm": rainfall})

    events = extract_events(df, timestep_min=15, ietd_hours=6, min_event_depth_mm=0.1, min_records=1)

    assert len(events) == 2
    assert events[0].volume_mm == 5.0
    assert events[0].duration_hours == 1.0
    assert events[0].maximum_intensity_mm_h == 8.0
    assert events[1].volume_mm == 3.0
