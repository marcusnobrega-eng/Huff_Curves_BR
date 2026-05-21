"""Map outputs for station-level Huff results."""

from __future__ import annotations

import os
import tempfile
import warnings
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "huff_curves_br_mpl"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DOMINANT_QUARTILE_COLORS = {
    1: "#2b83ba",
    2: "#abdda4",
    3: "#fdae61",
    4: "#d7191c",
}


def _read_results(results: str | Path | pd.DataFrame) -> pd.DataFrame:
    if isinstance(results, pd.DataFrame):
        return results.copy()
    return pd.read_csv(results)


def _load_layer(path: str | Path | None):
    if path is None:
        return None
    try:
        import geopandas as gpd
    except ImportError:
        warnings.warn("geopandas is not installed; reference shapefiles will not be drawn", stacklevel=2)
        return None

    layer = gpd.read_file(path)
    if layer.empty:
        return layer
    if layer.crs is not None and layer.crs.to_epsg() != 4326:
        layer = layer.to_crs(4326)
    return layer


def _prepare_axes(ax, boundary_path: str | Path | None, biomes_path: str | Path | None) -> None:
    biomes = _load_layer(biomes_path)
    boundary = _load_layer(boundary_path)

    if biomes is not None and not biomes.empty:
        biomes.plot(ax=ax, facecolor="#f2efe6", edgecolor="#d8d2c4", linewidth=0.35)
    if boundary is not None and not boundary.empty:
        boundary.boundary.plot(ax=ax, color="#3b3b3b", linewidth=0.8)
    else:
        ax.set_xlim(-75, -30)
        ax.set_ylim(-35, 7)

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True, color="#e6e6e6", linewidth=0.5)
    ax.set_aspect("equal", adjustable="box")


def _prepare_axes_with_layers(ax, boundary=None, biomes=None) -> None:
    if biomes is not None and not biomes.empty:
        biomes.plot(ax=ax, facecolor="#f5f1e8", edgecolor="#d6cfc1", linewidth=0.25)
    if boundary is not None and not boundary.empty:
        boundary.boundary.plot(ax=ax, color="#303030", linewidth=0.6)
    else:
        ax.set_xlim(-75, -30)
        ax.set_ylim(-35, 7)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect("equal", adjustable="box")


def _valid_station_points(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    if "lon" not in data.columns:
        data["lon"] = np.nan
    if "lat" not in data.columns:
        data["lat"] = np.nan
    data["lon"] = pd.to_numeric(data["lon"], errors="coerce")
    data["lat"] = pd.to_numeric(data["lat"], errors="coerce")
    return data.dropna(subset=["lon", "lat"])


def plot_dominant_quartile_map(
    results: str | Path | pd.DataFrame,
    output_path: str | Path,
    boundary_path: str | Path | None = None,
    biomes_path: str | Path | None = None,
) -> Path:
    """Plot the dominant Huff quartile for each successfully processed station."""
    df = _valid_station_points(_read_results(results))
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(9, 9))
    _prepare_axes(ax, boundary_path, biomes_path)
    ax.set_title("Dominant Empirical Huff Quartile")

    plotted = False
    if "dominant_quartile" in df.columns:
        dominant = pd.to_numeric(df["dominant_quartile"], errors="coerce")
    else:
        dominant = pd.Series(np.nan, index=df.index)
    for quartile, color in DOMINANT_QUARTILE_COLORS.items():
        subset = df[dominant == quartile]
        if subset.empty:
            continue
        ax.scatter(
            subset["lon"],
            subset["lat"],
            s=28,
            c=color,
            label=f"Q{quartile}",
            edgecolors="white",
            linewidths=0.4,
            alpha=0.9,
        )
        plotted = True

    if plotted:
        ax.legend(title="Quartile", loc="lower left", frameon=True)
    else:
        ax.text(0.5, 0.5, "No valid station results", transform=ax.transAxes, ha="center", va="center")

    fig.tight_layout()
    fig.savefig(output, dpi=220)
    plt.close(fig)
    return output


def plot_numeric_station_map(
    results: str | Path | pd.DataFrame,
    column: str,
    output_path: str | Path,
    title: str | None = None,
    boundary_path: str | Path | None = None,
    biomes_path: str | Path | None = None,
    cmap: str = "viridis",
) -> Path:
    """Plot a numeric station-level result column."""
    df = _valid_station_points(_read_results(results))
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(9, 9))
    _prepare_axes(ax, boundary_path, biomes_path)
    ax.set_title(title or column)

    if column not in df.columns:
        ax.text(0.5, 0.5, f"Missing column: {column}", transform=ax.transAxes, ha="center", va="center")
    else:
        values = pd.to_numeric(df[column], errors="coerce")
        valid = df[np.isfinite(values)].copy()
        values = values[np.isfinite(values)]
        if valid.empty:
            ax.text(0.5, 0.5, f"No valid values for {column}", transform=ax.transAxes, ha="center", va="center")
        else:
            scatter = ax.scatter(
                valid["lon"],
                valid["lat"],
                c=values,
                s=30,
                cmap=cmap,
                edgecolors="white",
                linewidths=0.4,
                alpha=0.9,
            )
            cbar = fig.colorbar(scatter, ax=ax, shrink=0.7)
            cbar.set_label(column)

    fig.tight_layout()
    fig.savefig(output, dpi=220)
    plt.close(fig)
    return output


