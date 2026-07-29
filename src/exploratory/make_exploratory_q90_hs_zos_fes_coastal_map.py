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
from matplotlib.ticker import FixedLocator, FormatStrFormatter
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
RATIO_FIELD = "zos_to_fes_q90_ratio"
WAVE_SETUP_FIELD = "wave_setup_proxy_q90_m"
COMBINED_RATIO_FIELD = "zos_plus_wave_setup_to_fes_q90_ratio"
SSH_TOTAL_Q90_FIELD = "ssh_total_q90_m"
HS_FILTERED_FIELD = "hs_q90_ge_0p5_m"
CONDITIONAL_SSH_FIELD = "conditional_ssh_q90_m"
CONDITIONAL_SELECTOR_FIELD = "conditional_uses_ssh_total"
COASTAL_VALUE_FIELDS = (
    *VALUE_FIELDS,
    RATIO_FIELD,
    WAVE_SETUP_FIELD,
    COMBINED_RATIO_FIELD,
    SSH_TOTAL_Q90_FIELD,
    CONDITIONAL_SSH_FIELD,
    CONDITIONAL_SELECTOR_FIELD,
)
DAILY_SERIES_CONVENTIONS = {
    "VHM0": (
        "WAVERYS significant wave height; daily maximum retained from the "
        "original 3-hourly source during preprocessing"
    ),
    "zos": "GLORYS12 daily sea-surface height at 00:00 UTC",
    "tide_daily_max": (
        "FES2022 evaluated hourly from 00:00 to 23:00 UTC; daily maximum "
        "retained"
    ),
}
HS_COLORS = (
    "#E6F7FF",
    "#A6DEF7",
    "#4CBFE6",
    "#0099D1",
    "#007AB8",
    "#1AA64C",
    "#8CCC00",
    "#E6CC00",
    "#FF8000",
    "#D90000",
)


def _resample_palette(
    colors: tuple[str, ...],
    class_count: int,
) -> tuple[str, ...]:
    """Interpolate user-provided color anchors to a requested class count."""
    colormap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "user_specified_hs_interpolated",
        colors,
    )
    return tuple(
        matplotlib.colors.to_hex(color)
        for color in colormap(np.linspace(0.0, 1.0, class_count))
    )


