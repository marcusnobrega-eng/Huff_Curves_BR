import numpy as np
import pandas as pd

from huff_curves_br.events import RainfallEvent
from huff_curves_br.huff import assign_huff_quartile, compute_huff_result, event_cumulative_curve, flatten_huff_result


def _event(values):
    values = np.asarray(values, dtype=float)
    duration_hours = values.size * 15 / 60
    volume = float(values.sum())
    return RainfallEvent(
        start=pd.Timestamp("2020-01-01 00:00"),
        end=pd.Timestamp("2020-01-01 00:00") + pd.Timedelta(minutes=15 * (values.size - 1)),
        timestep_min=15,
        rainfall_mm=values,
        duration_hours=duration_hours,
        volume_mm=volume,
        average_intensity_mm_h=volume / duration_hours,
        maximum_intensity_mm_h=float(values.max() * 60 / 15),
    )


def test_event_quartile_detects_early_peak():
    tau, cumulative = event_cumulative_curve(_event([3, 2, 0, 0, 0, 0, 0, 0]))

    assert assign_huff_quartile(tau, cumulative) == 1


def test_compute_huff_result_flattens_coefficients():
    events = [_event([3, 2, 1, 0, 0, 0, 0, 0]), _event([2, 2, 1, 1, 0, 0, 0, 0])]

    result = compute_huff_result("123", -15.0, -47.0, 15, events)
    row = flatten_huff_result(result)

    assert result.dominant_quartile == 1
    assert row["station_id"] == "123"
    assert row["q1_n_events"] == 2
    assert "q1_coef_8" in row
