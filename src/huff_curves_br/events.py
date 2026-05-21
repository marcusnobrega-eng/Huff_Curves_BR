"""Rainfall event extraction."""

from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd

from .constants import (
    DEFAULT_IETD_HOURS,
    DEFAULT_MAX_EVENT_DURATION_HOURS,
    DEFAULT_MIN_EVENT_DEPTH_MM,
    DEFAULT_MIN_EVENT_RECORDS,
)
from .series import rainfall_column


@dataclass(frozen=True)
class RainfallEvent:
    start: pd.Timestamp
    end: pd.Timestamp
    timestep_min: float
    rainfall_mm: np.ndarray
    duration_hours: float
    volume_mm: float
    average_intensity_mm_h: float
    maximum_intensity_mm_h: float


def extract_events(
    df: pd.DataFrame,
    timestep_min: float,
    ietd_hours: float = DEFAULT_IETD_HOURS,
    min_event_depth_mm: float = DEFAULT_MIN_EVENT_DEPTH_MM,
    min_records: int = DEFAULT_MIN_EVENT_RECORDS,
    max_event_duration_hours: float = DEFAULT_MAX_EVENT_DURATION_HOURS,
) -> List[RainfallEvent]:
    """Extract events by splitting wet clusters at dry gaps >= IETD."""
    if df.empty or not np.isfinite(timestep_min) or timestep_min <= 0:
        return []

    data = df.copy()
    data["datetime"] = pd.to_datetime(data["datetime"])
    rain_col = rainfall_column(data)
    rain = pd.to_numeric(data[rain_col], errors="coerce").to_numpy(dtype=float)
    wet_idx = np.flatnonzero(np.isfinite(rain) & (rain > 0))
    if wet_idx.size == 0:
        return []

    dry_gap_steps = np.diff(wet_idx) - 1
    dry_gap_hours = dry_gap_steps * timestep_min / 60.0
    split_pos = np.flatnonzero(dry_gap_hours >= ietd_hours)

    starts = np.r_[wet_idx[0], wet_idx[split_pos + 1]]
    ends = np.r_[wet_idx[split_pos], wet_idx[-1]]

    events = []  # type: List[RainfallEvent]
    for start_idx, end_idx in zip(starts, ends):
        event_rain = rain[start_idx : end_idx + 1]
        event_zero = np.where(np.isfinite(event_rain), event_rain, 0.0)
        volume_mm = float(np.sum(event_zero))
        duration_hours = float(event_zero.size * timestep_min / 60.0)

        if event_zero.size < min_records:
            continue
        if duration_hours > max_event_duration_hours:
            continue
        if volume_mm < min_event_depth_mm:
            continue

        max_depth = float(np.nanmax(event_rain)) if np.isfinite(event_rain).any() else float("nan")
        max_intensity = float(max_depth * 60.0 / timestep_min) if np.isfinite(max_depth) else float("nan")
        avg_intensity = float(volume_mm / duration_hours) if duration_hours > 0 else float("nan")

        events.append(
            RainfallEvent(
                start=pd.Timestamp(data["datetime"].iloc[start_idx]),
                end=pd.Timestamp(data["datetime"].iloc[end_idx]),
                timestep_min=float(timestep_min),
                rainfall_mm=event_rain.astype(float),
                duration_hours=duration_hours,
                volume_mm=volume_mm,
                average_intensity_mm_h=avg_intensity,
                maximum_intensity_mm_h=max_intensity,
            )
        )

    return events