HS_COLORS_15 = _resample_palette(HS_COLORS, 15)
SEA_LEVEL_COLORS = (
    "#ffffcc",
    "#ffeda0",
    "#fed976",
    "#feb24c",
    "#fd8d3c",
    "#fc4e2a",
    "#e31a1c",
    "#bd0026",
    "#800026",
    "#4a0066",
)
RATIO_BOUNDARIES = np.asarray(
    [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.6, 2.0, 2.6, 3.4],
    dtype=float,
)
RATIO_TICKS = np.asarray(
    [0.0, 0.4, 0.8, 1.0, 1.6, 2.0, 2.6, 3.4],
    dtype=float,
)
PANEL_SPECS = (
    {
        "field": "hs_q90_m",
        "variable": "VHM0",
        "panel": "A",
        "title": r"$H_s$",
        "colorbar_label": r"$q_{90}(H_s)$ (m)",
        "colors": HS_COLORS_15,
        "boundaries": np.round(np.arange(0.0, 3.0 + 0.1, 0.2), 2),
        "ticks": np.asarray(
            [0.0, 0.4, 0.8, 1.2, 1.6, 2.0, 2.4, 2.8, 3.0],
            dtype=float,
        ),
        "tick_format": "%.1f",
        "extend": "max",
        "palette_source": (
            "linear interpolation of the 10 user-specified Hs color anchors"
        ),
    },
    {
        "field": "zos_q90_m",
        "variable": "zos",
        "panel": "B",
        "title": r"$zos$",
        "colorbar_label": r"$q_{90}(zos)$ (m)",
        "colors": SEA_LEVEL_COLORS,
        "boundaries": np.round(np.linspace(0.0, 0.4, 11), 2),
        "ticks": np.round(np.linspace(0.0, 0.4, 6), 2),
        "tick_format": "%.2f",
        "extend": "max",
        "palette_source": "10 user-specified sea-level colors",
    },
    {
        "field": "fes_tide_daily_max_q90_m",
        "variable": "tide_daily_max",
        "panel": "C",
        "title": "FES2022 tide",
        "colorbar_label": r"$q_{90}(\mathrm{daily\ maximum\ tide})$ (m)",
        "colors": SEA_LEVEL_COLORS,
        "boundaries": np.round(np.linspace(0.0, 5.0, 11), 2),
        "ticks": np.round(np.linspace(0.0, 5.0, 11), 2),
        "tick_format": "%.1f",
        "extend": "neither",
        "palette_source": "10 user-specified sea-level colors",
    },
)
WAVE_SETUP_PANEL_SPECS = (
    {
        "field": WAVE_SETUP_FIELD,
        "variable": "derived_from_VHM0",
        "panel": "A",
        "title": r"Wave-setup proxy ($0.2H_s$)",
        "colorbar_label": r"$0.2\,q_{90}(H_s)$ (m)",
        "colors": HS_COLORS_15,
        "boundaries": np.round(np.arange(0.0, 0.60 + 0.02, 0.04), 2),
        "ticks": np.asarray(
            [0.0, 0.08, 0.16, 0.24, 0.32, 0.40, 0.48, 0.60],
            dtype=float,
        ),
        "tick_format": "%.2f",
        "extend": "max",
        "palette_source": (
            "linear interpolation of the 10 user-specified Hs color anchors"
        ),
    },
    PANEL_SPECS[1],
    PANEL_SPECS[2],
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


def _attach_catalog_ssh_total_q90(
    native_grid: pd.DataFrame,
    grid_source: Path,
) -> pd.DataFrame:
    """Attach the production q90 threshold of the daily SSH_total series."""
    if not grid_source.exists():
        raise FileNotFoundError(grid_source)
    catalog = pd.read_csv(grid_source)
    required = {"grid_lat", "grid_lon", "thr_ssh_total_abs"}
    missing = sorted(required.difference(catalog.columns))
    if missing:
        raise ValueError(
            f"{grid_source} lacks required column(s): {', '.join(missing)}"
        )
    source = catalog[list(required)].copy()
    for frame in (native_grid, source):
        frame["_grid_lat_key"] = pd.to_numeric(
            frame["grid_lat"],
            errors="coerce",
        ).round(3)
        frame["_grid_lon_key"] = pd.to_numeric(
            frame["grid_lon"],
            errors="coerce",
        ).round(3)
    source["thr_ssh_total_abs"] = pd.to_numeric(
        source["thr_ssh_total_abs"],
        errors="coerce",
    )
    source = source.dropna().drop_duplicates(
        ["_grid_lat_key", "_grid_lon_key"]
    )
    output = native_grid.merge(
        source[
            ["_grid_lat_key", "_grid_lon_key", "thr_ssh_total_abs"]
        ],
        on=["_grid_lat_key", "_grid_lon_key"],
        how="left",
        validate="one_to_one",
    )
    output[SSH_TOTAL_Q90_FIELD] = output.pop("thr_ssh_total_abs")
    output = output.drop(columns=["_grid_lat_key", "_grid_lon_key"])
    if output[SSH_TOTAL_Q90_FIELD].notna().sum() != len(output):
        raise RuntimeError(
            "The production SSH_total q90 could not be matched to every "
            "native coastal point"
        )
    return output


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
            "daily_series_conventions": DAILY_SERIES_CONVENTIONS,
            "variables": variable_metadata,
        }
    return output, metadata


