"""ANA telemetric sub-daily rainfall downloader."""

from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests

from .constants import ANA_ENDPOINT


@dataclass(frozen=True)
class AnaDownloadConfig:
    endpoint: str = ANA_ENDPOINT
    timeout_seconds: int = 60
    chunk_days: int = 90
    retries: int = 3
    retry_sleep_seconds: float = 3.0


def _format_ana_date(value: str | datetime | pd.Timestamp) -> str:
    ts = pd.Timestamp(value)
    return f"{ts.day}/{ts.month}/{ts.year}"


def iter_date_chunks(start: str | datetime, end: str | datetime, chunk_days: int) -> Iterable[tuple[pd.Timestamp, pd.Timestamp]]:
    """Yield inclusive date chunks for ANA requests."""
    start_ts = pd.Timestamp(start).normalize()
    end_ts = pd.Timestamp(end).normalize()
    if end_ts < start_ts:
        raise ValueError("end date must be on or after start date")
    if chunk_days < 1:
        raise ValueError("chunk_days must be positive")

    cur = start_ts
    while cur <= end_ts:
        nxt = min(cur + pd.Timedelta(days=chunk_days - 1), end_ts)
        yield cur, nxt
        cur = nxt + pd.Timedelta(days=1)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _text_as_float(text: str | None) -> float:
    if text is None:
        return float("nan")
    text = text.strip().replace(",", ".")
    if not text:
        return float("nan")
    try:
        return float(text)
    except ValueError:
        return float("nan")


def _text_as_datetime(text: str | None) -> pd.Timestamp:
    value = (text or "").strip()
    if not value:
        return pd.NaT

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
    ):
        parsed = pd.to_datetime(value, format=fmt, errors="coerce")
        if pd.notna(parsed):
            return pd.Timestamp(parsed)

    return pd.Timestamp(pd.to_datetime(value, errors="coerce", dayfirst=True))


def _parse_record_elements(root: ET.Element) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for elem in root.iter():
        children = list(elem)
        if not children:
            continue
        fields = {_local_name(child.tag): (child.text or "") for child in children}
        if "DataHora" in fields and ("Chuva" in fields or "Nivel" in fields or "Vazao" in fields):
            records.append(fields)
    return records


def _parse_ana_xml(text: str) -> pd.DataFrame:
    """Parse ANA XML text into a normalized dataframe.

    The service has historically returned simple XML. The regex fallback keeps
    the parser useful if the response is wrapped in an unexpected XML envelope.
    """
    records: list[dict[str, str]] = []
    try:
        root = ET.fromstring(text.encode("utf-8"))
        records = _parse_record_elements(root)
        if not records:
            embedded = "\n".join(part for part in root.itertext() if "<DataHora>" in part)
            if embedded:
                try:
                    records = _parse_record_elements(ET.fromstring(embedded.encode("utf-8")))
                except ET.ParseError:
                    records = []
    except ET.ParseError:
        records = []

    if not records:
        dates = re.findall(r"<DataHora>(.*?)</DataHora>", text, flags=re.IGNORECASE | re.DOTALL)
        codes = re.findall(r"<CodEstacao>(.*?)</CodEstacao>", text, flags=re.IGNORECASE | re.DOTALL)
        rain = re.findall(r"<Chuva>(.*?)</Chuva>|<Chuva\s*/>", text, flags=re.IGNORECASE | re.DOTALL)
        stage = re.findall(r"<Nivel>(.*?)</Nivel>|<Nivel\s*/>", text, flags=re.IGNORECASE | re.DOTALL)
        flow = re.findall(r"<Vazao>(.*?)</Vazao>|<Vazao\s*/>", text, flags=re.IGNORECASE | re.DOTALL)

        def pick(match: str | tuple[str, ...]) -> str:
            if isinstance(match, tuple):
                return next((x for x in match if x), "")
            return match

        n = len(dates)
        for idx in range(n):
            records.append(
                {
                    "CodEstacao": codes[idx] if idx < len(codes) else "",
                    "DataHora": dates[idx],
                    "Chuva": pick(rain[idx]) if idx < len(rain) else "",
                    "Nivel": pick(stage[idx]) if idx < len(stage) else "",
                    "Vazao": pick(flow[idx]) if idx < len(flow) else "",
                }
            )

    rows = []
    for rec in records:
        rows.append(
            {
                "station_id": str(rec.get("CodEstacao", "")).strip(),
                "datetime": _text_as_datetime(rec.get("DataHora")),
                "rainfall_mm": _text_as_float(rec.get("Chuva")),
                "stage_m": _text_as_float(rec.get("Nivel")),
                "flow_m3_s": _text_as_float(rec.get("Vazao")),
            }
        )

    df = pd.DataFrame(rows, columns=["station_id", "datetime", "rainfall_mm", "stage_m", "flow_m3_s"])
    df = df.dropna(subset=["datetime"])
    if not df.empty:
        df["station_id"] = df["station_id"].astype(str).str.replace(r"\.0$", "", regex=True)
        df = df.sort_values("datetime").drop_duplicates(subset=["datetime"], keep="last").reset_index(drop=True)
    return df


