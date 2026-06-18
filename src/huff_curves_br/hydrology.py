"""
SCS-CN design-storm rainfall-runoff engine.
=============================================
Computes a design hydrograph at a catchment outlet from:
  - a design rainfall depth and duration,
  - a dimensionless Huff temporal pattern (cumulative mass curve),
  - SCS Curve Number losses,
  - the SCS dimensionless unit hydrograph.

The purpose is a CONTROLLED comparison: holding catchment, CN, time of
concentration, depth, and duration fixed, only the temporal pattern (the
Huff cumulative curve) is varied between the original Huff (1967) reference
and the locally derived Brazilian curve. Differences in peak discharge and
time-to-peak are therefore attributable solely to the hyetograph shape.

References
----------
USDA-NRCS National Engineering Handbook, Part 630 (Hydrology), chs. 9, 10, 16.
USDA-NRCS TR-55 (1986). Urban Hydrology for Small Watersheds.
Kirpich, Z.P. (1940). Time of concentration of small agricultural watersheds.
"""

from dataclasses import dataclass
from typing import Callable, Tuple

import numpy as np


# ── time of concentration ──────────────────────────────────────────────────
def kirpich_tc_hours(length_m: float, slope_m_per_m: float) -> float:
    """Kirpich (1940) time of concentration.

    Tc[min] = 0.0078 * L_ft^0.77 * S^-0.385, returned in hours.
    L in metres is converted to feet; slope is dimensionless (m/m).
    """
    if length_m <= 0 or slope_m_per_m <= 0:
        return float("nan")
    length_ft = length_m / 0.3048
    tc_min = 0.0078 * (length_ft ** 0.77) * (slope_m_per_m ** -0.385)
    return tc_min / 60.0


def hack_length_km(area_km2: float) -> float:
    """Estimate main-channel length from drainage area (Hack's law).

    L[km] ~= 1.4 * A[km2]^0.6  (commonly used exponent ~0.6).
    """
    if area_km2 <= 0:
        return float("nan")
    return 1.4 * (area_km2 ** 0.6)


# ── SCS-CN losses ───────────────────────────────────────────────────────────
def scs_potential_retention_mm(cn: float) -> float:
    """Maximum potential retention S (mm) from the Curve Number."""
    cn = float(np.clip(cn, 1.0, 100.0))
    return 25400.0 / cn - 254.0


def scs_cumulative_runoff_mm(
    cum_rain_mm: np.ndarray,
    cn: float,
    ia_ratio: float = 0.2,
) -> np.ndarray:
    """Cumulative direct runoff depth (mm) from cumulative rainfall.

    Q = (P - Ia)^2 / (P - Ia + S)   for P > Ia, else 0,
    with Ia = ia_ratio * S. Applied to the cumulative rainfall series so
    that incremental (per-step) runoff is its first difference.
    """
    p = np.asarray(cum_rain_mm, dtype=float)
    s = scs_potential_retention_mm(cn)
    ia = ia_ratio * s
    excess = p - ia
    q = np.where(excess > 0.0, excess ** 2 / (excess + s), 0.0)
    return q


# ── SCS dimensionless unit hydrograph ──────────────────────────────────────
# Standard SCS dimensionless UH (t/Tp, q/qp), PRF = 484.
_SCS_TR = np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0,
                    1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6,
                    2.8, 3.0, 3.5, 4.0, 4.5, 5.0])
_SCS_QR = np.array([0.0, 0.03, 0.10, 0.19, 0.31, 0.47, 0.66, 0.82, 0.93, 0.99,
                    1.00, 0.99, 0.93, 0.86, 0.78, 0.68, 0.56, 0.39, 0.28,
                    0.207, 0.147, 0.107, 0.077, 0.055, 0.025, 0.011, 0.005,
                    0.000])


def scs_unit_hydrograph(
    tc_hours: float,
    area_km2: float,
    dt_hours: float,
    excess_duration_hours: float,
) -> Tuple[np.ndarray, float, float]:
    """Build the SCS unit hydrograph ordinates (m^3/s per mm of excess).

    Lag  L = 0.6 * Tc; unit-rainfall duration D = excess_duration (the
    computational time step of the excess hyetograph). Time to peak
    Tp = D/2 + L; peak factor 0.208 (SI form of PRF 484):
        qp = 0.208 * A[km2] / Tp[h]   (m^3/s per mm).
    Returns (uh_ordinates, tp_hours, qp_per_mm).
    """
    lag = 0.6 * tc_hours
    d = excess_duration_hours
    tp = d / 2.0 + lag
    qp = 0.208 * area_km2 / tp     # m3/s per mm of excess rainfall
    t = np.arange(0.0, _SCS_TR[-1] * tp + dt_hours, dt_hours)
    uh = np.interp(t / tp, _SCS_TR, _SCS_QR) * qp
    return uh, tp, qp