def _describe_reused_quantiles(
    input_path: Path,
    grid_source: Path,
    native_data_path: Path,
    native_grid: pd.DataFrame,
) -> dict[str, Any]:
    """Rebuild complete provenance without rereading the large data fields."""
    if not input_path.exists():
        raise FileNotFoundError(input_path)
    source_grid = _read_native_grid_coordinates(grid_source)
    with xr.open_dataset(input_path) as dataset:
        missing = sorted(set(VARIABLES).difference(dataset.data_vars))
        if missing:
            raise ValueError(
                "Unified dataset lacks required variable(s): "
                + ", ".join(missing)
            )
        times = pd.to_datetime(dataset["time"].values)
        variable_metadata: dict[str, Any] = {}
        for variable, field in zip(VARIABLES, VALUE_FIELDS):
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
                    _numeric_stats(native_grid[field])
                ),
            }
        return {
            "input": _relative(input_path),
            "input_size_bytes": int(input_path.stat().st_size),
            "grid_source": _relative(grid_source),
            "quantile": QUANTILE,
            "quantile_method": "numpy.nanquantile(method='linear')",
            "quantile_dimension": "time",
            "minimum_valid_fraction": MIN_VALID_FRACTION,
            "candidate_grid_points": int(len(source_grid)),
            "retained_grid_points": int(len(native_grid)),
            "time_steps": int(dataset.sizes["time"]),
            "period_start": times.min().date().isoformat(),
            "period_end": times.max().date().isoformat(),
            "daily_series_conventions": DAILY_SERIES_CONVENTIONS,
            "variables": variable_metadata,
            "calculation_performed_this_run": False,
            "reused_native_grid_table": _relative(native_data_path),
        }


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
    if panel:
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
    finite = np.isfinite(values)
    class_indices = np.full(values.shape, -1, dtype=int)
    class_indices[finite] = np.clip(
        np.digitize(values[finite], boundaries[1:-1]),
        0,
        len(boundaries) - 2,
    )
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
    ticks: np.ndarray,
    label: str,
    tick_format: str,
    extend: str,
    reference_value: float | None = None,
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
        ticks=ticks,
        spacing="uniform",
        drawedges=True,
        extend=extend,
        extendrect=True,
    )
    colorbar.set_label(label, fontsize=9.2, labelpad=2.5)
    colorbar.ax.xaxis.set_major_formatter(FormatStrFormatter(tick_format))
    colorbar.ax.tick_params(labelsize=7.7, length=2.8)
    colorbar.outline.set_linewidth(0.7)
    if reference_value is not None:
        colorbar.ax.axvline(
            reference_value,
            color="#111827",
            linewidth=1.25,
            zorder=5,
        )


