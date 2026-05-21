import numpy as np
import pandas as pd

from huff_curves_br.regional import regional_huff_coefficients


def test_regional_huff_coefficients_use_station_median_curves():
    stations = pd.DataFrame(
        {
            "station_id": ["1", "2"],
            "status": ["ok", "ok"],
            "state_code": ["11", "11"],
            "state_name": ["Rondonia", "Rondonia"],
            "n_events": [10, 20],
            "years_span": [1.0, 2.0],
            "kge_mean": [0.8, 0.9],
            "missing_fraction": [0.1, 0.2],
            "q1_n_events": [8, 10],
            "q2_n_events": [1, 5],
            "q3_n_events": [1, 3],
            "q4_n_events": [0, 2],
            "q1_max_intensity_mm_h": [20.0, 30.0],
            "q2_max_intensity_mm_h": [10.0, 15.0],
            "q3_max_intensity_mm_h": [8.0, 12.0],
            "q4_max_intensity_mm_h": [0.0, 7.0],
        }
    )
    tau = np.round(np.arange(0, 1.001, 0.02), 2)
    curves = pd.DataFrame(
        [
            {"station_id": station_id, "quartile": quartile, "tau": t, "median": t ** (0.75 + quartile / 10)}
            for station_id in ["1", "2"]
            for quartile in range(1, 5)
            for t in tau
        ]
    )

    coeffs, long_curves = regional_huff_coefficients(stations, curves, "state_code", "state_name", "state")

    assert len(coeffs) == 1
    assert coeffs.loc[0, "n_stations"] == 2
    assert coeffs.loc[0, "n_events"] == 30
    assert coeffs.loc[0, "dominant_quartile"] == 1
    assert coeffs.loc[0, "q1_n_curve_stations"] == 2
    assert "q1_coef_8" in coeffs.columns
    assert len(long_curves) == 4 * len(tau)