def plot_station_maps(
    results: str | Path | pd.DataFrame,
    output_dir: str | Path,
    boundary_path: str | Path | None = None,
    biomes_path: str | Path | None = None,
) -> dict[str, Path]:
    """Generate the standard map set from the station result table."""
    output_dir = Path(output_dir)
    paths = {
        "dominant_quartile": plot_dominant_quartile_map(
            results,
            output_dir / "map_dominant_quartile.png",
            boundary_path=boundary_path,
            biomes_path=biomes_path,
        ),
        "kge_mean": plot_numeric_station_map(
            results,
            "kge_mean",
            output_dir / "map_kge_mean.png",
            title="Mean KGE Against Original Huff Curves",
            boundary_path=boundary_path,
            biomes_path=biomes_path,
            cmap="magma",
        ),
        "n_events": plot_numeric_station_map(
            results,
            "n_events",
            output_dir / "map_event_count.png",
            title="Number of Rainfall Events",
            boundary_path=boundary_path,
            biomes_path=biomes_path,
            cmap="cividis",
        ),
    }
    return paths


def _station_intensity(df: pd.DataFrame) -> pd.Series:
    intensity_cols = [f"q{q}_max_intensity_mm_h" for q in range(1, 5) if f"q{q}_max_intensity_mm_h" in df.columns]
    if not intensity_cols:
        return pd.Series(np.nan, index=df.index)
    return df[intensity_cols].apply(pd.to_numeric, errors="coerce").max(axis=1, skipna=True)


def plot_station_diagnostic_panel(
    results: str | Path | pd.DataFrame,
    output_path: str | Path,
    boundary_path: str | Path | None = None,
    biomes_path: str | Path | None = None,
) -> Path:
    """Create a multi-panel diagnostic map for the station Huff dataset."""
    df = _valid_station_points(_read_results(results))
    df["max_intensity_mm_h"] = _station_intensity(df)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    boundary = _load_layer(boundary_path)
    biomes = _load_layer(biomes_path)

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.ravel()

    _prepare_axes_with_layers(axes[0], boundary, biomes)
    dominant = pd.to_numeric(df["dominant_quartile"], errors="coerce") if "dominant_quartile" in df.columns else pd.Series(np.nan, index=df.index)
    plotted = False
    for quartile, color in DOMINANT_QUARTILE_COLORS.items():
        subset = df[dominant == quartile]
        if subset.empty:
            continue
        axes[0].scatter(subset["lon"], subset["lat"], s=10, c=color, label=f"Q{quartile}", alpha=0.85, linewidths=0)
        plotted = True
    axes[0].set_title("Dominant Quartile")
    if plotted:
        axes[0].legend(loc="lower left", fontsize=8, frameon=True)

    numeric_specs = [
        ("max_intensity_mm_h", "Max Event Intensity (mm/h)", "inferno"),
        ("n_events", "Events Used", "viridis"),
        ("years_span", "Years Available", "cividis"),
        ("kge_mean", "Mean KGE vs Huff", "magma"),
        ("missing_fraction", "Missing Fraction", "plasma_r"),
    ]
    for ax, (column, title, cmap) in zip(axes[1:], numeric_specs):
        _prepare_axes_with_layers(ax, boundary, biomes)
        values = pd.to_numeric(df[column], errors="coerce") if column in df.columns else pd.Series(np.nan, index=df.index)
        valid = df[np.isfinite(values)]
        values = values[np.isfinite(values)]
        if valid.empty:
            ax.text(0.5, 0.5, "No valid values", transform=ax.transAxes, ha="center", va="center")
        else:
            scatter = ax.scatter(
                valid["lon"],
                valid["lat"],
                c=values,
                s=9,
                cmap=cmap,
                alpha=0.85,
                linewidths=0,
            )
            cbar = fig.colorbar(scatter, ax=ax, shrink=0.75)
            cbar.ax.tick_params(labelsize=8)
        ax.set_title(title)

    fig.tight_layout()
    fig.savefig(output, dpi=240)
    plt.close(fig)
    return output


def plot_region_choropleth(
    regions,
    column: str,
    output_path: str | Path,
    title: str | None = None,
    cmap: str = "viridis",
    categorical: bool = False,
) -> Path:
    """Plot a regional GeoDataFrame column."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    gdf = regions.copy()
    fig, ax = plt.subplots(figsize=(9, 9))
    if categorical:
        gdf.plot(column=column, categorical=True, legend=True, ax=ax, edgecolor="#ffffff", linewidth=0.15)
    else:
        gdf[column] = pd.to_numeric(gdf[column], errors="coerce") if column in gdf.columns else np.nan
        gdf.plot(column=column, legend=True, ax=ax, cmap=cmap, edgecolor="#ffffff", linewidth=0.15)
    ax.set_title(title or column)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(output, dpi=220)
    plt.close(fig)
    return output
