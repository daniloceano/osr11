r"""Generate supplementary regional zooms of the integrated coastal-risk index.

Suggested LaTeX figure block (requires ``\usepackage{graphicx}``)
-----------------------------------------------------------------
\begin{figure*}[htbp]
    \centering
    \includegraphics[width=\textwidth]{outputs/article_figures/supplementary_integrated_risk_zooms.png}
    \caption{Regional detail of the integrated compound coastal-risk index
    for municipalities along (a) the coast from Rio Grande do Sul to Rio de
    Janeiro and (b) the coast from Par\'a to Piau\'i. The integrated index is
    obtained by Min--Max normalizing to the interval [0,1] the product of the
    Social Vulnerability Index (scaled from 0 to 1) and the normalized
    frequency-duration-intensity Hazard Index transferred from the native
    ocean grid. Both panels use the same discrete class
    limits and green-to-red palette as the integrated-risk panel in the main
    figure, allowing direct comparison between regions.
    Coastal municipalities from neighboring states that intersect the fixed
    map windows are also colored. White lines delimit coastal municipalities,
    light-gray lines delimit Brazilian states, and dark-gray lines delimit
    countries. Gray shading denotes land, the darker-gray coastal polygon
    denotes a municipality without a valid integrated-risk value, and light
    blue denotes the ocean. The index is comparative among Brazilian coastal
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
NORTH_NORTHEAST_STATES = ("PA", "MA", "PI")
SOUTH_SOUTHEAST_EXTENT = (-54.8, -39.8, -34.5, -20.2)
NORTH_NORTHEAST_EXTENT = (-52.8, -40.0, -4.3, 1.8)
CONTEXT_EXTENT = (-56.0, -38.0, -35.5, 3.0)

RISK_BOUNDARIES = np.linspace(0.0, 1.0, 9)

LAND_COLOR = "#ddddda"
OCEAN_COLOR = "#e9f3f7"
NO_DATA_COLOR = "#c7c7c4"
MUNICIPAL_BOUNDARY_COLOR = "#f8fafc"
STATE_BORDER_COLOR = "#92928e"
COUNTRY_BORDER_COLOR = "#555553"
COAST_COLOR = "#334155"
GRID_COLOR = "#9aa9b0"


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


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
    longitude_step = 3.0 if east - west > 13.0 else 2.0
    latitude_step = 3.0 if north - south > 10.0 else 2.0
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
    grid.xlabel_style = {"size": 9, "color": "#374151"}
    grid.ylabel_style = {"size": 9, "color": "#374151"}

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
    valid.plot(
        ax=axis,
        column=RISK_KEY,
        cmap=cmap,
        norm=norm,
        edgecolor=MUNICIPAL_BOUNDARY_COLOR,
        linewidth=0.32,
        zorder=3,
    )
    _draw_context(axis, coastline)
    axis.set_extent(extent, crs=ccrs.PlateCarree())
    return {
        "panel": panel_label,
        "title": title,
        "focus_states": list(states),
        "states_with_visible_municipalities": sorted(
            regional["state"].dropna().astype(str).unique().tolist()
        ),
        "extent": list(extent),
        "municipality_count": int(len(regional)),
        "valid_risk_count": int(valid[RISK_KEY].notna().sum()),
        "missing_risk_municipalities": regional.loc[
            regional[RISK_KEY].isna(),
            ["municipality_name", "state"],
        ].to_dict(orient="records"),
        "statistics": _numeric_stats(valid[RISK_KEY]),
    }


def _write_metadata(panels: list[dict[str, Any]]) -> None:
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
        "risk_definition": (
            "Min-Max normalization to [0,1] of "
            "(SVI_Coast_2022 / 100) * Hazard_Index, where Hazard_Index is "
            "the native-grid normalized equal-weight combination of "
            "compound-event frequency, mean overlap duration, and mean "
            "normalized intensity"
        ),
        "panels": panels,
        "colorbar": {
            "type": "discrete",
            "boundaries": RISK_BOUNDARIES.tolist(),
            "colors": list(RISK_COLORS),
            "label": "Integrated risk index (0-1)",
            "shared_between_panels": True,
            "scale_matches_main_figure": True,
        },
        "map_context": {
            "crs": OUTPUT_CRS,
            "land_color": LAND_COLOR,
            "ocean_color": OCEAN_COLOR,
            "no_data_municipality_color": NO_DATA_COLOR,
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
    cmap = ListedColormap(
        RISK_COLORS,
        name="composite_score_inverted_green_to_red_integrated_risk",
    )
    norm = BoundaryNorm(RISK_BOUNDARIES, cmap.N, clip=True)

    figure = plt.figure(figsize=(13.2, 5.8), constrained_layout=False)
    grid_spec = figure.add_gridspec(
        1,
        2,
        width_ratios=(1.0, 1.82),
        left=0.055,
        right=0.985,
        top=0.93,
        bottom=0.19,
        wspace=0.10,
    )
    axes = [
        figure.add_subplot(grid_spec[0, 0], projection=ccrs.PlateCarree()),
        figure.add_subplot(grid_spec[0, 1], projection=ccrs.PlateCarree()),
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
            states=NORTH_NORTHEAST_STATES,
            extent=NORTH_NORTHEAST_EXTENT,
            title="Pará–Piauí",
            panel_label="B",
            cmap=cmap,
            norm=norm,
        ),
    ]

    mappable = ScalarMappable(norm=norm, cmap=cmap)
    mappable.set_array([])
    colorbar_axis = figure.add_axes([0.22, 0.085, 0.60, 0.035])
    colorbar = figure.colorbar(
        mappable,
        cax=colorbar_axis,
        orientation="horizontal",
        boundaries=RISK_BOUNDARIES,
        ticks=RISK_BOUNDARIES,
        spacing="uniform",
        drawedges=True,
    )
    colorbar.set_label("Integrated risk index (0–1)", fontsize=10)
    colorbar.ax.tick_params(labelsize=9, length=3)
    colorbar.outline.set_linewidth(0.75)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        OUTPUT_PATH,
        dpi=ARTICLE_DPI,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(figure)
    _write_metadata(panels)
    print(_relative(OUTPUT_PATH))


if __name__ == "__main__":
    main()
