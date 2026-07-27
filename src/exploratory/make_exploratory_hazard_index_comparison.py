"""Compare the former count-only and current multimetric Hazard Indices.

This exploratory audit contrasts the superseded count-only calculation with
the current equal-weight product based on compound-event frequency, mean
overlap duration, and mean normalized compound intensity:

    former_count_only = minmax(compound_c)

    current_multimetric_raw = (
        minmax(compound_c)
        + minmax(mean_overl)
        + minmax(mean_compo)
    ) / 3

    current_multimetric = minmax(current_multimetric_raw)

    difference = former_count_only - current_multimetric

The first two maps share the same discrete 0--1 scale. The difference map uses
a symmetric discrete scale centered at zero, so warm colors indicate that the
former count-only index is larger and cool colors indicate that the current
multimetric index is larger.

The script also calculates the same multimetric formula over all 808 native
ocean grid points, normalizes that native-grid product to 0--1, and transposes
it to short coastline segments following the design of the coastal
compound-event-rate map.

Run from the repository root:

    python src/exploratory/make_exploratory_hazard_index_comparison.py
"""
from __future__ import annotations

from datetime import date, datetime, timezone
import json
import math
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import cartopy.crs as ccrs
import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.ticker import FormatStrFormatter
import numpy as np
import pandas as pd
from shapely.geometry import MultiLineString
from shapely.ops import linemerge, unary_union

from src.figures_article.make_article_supplementary_integrated_risk_zooms import (
    COASTLINE_PATH,
    COUNTRY_BORDER_COLOR,
    LAND_COLOR,
    MUNICIPAL_BOUNDARY_COLOR,
    NO_DATA_COLOR,
    OCEAN_COLOR,
    RISK_COLORS,
    RISK_METADATA_PATH,
    RISK_PATH,
    STATE_BORDER_COLOR,
    _draw_context,
    _numeric_stats,
    _read_inputs,
    _relative,
    _setup_axis,
)
from src.risk_integration.coastal_projection import (
    line_parts as _line_parts,
    project_values_to_coastline,
)
from src.risk_integration.hazard_index import derive_native_hazard_index


OUTPUT_DIR = ROOT / "outputs" / "exploratory_hazard_index_comparison"
FIGURE_DIR = OUTPUT_DIR / "figures"
DATA_DIR = OUTPUT_DIR / "data"
METADATA_DIR = OUTPUT_DIR / "metadata"
RUN_DATE = date.today().strftime("%Y%m%d")
FIGURE_PATH = (
    FIGURE_DIR
    / f"explore_hazard_index_count_only_vs_multimetric_{RUN_DATE}.png"
)
DATA_PATH = DATA_DIR / "municipal_hazard_index_count_only_vs_multimetric.csv"
METADATA_PATH = (
    METADATA_DIR
    / "explore_hazard_index_count_only_vs_multimetric_metadata.json"
)
COASTAL_FIGURE_PATH = (
    FIGURE_DIR
    / f"explore_multimetric_hazard_index_coastline_{RUN_DATE}.png"
)
COASTAL_SEGMENTS_PATH = (
    DATA_DIR / "multimetric_hazard_index_coastline_segments.geojson"
)
NATIVE_GRID_SOURCE_PATH = (
    ROOT / "outputs" / "storm_catalog" / "compound" / "compound_metrics.csv"
)
NATIVE_GRID_DATA_PATH = DATA_DIR / "native_grid_multimetric_hazard_index.csv"

MAP_EXTENT = (-56.0, -27.0, -36.5, 7.0)
COASTAL_MAP_EXTENT = (-56.0, -32.0, -35.5, 6.5)
EXPLORATORY_DPI = 150
INDEX_BOUNDARIES = np.linspace(0.0, 1.0, 9)
REQUIRED_FIELDS = {
    "municipality_name",
    "state",
    "grid_lat",
    "grid_lon",
    "compound_c",
    "mean_overl",
    "mean_compo",
    "Hazard_Frequency",
    "Hazard_Duration",
    "Hazard_Intensity",
    "Hazard_Index_raw",
    "Hazard_Index",
    "CountOnly_Hazard_Index",
}