def fetch_station_chunk(
    station_id: str,
    start: str | datetime,
    end: str | datetime,
    config: AnaDownloadConfig | None = None,
) -> pd.DataFrame:
    """Fetch one station/date chunk from ANA."""
    cfg = config or AnaDownloadConfig()
    params = {
        "codEstacao": str(station_id),
        "dataInicio": _format_ana_date(start),
        "dataFim": _format_ana_date(end),
    }

    last_error: Exception | None = None
    for attempt in range(cfg.retries):
        try:
            response = requests.get(cfg.endpoint, params=params, timeout=cfg.timeout_seconds)
            if response.status_code == 429 and attempt < cfg.retries - 1:
                retry_after = _text_as_float(response.headers.get("Retry-After"))
                if not pd.notna(retry_after) or retry_after <= 0:
                    retry_after = cfg.retry_sleep_seconds * (attempt + 1) ** 2
                time.sleep(retry_after)
                continue
            response.raise_for_status()
            df = _parse_ana_xml(response.text)
            if not df.empty:
                df["station_id"] = str(station_id)
            return df
        except Exception as exc:  # pragma: no cover - network behavior
            last_error = exc
            if attempt < cfg.retries - 1:
                time.sleep(cfg.retry_sleep_seconds * (attempt + 1))

    raise RuntimeError(f"ANA request failed for station {station_id} from {start} to {end}: {last_error}") from last_error


def download_station(
    station_id: str,
    start: str | datetime,
    end: str | datetime,
    config: AnaDownloadConfig | None = None,
) -> pd.DataFrame:
    """Download a full station period by chunking ANA requests."""
    cfg = config or AnaDownloadConfig()
    frames = []
    for chunk_start, chunk_end in iter_date_chunks(start, end, cfg.chunk_days):
        chunk = fetch_station_chunk(station_id, chunk_start, chunk_end, cfg)
        if not chunk.empty:
            frames.append(chunk)

    if not frames:
        return pd.DataFrame(columns=["station_id", "datetime", "rainfall_mm", "stage_m", "flow_m3_s"])

    df = pd.concat(frames, ignore_index=True)
    df = df.sort_values("datetime").drop_duplicates(subset=["datetime"], keep="last").reset_index(drop=True)
    return df


def cache_path(raw_dir: str | Path, station_id: str) -> Path:
    return Path(raw_dir) / "ana" / f"{station_id}.csv"


def save_station_cache(df: pd.DataFrame, raw_dir: str | Path, station_id: str) -> Path:
    path = cache_path(raw_dir, station_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def load_station_cache(raw_dir: str | Path, station_id: str) -> pd.DataFrame:
    path = cache_path(raw_dir, station_id)
    if not path.exists():
        return pd.DataFrame(columns=["station_id", "datetime", "rainfall_mm", "stage_m", "flow_m3_s"])
    df = pd.read_csv(path, parse_dates=["datetime"])
    if "rainfall_mm_h" in df.columns and "rainfall_mm" not in df.columns:
        df = df.rename(columns={"rainfall_mm_h": "rainfall_mm"})
    if "station_id" in df.columns:
        df["station_id"] = df["station_id"].astype(str).str.replace(r"\.0$", "", regex=True)
    return df
