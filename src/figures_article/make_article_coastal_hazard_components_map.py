r"""Generate the article coastal Hazard Index and component maps.

Suggested LaTeX figure block (requires ``\usepackage{graphicx}``)
-----------------------------------------------------------------
\begin{figure*}[htbp]
    \centering
    \includegraphics[width=\textwidth]{outputs/article_figures/coastal_hazard_index_components.png}
    \caption{Compound coastal-event characteristics and composite Hazard
    Index along the Brazilian coast during 1993--2025: (a) mean annual
    compound-event frequency (events~yr$^{-1}$), (b) mean integrated
    severity (dimensionless), and (c) the composite Hazard Index.
    Panels (a)--(b) show the native-grid values
    without the additional cross-grid Min--Max scaling used to construct the
    Hazard Index. The intensity in panel (c) is the dimensionless compound
    event-level metric stored in the catalog: for each event, how far each
    driver rose above its own local q90 detection threshold, rescaled by the
    5th--95th percentiles of those excesses pooled over the domain and
    averaged with equal weights. Subtracting the local threshold keeps the
    astronomical tide, which dominates the absolute sea level in the
    macrotidal north, out of the severity score. To calculate panel (d), the
    three components are Min--Max normalized over the 808-point native ocean
    grid, averaged with equal weights, and the mean is Min--Max normalized
    again to obtain the final Hazard Index on a 0--1 scale. For visualization,
    the Natural Earth 10-m coastline is divided
    into segments no longer than 5~km and each segment receives the value at
    its nearest native grid point using distances in SIRGAS 2000 / Brazil
    Polyconic (EPSG:5880). Panels (a)--(c) use the discrete reversed-magma
    palette of the former annual compound-event-rate figure; panel (d) uses
    the green-to-red integrated-risk palette. Gray shading denotes land,
    light blue denotes the ocean, dark-gray lines delimit countries, and
    lighter gray lines delimit Brazilian states.}
    \label{fig:coastal-hazard-components}
\end{figure*}

Run from the repository root:

    python src/figures_article/make_article_coastal_hazard_components_map.py
"""
from __future__ import annotations

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

from src.figures_article.make_article_supplementary_integrated_risk_zooms import (
    ARTICLE_DPI,
    COASTLINE_PATH,
    COUNTRY_BORDER_COLOR,
    LAND_COLOR,
    OCEAN_COLOR,
    RISK_COLORS,
    STATE_BORDER_COLOR,
    _numeric_stats,
    _relative,
)
from src.risk_integration.coastal_projection import (
    COASTAL_MAP_EXTENT,
    line_parts as _line_parts,
    project_values_to_coastline,
    read_coastal_inputs,
)
from src.risk_integration.hazard_index import (
    NATIVE_GRID_SOURCE,
    derive_native_hazard_index,
)
from src.risk_integration.palettes import component_colors


OUT_DIR = ROOT / "outputs" / "article_figures"
DATA_DIR = OUT_DIR / "data"
METADATA_DIR = OUT_DIR / "metadata"
OUTPUT_PATH = OUT_DIR / "coastal_hazard_index_components.png"
GRID_DATA_PATH = DATA_DIR / "coastal_hazard_components_native_grid.csv"
SEGMENT_DATA_PATH = DATA_DIR / "coastal_hazard_components_segments.geojson"
METADATA_PATH = (
    METADATA_DIR / "article_coastal_hazard_index_components_metadata.json"
)