CURRENT_KEY = "hazard_former_count_only"
RAW_ALTERNATIVE_KEY = "hazard_current_multimetric_raw"
ALTERNATIVE_KEY = "hazard_current_multimetric"
DIFFERENCE_KEY = "hazard_count_only_minus_multimetric"


def _minmax(series: pd.Series) -> pd.Series:
    """Min--Max normalize finite values while preserving missing values."""
    values = pd.to_numeric(series, errors="coerce")
    finite = values[np.isfinite(values)]
    if finite.empty:
        raise ValueError(f"No finite values are available for {series.name!r}")
    lower = float(finite.min())
    upper = float(finite.max())
    if math.isclose(lower, upper):
        result = pd.Series(np.nan, index=values.index, dtype=float)
        result.loc[finite.index] = 0.0
        return result
    return (values - lower) / (upper - lower)


def _derive_indices(
    municipalities: gpd.GeoDataFrame,
) -> tuple[gpd.GeoDataFrame, dict[str, pd.Series]]:
    missing = sorted(REQUIRED_FIELDS.difference(municipalities.columns))
    if missing:
        raise RuntimeError(
            f"{_relative(RISK_PATH)} lacks required fields: {', '.join(missing)}"
        )

    result = municipalities.copy()
    components = {
        "frequency": pd.to_numeric(result["Hazard_Frequency"], errors="coerce"),
        "duration": pd.to_numeric(result["Hazard_Duration"], errors="coerce"),
        "intensity": pd.to_numeric(result["Hazard_Intensity"], errors="coerce"),
    }
    result[CURRENT_KEY] = pd.to_numeric(
        result["CountOnly_Hazard_Index"],
        errors="coerce",
    )
    result[RAW_ALTERNATIVE_KEY] = pd.to_numeric(
        result["Hazard_Index_raw"],
        errors="coerce",
    )
    result[ALTERNATIVE_KEY] = pd.to_numeric(
        result["Hazard_Index"],
        errors="coerce",
    )
    result[DIFFERENCE_KEY] = (
        result[CURRENT_KEY] - result[ALTERNATIVE_KEY]
    )
    return result, components