# ── design hyetograph from a Huff cumulative curve ─────────────────────────
def huff_design_hyetograph(
    total_depth_mm: float,
    duration_hours: float,
    dt_hours: float,
    huff_cdf: Callable[[np.ndarray], np.ndarray],
) -> Tuple[np.ndarray, np.ndarray]:
    """Discretise a design storm using a Huff dimensionless mass curve.

    huff_cdf maps normalised time tau in [0,1] to cumulative fraction in
    [0,1]. Returns (time_edges_hours, incremental_depth_mm) where the
    incremental array has one value per time step.
    """
    n = max(1, int(round(duration_hours / dt_hours)))
    edges = np.linspace(0.0, duration_hours, n + 1)
    tau = edges / duration_hours
    cdf = np.clip(huff_cdf(tau), 0.0, 1.0)
    cdf = np.maximum.accumulate(cdf)
    cdf[0], cdf[-1] = 0.0, 1.0
    incr = np.diff(cdf) * total_depth_mm
    return edges, incr


@dataclass(frozen=True)
class HydrographResult:
    time_hours: np.ndarray
    discharge_m3s: np.ndarray
    peak_discharge_m3s: float
    time_to_peak_hours: float
    runoff_depth_mm: float


def design_hydrograph(
    total_depth_mm: float,
    duration_hours: float,
    huff_cdf: Callable[[np.ndarray], np.ndarray],
    cn: float,
    tc_hours: float,
    area_km2: float,
    dt_hours: float = None,
    ia_ratio: float = 0.2,
) -> HydrographResult:
    """Full SCS-CN design hydrograph for one catchment and one Huff pattern."""
    if dt_hours is None:
        # computational step: a fraction of Tc, capped to the storm
        dt_hours = max(min(tc_hours / 10.0, duration_hours / 12.0), 1e-3)

    edges, incr_rain = huff_design_hyetograph(
        total_depth_mm, duration_hours, dt_hours, huff_cdf)
    cum_rain = np.r_[0.0, np.cumsum(incr_rain)]
    cum_runoff = scs_cumulative_runoff_mm(cum_rain, cn, ia_ratio)
    incr_runoff = np.diff(cum_runoff)              # mm of excess per step

    uh, tp, qp = scs_unit_hydrograph(tc_hours, area_km2, dt_hours, dt_hours)

    # convolve excess hyetograph with the unit hydrograph
    q = np.convolve(incr_runoff, uh)               # m3/s
    t = np.arange(q.size) * dt_hours

    peak = float(np.max(q)) if q.size else float("nan")
    t_peak = float(t[int(np.argmax(q))]) if q.size else float("nan")
    runoff_depth = float(cum_runoff[-1])

    return HydrographResult(
        time_hours=t,
        discharge_m3s=q,
        peak_discharge_m3s=peak,
        time_to_peak_hours=t_peak,
        runoff_depth_mm=runoff_depth,
    )


def _hydrograph_duration_hours(result: "HydrographResult") -> float:
    """Time (h) from storm start until discharge falls below 1 % of peak."""
    q = result.discharge_m3s
    t = result.time_hours
    if q.size == 0 or result.peak_discharge_m3s <= 0:
        return float("nan")
    above = np.where(q >= 0.01 * result.peak_discharge_m3s)[0]
    return float(t[above[-1]]) if above.size else float("nan")


def compare_patterns(
    total_depth_mm: float,
    duration_hours: float,
    huff_reference: Callable[[np.ndarray], np.ndarray],
    huff_local: Callable[[np.ndarray], np.ndarray],
    cn: float,
    tc_hours: float,
    area_km2: float,
    **kw,
) -> dict:
    """Compare reference vs local Huff pattern for one catchment.

    Returns peak discharge, time-to-peak, runoff coefficient, hydrograph
    duration, and their differences (local relative to reference).

    Note: total runoff depth is pattern-independent in the SCS-CN model
    (it depends only on total rainfall depth and CN), so the runoff
    coefficient is identical for both patterns.  It is reported as a
    catchment descriptor rather than a change metric.
    """
    ref = design_hydrograph(total_depth_mm, duration_hours, huff_reference,
                            cn, tc_hours, area_km2, **kw)
    loc = design_hydrograph(total_depth_mm, duration_hours, huff_local,
                            cn, tc_hours, area_km2, **kw)
    d_qp = loc.peak_discharge_m3s - ref.peak_discharge_m3s
    d_qp_pct = (100.0 * d_qp / ref.peak_discharge_m3s
                if ref.peak_discharge_m3s > 0 else float("nan"))
    d_tp = loc.time_to_peak_hours - ref.time_to_peak_hours
    rc = ref.runoff_depth_mm / total_depth_mm if total_depth_mm > 0 else float("nan")
    dur_ref = _hydrograph_duration_hours(ref)
    dur_loc = _hydrograph_duration_hours(loc)
    d_dur = dur_loc - dur_ref
    return {
        "qp_ref_m3s":    ref.peak_discharge_m3s,
        "qp_local_m3s":  loc.peak_discharge_m3s,
        "d_qp_pct":      d_qp_pct,
        "tp_ref_h":      ref.time_to_peak_hours,
        "tp_local_h":    loc.time_to_peak_hours,
        "d_tp_h":        d_tp,
        "runoff_mm":     ref.runoff_depth_mm,
        "rc":            rc,
        "duration_ref_h":   dur_ref,
        "duration_local_h": dur_loc,
        "d_duration_h":     d_dur,
    }
