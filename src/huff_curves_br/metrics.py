"""Curve-comparison metrics used by the Huff workflow."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MetricResult:
    ia: float
    nse: float
    pbias: float
    kge: float
    rmse: float
    mae: float
    r2: float
    n_valid: int


def _finite_pairs(candidate: np.ndarray, reference: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    candidate = np.asarray(candidate, dtype=float).reshape(-1)
    reference = np.asarray(reference, dtype=float).reshape(-1)
    n = min(candidate.size, reference.size)
    candidate = candidate[:n]
    reference = reference[:n]
    ok = np.isfinite(candidate) & np.isfinite(reference)
    return candidate[ok], reference[ok]


def kling_gupta_efficiency(candidate: np.ndarray, reference: np.ndarray) -> float:
    """Return KGE where candidate is empirical and reference is original Huff."""
    candidate, reference = _finite_pairs(candidate, reference)
    if candidate.size < 2:
        return float("nan")

    std_candidate = np.std(candidate, ddof=1)
    std_reference = np.std(reference, ddof=1)
    mean_candidate = np.mean(candidate)
    mean_reference = np.mean(reference)

    if std_candidate <= 0 or std_reference <= 0 or abs(mean_reference) <= np.finfo(float).eps:
        return float("nan")

    r = np.corrcoef(candidate, reference)[0, 1]
    alpha = std_candidate / std_reference
    beta = mean_candidate / mean_reference
    return float(1.0 - np.sqrt((r - 1.0) ** 2 + (alpha - 1.0) ** 2 + (beta - 1.0) ** 2))


def fitness_metrics(candidate: np.ndarray, reference: np.ndarray) -> MetricResult:
    """Compute similarity metrics between an empirical and reference Huff curve."""
    candidate, reference = _finite_pairs(candidate, reference)
    n = candidate.size
    if n < 2:
        return MetricResult(*(float("nan"),) * 7, n_valid=n)

    residual = candidate - reference
    sse = float(np.sum(residual**2))
    mean_ref = float(np.mean(reference))
    mean_candidate = float(np.mean(candidate))
    std_ref = float(np.std(reference, ddof=1))
    std_candidate = float(np.std(candidate, ddof=1))

    rmse = float(np.sqrt(np.mean(residual**2)))
    mae = float(np.mean(np.abs(residual)))

    pbias_den = float(np.sum(reference))
    pbias = float(100.0 * np.sum(residual) / pbias_den) if abs(pbias_den) > np.finfo(float).eps else float("nan")

    if std_ref > 0 and std_candidate > 0:
        r = float(np.corrcoef(candidate, reference)[0, 1])
        r2 = r**2
    else:
        r = float("nan")
        r2 = float("nan")

    den_nse = float(np.sum((reference - mean_ref) ** 2))
    if den_nse > np.finfo(float).eps:
        nse = float(1.0 - sse / den_nse)
    else:
        nse = 1.0 if sse <= np.finfo(float).eps else float("nan")

    den_ia = float(np.sum((np.abs(candidate - mean_ref) + np.abs(reference - mean_ref)) ** 2))
    if den_ia > np.finfo(float).eps:
        ia = float(1.0 - sse / den_ia)
    else:
        ia = 1.0 if sse <= np.finfo(float).eps else float("nan")

    if np.isfinite(r) and std_ref > 0 and abs(mean_ref) > np.finfo(float).eps:
        alpha = std_candidate / std_ref
        beta = mean_candidate / mean_ref
        kge = float(1.0 - np.sqrt((r - 1.0) ** 2 + (alpha - 1.0) ** 2 + (beta - 1.0) ** 2))
    else:
        kge = float("nan")

    return MetricResult(ia=ia, nse=nse, pbias=pbias, kge=kge, rmse=rmse, mae=mae, r2=r2, n_valid=n)

