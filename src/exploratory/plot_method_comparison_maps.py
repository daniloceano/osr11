"""Coastal maps of each hazard component: legacy method, MHWS method, difference.

Draws one figure per component in the cartographic style of
``outputs/article_figures/coastal_hazard_index_components.png``, reusing the
same coastline projection, the same Natural Earth context and the same
segment rendering, so the maps can be read against the published figure without
a change of visual convention.

Each figure carries three panels:

    (a) legacy   — SSH_total detector
    (b) new      — zos detector conditioned on SWL > MHWS
    (c) Δ        — new minus legacy, on a diverging scale centred at zero

The difference panel is the point of the exercise: it shows where the change of
detector moved the component, and in which direction. Red means the new method
raised the component there, blue means it lowered it.

Values are consumed as computed by
:mod:`compare_methods_ssh_total_vs_mhws` — nothing is renormalized here, so the
0-1 scales are the ones the hazard index actually uses.

Read-only. Publishes nothing: output goes to the comparison folder, not to
``outputs/article_figures``.

Usage:
    python -m src.exploratory.plot_method_comparison_maps

Output:
    outputs/method_comparison_ssh_total_vs_mhws/figures/map_<component>_legacy_vs_mhws.png
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import cartopy.crs as ccrs
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.cm import ScalarMappable
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.ticker import FixedLocator, FormatStrFormatter
from shapely.geometry import MultiLineString
from shapely.ops import linemerge, unary_union

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.figures_article.make_article_coastal_hazard_components_map import (  # noqa: E402
    GRID_COLOR,
    _draw_context,
    _natural_earth_context,
)
from src.figures_article.make_article_supplementary_integrated_risk_zooms import (  # noqa: E402
    ARTICLE_DPI,
    LAND_COLOR,
    OCEAN_COLOR,
)
from src.risk_integration.coastal_projection import (  # noqa: E402
    COASTAL_MAP_EXTENT,
    line_parts,
    project_values_to_coastline,
    read_coastal_inputs,
)
from src.risk_integration.palettes import component_colors, diverging_colors  # noqa: E402

SOURCE = (
    ROOT / "outputs" / "method_comparison_ssh_total_vs_mhws" / "hazard_by_point.csv"
)
OUT_DIR = ROOT / "outputs" / "method_comparison_ssh_total_vs_mhws" / "figures"

#: Component -> (display name, short slug).
COMPONENTS = (
    ("Hazard_Frequency", "Frequência", "frequency"),
    ("Hazard_Duration", "Duração", "duration"),
    ("Hazard_Intensity", "Intensidade", "intensity"),
    ("Hazard_Index", "Índice de perigo", "index"),
)

VALUE_BOUNDARIES = np.linspace(0.0, 1.0, 9)
DIFF_BOUNDARIES = np.round(np.arange(-0.6, 0.61, 0.15), 3)
SEGMENT_LINEWIDTH = 4.0


def _setup_axis(
    axis: plt.Axes,
    *,
    title: str,
    panel_label: str,
    draw_left_labels: bool,
) -> None:
    crs = ccrs.PlateCarree()
    land, _, _ = _natural_earth_context()
    axis.set_facecolor(OCEAN_COLOR)
    axis.add_geometries(
        land, crs=crs, facecolor=LAND_COLOR, edgecolor="none", zorder=0.5
    )
    axis.set_extent(COASTAL_MAP_EXTENT, crs=crs)
    grid = axis.gridlines(
        crs=crs, draw_labels=True, linewidth=0.35, color=GRID_COLOR,
        alpha=0.55, linestyle="--", zorder=1.2,
    )
    grid.xlocator = FixedLocator(np.arange(-55.0, -29.9, 10.0))
    grid.ylocator = FixedLocator(np.arange(-35.0, 10.0, 10.0))
    grid.top_labels = False
    grid.right_labels = False
    grid.left_labels = draw_left_labels
    grid.bottom_labels = True
    grid.xlabel_style = {"size": 7.5, "color": "#374151"}
    grid.ylabel_style = {"size": 7.5, "color": "#374151"}
    axis.set_title(title, fontsize=10.0, fontweight="bold", pad=6)
    axis.text(
        0.03, 0.972, panel_label, transform=axis.transAxes, ha="left", va="top",
        fontsize=10.5, fontweight="bold",
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "white",
              "edgecolor": "#cbd5e1", "alpha": 0.94},
        zorder=10,
    )


def _draw_segments(
    axis: plt.Axes,
    segments: gpd.GeoDataFrame,
    field: str,
    cmap: ListedColormap,
    boundaries: np.ndarray,
) -> None:
    values = segments[field].to_numpy(dtype=float)
    class_indices = np.digitize(values, boundaries[1:-1])
    for class_index in range(len(boundaries) - 1):
        geometries = segments.geometry[class_indices == class_index].tolist()
        if not geometries:
            continue
        dissolved = unary_union(geometries)
        merged = (
            linemerge(dissolved)
            if isinstance(dissolved, MultiLineString)
            else dissolved
        )
        axis.add_geometries(
            line_parts(merged), crs=ccrs.PlateCarree(), facecolor="none",
            edgecolor=cmap(class_index), linewidth=SEGMENT_LINEWIDTH, zorder=8,
        )
    axis.set_extent(COASTAL_MAP_EXTENT, crs=ccrs.PlateCarree())


def _colorbar(
    figure: plt.Figure,
    axis: plt.Axes,
    *,
    cmap: ListedColormap,
    boundaries: np.ndarray,
    label: str,
    tick_format: str,
) -> None:
    position = axis.get_position()
    cax = figure.add_axes(
        [position.x0, position.y0 - 0.055, position.width, 0.016]
    )
    norm = BoundaryNorm(boundaries, cmap.N, clip=True)
    mappable = ScalarMappable(norm=norm, cmap=cmap)
    mappable.set_array([])
    bar = figure.colorbar(
        mappable, cax=cax, orientation="horizontal", boundaries=boundaries,
        ticks=boundaries, spacing="uniform", drawedges=True,
    )
    bar.set_label(label, fontsize=8.5, labelpad=2.0)
    bar.ax.xaxis.set_major_formatter(FormatStrFormatter(tick_format))
    bar.ax.tick_params(labelsize=7.2, length=2.6)
    labels = bar.ax.get_xticklabels()
    if labels:
        labels[0].set_horizontalalignment("left")
        labels[-1].set_horizontalalignment("right")
    bar.outline.set_linewidth(0.7)


def build_figure(
    segments: gpd.GeoDataFrame,
    coastline: gpd.GeoDataFrame,
    *,
    field: str,
    display_name: str,
    slug: str,
) -> dict[str, Any]:
    value_cmap = ListedColormap(component_colors(len(VALUE_BOUNDARIES) - 1))
    diff_cmap = ListedColormap(diverging_colors(len(DIFF_BOUNDARIES) - 1))

    figure, axes = plt.subplots(
        1, 3, figsize=(12.6, 6.4),
        subplot_kw={"projection": ccrs.PlateCarree()},
    )

    panels = (
        (f"{field}_legacy", "legado — SSH_total", "(a)", value_cmap, VALUE_BOUNDARIES),
        (f"{field}_mhws", "novo — zos + condição MHWS", "(b)", value_cmap, VALUE_BOUNDARIES),
        ("_delta", "Δ  novo − legado", "(c)", diff_cmap, DIFF_BOUNDARIES),
    )

    stats: dict[str, Any] = {}
    for index, (column, title, label, cmap, boundaries) in enumerate(panels):
        axis = axes[index]
        _setup_axis(axis, title=title, panel_label=label, draw_left_labels=index == 0)
        _draw_context(axis, coastline)
        _draw_segments(axis, segments, column, cmap, boundaries)
        values = pd.to_numeric(segments[column], errors="coerce").dropna()
        stats[column] = {
            "min": round(float(values.min()), 4),
            "max": round(float(values.max()), 4),
            "mean": round(float(values.mean()), 4),
        }

    figure.suptitle(
        f"{display_name} — método legado × método MHWS",
        fontsize=13.0, fontweight="bold", y=0.955,
    )

    figure.subplots_adjust(left=0.045, right=0.985, top=0.88, bottom=0.16, wspace=0.10)
    _colorbar(figure, axes[0], cmap=value_cmap, boundaries=VALUE_BOUNDARIES,
              label="componente normalizada (0–1)", tick_format="%.2f")
    _colorbar(figure, axes[1], cmap=value_cmap, boundaries=VALUE_BOUNDARIES,
              label="componente normalizada (0–1)", tick_format="%.2f")
    _colorbar(figure, axes[2], cmap=diff_cmap, boundaries=DIFF_BOUNDARIES,
              label="diferença (vermelho = novo maior)", tick_format="%.2f")

    figure.text(
        0.5, 0.045,
        "Segmentos costeiros Natural Earth de até 5 km, cada um com o valor do ponto de grade nativo mais próximo. "
        "Valores consumidos como calculados — nada é renormalizado aqui.",
        ha="center", va="top", fontsize=7.6, color="#374151",
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"map_{slug}_legacy_vs_mhws.png"
    figure.savefig(out, dpi=ARTICLE_DPI, bbox_inches="tight")
    plt.close(figure)
    print(f"Saved: {out}")
    return {"output": str(out.relative_to(ROOT)), "statistics": stats}


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(
            f"{SOURCE} not found. Run compare_methods_ssh_total_vs_mhws first."
        )
    grid = pd.read_csv(SOURCE)
    grid = grid.rename(
        columns={"grid_lat_legacy": "grid_lat", "grid_lon_legacy": "grid_lon"}
    )
    for field, _, _ in COMPONENTS:
        grid[f"{field}_delta"] = grid[f"{field}_mhws"] - grid[f"{field}_legacy"]

    municipalities, coastline = read_coastal_inputs()
    fields = [
        name
        for field, _, _ in COMPONENTS
        for name in (f"{field}_legacy", f"{field}_mhws", f"{field}_delta")
    ]
    segments, _ = project_values_to_coastline(
        grid, fields, municipalities=municipalities, coastline=coastline
    )

    for field, display_name, slug in COMPONENTS:
        panel_segments = segments.copy()
        panel_segments["_delta"] = panel_segments[f"{field}_delta"]
        build_figure(
            panel_segments, coastline,
            field=field, display_name=display_name, slug=slug,
        )


if __name__ == "__main__":
    main()
