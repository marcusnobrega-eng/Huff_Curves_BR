"""Rainfall time-series cleaning and regularization."""

from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd

from .constants import (
    DEFAULT_DAILY_MIN_DEPTH_MM,
    DEFAULT_FIXED_DAY_START_HOUR,
    DEFAULT_MAX_INTENSITY_MM_H,
)


@dataclass(frozen=True)
class SeriesDiagnostics:
    timestep_min: float
    n_observations: int
    missing_fraction: float
    years_span: float
    first_timestamp: Optional[pd.Timestamp]
    last_timestamp: Optional[pd.Timestamp]
    has_full_zero_year: bool
    max_daily_mm: float


def infer_timestep_minutes(datetime_values: pd.Series) -> float:
    values = pd.to_datetime(datetime_values).dropna().sort_values().drop_duplicates()
    if values.size < 2:
        return float("nan")
    diffs = values.diff().dropna().dt.total_seconds().to_numpy() / 60.0
    diffs = diffs[np.isfinite(diffs) & (diffs > 0)]
    if diffs.size == 0:
        return float("nan")
    return float(np.median(diffs))


def rainfall_column(df: pd.DataFrame) -> str:
    """Return the rainfall depth column name, accepting the old intensity name."""
    if "rainfall_mm" in df.columns:
        return "rainfall_mm"
    if "rainfall_mm_h" in df.columns:
        return "rainfall_mm_h"
    raise ValueError("Input dataframe must contain a rainfall_mm column")


def regularize_series(df: pd.DataFrame, timestep_min: Optional[float] = None) -> pd.DataFrame:
    """Sort, de-duplicate, and place rainfall data on a fixed time grid."""
    if "datetime" not in df.columns:
        raise ValueError("Input dataframe must contain a datetime column")
    rain_col = rainfall_column(df)

    out = df[["datetime", rain_col]].rename(columns={rain_col: "rainfall_mm"}).copy()
    out["datetime"] = pd.to_datetime(out["datetime"], errors="coerce")
    out["rainfall_mm"] = pd.to_numeric(out["rainfall_mm"], errors="coerce")
    out = out.dropna(subset=["datetime"])
    out = out.sort_values("datetime").drop_duplicates(subset=["datetime"], keep="last")

    if out.empty:
        return pd.DataFrame(columns=["datetime", "rainfall_mm"])

    dt_min = float(timestep_min) if timestep_min is not None else infer_timestep_minutes(out["datetime"])
    if not np.isfinite(dt_min) or dt_min <= 0:
        return out.reset_index(drop=True)

    start = out["datetime"].iloc[0]
    end = out["datetime"].iloc[-1]
    grid = pd.date_range(start=start, end=end, freq=pd.Timedelta(minutes=dt_min))
    regular = pd.DataFrame({"datetime": grid})
    regular = regular.merge(out, on="datetime", how="left")
    return regular


def clean_rainfall_values(
    df: pd.DataFrame,
    max_intensity_mm_h: float = DEFAULT_MAX_INTENSITY_MM_H,
) -> pd.DataFrame:
    """Apply simple rainfall value QC."""
    out = df.copy()
    rain_col = rainfall_column(out)
    if rain_col != "rainfall_mm":
        out = out.rename(columns={rain_col: "rainfall_mm"})
    rain = pd.to_numeric(out["rainfall_mm"], errors="coerce")
    rain = rain.mask(rain < 0)
    if "datetime" in out.columns:
        timestep_min = infer_timestep_minutes(out["datetime"])
        if np.isfinite(timestep_min) and timestep_min > 0:
            max_depth_mm = max_intensity_mm_h * timestep_min / 60.0
            rain = rain.mask(rain > max_depth_mm)
    out["rainfall_mm"] = rain
    return out


def fixed_daily_volumes(
    df: pd.DataFrame,
    timestep_min: float,
    start_hour: int = DEFAULT_FIXED_DAY_START_HOUR,
    min_depth_mm: float = DEFAULT_DAILY_MIN_DEPTH_MM,
) -> pd.Series:
    """Compute fixed-window daily rainfall volumes starting at start_hour."""
    if df.empty or not np.isfinite(timestep_min) or timestep_min <= 0:
        return pd.Series(dtype=float)

    samples_per_day = int(round(24 * 60 / timestep_min))
    if samples_per_day <= 0:
        return pd.Series(dtype=float)

    data = df.copy()
    data["datetime"] = pd.to_datetime(data["datetime"])
    rain_col = rainfall_column(data)
    rain = pd.to_numeric(data[rain_col], errors="coerce").to_numpy(dtype=float)
    starts = data.index[
        (data["datetime"].dt.hour == start_hour)
        & (data["datetime"].dt.minute == 0)
        & (data["datetime"].dt.second == 0)
    ].to_numpy()

    volumes = []  # type: List[float]
    labels = []  # type: List[pd.Timestamp]
    for idx in starts:
        end_idx = idx + samples_per_day
        if end_idx > rain.size:
            continue
        window = rain[idx:end_idx]
        volume = float(np.nansum(window))
        if volume < min_depth_mm:
            volume = float("nan")
        volumes.append(volume)
        labels.append(pd.Timestamp(data["datetime"].iloc[idx]))

    return pd.Series(volumes, index=pd.DatetimeIndex(labels), name="daily_volume_mm", dtype=float)


def has_full_zero_calendar_year(df: pd.DataFrame, timestep_min: float, completeness: float = 0.95) -> bool:
    """Return true if a nearly complete calendar year has exactly zero valid rainfall."""
    if df.empty or not np.isfinite(timestep_min) or timestep_min <= 0:
        return False

    data = df.copy()
    data["datetime"] = pd.to_datetime(data["datetime"])
    rain_col = rainfall_column(data)
    rain = pd.to_numeric(data[rain_col], errors="coerce")
    samples_per_day = 24 * 60 / timestep_min

    for year, group in data.groupby(data["datetime"].dt.year):
        expected = (366 if pd.Timestamp(year=year, month=12, day=31).is_leap_year else 365) * samples_per_day
        valid = rain.loc[group.index].dropna()
        if len(group) >= completeness * expected and len(valid) >= completeness * expected and (valid == 0).all():
            return True
    return False


def diagnostics(df: pd.DataFrame, timestep_min: Optional[float] = None) -> SeriesDiagnostics:
    """Summarize a regularized rainfall series."""
    if df.empty:
        return SeriesDiagnostics(
            timestep_min=float("nan"),
            n_observations=0,
            missing_fraction=float("nan"),
            years_span=float("nan"),
            first_timestamp=None,
            last_timestamp=None,
            has_full_zero_year=False,
            max_daily_mm=float("nan"),
        )

    dt_min = float(timestep_min) if timestep_min is not None else infer_timestep_minutes(df["datetime"])
    rain_col = rainfall_column(df)
    rain = pd.to_numeric(df[rain_col], errors="coerce")
    first = pd.Timestamp(df["datetime"].min())
    last = pd.Timestamp(df["datetime"].max())
    years_span = float((last - first).days / 365.2425) if last >= first else float("nan")
    daily = fixed_daily_volumes(df, dt_min)
    max_daily = float(daily.max(skipna=True)) if not daily.empty else float("nan")

    return SeriesDiagnostics(
        timestep_min=dt_min,
        n_observations=int(len(df)),
        missing_fraction=float(rain.isna().mean()),
        years_span=years_span,
        first_timestamp=first,
        last_timestamp=last,
        has_full_zero_year=has_full_zero_calendar_year(df, dt_min),
        max_daily_mm=max_daily,
    )
