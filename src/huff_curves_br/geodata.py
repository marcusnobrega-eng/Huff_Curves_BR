"""Geospatial reference layers and station spatial joins."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import requests

from .constants import IBGE_BIOMES_2025_ZIP_URL, IBGE_LOCALIDADES_API, IBGE_MALHAS_API
from .reference import download_file, extract_zip


def _require_geopandas():
    try:
        import geopandas as gpd
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ImportError("Install the geo extra to use geospatial outputs: pip install -e '.[geo]'") from exc
    return gpd


def _geojson_url(intrarregiao: str | None = None, quality: str = "intermediaria") -> str:
    url = f"{IBGE_MALHAS_API}/paises/BR?formato=application/vnd.geo+json&qualidade={quality}"
    if intrarregiao:
        url = f"{url}&intrarregiao={intrarregiao}"
    return url


def _download_text(url: str, output_path: Path, overwrite: bool = False, timeout_seconds: int = 120) -> Path:
    if output_path.exists() and not overwrite:
        return output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    output_path.write_bytes(response.content)
    return output_path


def _download_json(url: str, timeout_seconds: int = 120) -> Any:
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    return response.json()


def _state_metadata() -> pd.DataFrame:
    records = _download_json(f"{IBGE_LOCALIDADES_API}/estados")
    rows = []
    for rec in records:
        rows.append(
            {
                "state_code": str(rec["id"]),
                "state_abbrev": rec.get("sigla"),
                "state_name": rec.get("nome"),
                "region_code": str(rec.get("regiao", {}).get("id", "")),
                "region_abbrev": rec.get("regiao", {}).get("sigla"),
                "region_name": rec.get("regiao", {}).get("nome"),
            }
        )
    return pd.DataFrame(rows)


def _municipality_metadata() -> pd.DataFrame:
    records = _download_json(f"{IBGE_LOCALIDADES_API}/municipios")
    rows = []
    for rec in records:
        microrregiao = rec.get("microrregiao") or {}
        mesorregiao = microrregiao.get("mesorregiao") or {}
        uf = mesorregiao.get("UF") or {}
        if not uf:
            imediata = rec.get("regiao-imediata") or {}
            intermediaria = imediata.get("regiao-intermediaria") or {}
            uf = intermediaria.get("UF") or {}
        region = uf.get("regiao", {})
        rows.append(
            {
                "municipality_code": str(rec["id"]),
                "municipality_name": rec.get("nome"),
                "state_code": str(uf.get("id", "")),
                "state_abbrev": uf.get("sigla"),
                "state_name": uf.get("nome"),
                "region_code": str(region.get("id", "")),
                "region_abbrev": region.get("sigla"),
                "region_name": region.get("nome"),
            }
        )
    return pd.DataFrame(rows)


def _normalize_states(states_geojson: Path, output_path: Path) -> Path:
    gpd = _require_geopandas()
    states = gpd.read_file(states_geojson).rename(columns={"codarea": "state_code"})
    states["state_code"] = states["state_code"].astype(str)
    states = states.merge(_state_metadata(), on="state_code", how="left")
    states = states.to_crs(4326)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    states.to_file(output_path, driver="GPKG")
    return output_path


def _normalize_municipalities(municipalities_geojson: Path, output_path: Path) -> Path:
    gpd = _require_geopandas()
    municipalities = gpd.read_file(municipalities_geojson).rename(columns={"codarea": "municipality_code"})
    municipalities["municipality_code"] = municipalities["municipality_code"].astype(str)
    municipalities = municipalities.merge(_municipality_metadata(), on="municipality_code", how="left")
    municipalities = municipalities.to_crs(4326)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    municipalities.to_file(output_path, driver="GPKG")
    return output_path


def _normalize_brazil(brazil_geojson: Path, output_path: Path) -> Path:
    gpd = _require_geopandas()
    brazil = gpd.read_file(brazil_geojson).to_crs(4326)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    brazil.to_file(output_path, driver="GPKG")
    return output_path


def _find_shapefile(path: Path) -> Path:
    candidates = sorted(path.rglob("*.shp"))
    if not candidates:
        raise FileNotFoundError(f"No shapefile found under {path}")
    terrestrial = [p for p in candidates if "sist" not in p.name.lower() and "mar" not in p.name.lower()]
    return terrestrial[0] if terrestrial else candidates[0]


def _choose_biome_name_column(columns: list[str]) -> str | None:
    preferred = ["NM_BIOMA", "NOME_BIOMA", "NOME", "NAME", "BIOMA", "BIOME"]
    lower_lookup = {c.lower(): c for c in columns}
    for candidate in preferred:
        if candidate.lower() in lower_lookup:
            return lower_lookup[candidate.lower()]
    text_candidates = [c for c in columns if "nome" in c.lower() or c.lower().startswith("nm_")]
    if text_candidates:
        return text_candidates[0]
    candidates = [c for c in columns if "bioma" in c.lower() and not c.lower().startswith(("cd", "id"))]
    return candidates[0] if candidates else None


def _normalize_biomes(shapefile_path: Path, output_path: Path) -> Path:
    gpd = _require_geopandas()
    biomes = gpd.read_file(shapefile_path).to_crs(4326)
    name_col = _choose_biome_name_column(list(biomes.columns))
    if name_col is None:
        object_cols = [c for c in biomes.columns if c != "geometry" and biomes[c].dtype == object]
        name_col = object_cols[0] if object_cols else None
    biomes["biome_name"] = biomes[name_col].astype(str) if name_col else "unknown"
    keep = ["biome_name", "geometry"]
    extra_cols = [c for c in biomes.columns if c not in keep and c != "geometry"]
    biomes = biomes[extra_cols[:6] + keep]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    biomes.to_file(output_path, driver="GPKG")
    return output_path


def download_ibge_reference_layers(
    reference_dir: str | Path = "data/reference/ibge",
    quality: str = "intermediaria",
    overwrite: bool = False,
) -> dict[str, Path]:
    """Download and normalize IBGE Brazil, state, municipality, and biome layers."""
    reference_dir = Path(reference_dir)
    downloads = reference_dir / "downloads"
    normalized = reference_dir / "normalized"

    brazil_geojson = _download_text(_geojson_url(quality=quality), downloads / "brazil.geojson", overwrite)
    states_geojson = _download_text(_geojson_url("UF", quality), downloads / "states.geojson", overwrite)
    municipalities_geojson = _download_text(
        _geojson_url("municipio", quality),
        downloads / "municipalities.geojson",
        overwrite,
        timeout_seconds=240,
    )
    biomes_zip = download_file(IBGE_BIOMES_2025_ZIP_URL, downloads / "biomes_2025.zip", overwrite=overwrite)
    biomes_extract_dir = downloads / "biomes_2025"
    if overwrite or not biomes_extract_dir.exists():
        extract_zip(biomes_zip, biomes_extract_dir, overwrite=overwrite)

    paths = {
        "brazil": _normalize_brazil(brazil_geojson, normalized / "brazil.gpkg"),
        "states": _normalize_states(states_geojson, normalized / "states.gpkg"),
        "municipalities": _normalize_municipalities(municipalities_geojson, normalized / "municipalities.gpkg"),
        "biomes": _normalize_biomes(_find_shapefile(biomes_extract_dir), normalized / "biomes.gpkg"),
    }
    return paths


def ibge_reference_paths(reference_dir: str | Path = "data/reference/ibge") -> dict[str, Path]:
    reference_dir = Path(reference_dir)
    normalized = reference_dir / "normalized"
    return {
        "brazil": normalized / "brazil.gpkg",
        "states": normalized / "states.gpkg",
        "municipalities": normalized / "municipalities.gpkg",
        "biomes": normalized / "biomes.gpkg",
    }


def load_ibge_reference_layers(reference_dir: str | Path = "data/reference/ibge") -> dict[str, object]:
    """Load normalized IBGE layers, downloading them first if needed."""
    gpd = _require_geopandas()
    paths = ibge_reference_paths(reference_dir)
    if not all(path.exists() for path in paths.values()):
        paths = download_ibge_reference_layers(reference_dir)
    return {name: gpd.read_file(path) for name, path in paths.items()}


def station_results_to_geodata(results: str | Path | pd.DataFrame):
    """Convert station results to a WGS84 GeoDataFrame."""
    gpd = _require_geopandas()
    df = pd.read_csv(results) if not isinstance(results, pd.DataFrame) else results.copy()
    df["station_id"] = df["station_id"].astype(str).str.replace(r"\.0$", "", regex=True)
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df = df.dropna(subset=["lon", "lat"])
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["lon"], df["lat"]), crs=4326)


def _spatial_join_columns(points, polygons, columns: list[str], suffix: str, fallback_distance_m: float = 75_000):
    gpd = _require_geopandas()
    right = polygons[columns + ["geometry"]].copy()
    right = right.to_crs(points.crs)
    joined = gpd.sjoin(points, right, how="left", predicate="within", rsuffix=suffix)
    index_cols = [c for c in joined.columns if c.startswith("index_")]
    joined = joined.drop(columns=index_cols, errors="ignore")

    if columns:
        missing = joined[columns[0]].isna()
        if missing.any():
            missing_points = points.loc[joined.index[missing]].copy()
            nearest = gpd.sjoin_nearest(
                missing_points.to_crs(3857),
                right.to_crs(3857),
                how="left",
                max_distance=fallback_distance_m,
                distance_col=f"{suffix}_distance_m",
                rsuffix=f"{suffix}_nearest",
            ).to_crs(points.crs)
            for col in columns:
                if col in nearest.columns:
                    joined.loc[nearest.index, col] = nearest[col]
    return joined


def enrich_station_geography(
    station_results: str | Path | pd.DataFrame,
    municipalities=None,
    states=None,
    biomes=None,
):
    """Attach municipality, state, region, and biome names to station result points."""
    points = station_results_to_geodata(station_results)
    if municipalities is not None:
        muni_cols = [
            "municipality_code",
            "municipality_name",
            "state_code",
            "state_abbrev",
            "state_name",
            "region_code",
            "region_abbrev",
            "region_name",
        ]
        points = _spatial_join_columns(points, municipalities, [c for c in muni_cols if c in municipalities.columns], "muni")
    elif states is not None:
        state_cols = ["state_code", "state_abbrev", "state_name", "region_code", "region_abbrev", "region_name"]
        points = _spatial_join_columns(points, states, [c for c in state_cols if c in states.columns], "state")

    if biomes is not None:
        biome_cols = ["biome_name"]
        points = _spatial_join_columns(points, biomes, [c for c in biome_cols if c in biomes.columns], "biome")

    return points
