r"""Generate supplementary regional zooms of the integrated coastal-risk index.

Suggested LaTeX figure block (requires ``\usepackage{graphicx}``)
-----------------------------------------------------------------
\begin{figure*}[htbp]
    \centering
    \includegraphics[width=\textwidth]{outputs/article_figures/supplementary_integrated_risk_zooms.png}
    \caption{Regional detail of the integrated compound coastal-risk index
    for municipalities along (a) the coast from Rio Grande do Sul to Rio de
    Janeiro, (b) Esp\'irito Santo to Rio Grande do Norte, (c) Piau\'i to
    Par\'a, and (d) Rio Grande do Norte to Piau\'i. The integrated index is the
    geometric mean of the
    fixed-anchor municipal Hazard Index, population exposure, and social
    vulnerability transformed with the standard-normal CDF, without a floor
    or final Min--Max normalization. All panels use the same discrete class
    limits and green-to-red palette as the integrated-risk panel in the main
    figure, allowing direct comparison between regions. The darkest green is
    reserved for the isolated zero class; positive values begin with the next
    green class.
    Coastal municipalities from neighboring states that intersect the fixed
    map windows are also colored. White lines delimit coastal municipalities,
    light-gray lines delimit Brazilian states, and dark-gray lines delimit
    countries. Gray shading denotes land, contrasting taupe coastal polygons
    denote municipalities without a valid integrated-risk value, and light
    blue denotes the ocean and estuarine channels. A 200-km scale bar is shown
    in every panel, and the locator inset identifies the four fixed windows
    along the Brazilian coast. The index is comparative among Brazilian coastal
    municipalities and does not represent absolute expected damage.}
    \label{fig:supplementary-integrated-risk-zooms}
\end{figure*}

Run from the repository root:

    python src/figures_article/make_article_supplementary_integrated_risk_zooms.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import lru_cache
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
from matplotlib.ticker import FixedLocator
import numpy as np
import pandas as pd
from shapely.geometry import box

from src.risk_integration.palettes import RISK_COLORS

try:
    from config.plot_config import apply_publication_style

    apply_publication_style()
except Exception:
    pass


RISK_PATH = ROOT / "site" / "public" / "data" / "risk_index_municipalities.geojson"
RISK_METADATA_PATH = ROOT / "site" / "public" / "data" / "risk_index_metadata.json"
COASTLINE_PATH = ROOT / "data" / "ne_10m_coastline" / "ne_10m_coastline.shp"
OUT_DIR = ROOT / "outputs" / "article_figures"
METADATA_DIR = OUT_DIR / "metadata"
OUTPUT_PATH = OUT_DIR / "supplementary_integrated_risk_zooms.png"
OUTPUT_METADATA_PATH = (
    METADATA_DIR / "supplementary_integrated_risk_zooms_metadata.json"
)

OUTPUT_CRS = "EPSG:4326"
RISK_KEY = "Risk_Hazard"
ARTICLE_DPI = 300

SOUTH_SOUTHEAST_STATES = ("RS", "SC", "PR", "SP", "RJ")
EAST_NORTHEAST_STATES = ("ES", "BA", "SE", "AL", "PE", "PB", "RN")
NORTHEAST_STATES = ("RN", "CE", "PI")
NORTH_STATES = ("PI", "MA", "PA")
SOUTH_SOUTHEAST_EXTENT = (-54.8, -39.8, -34.5, -20.2)
EAST_NORTHEAST_EXTENT = (-42.5, -34.0, -22.5, -4.5)
NORTHEAST_EXTENT = (-42.5, -34.5, -7.5, -1.5)
NORTH_EXTENT = (-52.8, -40.0, -4.3, 1.8)
CONTEXT_EXTENT = (-56.0, -33.0, -35.5, 3.0)

RISK_CLASS_COUNT = 8
ZERO_CLASS_EPSILON = 1e-6

LAND_COLOR = "#ddddda"
OCEAN_COLOR = "#e9f3f7"
NO_DATA_COLOR = "#968d80"
ZERO_EVENT_COLOR = RISK_COLORS[0]
MUNICIPAL_BOUNDARY_COLOR = "#f8fafc"
STATE_BORDER_COLOR = "#92928e"
COUNTRY_BORDER_COLOR = "#555553"
COAST_COLOR = "#334155"
GRID_COLOR = "#9aa9b0"
LOCATOR_COLORS = ("#b91c1c", "#1d4ed8", "#b45309", "#6d28d9")


def _map_aspect(extent: tuple[float, float, float, float]) -> float:
    """Approximate projected width/height for a PlateCarree regional window."""
    west, east, south, north = extent
    mean_latitude = np.deg2rad((south + north) / 2.0)
    return (east - west) * np.cos(mean_latitude) / (north - south)


def _row_layout(
    extents: tuple[
        tuple[float, float, float, float],
        tuple[float, float, float, float],
    ],
) -> tuple[tuple[float, float], float]:
    aspects = tuple(_map_aspect(extent) for extent in extents)
    return aspects, sum(aspects)


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _integrated_risk_boundaries(values: pd.Series) -> np.ndarray:
    """Match the data-scaled classes of the main integrated-risk panel."""
    observed_maximum = float(values.max(skipna=True))
    intervals = RISK_CLASS_COUNT - 1
    step = np.floor(observed_maximum / intervals * 100.0) / 100.0
    if not np.isfinite(step) or step <= 0:
        raise ValueError("Integrated-risk values do not define positive classes")
    return np.concatenate(
        ([0.0, ZERO_CLASS_EPSILON], step * np.arange(1, intervals + 1))
    )


def _numeric_stats(series: pd.Series) -> dict[str, float | int | None]:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return {"count": 0, "min": None, "mean": None, "median": None, "max": None}
    return {
        "count": int(values.count()),
        "min": round(float(values.min()), 6),
        "mean": round(float(values.mean()), 6),
        "median": round(float(values.median()), 6),
        "max": round(float(values.max()), 6),
    }


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
    brazil_states = tuple(
        record.geometry
        for record in shapereader.Reader(state_path).records()
        if record.attributes.get("ADM0_NAME") == "Brazil"
        and _geometry_intersects_extent(record.geometry, CONTEXT_EXTENT)
    )
    return land, countries, brazil_states


def _read_inputs() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    if not RISK_PATH.exists():
        raise FileNotFoundError(RISK_PATH)
    if not COASTLINE_PATH.exists():
        raise FileNotFoundError(COASTLINE_PATH)

    municipalities = gpd.read_file(RISK_PATH)
    if municipalities.crs is None:
        municipalities = municipalities.set_crs(OUTPUT_CRS)
    elif str(municipalities.crs).upper() != OUTPUT_CRS:
        municipalities = municipalities.to_crs(OUTPUT_CRS)

    required = {"state", "municipality_name", RISK_KEY}
    missing = sorted(required.difference(municipalities.columns))
    if missing:
        raise RuntimeError(
            f"{_relative(RISK_PATH)} lacks required fields: {', '.join(missing)}"
        )

    coastline = gpd.read_file(COASTLINE_PATH)
    if coastline.crs is None:
        coastline = coastline.set_crs(OUTPUT_CRS)
    elif str(coastline.crs).upper() != OUTPUT_CRS:
        coastline = coastline.to_crs(OUTPUT_CRS)
    return municipalities, coastline


def _setup_axis(
    axis: plt.Axes,
    *,
    extent: tuple[float, float, float, float],
    title: str,
    panel_label: str,
    draw_left_labels: bool = True,
    draw_bottom_labels: bool = True,
    graticule_step: float | None = None,
    label_size: float = 9,
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
    axis.set_extent(extent, crs=crs)

    west, east, south, north = extent
    # ``graticule_step`` overrides the automatic spacing. The multipanel figure
    # asks for a coarser graticule so the bottom labels stop crowding once the
    # panels are pushed together.
    longitude_step = graticule_step or (3.0 if east - west > 13.0 else 2.0)
    latitude_step = graticule_step or (3.0 if north - south > 10.0 else 2.0)
    longitudes = np.arange(
        np.ceil(west / longitude_step) * longitude_step,
        east + 0.01,
        longitude_step,
    )
    latitudes = np.arange(
        np.ceil(south / latitude_step) * latitude_step,
        north + 0.01,
        latitude_step,
    )
    grid = axis.gridlines(
        crs=crs,
        draw_labels=True,
        linewidth=0.4,
        color=GRID_COLOR,
        alpha=0.62,
        linestyle="--",
        zorder=1.2,
    )
    grid.xlocator = FixedLocator(longitudes)
    grid.ylocator = FixedLocator(latitudes)
    grid.top_labels = False
    grid.right_labels = False
    grid.left_labels = draw_left_labels
    grid.bottom_labels = draw_bottom_labels
    grid.xlabel_style = {"size": label_size, "color": "#374151"}
    grid.ylabel_style = {"size": label_size, "color": "#374151"}

    # An empty title is a request to draw none, so a figure can rely on the
    # panel letters alone and recover the vertical space.
    if title:
        axis.set_title(title, loc="center", fontsize=11, fontweight="bold", pad=7)
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
    _, countries, brazil_states = _natural_earth_context()
    axis.add_geometries(
        brazil_states,
        crs=crs,
        facecolor="none",
        edgecolor=STATE_BORDER_COLOR,
        linewidth=0.55,
        alpha=0.98,
        zorder=5,
    )
    axis.add_geometries(
        countries,
        crs=crs,
        facecolor="none",
        edgecolor=COUNTRY_BORDER_COLOR,
        linewidth=0.8,
        alpha=1.0,
        zorder=5.2,
    )
    axis.add_geometries(
        coastline.geometry,
        crs=crs,
        facecolor="none",
        edgecolor=COAST_COLOR,
        linewidth=0.55,
        zorder=5.4,
    )


def _draw_scale_bar(
    axis: plt.Axes,
    extent: tuple[float, float, float, float],
    distance_km: int = 200,
) -> None:
    """Draw the same geodesic-distance approximation in every regional panel."""
    west, east, south, north = extent
    latitude = south + 0.075 * (north - south)
    km_per_degree_lon = 111.32 * np.cos(np.deg2rad(latitude))
    length_degrees = distance_km / km_per_degree_lon
    x_end = east - 0.055 * (east - west)
    x_start = x_end - length_degrees
    crs = ccrs.PlateCarree()
    axis.plot(
        [x_start, x_end],
        [latitude, latitude],
        color="#111827",
        linewidth=2.4,
        solid_capstyle="butt",
        transform=crs,
        zorder=9,
    )
    axis.plot(
        [x_start, x_start, x_end, x_end],
        [latitude - 0.04, latitude + 0.04, latitude + 0.04, latitude - 0.04],
        color="#111827",
        linewidth=1.0,
        transform=crs,
        zorder=9,
    )
    axis.text(
        (x_start + x_end) / 2,
        latitude + 0.025 * (north - south),
        f"{distance_km} km",
        ha="center",
        va="bottom",
        fontsize=8,
        color="#111827",
        transform=crs,
        zorder=9,
    )


def _draw_locator(axis: plt.Axes) -> None:
    crs = ccrs.PlateCarree()
    locator = axis.inset_axes(
        [0.53, 0.20, 0.38, 0.36],
        projection=crs,
    )
    land, countries, _ = _natural_earth_context()
    locator.set_facecolor(OCEAN_COLOR)
    locator.add_geometries(
        land,
        crs=crs,
        facecolor=LAND_COLOR,
        edgecolor=COUNTRY_BORDER_COLOR,
        linewidth=0.3,
        zorder=1,
    )
    locator.add_geometries(
        countries,
        crs=crs,
        facecolor="none",
        edgecolor=COUNTRY_BORDER_COLOR,
        linewidth=0.35,
        zorder=2,
    )
    locator.set_extent((-75.0, -32.0, -36.0, 7.0), crs=crs)
    for label, extent, color in zip(
        "ABCD",
        (
            SOUTH_SOUTHEAST_EXTENT,
            EAST_NORTHEAST_EXTENT,
            NORTH_EXTENT,
            NORTHEAST_EXTENT,
        ),
        LOCATOR_COLORS,
    ):
        west, east, south, north = extent
        locator.add_geometries(
            [box(west, south, east, north)],
            crs=crs,
            facecolor="none",
            edgecolor=color,
            linewidth=1.2,
            zorder=3,
        )
        locator.text(
            (west + east) / 2,
            (south + north) / 2,
            label,
            transform=crs,
            ha="center",
            va="center",
            fontsize=6.5,
            fontweight="bold",
            color=color,
            zorder=4,
        )
    locator.set_title("Location", fontsize=7, pad=2)
    locator.set_xticks([])
    locator.set_yticks([])


def _plot_region(
    axis: plt.Axes,
    municipalities: gpd.GeoDataFrame,
    coastline: gpd.GeoDataFrame,
    *,
    states: tuple[str, ...],
    extent: tuple[float, float, float, float],
    title: str,
    panel_label: str,
    cmap: ListedColormap,
    norm: BoundaryNorm,
) -> dict[str, Any]:
    west, east, south, north = extent
    map_window = box(west, south, east, north)
    regional = municipalities[
        municipalities.geometry.intersects(map_window)
    ].copy()
    if regional.empty:
        raise RuntimeError(
            f"No coastal municipalities intersect the map window for {', '.join(states)}"
        )

    _setup_axis(
        axis,
        extent=extent,
        title=title,
        panel_label=panel_label,
    )
    regional.plot(
        ax=axis,
        facecolor=NO_DATA_COLOR,
        edgecolor=MUNICIPAL_BOUNDARY_COLOR,
        linewidth=0.32,
        zorder=2,
    )
    valid = regional[regional[RISK_KEY].notna()].copy()
    positive = valid[valid[RISK_KEY] > 0]
    zeros = valid[valid[RISK_KEY].eq(0)]
    positive.plot(
        ax=axis,
        column=RISK_KEY,
        cmap=cmap,
        norm=norm,
        edgecolor=MUNICIPAL_BOUNDARY_COLOR,
        linewidth=0.32,
        zorder=3,
    )
    if not zeros.empty:
        zeros.plot(
            ax=axis,
            color=ZERO_EVENT_COLOR,
            edgecolor=MUNICIPAL_BOUNDARY_COLOR,
            linewidth=0.32,
            zorder=3.1,
        )
    _draw_context(axis, coastline)
    _draw_scale_bar(axis, extent)
    axis.set_extent(extent, crs=ccrs.PlateCarree())
    return {
        "panel": panel_label,
        "title": title,
        "focus_states": list(states),
        "states_with_visible_municipalities": sorted(
            regional["state"].dropna().astype(str).unique().tolist()
        ),
        "extent": list(extent),
        "map_aspect_ratio": round(_map_aspect(extent), 6),
        "scale_bar_km": 200,
        "municipality_count": int(len(regional)),
        "valid_risk_count": int(valid[RISK_KEY].notna().sum()),
        "missing_risk_municipalities": regional.loc[
            regional[RISK_KEY].isna(),
            ["municipality_name", "state"],
        ].to_dict(orient="records"),
        "statistics": _numeric_stats(valid[RISK_KEY]),
    }


def _write_metadata(
    panels: list[dict[str, Any]],
    risk_boundaries: np.ndarray,
) -> None:
    source_metadata: dict[str, Any] = {}
    if RISK_METADATA_PATH.exists():
        source_metadata = json.loads(RISK_METADATA_PATH.read_text(encoding="utf-8"))
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "output": _relative(OUTPUT_PATH),
        "source": _relative(RISK_PATH),
        "source_metadata": _relative(RISK_METADATA_PATH),
        "source_scope": source_metadata.get("scope"),
        "risk_key": RISK_KEY,
        "risk_definition": source_metadata.get("integrated_risk_formula", {}).get(
            "expression",
            "Risk_Hazard=(Hazard_Index_mun*Exposure_Index*"
            "Vulnerability_CDF_PC1)^(1/3)",
        ),
        "integrated_risk_normalization": source_metadata.get(
            "integrated_risk_normalization"
        ),
        "panels": panels,
        "layout": {
            "rows": 2,
            "columns": 2,
            "cell_sizing": "derived from each extent's latitude-corrected map aspect",
        },
        "colorbar": {
            "type": "discrete",
            "boundaries": risk_boundaries.tolist(),
            "colors": list(RISK_COLORS[: len(risk_boundaries) - 1]),
            "label": "Integrated risk index (0-1)",
            "tick_labels": [
                "0",
                *[f"{value:g}" for value in risk_boundaries[2:]],
            ],
            "zero_class": {
                "interval": [0.0, 1e-6],
                "upper_bound_exclusive": True,
                "color": ZERO_EVENT_COLOR,
            },
            "shared_between_panels": True,
            "scale_matches_main_figure": True,
        },
        "map_context": {
            "crs": OUTPUT_CRS,
            "land_color": LAND_COLOR,
            "ocean_color": OCEAN_COLOR,
            "no_data_municipality_color": NO_DATA_COLOR,
            "zero_accepted_event_color": ZERO_EVENT_COLOR,
            "estuarine_channel_color": OCEAN_COLOR,
            "locator_inset": {
                "host_panel": "A",
                "extent": [-75.0, -32.0, -36.0, 7.0],
                "panel_rectangle_colors": list(LOCATOR_COLORS),
            },
            "coastline": _relative(COASTLINE_PATH),
            "country_boundaries": "Natural Earth 10m admin_0_boundary_lines_land",
            "brazilian_state_boundaries": (
                "Natural Earth 10m admin_1_states_provinces_lines"
            ),
        },
        "output_format": "PNG",
        "dpi": ARTICLE_DPI,
    }
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_METADATA_PATH.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    municipalities, coastline = _read_inputs()
    risk_boundaries = _integrated_risk_boundaries(municipalities[RISK_KEY])
    cmap = ListedColormap(
        list(RISK_COLORS[: len(risk_boundaries) - 1]),
        name="composite_score_inverted_green_to_red_integrated_risk",
    )
    norm = BoundaryNorm(risk_boundaries, cmap.N, clip=True)

    top_widths, top_aspect_sum = _row_layout(
        (SOUTH_SOUTHEAST_EXTENT, EAST_NORTHEAST_EXTENT)
    )
    bottom_widths, bottom_aspect_sum = _row_layout(
        (NORTH_EXTENT, NORTHEAST_EXTENT)
    )
    row_heights = (1.0 / top_aspect_sum, 1.0 / bottom_aspect_sum)

    figure = plt.figure(figsize=(13.2, 12.8), constrained_layout=False)
    outer_grid = figure.add_gridspec(
        2,
        1,
        left=0.055,
        right=0.985,
        top=0.96,
        bottom=0.11,
        height_ratios=row_heights,
        hspace=0.075,
    )
    top_grid = outer_grid[0, 0].subgridspec(
        1,
        2,
        width_ratios=top_widths,
        wspace=0.045,
    )
    bottom_grid = outer_grid[1, 0].subgridspec(
        1,
        2,
        width_ratios=bottom_widths,
        wspace=0.045,
    )
    axes = [
        figure.add_subplot(top_grid[0, 0], projection=ccrs.PlateCarree()),
        figure.add_subplot(top_grid[0, 1], projection=ccrs.PlateCarree()),
        figure.add_subplot(bottom_grid[0, 0], projection=ccrs.PlateCarree()),
        figure.add_subplot(bottom_grid[0, 1], projection=ccrs.PlateCarree()),
    ]
    panels = [
        _plot_region(
            axes[0],
            municipalities,
            coastline,
            states=SOUTH_SOUTHEAST_STATES,
            extent=SOUTH_SOUTHEAST_EXTENT,
            title="Rio Grande do Sul–Rio de Janeiro",
            panel_label="A",
            cmap=cmap,
            norm=norm,
        ),
        _plot_region(
            axes[1],
            municipalities,
            coastline,
            states=EAST_NORTHEAST_STATES,
            extent=EAST_NORTHEAST_EXTENT,
            title="Espírito Santo–Rio Grande do Norte",
            panel_label="B",
            cmap=cmap,
            norm=norm,
        ),
        _plot_region(
            axes[2],
            municipalities,
            coastline,
            states=NORTH_STATES,
            extent=NORTH_EXTENT,
            title="Piauí–Pará",
            panel_label="C",
            cmap=cmap,
            norm=norm,
        ),
        _plot_region(
            axes[3],
            municipalities,
            coastline,
            states=NORTHEAST_STATES,
            extent=NORTHEAST_EXTENT,
            title="Rio Grande do Norte–Piauí",
            panel_label="D",
            cmap=cmap,
            norm=norm,
        ),
    ]
    _draw_locator(axes[0])

    mappable = ScalarMappable(norm=norm, cmap=cmap)
    mappable.set_array([])
    colorbar_axis = figure.add_axes([0.22, 0.045, 0.60, 0.025])
    colorbar = figure.colorbar(
        mappable,
        cax=colorbar_axis,
        orientation="horizontal",
        boundaries=risk_boundaries,
        ticks=[risk_boundaries[1] / 2, *risk_boundaries[2:]],
        spacing="uniform",
        drawedges=True,
    )
    colorbar.set_label("Integrated risk index (0–1)", fontsize=10)
    colorbar.ax.tick_params(labelsize=9, length=3)
    colorbar.ax.set_xticklabels(
        ["0", *[f"{value:g}" for value in risk_boundaries[2:]]]
    )
    colorbar.outline.set_linewidth(0.75)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with plt.rc_context({"savefig.bbox": None}):
        figure.savefig(
            OUTPUT_PATH,
            dpi=ARTICLE_DPI,
            bbox_inches=None,
            facecolor="white",
        )
    plt.close(figure)
    _write_metadata(panels, risk_boundaries)
    print(_relative(OUTPUT_PATH))


if __name__ == "__main__":
    main()
