r"""Map coastal q90 fields for waves, dynamic sea level, and FES2022 tide.

The quantiles are calculated independently at each native WAVERYS-grid point
used by the production compound-event catalogue.  Values are then assigned to
short Natural Earth coastline segments only for display; there is no spatial
interpolation, normalization, or change of units.

Run from the repository root:

    python src/exploratory/make_exploratory_q90_hs_zos_fes_coastal_map.py

For layout-only iterations after the native-grid table has been generated:

    python src/exploratory/make_exploratory_q90_hs_zos_fes_coastal_map.py \
        --reuse-data
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from functools import lru_cache
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import cartopy.crs as ccrs
from cartopy.io import shapereader
import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.ticker import FixedLocator, FormatStrFormatter, MaxNLocator
import numpy as np
import pandas as pd
from shapely.geometry import MultiLineString
from shapely.ops import linemerge, unary_union
import xarray as xr

from src.risk_integration.coastal_projection import (
    COASTAL_MAP_EXTENT,
    line_parts,
    project_values_to_coastline,
    read_coastal_inputs,
)


DEFAULT_INPUT = (
    ROOT / "data" / "unified" / "metocean_brazil_unified_waverys_grid.nc"
)
DEFAULT_GRID_SOURCE = (
    ROOT / "outputs" / "storm_catalog" / "compound" / "compound_metrics.csv"
)
DEFAULT_OUTPUT_DIR = (
    ROOT / "outputs" / "exploratory_q90_hs_zos_fes_coastal"
)

QUANTILE = 0.90
MIN_VALID_FRACTION = 0.80
VARIABLES = ("VHM0", "zos", "tide_daily_max")
VALUE_FIELDS = (
    "hs_q90_m",
    "zos_q90_m",
    "fes_tide_daily_max_q90_m",
)
PANEL_SPECS = (
    {
        "field": "hs_q90_m",
        "variable": "VHM0",
        "panel": "A",
        "title": r"$H_s$",
        "colorbar_label": r"$q_{90}(H_s)$ (m)",
        "colormap": "magma",
        "sample_range": (0.10, 0.92),
        "tick_format": "%.2f",
    },
    {
        "field": "zos_q90_m",
        "variable": "zos",
        "panel": "B",
        "title": r"$zos$",
        "colorbar_label": r"$q_{90}(zos)$ (m)",
        "colormap": "PuBuGn",
        "sample_range": (0.18, 0.95),
        "tick_format": "%.2f",
    },
    {
        "field": "fes_tide_daily_max_q90_m",
        "variable": "tide_daily_max",
        "panel": "C",
        "title": "FES2022 tide",
        "colorbar_label": r"$q_{90}(\mathrm{daily\ maximum\ tide})$ (m)",
        "colormap": "viridis",
        "sample_range": (0.08, 0.94),
        "tick_format": "%.1f",
    },
)

CONTEXT_EXTENT = (-74.5, -32.0, -35.5, 7.0)
LAND_COLOR = "#ddddda"
OCEAN_COLOR = "#e9f3f7"
STATE_BORDER_COLOR = "#92928e"
COUNTRY_BORDER_COLOR = "#555553"
COAST_COLOR = "#334155"
GRID_COLOR = "#9aa9b0"
OUTPUT_CRS = "EPSG:4326"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Calculate and map coastal q90 values of Hs, zos, and the "
            "FES2022 daily-maximum astronomical tide."
        )
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument(
        "--grid-source",
        type=Path,
        default=DEFAULT_GRID_SOURCE,
        help=(
            "Production table defining the native coastal grid points. "
            "Only grid_lat and grid_lon are used."
        ),
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dpi", type=int, default=180)
    parser.add_argument(
        "--reuse-data",
        action="store_true",
        help=(
            "Reuse the previously generated native-grid q90 CSV and skip "
            "the relatively expensive NetCDF quantile calculation."
        ),
    )
    return parser.parse_args()


def _relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def _numeric_stats(values: pd.Series | np.ndarray) -> dict[str, Any]:
    numeric = pd.to_numeric(pd.Series(values), errors="coerce").dropna()
    if numeric.empty:
        return {
            "count": 0,
            "min": None,
            "mean": None,
            "median": None,
            "max": None,
        }
    return {
        "count": int(numeric.count()),
        "min": round(float(numeric.min()), 6),
        "mean": round(float(numeric.mean()), 6),
        "median": round(float(numeric.median()), 6),
        "max": round(float(numeric.max()), 6),
    }


def _read_native_grid_coordinates(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    source = pd.read_csv(path)
    required = {"grid_lat", "grid_lon"}
    missing = sorted(required.difference(source.columns))
    if missing:
        raise ValueError(
            f"{path} lacks required column(s): {', '.join(missing)}"
        )
    grid = (
        source[["grid_lat", "grid_lon"]]
        .apply(pd.to_numeric, errors="coerce")
        .dropna()
        .drop_duplicates()
        .sort_values(["grid_lat", "grid_lon"])
        .reset_index(drop=True)
    )
    if grid.empty:
        raise RuntimeError(f"No valid grid coordinates found in {path}")
    return grid


def _nearest_indices(
    coordinate: np.ndarray,
    targets: np.ndarray,
    *,
    name: str,
) -> np.ndarray:
    indices = np.abs(coordinate[:, None] - targets[None, :]).argmin(axis=0)
    errors = np.abs(coordinate[indices] - targets)
    tolerance = max(0.051, float(np.median(np.diff(coordinate))) / 2.0 + 1e-4)
    if np.any(errors > tolerance):
        bad = np.flatnonzero(errors > tolerance)[:5]
        details = ", ".join(
            f"{targets[index]:.4f}->{coordinate[indices[index]]:.4f}"
            for index in bad
        )
        raise ValueError(
            f"Some {name} targets do not match the NetCDF grid: {details}"
        )
    return indices.astype(int)


def _calculate_native_quantiles(
    input_path: Path,
    grid_source: Path,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if not input_path.exists():
        raise FileNotFoundError(input_path)
    grid = _read_native_grid_coordinates(grid_source)
    print(
        f"Opening {_relative(input_path)} for {len(grid)} native points",
        flush=True,
    )
    with xr.open_dataset(input_path) as dataset:
        missing = sorted(set(VARIABLES).difference(dataset.data_vars))
        if missing:
            raise ValueError(
                "Unified dataset lacks required variable(s): "
                + ", ".join(missing)
            )
        for dimension in ("time", "latitude", "longitude"):
            if dimension not in dataset.dims:
                raise ValueError(
                    f"Unified dataset lacks required dimension {dimension!r}"
                )

        latitude = dataset["latitude"].values.astype(float)
        longitude = dataset["longitude"].values.astype(float)
        lat_index = _nearest_indices(
            latitude,
            grid["grid_lat"].to_numpy(dtype=float),
            name="latitude",
        )
        lon_index = _nearest_indices(
            longitude,
            grid["grid_lon"].to_numpy(dtype=float),
            name="longitude",
        )
        point_indexers = {
            "latitude": xr.DataArray(lat_index, dims="point"),
            "longitude": xr.DataArray(lon_index, dims="point"),
        }

        quantiles: dict[str, np.ndarray] = {}
        valid_fractions: dict[str, np.ndarray] = {}
        variable_metadata: dict[str, Any] = {}
        for variable, field in zip(VARIABLES, VALUE_FIELDS):
            print(
                f"Calculating q{int(QUANTILE * 100)} for {variable} ...",
                flush=True,
            )
            values = dataset[variable].isel(**point_indexers).values
            valid_fraction = np.mean(np.isfinite(values), axis=0)
            with np.errstate(all="ignore"):
                quantile = np.nanquantile(
                    values,
                    QUANTILE,
                    axis=0,
                    method="linear",
                )
            quantiles[field] = quantile.astype(float)
            valid_fractions[f"{variable}_valid_fraction"] = (
                valid_fraction.astype(float)
            )
            variable_metadata[variable] = {
                "source_variable": variable,
                "source_attributes": {
                    key: (
                        value.item()
                        if isinstance(value, np.generic)
                        else value
                    )
                    for key, value in dataset[variable].attrs.items()
                },
                "native_grid_q90_statistics_before_coverage_filter": (
                    _numeric_stats(quantile)
                ),
            }
            del values

        common_valid = np.ones(len(grid), dtype=bool)
        for variable in VARIABLES:
            common_valid &= (
                valid_fractions[f"{variable}_valid_fraction"]
                >= MIN_VALID_FRACTION
            )
        for field in VALUE_FIELDS:
            common_valid &= np.isfinite(quantiles[field])
        if not np.any(common_valid):
            raise RuntimeError(
                "No native grid point has adequate coverage in all variables"
            )

        output = grid.loc[common_valid].reset_index(drop=True).copy()
        for field in VALUE_FIELDS:
            output[field] = quantiles[field][common_valid]
        for field, values in valid_fractions.items():
            output[field] = values[common_valid]

        times = pd.to_datetime(dataset["time"].values)
        metadata = {
            "input": _relative(input_path),
            "input_size_bytes": int(input_path.stat().st_size),
            "grid_source": _relative(grid_source),
            "quantile": QUANTILE,
            "quantile_method": "numpy.nanquantile(method='linear')",
            "quantile_dimension": "time",
            "minimum_valid_fraction": MIN_VALID_FRACTION,
            "candidate_grid_points": int(len(grid)),
            "retained_grid_points": int(len(output)),
            "time_steps": int(dataset.sizes["time"]),
            "period_start": times.min().date().isoformat(),
            "period_end": times.max().date().isoformat(),
            "daily_series_conventions": {
                "VHM0": (
                    "WAVERYS significant wave height; daily maximum retained "
                    "from the original 3-hourly source during preprocessing"
                ),
                "zos": "GLORYS12 daily sea-surface height at 00:00 UTC",
                "tide_daily_max": (
                    "FES2022 evaluated hourly from 00:00 to 23:00 UTC; "
                    "daily maximum retained"
                ),
            },
            "variables": variable_metadata,
        }
    return output, metadata


def _geometry_intersects_extent(
    geometry: object,
    extent: tuple[float, float, float, float],
) -> bool:
    minx, miny, maxx, maxy = geometry.bounds
    west, east, south, north = extent
    return not (
        maxx < west or minx > east or maxy < south or miny > north
    )


@lru_cache(maxsize=1)
def _natural_earth_context() -> tuple[
    tuple[object, ...],
    tuple[object, ...],
    tuple[object, ...],
]:
    land_path = shapereader.natural_earth(
        resolution="10m",
        category="physical",
        name="land",
    )
    country_path = shapereader.natural_earth(
        resolution="10m",
        category="cultural",
        name="admin_0_boundary_lines_land",
    )
    state_path = shapereader.natural_earth(
        resolution="10m",
        category="cultural",
        name="admin_1_states_provinces_lines",
    )
    land = tuple(
        geometry
        for geometry in shapereader.Reader(land_path).geometries()
        if _geometry_intersects_extent(geometry, CONTEXT_EXTENT)
    )
    countries = tuple(
        geometry
        for geometry in shapereader.Reader(country_path).geometries()
        if _geometry_intersects_extent(geometry, CONTEXT_EXTENT)
    )
    states = tuple(
        record.geometry
        for record in shapereader.Reader(state_path).records()
        if record.attributes.get("ADM0_NAME") == "Brazil"
        and _geometry_intersects_extent(record.geometry, CONTEXT_EXTENT)
    )
    return land, countries, states


def _nice_boundaries(values: pd.Series, target_classes: int = 9) -> np.ndarray:
    finite = pd.to_numeric(values, errors="coerce").dropna().to_numpy()
    if finite.size == 0:
        raise ValueError("Cannot define color classes from empty values")
    minimum = float(np.min(finite))
    maximum = float(np.max(finite))
    if np.isclose(minimum, maximum):
        padding = max(abs(minimum) * 0.05, 0.01)
        minimum -= padding
        maximum += padding
    locator = MaxNLocator(
        nbins=target_classes,
        min_n_ticks=7,
        steps=[1.0, 2.0, 2.5, 5.0, 10.0],
    )
    boundaries = np.asarray(locator.tick_values(minimum, maximum), dtype=float)
    if len(boundaries) < 7:
        boundaries = np.linspace(minimum, maximum, target_classes + 1)
    return boundaries


def _discrete_colormap(
    name: str,
    class_count: int,
    sample_range: tuple[float, float],
) -> ListedColormap:
    base = matplotlib.colormaps[name]
    samples = np.linspace(sample_range[0], sample_range[1], class_count)
    return ListedColormap(
        [matplotlib.colors.to_hex(base(value)) for value in samples],
        name=f"{name}_discrete_{class_count}",
    )


def _setup_axis(
    axis: plt.Axes,
    *,
    panel: str,
    title: str,
    draw_left_labels: bool,
) -> None:
    crs = ccrs.PlateCarree()
    land, countries, states = _natural_earth_context()
    axis.set_facecolor(OCEAN_COLOR)
    axis.add_geometries(
        land,
        crs=crs,
        facecolor=LAND_COLOR,
        edgecolor="none",
        zorder=0.5,
    )
    axis.add_geometries(
        states,
        crs=crs,
        facecolor="none",
        edgecolor=STATE_BORDER_COLOR,
        linewidth=0.42,
        zorder=4.5,
    )
    axis.add_geometries(
        countries,
        crs=crs,
        facecolor="none",
        edgecolor=COUNTRY_BORDER_COLOR,
        linewidth=0.70,
        zorder=4.7,
    )
    axis.set_extent(COASTAL_MAP_EXTENT, crs=crs)
    grid = axis.gridlines(
        crs=crs,
        draw_labels=True,
        linewidth=0.35,
        color=GRID_COLOR,
        alpha=0.55,
        linestyle="--",
        zorder=1.2,
    )
    grid.xlocator = FixedLocator(np.arange(-55.0, -29.9, 5.0))
    grid.ylocator = FixedLocator(np.arange(-35.0, 10.0, 5.0))
    grid.top_labels = False
    grid.right_labels = False
    grid.left_labels = draw_left_labels
    grid.bottom_labels = True
    grid.xlabel_style = {"size": 8.5, "color": "#374151"}
    grid.ylabel_style = {"size": 8.5, "color": "#374151"}
    axis.set_title(title, fontsize=11.0, fontweight="bold", pad=6)
    axis.text(
        0.018,
        0.975,
        panel,
        transform=axis.transAxes,
        ha="left",
        va="top",
        fontsize=11,
        fontweight="bold",
        bbox={
            "boxstyle": "round,pad=0.25",
            "facecolor": "white",
            "edgecolor": "#cbd5e1",
            "alpha": 0.94,
        },
        zorder=10,
    )


def _plot_coastal_field(
    axis: plt.Axes,
    segments: gpd.GeoDataFrame,
    coastline: gpd.GeoDataFrame,
    *,
    field: str,
    panel: str,
    title: str,
    cmap: ListedColormap,
    boundaries: np.ndarray,
    draw_left_labels: bool,
) -> None:
    _setup_axis(
        axis,
        panel=panel,
        title=title,
        draw_left_labels=draw_left_labels,
    )
    axis.add_geometries(
        coastline.geometry,
        crs=ccrs.PlateCarree(),
        facecolor="none",
        edgecolor=COAST_COLOR,
        linewidth=0.45,
        zorder=5.0,
    )
    values = segments[field].to_numpy(dtype=float)
    class_indices = np.digitize(values, boundaries[1:-1])
    for class_index in range(len(boundaries) - 1):
        geometries = segments.geometry[
            class_indices == class_index
        ].tolist()
        if not geometries:
            continue
        dissolved = unary_union(geometries)
        merged = (
            linemerge(dissolved)
            if isinstance(dissolved, MultiLineString)
            else dissolved
        )
        axis.add_geometries(
            line_parts(merged),
            crs=ccrs.PlateCarree(),
            facecolor="none",
            edgecolor=cmap(class_index),
            linewidth=3.8,
            zorder=8.0,
        )
    axis.set_extent(COASTAL_MAP_EXTENT, crs=ccrs.PlateCarree())


def _add_colorbar(
    figure: plt.Figure,
    axis: plt.Axes,
    *,
    cmap: ListedColormap,
    boundaries: np.ndarray,
    label: str,
    tick_format: str,
) -> None:
    position = axis.get_position()
    colorbar_axis = figure.add_axes(
        [position.x0, position.y0 - 0.058, position.width, 0.016]
    )
    norm = BoundaryNorm(boundaries, cmap.N, clip=True)
    mappable = ScalarMappable(norm=norm, cmap=cmap)
    mappable.set_array([])
    colorbar = figure.colorbar(
        mappable,
        cax=colorbar_axis,
        orientation="horizontal",
        boundaries=boundaries,
        ticks=boundaries,
        spacing="uniform",
        drawedges=True,
    )
    colorbar.set_label(label, fontsize=9.2, labelpad=2.5)
    colorbar.ax.xaxis.set_major_formatter(FormatStrFormatter(tick_format))
    colorbar.ax.tick_params(labelsize=7.7, length=2.8)
    colorbar.outline.set_linewidth(0.7)


def _plot_figure(
    segments: gpd.GeoDataFrame,
    coastline: gpd.GeoDataFrame,
    output_path: Path,
    dpi: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    figure, axes = plt.subplots(
        1,
        3,
        figsize=(10.8, 6.8),
        constrained_layout=False,
        subplot_kw={"projection": ccrs.PlateCarree()},
    )
    figure.subplots_adjust(
        left=0.045,
        right=0.99,
        top=0.965,
        bottom=0.125,
        wspace=0.025,
    )
    colorbar_metadata: dict[str, Any] = {}
    panel_metadata: dict[str, Any] = {}
    colorbar_objects: list[
        tuple[plt.Axes, ListedColormap, np.ndarray, dict[str, Any]]
    ] = []
    for index, (axis, spec) in enumerate(zip(axes, PANEL_SPECS)):
        boundaries = _nice_boundaries(segments[spec["field"]])
        cmap = _discrete_colormap(
            spec["colormap"],
            len(boundaries) - 1,
            spec["sample_range"],
        )
        _plot_coastal_field(
            axis,
            segments,
            coastline,
            field=spec["field"],
            panel=spec["panel"],
            title=spec["title"],
            cmap=cmap,
            boundaries=boundaries,
            draw_left_labels=index == 0,
        )
        panel_metadata[spec["panel"]] = {
            "field": spec["field"],
            "source_variable": spec["variable"],
            "title": spec["title"],
            "statistics_on_coastline_segments": _numeric_stats(
                segments[spec["field"]]
            ),
        }
        colorbar_objects.append((axis, cmap, boundaries, spec))
        colorbar_metadata[spec["panel"]] = {
            "type": "discrete",
            "boundaries": boundaries.tolist(),
            "colors": list(cmap.colors),
            "source_colormap": spec["colormap"],
            "source_sample_range": list(spec["sample_range"]),
            "label": spec["colorbar_label"],
        }

    figure.canvas.draw()
    for axis, cmap, boundaries, spec in colorbar_objects:
        _add_colorbar(
            figure,
            axis,
            cmap=cmap,
            boundaries=boundaries,
            label=spec["colorbar_label"],
            tick_format=spec["tick_format"],
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        output_path,
        dpi=dpi,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(figure)
    return panel_metadata, colorbar_metadata


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    figure_path = output_dir / "figures" / "q90_hs_zos_fes_coastal.png"
    native_data_path = (
        output_dir / "data" / "q90_hs_zos_fes_native_grid.csv"
    )
    segment_data_path = (
        output_dir / "data" / "q90_hs_zos_fes_coastal_segments.geojson"
    )
    metadata_path = (
        output_dir / "metadata" / "q90_hs_zos_fes_metadata.json"
    )
    for directory in (
        figure_path.parent,
        native_data_path.parent,
        metadata_path.parent,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    if args.reuse_data:
        if not native_data_path.exists():
            raise FileNotFoundError(
                f"--reuse-data requested but {native_data_path} is absent"
            )
        native_grid = pd.read_csv(native_data_path)
        quantile_metadata: dict[str, Any] = {
            "reused_native_grid_table": _relative(native_data_path),
            "warning": (
                "The q90 values were not recalculated during this run. "
                "See the original metadata for their source details."
            ),
        }
    else:
        native_grid, quantile_metadata = _calculate_native_quantiles(
            args.input.resolve(),
            args.grid_source.resolve(),
        )
        native_grid.to_csv(
            native_data_path,
            index=False,
            float_format="%.7f",
        )

    missing = sorted(
        {"grid_lat", "grid_lon", *VALUE_FIELDS}.difference(
            native_grid.columns
        )
    )
    if missing:
        raise ValueError(
            "Native q90 table lacks required field(s): " + ", ".join(missing)
        )

    municipalities, coastline = read_coastal_inputs()
    segments, assignment_metadata = project_values_to_coastline(
        native_grid,
        VALUE_FIELDS,
        municipalities=municipalities,
        coastline=coastline,
    )
    segments.to_file(segment_data_path, driver="GeoJSON")
    panel_metadata, colorbar_metadata = _plot_figure(
        segments,
        coastline,
        figure_path,
        args.dpi,
    )

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "purpose": (
            "Exploratory comparison of local temporal q90 fields for "
            "significant wave height, dynamic sea level, and astronomical tide"
        ),
        "quantile_calculation": quantile_metadata,
        "native_grid_statistics": {
            field: _numeric_stats(native_grid[field])
            for field in VALUE_FIELDS
        },
        "coastal_projection": assignment_metadata,
        "panels": panel_metadata,
        "colorbars": colorbar_metadata,
        "map": {
            "extent": list(COASTAL_MAP_EXTENT),
            "land_color": LAND_COLOR,
            "ocean_color": OCEAN_COLOR,
            "country_boundaries": (
                "Natural Earth 10m admin_0_boundary_lines_land"
            ),
            "brazilian_state_boundaries": (
                "Natural Earth 10m admin_1_states_provinces_lines"
            ),
            "display_note": (
                "Native-grid values are assigned to the nearest short "
                "coastline segment solely for visualization"
            ),
        },
        "outputs": {
            "figure": _relative(figure_path),
            "native_grid_table": _relative(native_data_path),
            "coastal_segments": _relative(segment_data_path),
            "metadata": _relative(metadata_path),
        },
        "dpi": int(args.dpi),
    }
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(_relative(figure_path))
    print(_relative(native_data_path))
    print(_relative(segment_data_path))
    print(_relative(metadata_path))


if __name__ == "__main__":
    main()