def _plot_figure(
    segments: gpd.GeoDataFrame,
    coastline: gpd.GeoDataFrame,
    output_path: Path,
    dpi: int,
    panel_specs: tuple[dict[str, Any], ...] = PANEL_SPECS,
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
    if len(panel_specs) != len(axes):
        raise ValueError("The three-panel layout requires exactly 3 specs")
    for index, (axis, spec) in enumerate(zip(axes, panel_specs)):
        boundaries = np.asarray(spec["boundaries"], dtype=float)
        cmap = ListedColormap(
            spec["colors"],
            name=f"user_specified_{spec['field']}",
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
            "palette_source": spec["palette_source"],
            "ticks": np.asarray(spec["ticks"], dtype=float).tolist(),
            "extend": spec["extend"],
            "vmin": float(boundaries[0]),
            "vmax": float(boundaries[-1]),
            "segments_above_vmax": int(
                (segments[spec["field"]] > boundaries[-1]).sum()
            ),
            "label": spec["colorbar_label"],
        }

    figure.canvas.draw()
    for axis, cmap, boundaries, spec in colorbar_objects:
        _add_colorbar(
            figure,
            axis,
            cmap=cmap,
            boundaries=boundaries,
            ticks=np.asarray(spec["ticks"], dtype=float),
            label=spec["colorbar_label"],
            tick_format=spec["tick_format"],
            extend=spec["extend"],
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


def _plot_ratio_figure(
    segments: gpd.GeoDataFrame,
    coastline: gpd.GeoDataFrame,
    output_path: Path,
    dpi: int,
) -> dict[str, Any]:
    """Compare two q90-component ratios on the coastline."""
    figure, axes = plt.subplots(
        1,
        2,
        figsize=(7.8, 7.0),
        constrained_layout=False,
        subplot_kw={"projection": ccrs.PlateCarree()},
    )
    figure.subplots_adjust(
        left=0.065,
        right=0.985,
        top=0.93,
        bottom=0.12,
        wspace=0.025,
    )
    cmap = ListedColormap(
        SEA_LEVEL_COLORS,
        name="user_specified_q90_component_to_fes_ratios",
    )
    ratio_specs = (
        {
            "panel": "A",
            "field": RATIO_FIELD,
            "title": (
                "Dynamic / astronomical\n"
                r"$q_{90}(zos)\,/\,q_{90}(\mathrm{FES2022\ tide})$"
            ),
            "definition": (
                "q90(zos) divided by q90(FES2022 daily-maximum tide)"
            ),
            "ratio_above_1": (
                "The zos q90 exceeds the FES2022 tide q90"
            ),
        },
        {
            "panel": "B",
            "field": COMBINED_RATIO_FIELD,
            "title": (
                "Dynamic + wave proxy / astronomical\n"
                r"$[q_{90}(zos)+0.2q_{90}(H_s)]"
                r"\,/\,q_{90}(\mathrm{FES2022\ tide})$"
            ),
            "definition": (
                "[q90(zos) + 0.2 * q90(Hs)] divided by "
                "q90(FES2022 daily-maximum tide)"
            ),
            "ratio_above_1": (
                "The sum of the zos q90 and empirical wave-setup proxy "
                "exceeds the FES2022 tide q90"
            ),
        },
    )
    panel_metadata: dict[str, Any] = {}
    for index, (axis, spec) in enumerate(zip(axes, ratio_specs)):
        _plot_coastal_field(
            axis,
            segments,
            coastline,
            field=spec["field"],
            panel=spec["panel"],
            title=spec["title"],
            cmap=cmap,
            boundaries=RATIO_BOUNDARIES,
            draw_left_labels=index == 0,
        )
        panel_metadata[spec["panel"]] = {
            "field": spec["field"],
            "definition": spec["definition"],
            "unit": "dimensionless",
            "interpretation": {
                "ratio_below_1": (
                    "The FES2022 astronomical-tide q90 exceeds the numerator"
                ),
                "ratio_equal_1": (
                    "The numerator and FES2022 tide q90 magnitudes are equal"
                ),
                "ratio_above_1": spec["ratio_above_1"],
            },
            "native_grid_statistics": None,
            "native_points_above_1": None,
            "coastline_segment_statistics": _numeric_stats(
                segments[spec["field"]]
            ),
        }

    figure.canvas.draw()
    left_position = axes[0].get_position()
    right_position = axes[1].get_position()
    colorbar_axis = figure.add_axes(
        [
            left_position.x0,
            min(left_position.y0, right_position.y0) - 0.058,
            right_position.x1 - left_position.x0,
            0.016,
        ]
    )
    norm = BoundaryNorm(RATIO_BOUNDARIES, cmap.N, clip=True)
    mappable = ScalarMappable(norm=norm, cmap=cmap)
    mappable.set_array([])
    colorbar = figure.colorbar(
        mappable,
        cax=colorbar_axis,
        orientation="horizontal",
        boundaries=RATIO_BOUNDARIES,
        ticks=RATIO_TICKS,
        spacing="uniform",
        drawedges=True,
        extend="neither",
    )
    colorbar.set_label(
        r"Ratio to $q_{90}(\mathrm{FES2022\ tide})$ (–)",
        fontsize=9.2,
        labelpad=2.5,
    )
    colorbar.ax.xaxis.set_major_formatter(FormatStrFormatter("%.1f"))
    colorbar.ax.tick_params(labelsize=7.7, length=2.8)
    colorbar.outline.set_linewidth(0.7)
    colorbar.ax.axvline(
        1.0,
        color="#111827",
        linewidth=1.25,
        zorder=5,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        output_path,
        dpi=dpi,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(figure)
    return {
        "layout": "1x2",
        "panels": panel_metadata,
        "important_distinction": (
            "Both panels combine temporal q90 component fields pointwise; "
            "neither is the temporal q90 of a daily component ratio or sum"
        ),
        "shared_colorbar": {
            "type": "discrete",
            "boundaries": RATIO_BOUNDARIES.tolist(),
            "ticks": RATIO_TICKS.tolist(),
            "colors": list(cmap.colors),
            "palette_source": (
                "user-specified hexadecimal sea-level palette"
            ),
            "extend": "neither",
            "reference_value": 1.0,
            "vmin": float(RATIO_BOUNDARIES[0]),
            "vmax": float(RATIO_BOUNDARIES[-1]),
            "segments_above_vmax": {
                spec["field"]: int(
                    (segments[spec["field"]] > RATIO_BOUNDARIES[-1]).sum()
                )
                for spec in ratio_specs
            },
        },
    }


def _plot_filtered_hs_conditional_ssh_figure(
    segments: gpd.GeoDataFrame,
    coastline: gpd.GeoDataFrame,
    output_path: Path,
    dpi: int,
) -> dict[str, Any]:
    """Plot filtered Hs q90 and the exploratory conditional sea-level q90."""
    figure, axes = plt.subplots(
        1,
        2,
        figsize=(7.8, 7.0),
        constrained_layout=False,
        subplot_kw={"projection": ccrs.PlateCarree()},
    )
    figure.subplots_adjust(
        left=0.065,
        right=0.985,
        top=0.93,
        bottom=0.12,
        wspace=0.025,
    )
    panel_specs = (
        {
            "panel": "A",
            "field": HS_FILTERED_FIELD,
            "title": (
                r"Filtered $q_{90}(H_s)$"
                "\n"
                r"coastal points with $q_{90}(H_s)<0.5$ m excluded"
            ),
            "boundaries": np.asarray(
                PANEL_SPECS[0]["boundaries"],
                dtype=float,
            ),
            "ticks": np.asarray(PANEL_SPECS[0]["ticks"], dtype=float),
            "colors": HS_COLORS_15,
            "label": r"$q_{90}(H_s)$ (m)",
            "tick_format": "%.1f",
            "extend": "max",
            "definition": (
                "Display hs_q90_m only where hs_q90_m >= 0.5 m; excluded "
                "coastal segments retain the neutral coastline color"
            ),
        },
        {
            "panel": "B",
            "field": CONDITIONAL_SSH_FIELD,
            "title": (
                r"Conditional sea-level $q_{90}$"
                "\n"
                r"$q<1:\ q_{90}(zos);\quad q\geq1:\ q_{90}(SSH_{total})$"
            ),
            "boundaries": np.round(np.linspace(0.0, 1.0, 11), 2),
            "ticks": np.round(np.linspace(0.0, 1.0, 6), 2),
            "colors": SEA_LEVEL_COLORS,
            "label": r"Conditional sea-level $q_{90}$ (m)",
            "tick_format": "%.1f",
            "extend": "neither",
            "definition": (
                "Use q90(zos) where the combined dynamic-plus-wave-proxy "
                "to astronomical ratio q is below 1; use the production "
                "q90(SSH_total) where q is greater than or equal to 1"
            ),
        },
    )
    panel_metadata: dict[str, Any] = {}
    colorbar_objects: list[
        tuple[plt.Axes, ListedColormap, np.ndarray, dict[str, Any]]
    ] = []
    for index, (axis, spec) in enumerate(zip(axes, panel_specs)):
        boundaries = np.asarray(spec["boundaries"], dtype=float)
        cmap = ListedColormap(
            spec["colors"],
            name=f"user_specified_{spec['field']}",
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
            "definition": spec["definition"],
            "unit": "m",
            "statistics_on_displayed_segments": _numeric_stats(
                segments[spec["field"]]
            ),
            "colorbar": {
                "type": "discrete",
                "boundaries": boundaries.tolist(),
                "ticks": np.asarray(spec["ticks"], dtype=float).tolist(),
                "colors": list(cmap.colors),
                "extend": spec["extend"],
                "label": spec["label"],
            },
        }
        colorbar_objects.append((axis, cmap, boundaries, spec))

    figure.canvas.draw()
    for axis, cmap, boundaries, spec in colorbar_objects:
        _add_colorbar(
            figure,
            axis,
            cmap=cmap,
            boundaries=boundaries,
            ticks=np.asarray(spec["ticks"], dtype=float),
            label=spec["label"],
            tick_format=spec["tick_format"],
            extend=spec["extend"],
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        output_path,
        dpi=dpi,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(figure)
    return {
        "layout": "1x2",
        "panels": panel_metadata,
        "ratio_q_definition": (
            "q = [q90(zos) + 0.2 * q90(Hs)] / "
            "q90(FES2022 daily-maximum tide)"
        ),
        "ssh_total_source": (
            "Production local q90 of the daily SSH_total = zos + "
            "tide_daily_max series, stored as thr_ssh_total_abs in "
            "outputs/storm_catalog/compound/compound_metrics.csv"
        ),
        "important_distinction": (
            "Panel B is a pointwise hybrid of two separately derived q90 "
            "fields selected by q; it is not the q90 of one homogeneous "
            "daily time series"
        ),
    }


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    figure_path = output_dir / "figures" / "q90_hs_zos_fes_coastal.png"
    wave_setup_figure_path = (
        output_dir
        / "figures"
        / "q90_wave_setup_proxy_zos_fes_coastal.png"
    )
    filtered_conditional_figure_path = (
        output_dir
        / "figures"
        / "q90_filtered_hs_conditional_ssh_coastal.png"
    )
    ratio_figure_path = (
        output_dir / "figures" / "q90_zos_to_fes_ratio_coastal.png"
    )
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
        quantile_metadata = _describe_reused_quantiles(
            args.input.resolve(),
            args.grid_source.resolve(),
            native_data_path,
            native_grid,
        )
    else:
        native_grid, quantile_metadata = _calculate_native_quantiles(
            args.input.resolve(),
            args.grid_source.resolve(),
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

    native_grid = _attach_catalog_ssh_total_q90(
        native_grid,
        args.grid_source.resolve(),
    )
    denominator = pd.to_numeric(
        native_grid["fes_tide_daily_max_q90_m"],
        errors="coerce",
    )
    numerator = pd.to_numeric(
        native_grid["zos_q90_m"],
        errors="coerce",
    )
    native_grid[RATIO_FIELD] = np.where(
        np.isfinite(numerator) & np.isfinite(denominator) & (denominator > 0),
        numerator / denominator,
        np.nan,
    )
    if native_grid[RATIO_FIELD].notna().sum() != len(native_grid):
        raise RuntimeError(
            "The zos/FES q90 ratio is undefined at one or more native points"
        )
    native_grid[WAVE_SETUP_FIELD] = (
        0.2 * pd.to_numeric(native_grid["hs_q90_m"], errors="coerce")
    )
    if native_grid[WAVE_SETUP_FIELD].notna().sum() != len(native_grid):
        raise RuntimeError(
            "The empirical wave-setup proxy is undefined at one or more "
            "native points"
        )
    native_grid[COMBINED_RATIO_FIELD] = np.where(
        np.isfinite(numerator)
        & np.isfinite(native_grid[WAVE_SETUP_FIELD])
        & np.isfinite(denominator)
        & (denominator > 0),
        (numerator + native_grid[WAVE_SETUP_FIELD]) / denominator,
        np.nan,
    )
    if native_grid[COMBINED_RATIO_FIELD].notna().sum() != len(native_grid):
        raise RuntimeError(
            "The combined (zos + wave-setup proxy)/FES q90 ratio is "
            "undefined at one or more native points"
        )
    native_grid[HS_FILTERED_FIELD] = native_grid["hs_q90_m"].where(
        native_grid["hs_q90_m"] >= 0.5
    )
    native_grid[CONDITIONAL_SELECTOR_FIELD] = (
        native_grid[COMBINED_RATIO_FIELD] >= 1.0
    ).astype(int)
    native_grid[CONDITIONAL_SSH_FIELD] = np.where(
        native_grid[CONDITIONAL_SELECTOR_FIELD] == 1,
        native_grid[SSH_TOTAL_Q90_FIELD],
        native_grid["zos_q90_m"],
    )
    if native_grid[CONDITIONAL_SSH_FIELD].notna().sum() != len(native_grid):
        raise RuntimeError(
            "The conditional sea-level q90 is undefined at one or more "
            "native points"
        )
    native_grid.to_csv(
        native_data_path,
        index=False,
        float_format="%.7f",
    )

    municipalities, coastline = read_coastal_inputs()
    segments, assignment_metadata = project_values_to_coastline(
        native_grid,
        COASTAL_VALUE_FIELDS,
        municipalities=municipalities,
        coastline=coastline,
    )
    segments[HS_FILTERED_FIELD] = segments["hs_q90_m"].where(
        segments["hs_q90_m"] >= 0.5
    )
    segments.to_file(segment_data_path, driver="GeoJSON")
    panel_metadata, colorbar_metadata = _plot_figure(
        segments,
        coastline,
        figure_path,
        args.dpi,
    )
    wave_setup_panel_metadata, wave_setup_colorbar_metadata = _plot_figure(
        segments,
        coastline,
        wave_setup_figure_path,
        args.dpi,
        panel_specs=WAVE_SETUP_PANEL_SPECS,
    )
    ratio_metadata = _plot_ratio_figure(
        segments,
        coastline,
        ratio_figure_path,
        args.dpi,
    )
    filtered_conditional_metadata = (
        _plot_filtered_hs_conditional_ssh_figure(
            segments,
            coastline,
            filtered_conditional_figure_path,
            args.dpi,
        )
    )
    for panel, field in (
        ("A", RATIO_FIELD),
        ("B", COMBINED_RATIO_FIELD),
    ):
        ratio_metadata["panels"][panel]["native_grid_statistics"] = (
            _numeric_stats(native_grid[field])
        )
        ratio_metadata["panels"][panel]["native_points_above_1"] = int(
            (native_grid[field] > 1.0).sum()
        )
    ratio_metadata["native_point_count"] = int(len(native_grid))

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "purpose": (
            "Exploratory comparison of local temporal q90 fields for "
            "significant wave height, dynamic sea level, and astronomical tide"
        ),
        "quantile_calculation": quantile_metadata,
        "native_grid_statistics": {
            field: _numeric_stats(native_grid[field])
            for field in COASTAL_VALUE_FIELDS
        },
        "filtered_hs_and_conditional_ssh": {
            **filtered_conditional_metadata,
            "hs_filter": {
                "threshold_m": 0.5,
                "operator": "exclude where hs_q90_m < 0.5",
                "native_points_excluded": int(
                    native_grid[HS_FILTERED_FIELD].isna().sum()
                ),
                "native_points_retained": int(
                    native_grid[HS_FILTERED_FIELD].notna().sum()
                ),
                "coastline_segments_excluded": int(
                    segments[HS_FILTERED_FIELD].isna().sum()
                ),
            },
            "conditional_ssh_selection": {
                "q_below_1_uses": "zos_q90_m",
                "q_greater_or_equal_1_uses": SSH_TOTAL_Q90_FIELD,
                "native_points_using_zos": int(
                    (
                        native_grid[CONDITIONAL_SELECTOR_FIELD] == 0
                    ).sum()
                ),
                "native_points_using_ssh_total": int(
                    (
                        native_grid[CONDITIONAL_SELECTOR_FIELD] == 1
                    ).sum()
                ),
                "conditional_field_statistics": _numeric_stats(
                    native_grid[CONDITIONAL_SSH_FIELD]
                ),
            },
        },
        "derived_wave_setup_proxy": {
            "field": WAVE_SETUP_FIELD,
            "definition": "wave_setup_proxy_q90_m = 0.2 * hs_q90_m",
            "quantile_identity": (
                "Because the coefficient is positive, "
                "q90(0.2 * Hs) = 0.2 * q90(Hs)"
            ),
            "coefficient": 0.2,
            "unit": "m",
            "purpose": "empirical visual proxy only",
            "limitation": (
                "This simple scaling is not a hydrodynamic wave-setup "
                "calculation and does not account for bathymetry, beach "
                "slope, wave period, direction, breaking, or dissipation"
            ),
            "native_grid_statistics": _numeric_stats(
                native_grid[WAVE_SETUP_FIELD]
            ),
            "coastline_segment_statistics": _numeric_stats(
                segments[WAVE_SETUP_FIELD]
            ),
        },
        "derived_component_to_fes_ratios": ratio_metadata,
        "coastal_projection": assignment_metadata,
        "panels": panel_metadata,
        "colorbars": colorbar_metadata,
        "wave_setup_proxy_panels": wave_setup_panel_metadata,
        "wave_setup_proxy_colorbars": wave_setup_colorbar_metadata,
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
            "three_panel_figure": _relative(figure_path),
            "wave_setup_proxy_three_panel_figure": _relative(
                wave_setup_figure_path
            ),
            "filtered_hs_conditional_ssh_figure": _relative(
                filtered_conditional_figure_path
            ),
            "zos_to_fes_ratio_figure": _relative(ratio_figure_path),
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
    print(_relative(wave_setup_figure_path))
    print(_relative(filtered_conditional_figure_path))
    print(_relative(ratio_figure_path))
    print(_relative(native_data_path))
    print(_relative(segment_data_path))
    print(_relative(metadata_path))


if __name__ == "__main__":
    main()