def _derive_native_grid_index() -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load the official native-grid Hazard Index and add audit aliases."""
    result, official_metadata = derive_native_hazard_index()
    components = {
        "frequency": result["Hazard_Frequency"],
        "duration": result["Hazard_Duration"],
        "intensity": result["Hazard_Intensity"],
    }
    result["frequency_minmax"] = result["Hazard_Frequency"]
    result["duration_minmax"] = result["Hazard_Duration"]
    result["intensity_minmax"] = result["Hazard_Intensity"]
    result[CURRENT_KEY] = result["Hazard_Frequency"]
    result[RAW_ALTERNATIVE_KEY] = result["Hazard_Index_raw"]
    result[ALTERNATIVE_KEY] = result["Hazard_Index"]
    result[DIFFERENCE_KEY] = (
        result[CURRENT_KEY] - result[ALTERNATIVE_KEY]
    )
    result = result.dropna(
        subset=["grid_lon", "grid_lat", ALTERNATIVE_KEY]
    ).copy()
    metadata = {
        "source": _relative(NATIVE_GRID_SOURCE_PATH),
        "normalization_domain": "all native ocean grid points",
        "grid_point_count": int(len(result)),
        "official_hazard_metadata": official_metadata,
        "formulas": {
            RAW_ALTERNATIVE_KEY: (
                "[minmax(compound_count_total) + "
                "minmax(mean_overlap_duration) + "
                "minmax(mean_compound_intensity_norm)] / 3"
            ),
            ALTERNATIVE_KEY: "Hazard_Index = norm_native(Hazard_Index_raw)",
        },
        "component_statistics": {
            key: _numeric_stats(series)
            for key, series in components.items()
        },
        "raw_index_statistics": _numeric_stats(
            result[RAW_ALTERNATIVE_KEY]
        ),
        "final_index_statistics": _numeric_stats(result[ALTERNATIVE_KEY]),
        "comparison_statistics": {
            CURRENT_KEY: _numeric_stats(result[CURRENT_KEY]),
            ALTERNATIVE_KEY: _numeric_stats(result[ALTERNATIVE_KEY]),
            DIFFERENCE_KEY: _numeric_stats(result[DIFFERENCE_KEY]),
        },
    }
    return result, metadata


def _build_coastal_segments(
    municipalities: gpd.GeoDataFrame,
    coastline: gpd.GeoDataFrame,
    native_grid: pd.DataFrame,
) -> tuple[gpd.GeoDataFrame, dict[str, Any]]:
    """Assign short coastal segments to the nearest native ocean point.

    Delegates to the canonical Step 4 implementation so this exploratory audit
    uses exactly the same coastline clipping, segmentation, and nearest-point
    association as the article figure and the website layer.
    """
    return project_values_to_coastline(
        native_grid,
        (CURRENT_KEY, ALTERNATIVE_KEY, DIFFERENCE_KEY),
        municipalities=municipalities,
        coastline=coastline,
    )


def _difference_boundaries(values: pd.Series) -> np.ndarray:
    finite = pd.to_numeric(values, errors="coerce").dropna()
    if finite.empty:
        raise ValueError("No finite differences are available")
    limit = math.ceil(float(finite.abs().max()) * 10.0) / 10.0
    limit = max(limit, 0.1)
    return np.linspace(-limit, limit, 9)


def _set_left_grid_labels(axis: plt.Axes, visible: bool) -> None:
    """Keep latitude labels only on the first map."""
    for gridliner in getattr(axis, "_gridliners", []):
        gridliner.left_labels = visible


def _plot_panel(
    axis: plt.Axes,
    municipalities: gpd.GeoDataFrame,
    coastline: gpd.GeoDataFrame,
    *,
    key: str,
    title: str,
    panel_label: str,
    cmap: ListedColormap,
    norm: BoundaryNorm,
    draw_left_labels: bool,
) -> dict[str, Any]:
    _setup_axis(
        axis,
        extent=MAP_EXTENT,
        title=title,
        panel_label=panel_label,
    )
    _set_left_grid_labels(axis, draw_left_labels)

    municipalities.plot(
        ax=axis,
        facecolor=NO_DATA_COLOR,
        edgecolor=MUNICIPAL_BOUNDARY_COLOR,
        linewidth=0.16,
        zorder=2,
    )
    valid = municipalities[municipalities[key].notna()].copy()
    valid.plot(
        ax=axis,
        column=key,
        cmap=cmap,
        norm=norm,
        edgecolor=MUNICIPAL_BOUNDARY_COLOR,
        linewidth=0.16,
        zorder=3,
    )
    _draw_context(axis, coastline)
    axis.set_extent(MAP_EXTENT, crs=ccrs.PlateCarree())
    return {
        "panel": panel_label,
        "title": title,
        "field": key,
        "statistics": _numeric_stats(valid[key]),
    }


def _add_colorbar(
    figure: plt.Figure,
    *,
    axes: tuple[plt.Axes, ...],
    cmap: ListedColormap,
    norm: BoundaryNorm,
    boundaries: np.ndarray,
    label: str,
) -> None:
    positions = [axis.get_position() for axis in axes]
    left = min(position.x0 for position in positions)
    right = max(position.x1 for position in positions)
    bottom = min(position.y0 for position in positions) - 0.085
    colorbar_axis = figure.add_axes([left, bottom, right - left, 0.026])
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
    colorbar.set_label(label, fontsize=10)
    colorbar.ax.xaxis.set_major_formatter(FormatStrFormatter("%.2f"))
    colorbar.ax.tick_params(labelsize=8, length=3)
    colorbar.outline.set_linewidth(0.75)


def _plot_coastal_panel(
    axis: plt.Axes,
    segments: gpd.GeoDataFrame,
    coastline: gpd.GeoDataFrame,
    *,
    key: str,
    title: str,
    panel_label: str,
    cmap: ListedColormap,
    norm: BoundaryNorm,
    boundaries: np.ndarray,
    draw_left_labels: bool,
) -> dict[str, Any]:
    _setup_axis(
        axis,
        extent=COASTAL_MAP_EXTENT,
        title=title,
        panel_label=panel_label,
    )
    _set_left_grid_labels(axis, draw_left_labels)
    _draw_context(axis, coastline)

    values = segments[key].to_numpy(dtype=float)
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
        "field": key,
        "statistics": _numeric_stats(segments[key]),
    }


def _plot_coastal_comparison(
    segments: gpd.GeoDataFrame,
    coastline: gpd.GeoDataFrame,
    *,
    index_cmap: ListedColormap,
    index_norm: BoundaryNorm,
    difference_cmap: ListedColormap,
    difference_norm: BoundaryNorm,
    difference_boundaries: np.ndarray,
) -> list[dict[str, Any]]:
    figure, axes = plt.subplots(
        1,
        3,
        figsize=(14.6, 6.4),
        constrained_layout=False,
        subplot_kw={"projection": ccrs.PlateCarree()},
    )
    figure.subplots_adjust(
        left=0.045,
        right=0.985,
        top=0.955,
        bottom=0.17,
        wspace=0.09,
    )
    panels = [
        _plot_coastal_panel(
            axes[0],
            segments,
            coastline,
            key=CURRENT_KEY,
            title="Former: count-only hazard",
            panel_label="A",
            cmap=index_cmap,
            norm=index_norm,
            boundaries=INDEX_BOUNDARIES,
            draw_left_labels=True,
        ),
        _plot_coastal_panel(
            axes[1],
            segments,
            coastline,
            key=ALTERNATIVE_KEY,
            title="Current: frequency + duration + intensity",
            panel_label="B",
            cmap=index_cmap,
            norm=index_norm,
            boundaries=INDEX_BOUNDARIES,
            draw_left_labels=False,
        ),
        _plot_coastal_panel(
            axes[2],
            segments,
            coastline,
            key=DIFFERENCE_KEY,
            title="Difference: count-only − multimetric",
            panel_label="C",
            cmap=difference_cmap,
            norm=difference_norm,
            boundaries=difference_boundaries,
            draw_left_labels=False,
        ),
    ]

    figure.canvas.draw()
    _add_colorbar(
        figure,
        axes=(axes[0], axes[1]),
        cmap=index_cmap,
        norm=index_norm,
        boundaries=INDEX_BOUNDARIES,
        label="Hazard index (0–1)",
    )
    _add_colorbar(
        figure,
        axes=(axes[2],),
        cmap=difference_cmap,
        norm=difference_norm,
        boundaries=difference_boundaries,
        label="Count-only − multimetric Hazard Index",
    )
    figure.savefig(
        COASTAL_FIGURE_PATH,
        dpi=EXPLORATORY_DPI,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(figure)
    return panels


def _write_data(
    municipalities: gpd.GeoDataFrame,
    components: dict[str, pd.Series],
) -> None:
    table = municipalities[
        [
            "municipality_name",
            "state",
            "compound_c",
            "mean_overl",
            "mean_compo",
            "Hazard_Index",
        ]
    ].copy()
    table["frequency_minmax"] = components["frequency"]
    table["duration_minmax"] = components["duration"]
    table["intensity_minmax"] = components["intensity"]
    table[CURRENT_KEY] = municipalities[CURRENT_KEY]
    table[RAW_ALTERNATIVE_KEY] = municipalities[RAW_ALTERNATIVE_KEY]
    table[ALTERNATIVE_KEY] = municipalities[ALTERNATIVE_KEY]
    table[DIFFERENCE_KEY] = municipalities[DIFFERENCE_KEY]
    table.to_csv(DATA_PATH, index=False, float_format="%.6f")


def _write_metadata(
    municipalities: gpd.GeoDataFrame,
    components: dict[str, pd.Series],
    panels: list[dict[str, Any]],
    coastal_panels: list[dict[str, Any]],
    difference_boundaries: np.ndarray,
    native_grid_metadata: dict[str, Any],
    coastal_assignment: dict[str, Any],
) -> None:
    component_table = pd.DataFrame(components)
    source_metadata: dict[str, Any] = {}
    if RISK_METADATA_PATH.exists():
        source_metadata = json.loads(
            RISK_METADATA_PATH.read_text(encoding="utf-8")
        )
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "figure_role": (
            "exploratory audit of the former count-only product against the "
            "current official multimetric Hazard Index"
        ),
        "source": _relative(RISK_PATH),
        "source_metadata": _relative(RISK_METADATA_PATH),
        "formulas": {
            CURRENT_KEY: (
                "CountOnly_Hazard_Index = minmax_municipal(compound_c)"
            ),
            RAW_ALTERNATIVE_KEY: (
                "[Hazard_Frequency + Hazard_Duration + Hazard_Intensity] / 3; "
                "components normalized across the 808-point native grid"
            ),
            ALTERNATIVE_KEY: (
                "official Hazard_Index = norm_native(Hazard_Index_raw)"
            ),
            DIFFERENCE_KEY: (
                "hazard_former_count_only - hazard_current_multimetric"
            ),
        },
        "component_interpretation": {
            "compound_c": (
                "absolute compound-event count over the 1993-2025 record"
            ),
            "mean_overl": "mean compound-event overlap duration in days",
            "mean_compo": (
                "mean normalized compound-event intensity; already normalized "
                "domain-wide at event level and re-scaled across the 808-point "
                "native grid for equal-weight aggregation"
            ),
        },
        "equal_weights": {
            "frequency": 1.0 / 3.0,
            "duration": 1.0 / 3.0,
            "intensity": 1.0 / 3.0,
        },
        "panels": panels,
        "component_statistics": {
            key: _numeric_stats(series)
            for key, series in components.items()
        },
        "component_pearson_correlations": (
            component_table.corr().round(6).to_dict()
        ),
        "count_only_vs_multimetric_pearson_correlation": round(
            float(
                municipalities[
                    [CURRENT_KEY, ALTERNATIVE_KEY]
                ].corr().iloc[0, 1]
            ),
            6,
        ),
        "colorbars": {
            "indices": {
                "type": "discrete",
                "boundaries": INDEX_BOUNDARIES.tolist(),
                "colors": list(RISK_COLORS),
                "shared_by_panels": ["A", "B"],
            },
            "difference": {
                "type": "discrete_diverging",
                "boundaries": difference_boundaries.tolist(),
                "center": 0.0,
                "meaning": (
                    "positive: former count-only index is larger; "
                    "negative: current multimetric index is larger"
                ),
            },
        },
        "map_context": {
            "extent": list(MAP_EXTENT),
            "land_color": LAND_COLOR,
            "ocean_color": OCEAN_COLOR,
            "no_data_color": NO_DATA_COLOR,
            "country_border_color": COUNTRY_BORDER_COLOR,
            "state_border_color": STATE_BORDER_COLOR,
            "coastline": _relative(COASTLINE_PATH),
        },
        "coastal_line_map": {
            "fields": [CURRENT_KEY, ALTERNATIVE_KEY, DIFFERENCE_KEY],
            "panels": coastal_panels,
            "map_extent": list(COASTAL_MAP_EXTENT),
            "native_grid_index": native_grid_metadata,
            "assignment": coastal_assignment,
            "colorbars": {
                "indices": {
                    "type": "discrete",
                    "boundaries": INDEX_BOUNDARIES.tolist(),
                    "colors": list(RISK_COLORS),
                    "shared_by_panels": ["A", "B"],
                },
                "difference": {
                    "type": "discrete_diverging",
                    "boundaries": difference_boundaries.tolist(),
                    "center": 0.0,
                },
            },
        },
        "source_scope": source_metadata.get("scope"),
        "outputs": {
            "municipal_comparison_figure": _relative(FIGURE_PATH),
            "coastal_line_figure": _relative(COASTAL_FIGURE_PATH),
            "municipal_table": _relative(DATA_PATH),
            "native_grid_table": _relative(NATIVE_GRID_DATA_PATH),
            "coastal_segments": _relative(COASTAL_SEGMENTS_PATH),
            "metadata": _relative(METADATA_PATH),
        },
        "output_format": "PNG",
        "dpi": EXPLORATORY_DPI,
    }
    METADATA_PATH.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    municipalities, coastline = _read_inputs()
    municipalities, components = _derive_indices(municipalities)
    native_grid, native_grid_metadata = _derive_native_grid_index()
    segments, coastal_assignment = _build_coastal_segments(
        municipalities,
        coastline,
        native_grid,
    )
    difference_boundaries = _difference_boundaries(
        pd.concat(
            [
                municipalities[DIFFERENCE_KEY],
                native_grid[DIFFERENCE_KEY],
            ],
            ignore_index=True,
        )
    )

    index_cmap = ListedColormap(
        RISK_COLORS,
        name="hazard_index_green_to_red",
    )
    index_norm = BoundaryNorm(
        INDEX_BOUNDARIES,
        index_cmap.N,
        clip=True,
    )
    difference_colors = plt.get_cmap("RdBu_r")(
        np.linspace(0.06, 0.94, len(difference_boundaries) - 1)
    )
    difference_cmap = ListedColormap(
        difference_colors,
        name="count_only_minus_multimetric_blue_to_red",
    )
    difference_norm = BoundaryNorm(
        difference_boundaries,
        difference_cmap.N,
        clip=True,
    )

    figure, axes = plt.subplots(
        1,
        3,
        figsize=(14.6, 6.4),
        constrained_layout=False,
        subplot_kw={"projection": ccrs.PlateCarree()},
    )
    figure.subplots_adjust(
        left=0.045,
        right=0.985,
        top=0.955,
        bottom=0.17,
        wspace=0.09,
    )
    panels = [
        _plot_panel(
            axes[0],
            municipalities,
            coastline,
            key=CURRENT_KEY,
            title="Former: count-only hazard",
            panel_label="A",
            cmap=index_cmap,
            norm=index_norm,
            draw_left_labels=True,
        ),
        _plot_panel(
            axes[1],
            municipalities,
            coastline,
            key=ALTERNATIVE_KEY,
            title="Current: frequency + duration + intensity",
            panel_label="B",
            cmap=index_cmap,
            norm=index_norm,
            draw_left_labels=False,
        ),
        _plot_panel(
            axes[2],
            municipalities,
            coastline,
            key=DIFFERENCE_KEY,
            title="Difference: count-only − multimetric",
            panel_label="C",
            cmap=difference_cmap,
            norm=difference_norm,
            draw_left_labels=False,
        ),
    ]

    figure.canvas.draw()
    _add_colorbar(
        figure,
        axes=(axes[0], axes[1]),
        cmap=index_cmap,
        norm=index_norm,
        boundaries=INDEX_BOUNDARIES,
        label="Hazard index (0–1)",
    )
    _add_colorbar(
        figure,
        axes=(axes[2],),
        cmap=difference_cmap,
        norm=difference_norm,
        boundaries=difference_boundaries,
        label="Count-only − multimetric Hazard Index",
    )

    for directory in (FIGURE_DIR, DATA_DIR, METADATA_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        FIGURE_PATH,
        dpi=EXPLORATORY_DPI,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(figure)
    coastal_panels = _plot_coastal_comparison(
        segments,
        coastline,
        index_cmap=index_cmap,
        index_norm=index_norm,
        difference_cmap=difference_cmap,
        difference_norm=difference_norm,
        difference_boundaries=difference_boundaries,
    )
    _write_data(municipalities, components)
    native_grid.to_csv(
        NATIVE_GRID_DATA_PATH,
        index=False,
        float_format="%.6f",
    )
    segments.to_file(
        COASTAL_SEGMENTS_PATH,
        driver="GeoJSON",
    )
    _write_metadata(
        municipalities,
        components,
        panels,
        coastal_panels,
        difference_boundaries,
        native_grid_metadata,
        coastal_assignment,
    )

    print(_relative(FIGURE_PATH))
    print(_relative(COASTAL_FIGURE_PATH))
    print(_relative(DATA_PATH))
    print(_relative(NATIVE_GRID_DATA_PATH))
    print(_relative(COASTAL_SEGMENTS_PATH))
    print(_relative(METADATA_PATH))


if __name__ == "__main__":
    main()
