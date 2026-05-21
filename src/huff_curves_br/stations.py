"""Station catalog loading and normalization."""

from pathlib import Path
from typing import Dict, Optional, Union

import pandas as pd


STATION_COLUMNS = {
    "Codigo": "station_id",
    "codigo": "station_id",
    "Code": "station_id",
    "Lat": "lat",
    "Latitude": "lat",
    "latitude": "lat",
    "Lon": "lon",
    "Longitude": "lon",
    "longitude": "lon",
    "Area": "area_km2",
    "area": "area_km2",
}


def load_station_catalog(path: Union[str, Path], limit: Optional[int] = None) -> pd.DataFrame:
    """Load a station catalog with station id, latitude, longitude, and optional area."""
    path = Path(path)
    df = pd.read_csv(path)
    df = df.rename(columns={c: STATION_COLUMNS.get(c, c) for c in df.columns})

    required = {"station_id", "lat", "lon"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Station catalog is missing required columns: {sorted(missing)}")

    out = df.copy()
    out["station_id"] = out["station_id"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    out["lat"] = pd.to_numeric(out["lat"], errors="coerce")
    out["lon"] = pd.to_numeric(out["lon"], errors="coerce")

    if "area_km2" in out.columns:
        out["area_km2"] = pd.to_numeric(out["area_km2"], errors="coerce")

    out = out.dropna(subset=["station_id", "lat", "lon"])
    out = out[out["station_id"] != ""]
    out = out.drop_duplicates(subset=["station_id"], keep="first")
    out = out.reset_index(drop=True)

    if limit is not None:
        out = out.head(limit).copy()

    return out


def station_record(row: pd.Series) -> Dict[str, object]:
    """Convert a station catalog row to a plain dictionary."""
    return {
        "station_id": str(row["station_id"]),
        "lat": float(row["lat"]),
        "lon": float(row["lon"]),
        "area_km2": float(row["area_km2"]) if "area_km2" in row and pd.notna(row["area_km2"]) else None,
    }
