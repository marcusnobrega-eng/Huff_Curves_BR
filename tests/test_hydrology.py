import numpy as np

from huff_curves_br.hydrology import (
    scs_potential_retention_mm,
    scs_cumulative_runoff_mm,
    kirpich_tc_hours,
    hack_length_km,
    design_hydrograph,
    compare_patterns,
)


def test_scs_runoff_matches_closed_form():
    s = scs_potential_retention_mm(75.0)          # = 84.67 mm
    p = 80.0
    ia = 0.2 * s
    expected = (p - ia) ** 2 / (p - ia + s)
    got = scs_cumulative_runoff_mm(np.array([p]), 75.0)[0]
    assert abs(got - expected) < 1e-6


def test_runoff_monotone_in_cn():
    p = np.array([60.0])
    q_low = scs_cumulative_runoff_mm(p, 60.0)[0]
    q_high = scs_cumulative_runoff_mm(p, 85.0)[0]
    assert q_high > q_low          # higher CN -> more runoff


def test_kirpich_and_hack_positive():
    L = hack_length_km(30.0) * 1000.0
    tc = kirpich_tc_hours(L, 0.03)
    assert tc > 0 and np.isfinite(tc)


def test_identical_patterns_give_zero_difference():
    pat = lambda t: np.clip(t ** 0.6, 0, 1)
    r = compare_patterns(80.0, 6.0, pat, pat, cn=75, tc_hours=1.5, area_km2=30.0)
    assert abs(r["d_qp_pct"]) < 1e-6
    assert abs(r["d_tp_h"]) < 1e-9


def test_peak_scales_with_area():
    pat = lambda t: np.clip(t ** 0.6, 0, 1)
    small = design_hydrograph(80.0, 6.0, pat, 75, 1.5, 10.0)
    big = design_hydrograph(80.0, 6.0, pat, 75, 1.5, 40.0)
    # same Tc/pattern -> peak proportional to area
    assert big.peak_discharge_m3s > small.peak_discharge_m3s


def test_scs_late_rain_more_efficient():
    """Marginal runoff ratio rises through the storm (SCS-CN nonlinearity)."""
    s = scs_potential_retention_mm(70.0)
    ia = 0.2 * s
    p = np.linspace(ia + 1, ia + 200, 50)
    q = scs_cumulative_runoff_mm(p, 70.0)
    dqdp = np.diff(q) / np.diff(p)
    assert dqdp[0] < dqdp[-1] < 1.0001     # increasing toward 1
