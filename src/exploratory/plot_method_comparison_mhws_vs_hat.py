"""Map MHWS and HAT hazard components side by side with their differences.

The script consumes the already-normalized comparison table.  It reuses the
canonical coastal projection and the visual primitives of the existing
SSH_total-versus-MHWS comparison; no values are recalculated here.

Usage:
    conda run -n osr11 python -m src.exploratory.plot_method_comparison_mhws_vs_hat

Output:
    outputs/method_comparison_mhws_vs_hat/figures/map_*_mhws_vs_hat.png
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import cartopy.crs as ccrs
import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.cm import ScalarMappable
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Rectangle

from src.exploratory.plot_method_comparison_maps import (
    DIFF_BOUNDARIES,
    SEGMENT_LINEWIDTH,
    VALUE_BOUNDARIES,
    _draw_segments,
    _setup_axis,
)
from src.figures_article.make_article_coastal_hazard_components_map import (
    _draw_context,
)
from src.figures_article.make_article_supplementary_integrated_risk_zooms import (
    ARTICLE_DPI,
)
from src.risk_integration.coastal_projection import (
    project_values_to_coastline,
    read_coastal_inputs,
)
from src.risk_integration.palettes import component_colors, diverging_colors

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT / "outputs" / "method_comparison_mhws_vs_hat" / "hazard_by_point.csv"
)
OUT_DIR = ROOT / "outputs" / "method_comparison_mhws_vs_hat" / "figures"
COMPONENTS = (
    ("Hazard_Frequency", "Frequência", "frequency"),
    ("Hazard_Severity", "Severidade integrada", "severity"),
    ("Hazard_Index", "Índice de perigo", "index"),
    ("Hazard_Duration", "Duração (diagnóstico aposentado)", "duration_diagnostic"),
    (
        "Hazard_Peak_Intensity",
        "Intensidade de pico (diagnóstico aposentado)",
        "peak_intensity_diagnostic",
    ),
)

ZERO_COLOR = "#D9D9D9"


def _draw_exact_zeros(
    axis: plt.Axes,
    segments: gpd.GeoDataFrame,
    field: str,
) -> int:
    """Overlay exact zeros in light gray without changing the numeric scale."""
    values = pd.to_numeric(segments[field], errors="coerce").to_numpy(dtype=float)
    geometries = segments.geometry[values == 0.0].tolist()
    if geometries:
        axis.add_geometries(
            geometries,
            crs=ccrs.PlateCarree(),
            facecolor="none",
            edgecolor=ZERO_COLOR,
            linewidth=SEGMENT_LINEWIDTH,
            zorder=9,
        )
    return len(geometries)


def _colorbar_with_zero(
    figure: plt.Figure,
    axis: plt.Axes,
    *,
    cmap: ListedColormap,
    boundaries: np.ndarray,
    label: str,
    ticks: np.ndarray,
) -> None:
    """Draw a two-decimal colorbar with a dedicated exact-zero gray swatch."""
    position = axis.get_position()
    gap = position.width * 0.100
    zero_width = position.width * 0.105
    bar_width = position.width - zero_width - gap
    y = position.y0 - 0.055
    height = 0.016

    zero_axis = figure.add_axes([position.x0, y, zero_width, height])
    zero_axis.add_patch(
        Rectangle(
            (0.0, 0.0),
            1.0,
            1.0,
            facecolor=ZERO_COLOR,
            edgecolor="#737373",
            linewidth=0.7,
        )
    )
    zero_axis.set_xlim(0.0, 1.0)
    zero_axis.set_ylim(0.0, 1.0)
    zero_axis.set_xticks([0.5], labels=["0.00"])
    zero_axis.set_yticks([])
    zero_axis.tick_params(axis="x", labelsize=7.2, length=2.6)
    for spine in zero_axis.spines.values():
        spine.set_visible(False)

    color_axis = figure.add_axes(
        [position.x0 + zero_width + gap, y, bar_width, height]
    )
    norm = BoundaryNorm(boundaries, cmap.N, clip=True)
    mappable = ScalarMappable(norm=norm, cmap=cmap)
    mappable.set_array([])
    bar = figure.colorbar(
        mappable,
        cax=color_axis,
        orientation="horizontal",
        boundaries=boundaries,
        ticks=ticks,
        spacing="uniform",
        drawedges=True,
    )
    bar.ax.set_xticklabels([f"{value:.2f}" for value in ticks])
    bar.set_label(label, fontsize=8.5, labelpad=2.0)
    bar.ax.tick_params(labelsize=7.2, length=2.6)
    bar.outline.set_linewidth(0.7)


def _build(
    segments: gpd.GeoDataFrame,
    coastline: gpd.GeoDataFrame,
    *,
    field: str,
    display: str,
    slug: str,
) -> dict[str, Any]:
    value_cmap = ListedColormap(component_colors(len(VALUE_BOUNDARIES) - 1))
    diff_cmap = ListedColormap(diverging_colors(len(DIFF_BOUNDARIES) - 1))
    figure, axes = plt.subplots(
        1,
        3,
        figsize=(12.6, 6.4),
        subplot_kw={"projection": ccrs.PlateCarree()},
    )
    panels = (
        (
            f"{field}_mhws",
            "vigente — portão/datum MHWS",
            "(a)",
            value_cmap,
            VALUE_BOUNDARIES,
        ),
        (
            f"{field}_hat",
            "experimental — portão/datum HAT",
            "(b)",
            value_cmap,
            VALUE_BOUNDARIES,
        ),
        ("_delta", "Δ  HAT − MHWS", "(c)", diff_cmap, DIFF_BOUNDARIES),
    )
    statistics: dict[str, Any] = {}
    for index, (column, title, label, cmap, boundaries) in enumerate(panels):
        axis = axes[index]
        _setup_axis(
            axis,
            title=title,
            panel_label=label,
            draw_left_labels=index == 0,
        )
        _draw_context(axis, coastline)
        _draw_segments(axis, segments, column, cmap, boundaries)
        _draw_exact_zeros(axis, segments, column)
        values = pd.to_numeric(segments[column], errors="coerce").dropna()
        statistics[column] = {
            "min": round(float(values.min()), 4),
            "max": round(float(values.max()), 4),
            "mean": round(float(values.mean()), 4),
        }

    figure.suptitle(
        f"{display} — MHWS × HAT",
        fontsize=13.0,
        fontweight="bold",
        y=0.955,
    )
    figure.subplots_adjust(
        left=0.045, right=0.985, top=0.88, bottom=0.16, wspace=0.10
    )
    value_ticks = np.append(VALUE_BOUNDARIES[1::2], VALUE_BOUNDARIES[-1])
    difference_ticks = DIFF_BOUNDARIES[::2]
    difference_ticks = difference_ticks[difference_ticks != 0.0]
    _colorbar_with_zero(
        figure,
        axes[0],
        cmap=value_cmap,
        boundaries=VALUE_BOUNDARIES,
        label="componente normalizada (0–1)",
        ticks=value_ticks,
    )
    _colorbar_with_zero(
        figure,
        axes[1],
        cmap=value_cmap,
        boundaries=VALUE_BOUNDARIES,
        label="componente normalizada (0–1)",
        ticks=value_ticks,
    )
    _colorbar_with_zero(
        figure,
        axes[2],
        cmap=diff_cmap,
        boundaries=DIFF_BOUNDARIES,
        label="diferença (vermelho = HAT maior)",
        ticks=difference_ticks,
    )
    figure.text(
        0.5,
        0.045,
        "Segmentos costeiros Natural Earth de até 5 km, associados ao ponto "
        "nativo mais próximo. Valores consumidos sem renormalização; zeros "
        "exatos aparecem em cinza claro.",
        ha="center",
        va="top",
        fontsize=7.6,
        color="#374151",
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    output = OUT_DIR / f"map_{slug}_mhws_vs_hat.png"
    figure.savefig(output, dpi=ARTICLE_DPI, bbox_inches="tight")
    plt.close(figure)
    print(f"Saved: {output}")
    return {
        "output": str(output.relative_to(ROOT)),
        "statistics": statistics,
    }


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(
            f"{SOURCE} not found; run compare_methods_mhws_vs_hat first"
        )
    grid = pd.read_csv(SOURCE).rename(
        columns={"grid_lat_mhws": "grid_lat", "grid_lon_mhws": "grid_lon"}
    )
    for field, _, _ in COMPONENTS:
        grid[f"{field}_delta"] = grid[f"{field}_hat"] - grid[f"{field}_mhws"]
    municipalities, coastline = read_coastal_inputs()
    fields = [
        column
        for field, _, _ in COMPONENTS
        for column in (f"{field}_mhws", f"{field}_hat", f"{field}_delta")
    ]
    segments, _ = project_values_to_coastline(
        grid,
        fields,
        municipalities=municipalities,
        coastline=coastline,
    )
    metadata = {}
    for field, display, slug in COMPONENTS:
        panel = segments.copy()
        panel["_delta"] = panel[f"{field}_delta"]
        metadata[field] = _build(
            panel,
            coastline,
            field=field,
            display=display,
            slug=slug,
        )
    (OUT_DIR / "figure_metadata.json").write_text(
        __import__("json").dumps(metadata, indent=2, ensure_ascii=False) + "\n"
    )


if __name__ == "__main__":
    main()