OUTPUT_CRS = "EPSG:4326"
CONTEXT_EXTENT = (-74.5, -32.0, -35.5, 6.5)
# Current q70/q99 catalogue ranges: frequency 0–2.97 events/yr and mean
# integrated severity 0–0.9483.  A narrow first bin isolates exact zeros,
# which are rendered in gray rather than as the lowest positive class.
FREQUENCY_BOUNDARIES = np.array([0.0, 0.015, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
SEVERITY_BOUNDARIES = np.array([0.0, 0.0042, 0.15, 0.30, 0.45, 0.60, 0.75, 0.95])
HAZARD_BOUNDARIES = np.array([0.0, 1e-6, 0.15, 0.30, 0.45, 0.60, 0.75, 0.95])
FREQUENCY_TICKS = np.array([0.0075, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
SEVERITY_TICKS = np.array([0.0021, 0.15, 0.30, 0.45, 0.60, 0.75, 0.95])
HAZARD_TICKS = HAZARD_BOUNDARIES
DISPLAY_COMPONENT_FIELDS = (
    "compound_count_annual_mean",
    "mean_integrated_severity",
)
NORMALIZED_COMPONENT_FIELDS = (
    "Hazard_Frequency",
    "Hazard_Severity",
)
PANEL_SPECS = (
    {
        "field": "compound_count_annual_mean",
        "panel": "A",
        "title": "Compound-event frequency",
        "boundaries": FREQUENCY_BOUNDARIES,
        "ticks": FREQUENCY_TICKS,
        "colorbar_label": r"Events yr$^{-1}$",
        "tick_format": "%.1f",
        "unit": "events per year",
        "palette": "component",
        "zero_is_gray": True,
    },
    {
        "field": "mean_integrated_severity",
        "panel": "B",
        "title": "Mean integrated severity",
        "boundaries": SEVERITY_BOUNDARIES,
        "ticks": SEVERITY_TICKS,
        "colorbar_label": "Mean integrated severity (dimensionless)",
        "tick_format": "%.2f",
        "unit": "dimensionless",
        "palette": "component",
        "zero_is_gray": True,
    },
    {
        "field": "Hazard_Index",
        "panel": "C",
        "title": "Composite Hazard Index",
        "boundaries": HAZARD_BOUNDARIES,
        "ticks": HAZARD_TICKS,
        "colorbar_label": "Hazard Index (0–1)",
        "tick_format": "%.2f",
        "unit": "0-1 index",
        "palette": "hazard",
        "zero_is_gray": True,
    },
)

GRID_COLOR = "#9aa9b0"
COAST_COLOR = "#334155"


def _geometry_intersects_extent(
    geometry: object,
    extent: tuple[float, float, float, float],
) -> bool:
    minx, miny, maxx, maxy = geometry.bounds
    west, east, south, north = extent
    return not (maxx < west or minx > east or maxy < south or miny > north)


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


def _build_coastal_segments(
    municipalities: gpd.GeoDataFrame,
    coastline: gpd.GeoDataFrame,
    native_grid: pd.DataFrame,
) -> tuple[gpd.GeoDataFrame, dict[str, Any]]:
    """Project the native-grid hazard fields onto the coastline for display."""
    return project_values_to_coastline(
        native_grid,
        (
            *DISPLAY_COMPONENT_FIELDS,
            *NORMALIZED_COMPONENT_FIELDS,
            "Hazard_Index_raw",
            "Hazard_Index",
        ),
        municipalities=municipalities,
        coastline=coastline,
    )


def _setup_axis(
    axis: plt.Axes,
    *,
    title: str,
    panel_label: str,
    draw_left_labels: bool,
    draw_bottom_labels: bool,
) -> None:
    crs = ccrs.PlateCarree()
    land, _, _ = _natural_earth_context()
    axis.set_facecolor(OCEAN_COLOR)
    axis.add_geometries(
        land,
        crs=crs,
        facecolor=LAND_COLOR,
        edgecolor="none",
        zorder=0.5,
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
    grid.bottom_labels = draw_bottom_labels
    grid.xlabel_style = {"size": 8.5, "color": "#374151"}
    grid.ylabel_style = {"size": 8.5, "color": "#374151"}
    axis.set_title(title, fontsize=10.5, fontweight="bold", pad=6)
    axis.text(
        0.018,
        0.975,
        panel_label,
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


def _draw_context(
    axis: plt.Axes,
    coastline: gpd.GeoDataFrame,
) -> None:
    crs = ccrs.PlateCarree()
    _, countries, states = _natural_earth_context()
    axis.add_geometries(
        states,
        crs=crs,
        facecolor="none",
        edgecolor=STATE_BORDER_COLOR,
        linewidth=0.45,
        alpha=0.96,
        zorder=5,
    )
    axis.add_geometries(
        countries,
        crs=crs,
        facecolor="none",
        edgecolor=COUNTRY_BORDER_COLOR,
        linewidth=0.75,
        alpha=0.98,
        zorder=5.2,
    )
    axis.add_geometries(
        coastline.geometry,
        crs=crs,
        facecolor="none",
        edgecolor=COAST_COLOR,
        linewidth=0.5,
        zorder=5.4,
    )


def _plot_segment_field(
    axis: plt.Axes,
    segments: gpd.GeoDataFrame,
    coastline: gpd.GeoDataFrame,
    *,
    field: str,
    title: str,
    panel_label: str,
    cmap: ListedColormap,
    boundaries: np.ndarray,
    unit: str,
    draw_left_labels: bool,
    draw_bottom_labels: bool,
) -> dict[str, Any]:
    _setup_axis(
        axis,
        title=title,
        panel_label=panel_label,
        draw_left_labels=draw_left_labels,
        draw_bottom_labels=draw_bottom_labels,
    )
    _draw_context(axis, coastline)
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
            _line_parts(merged),
            crs=ccrs.PlateCarree(),
            facecolor="none",
            edgecolor=cmap(class_index),
            linewidth=4.0,
            zorder=8,
        )
    axis.set_extent(COASTAL_MAP_EXTENT, crs=ccrs.PlateCarree())
    return {
        "panel": panel_label,
        "title": title,
        "field": field,
        "unit": unit,
        "statistics": _numeric_stats(segments[field]),
    }


def _add_colorbar(
    figure: plt.Figure,
    axis: plt.Axes,
    *,
    cmap: ListedColormap,
    boundaries: np.ndarray,
    ticks: np.ndarray,
    label: str,
    tick_format: str,
    vertical_offset: float,
    zero_is_gray: bool,
) -> None:
    position = axis.get_position()
    colorbar_axis = figure.add_axes(
        [position.x0, position.y0 - vertical_offset, position.width, 0.012]
    )
    norm = BoundaryNorm(boundaries, cmap.N, clip=True)
    mappable = ScalarMappable(norm=norm, cmap=cmap)
    mappable.set_array([])
    colorbar = figure.colorbar(
        mappable,
        cax=colorbar_axis,
        orientation="horizontal",
        boundaries=boundaries,
        ticks=(
            [float((boundaries[0] + boundaries[1]) / 2), *boundaries[2:]]
            if zero_is_gray
            else ticks
        ),
        spacing="uniform",
        drawedges=True,
    )
    colorbar.set_label(label, fontsize=9.0, labelpad=2.0)
    colorbar.ax.xaxis.set_major_formatter(FormatStrFormatter(tick_format))
    colorbar.ax.tick_params(labelsize=8, length=2.8)
    if zero_is_gray:
        labels = [label.get_text() for label in colorbar.ax.get_xticklabels()]
        if labels:
            labels[0] = "0"
            colorbar.ax.set_xticklabels(labels)
            colorbar.ax.get_xticklabels()[0].set_fontsize(7)
    tick_labels = colorbar.ax.get_xticklabels()
    if tick_labels:
        tick_labels[0].set_horizontalalignment("center")
        tick_labels[-1].set_horizontalalignment("right")
    colorbar.outline.set_linewidth(0.7)


def _write_metadata(
    native_metadata: dict[str, Any],
    assignment_metadata: dict[str, Any],
    panels: list[dict[str, Any]],
    panel_cmaps: dict[str, ListedColormap],
) -> None:
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "output": _relative(OUTPUT_PATH),
        "native_grid_source": _relative(NATIVE_GRID_SOURCE),
        "native_hazard_index": native_metadata,
        "coastline_source": _relative(COASTLINE_PATH),
        "coastal_assignment": assignment_metadata,
        "panels": panels,
        "colorbars": {
            spec["panel"]: {
                "field": spec["field"],
                "unit": spec["unit"],
                "type": "discrete",
                "boundaries": spec["boundaries"].tolist(),
                "ticks": spec["ticks"].tolist(),
                "colors": [
                    matplotlib.colors.to_hex(color)
                    for color in panel_cmaps[spec["field"]].colors
                ],
                "colormap": (
                    "matplotlib magma sampled from 0.95 to 0.12"
                    if spec["palette"] == "component"
                    else "integrated-risk green-to-red palette"
                ),
                "display_values": (
                    "native-grid values without cross-grid Min-Max scaling"
                    if spec["palette"] == "component"
                    else "normalized composite Hazard Index"
                ),
                "label": spec["colorbar_label"],
                "zero_is_gray": bool(spec.get("zero_is_gray", False)),
            }
            for spec in PANEL_SPECS
        },
        "map_context": {
            "extent": list(COASTAL_MAP_EXTENT),
            "land_color": LAND_COLOR,
            "ocean_color": OCEAN_COLOR,
            "country_boundaries": (
                "Natural Earth 10m admin_0_boundary_lines_land"
            ),
            "brazilian_state_boundaries": (
                "Natural Earth 10m admin_1_states_provinces_lines"
            ),
        },
        "layout": {
            "panel_grid": "1x3",
            "horizontal_subplot_spacing": 0.035,
            "individual_panel_colorbars": True,
            "purpose": (
                "remove unused horizontal canvas while preserving the "
                "geographic aspect ratio"
            ),
        },
        "outputs": {
            "figure": _relative(OUTPUT_PATH),
            "native_grid_table": _relative(GRID_DATA_PATH),
            "coastal_segments": _relative(SEGMENT_DATA_PATH),
            "metadata": _relative(METADATA_PATH),
        },
        "output_format": "PNG",
        "dpi": ARTICLE_DPI,
    }
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_PATH.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    municipalities, coastline = read_coastal_inputs()
    native_grid, native_metadata = derive_native_hazard_index()
    segments, assignment_metadata = _build_coastal_segments(
        municipalities,
        coastline,
        native_grid,
    )

    panel_cmaps: dict[str, ListedColormap] = {}
    for spec in PANEL_SPECS:
        field = spec["field"]
        if spec["palette"] == "component":
            panel_cmaps[field] = ListedColormap(
                (
                    ["#bdbdbd"]
                    + component_colors(len(spec["boundaries"]) - 2)
                    if spec.get("zero_is_gray")
                    else component_colors(len(spec["boundaries"]) - 1)
                ),
                name=f"magma_discrete_reversed_{field}",
            )
        else:
            panel_cmaps[field] = ListedColormap(
                RISK_COLORS,
                name="integrated_risk_green_to_red_hazard_index",
            )

    figure, axes = plt.subplots(
        1,
        3,
        figsize=(10.8, 7.2),
        constrained_layout=False,
        subplot_kw={"projection": ccrs.PlateCarree()},
    )
    figure.subplots_adjust(
        left=0.045,
        right=0.985,
        top=0.955,
        bottom=0.145,
        wspace=0.01,
    )
    panels: list[dict[str, Any]] = []
    for index, (axis, panel_spec) in enumerate(
        zip(np.atleast_1d(axes).flat, PANEL_SPECS)
    ):
        field = panel_spec["field"]
        axis.set_anchor("C")
        panels.append(
            _plot_segment_field(
                axis,
                segments,
                coastline,
                field=field,
                title=panel_spec["title"],
                panel_label=panel_spec["panel"],
                cmap=panel_cmaps[field],
                boundaries=panel_spec["boundaries"],
                unit=panel_spec["unit"],
                draw_left_labels=index == 0,
                draw_bottom_labels=True,
            )
        )

    figure.canvas.draw()
    for index, (axis, panel_spec) in enumerate(
        zip(np.atleast_1d(axes).flat, PANEL_SPECS)
    ):
        _add_colorbar(
            figure,
            axis,
            cmap=panel_cmaps[panel_spec["field"]],
            boundaries=panel_spec["boundaries"],
            ticks=panel_spec["ticks"],
            label=panel_spec["colorbar_label"],
            tick_format=panel_spec["tick_format"],
            vertical_offset=0.065,
            zero_is_gray=bool(panel_spec.get("zero_is_gray")),
        )

    for directory in (OUT_DIR, DATA_DIR, METADATA_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        OUTPUT_PATH,
        dpi=ARTICLE_DPI,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(figure)
    native_grid.to_csv(
        GRID_DATA_PATH,
        index=False,
        float_format="%.6f",
    )
    segments.to_file(SEGMENT_DATA_PATH, driver="GeoJSON")
    _write_metadata(
        native_metadata,
        assignment_metadata,
        panels,
        panel_cmaps,
    )
    print(_relative(OUTPUT_PATH))
    print(_relative(GRID_DATA_PATH))
    print(_relative(SEGMENT_DATA_PATH))
    print(_relative(METADATA_PATH))


if __name__ == "__main__":
    main()
