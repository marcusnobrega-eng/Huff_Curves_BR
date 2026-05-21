"""Empirical Huff curve derivation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .constants import (
    HUFF_FIT_DEGREE,
    HUFF_INTERP_STEP,
    HUFF_PERCENTILE_LEVELS,
    HUFF_REFERENCE_COEFFICIENTS,
    HUFF_REFERENCE_TAU,
)
from .events import RainfallEvent
from .metrics import MetricResult, fitness_metrics


@dataclass(frozen=True)
class QuartileResult:
    quartile: int
    n_events: int
    percent_of_events: float
    average_volume_mm: float
    std_volume_mm: float
    average_duration_hours: float
    std_duration_hours: float
    max_intensity_mm_h: float
    polynomial_coefficients: np.ndarray
    metrics: MetricResult
    tau_grid: np.ndarray
    median_curve: np.ndarray
    percentile_curves: dict[int, np.ndarray]


@dataclass(frozen=True)
class HuffResult:
    station_id: str
    lat: float
    lon: float
    timestep_min: float
    n_events: int
    dominant_quartile: int | None
    quartiles: dict[int, QuartileResult]


def original_huff_curves(tau: np.ndarray = HUFF_REFERENCE_TAU) -> np.ndarray:
    """Evaluate original Huff reference curves on tau."""
    tau = np.asarray(tau, dtype=float)
    curves = np.vstack([np.polyval(row, tau) for row in HUFF_REFERENCE_COEFFICIENTS])
    return sanitize_cdf(curves, force_endpoints=False)


def sanitize_cdf(values: np.ndarray, force_endpoints: bool = True) -> np.ndarray:
    """Clip and monotonize cumulative curves along the last axis."""
    arr = np.asarray(values, dtype=float).copy()
    original_shape = arr.shape
    arr = np.atleast_2d(arr)

    for i in range(arr.shape[0]):
        row = arr[i]
        finite = np.isfinite(row)
        if finite.sum() >= 2 and not finite.all():
            x = np.flatnonzero(finite)
            row[~finite] = np.interp(np.flatnonzero(~finite), x, row[finite])
        row[:] = np.clip(row, 0.0, 1.0)
        row[:] = np.maximum.accumulate(row)
        if force_endpoints and row.size:
            row[0] = 0.0
            row[-1] = 1.0
        arr[i] = np.clip(row, 0.0, 1.0)

    return arr.reshape(original_shape)


def event_cumulative_curve(event: RainfallEvent) -> tuple[np.ndarray, np.ndarray]:
    """Return tau and cumulative rainfall fraction for one event."""
    rainfall = np.asarray(event.rainfall_mm, dtype=float)
    depths = np.where(np.isfinite(rainfall), rainfall, 0.0)
    total = float(depths.sum())
    if total <= 0:
        return np.array([], dtype=float), np.array([], dtype=float)

    tau = np.arange(1, depths.size + 1, dtype=float) / depths.size
    cumulative = np.cumsum(depths) / total
    cumulative = sanitize_cdf(cumulative, force_endpoints=False)
    cumulative[-1] = 1.0
    return tau, cumulative


def assign_huff_quartile(tau: np.ndarray, cumulative: np.ndarray) -> int:
    """Assign event to the time quartile with the largest rainfall depth."""
    if tau.size == 0:
        return 0
    x = np.r_[0.0, tau]
    y = np.r_[0.0, cumulative]
    q_cum = np.interp([0.0, 0.25, 0.5, 0.75, 1.0], x, y)
    q_depths = np.diff(sanitize_cdf(q_cum, force_endpoints=True))
    return int(np.nanargmax(q_depths) + 1)


def _fit_quartile(
    quartile: int,
    events: list[RainfallEvent],
    event_quartiles: np.ndarray,
    curves: list[tuple[np.ndarray, np.ndarray]],
    tau_grid: np.ndarray,
    percentile_levels: tuple[int, ...],
) -> QuartileResult:
    idx = np.flatnonzero(event_quartiles == quartile)
    n_events = int(idx.size)
    n_total = int(len(events))

    volumes = np.array([events[i].volume_mm for i in idx], dtype=float)
    durations = np.array([events[i].duration_hours for i in idx], dtype=float)
    max_intensities = np.array([events[i].maximum_intensity_mm_h for i in idx], dtype=float)

    interpolated = []
    for i in idx:
        tau, cumulative = curves[i]
        if tau.size == 0:
            continue
        interpolated.append(np.interp(tau_grid, np.r_[0.0, tau], np.r_[0.0, cumulative]))

    if interpolated:
        arr = sanitize_cdf(np.vstack(interpolated), force_endpoints=True)
        percentile_curves = {
            level: sanitize_cdf(np.nanpercentile(arr, level, axis=0), force_endpoints=True)
            for level in percentile_levels
        }
        median_curve = percentile_curves[50] if 50 in percentile_curves else sanitize_cdf(np.nanmedian(arr, axis=0))
    else:
        percentile_curves = {level: np.full_like(tau_grid, np.nan, dtype=float) for level in percentile_levels}
        median_curve = np.full_like(tau_grid, np.nan, dtype=float)

    if np.isfinite(median_curve).sum() >= HUFF_FIT_DEGREE + 1 and n_events > 0:
        coeffs = np.polyfit(tau_grid, median_curve, HUFF_FIT_DEGREE)
        fitted_reference_tau = sanitize_cdf(np.polyval(coeffs, HUFF_REFERENCE_TAU), force_endpoints=False)
        reference = original_huff_curves(HUFF_REFERENCE_TAU)[quartile - 1]
        metrics = fitness_metrics(fitted_reference_tau, reference)
    else:
        coeffs = np.full(HUFF_FIT_DEGREE + 1, np.nan, dtype=float)
        metrics = MetricResult(*(float("nan"),) * 7, n_valid=0)

    return QuartileResult(
        quartile=quartile,
        n_events=n_events,
        percent_of_events=float(100.0 * n_events / n_total) if n_total else float("nan"),
        average_volume_mm=float(np.nanmean(volumes)) if volumes.size else float("nan"),
        std_volume_mm=float(np.nanstd(volumes, ddof=1)) if volumes.size > 1 else float("nan"),
        average_duration_hours=float(np.nanmean(durations)) if durations.size else float("nan"),
        std_duration_hours=float(np.nanstd(durations, ddof=1)) if durations.size > 1 else float("nan"),
        max_intensity_mm_h=float(np.nanmax(max_intensities)) if max_intensities.size else float("nan"),
        polynomial_coefficients=coeffs,
        metrics=metrics,
        tau_grid=tau_grid,
        median_curve=median_curve,
        percentile_curves=percentile_curves,
    )


def compute_huff_result(
    station_id: str,
    lat: float,
    lon: float,
    timestep_min: float,
    events: list[RainfallEvent],
    interp_step: float = HUFF_INTERP_STEP,
    percentile_levels: tuple[int, ...] = HUFF_PERCENTILE_LEVELS,
) -> HuffResult:
    """Compute empirical Huff curves and metrics for one station."""
    tau_grid = np.round(np.arange(0.0, 1.0 + interp_step / 2.0, interp_step), 10)
    curves: list[tuple[np.ndarray, np.ndarray]] = []
    event_quartiles = np.zeros(len(events), dtype=int)

    for i, event in enumerate(events):
        tau, cumulative = event_cumulative_curve(event)
        curves.append((tau, cumulative))
        event_quartiles[i] = assign_huff_quartile(tau, cumulative) if tau.size else 0

    quartiles = {
        q: _fit_quartile(q, events, event_quartiles, curves, tau_grid, percentile_levels)
        for q in range(1, 5)
    }

    counts = np.array([quartiles[q].n_events for q in range(1, 5)], dtype=int)
    dominant = int(np.argmax(counts) + 1) if counts.sum() > 0 else None

    return HuffResult(
        station_id=str(station_id),
        lat=float(lat),
        lon=float(lon),
        timestep_min=float(timestep_min),
        n_events=int(len(events)),
        dominant_quartile=dominant,
        quartiles=quartiles,
    )


def flatten_huff_result(result: HuffResult) -> dict[str, float | int | str | None]:
    """Flatten a station Huff result for CSV export."""
    row: dict[str, float | int | str | None] = {
        "station_id": result.station_id,
        "lat": result.lat,
        "lon": result.lon,
        "dt_min": result.timestep_min,
        "n_events": result.n_events,
        "dominant_quartile": result.dominant_quartile,
    }

    for q in range(1, 5):
        qr = result.quartiles[q]
        prefix = f"q{q}"
        row[f"{prefix}_n_events"] = qr.n_events
        row[f"{prefix}_percent_events"] = qr.percent_of_events
        row[f"{prefix}_avg_volume_mm"] = qr.average_volume_mm
        row[f"{prefix}_std_volume_mm"] = qr.std_volume_mm
        row[f"{prefix}_avg_duration_h"] = qr.average_duration_hours
        row[f"{prefix}_std_duration_h"] = qr.std_duration_hours
        row[f"{prefix}_max_intensity_mm_h"] = qr.max_intensity_mm_h
        row[f"{prefix}_kge"] = qr.metrics.kge
        row[f"{prefix}_r2"] = qr.metrics.r2
        row[f"{prefix}_rmse"] = qr.metrics.rmse
        row[f"{prefix}_mae"] = qr.metrics.mae
        for i, coef in enumerate(qr.polynomial_coefficients, start=1):
            row[f"{prefix}_coef_{i}"] = float(coef)

    kges = [result.quartiles[q].metrics.kge for q in range(1, 5)]
    row["kge_mean"] = float(np.nanmean(kges)) if np.isfinite(kges).any() else float("nan")
    return row
