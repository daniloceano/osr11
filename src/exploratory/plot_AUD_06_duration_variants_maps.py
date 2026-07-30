"""Coastal maps of the candidate duration components (AUD-06).

Draws the current definition and the four candidate replacements computed by
:mod:`audit_AUD_06_duration_variants`, each Min-Max normalized over the 808
native points exactly as the hazard index normalizes its components, so the
panels show what each candidate would contribute as the third component.

Same cartographic conventions as the article's coastal component figure.

Read-only. Adopts nothing.

Usage:
    python -m src.exploratory.plot_AUD_06_duration_variants_maps

Output:
    outputs/audit/AUD-06_duration_variants/figures/duration_variants_maps.png
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import cartopy.crs as ccrs
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

from src.exploratory.plot_method_comparison_maps import (  # noqa: E402
    VALUE_BOUNDARIES,
    _setup_axis,
)
from src.figures_article.make_article_coastal_hazard_components_map import (  # noqa: E402
    _draw_context,
)
from src.figures_article.make_article_supplementary_integrated_risk_zooms import (  # noqa: E402
    ARTICLE_DPI,
)
from src.risk_integration.coastal_projection import (  # noqa: E402
    COASTAL_MAP_EXTENT,
    line_parts,
    project_values_to_coastline,
    read_coastal_inputs,
)
from src.risk_integration.palettes import component_colors  # noqa: E402

SOURCE = (
    ROOT / "outputs" / "audit" / "AUD-06_duration_variants"
    / "duration_variants_by_point.csv"
)
SUMMARY = (
    ROOT / "outputs" / "audit" / "AUD-06_duration_variants"
    / "duration_variants_summary.json"
)
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-06_duration_variants" / "figures"

PANELS = (
    ("reference_driver_overlap_days", "atual\nsobreposição de 2 critérios", "(ref)"),
    ("opt1_full_criterion_days", "opção 1\nsobreposição dos 3 critérios", "(1)"),
    ("opt2_integrated_intensity", "opção 2\nintensidade integrada", "(2)"),
    ("opt3_integrated_excess_m_days", "opção 3\nexcesso integrado (m·dia)", "(3)"),
    ("opt4_p95_full_criterion_days", "opção 4\np95 dos 3 critérios", "(4)"),
)


def _minmax(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    finite = values[np.isfinite(values)]
    return (values - finite.min()) / (finite.max() - finite.min())


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(
            f"{SOURCE} not found. Run audit_AUD_06_duration_variants first."
        )
    grid = pd.read_csv(SOURCE)
    stats = json.loads(SUMMARY.read_text())["statistics"]

    normalized_fields = []
    for field, _, _ in PANELS:
        target = f"{field}_norm"
        grid[target] = _minmax(grid[field])
        normalized_fields.append(target)

    municipalities, coastline = read_coastal_inputs()
    segments, _ = project_values_to_coastline(
        grid, normalized_fields, municipalities=municipalities, coastline=coastline
    )

    cmap = ListedColormap(component_colors(len(VALUE_BOUNDARIES) - 1))
    figure, axes = plt.subplots(
        1, len(PANELS), figsize=(19.5, 6.6),
        subplot_kw={"projection": ccrs.PlateCarree()},
    )

    for index, (field, title, label) in enumerate(PANELS):
        axis = axes[index]
        _setup_axis(axis, title=title, panel_label=label, draw_left_labels=index == 0)
        _draw_context(axis, coastline)
        values = segments[f"{field}_norm"].to_numpy(dtype=float)
        class_indices = np.digitize(values, VALUE_BOUNDARIES[1:-1])
        for class_index in range(len(VALUE_BOUNDARIES) - 1):
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
                edgecolor=cmap(class_index), linewidth=3.4, zorder=8,
            )
        axis.set_extent(COASTAL_MAP_EXTENT, crs=ccrs.PlateCarree())

        s = stats[field]
        axis.text(
            0.5, -0.055,
            f"ρ|lat| = {s['spearman_vs_abs_latitude']:+.2f}   "
            f"ρ freq = {s['spearman_vs_frequency']:+.2f}",
            transform=axis.transAxes, ha="center", va="top", fontsize=8.4,
            color="#B2182B" if s["spearman_vs_frequency"] < 0 else "#1B5E20",
            fontweight="bold",
        )

    figure.suptitle(
        "AUD-06 — candidatas à terceira componente do perigo (detector MHWS)",
        fontsize=13.5, fontweight="bold", y=0.965,
    )
    figure.subplots_adjust(left=0.035, right=0.99, top=0.845, bottom=0.20, wspace=0.08)

    cax = figure.add_axes([0.32, 0.115, 0.36, 0.016])
    norm = BoundaryNorm(VALUE_BOUNDARIES, cmap.N, clip=True)
    mappable = ScalarMappable(norm=norm, cmap=cmap)
    mappable.set_array([])
    bar = figure.colorbar(
        mappable, cax=cax, orientation="horizontal", boundaries=VALUE_BOUNDARIES,
        ticks=VALUE_BOUNDARIES[::2], spacing="uniform", drawedges=True,
    )
    bar.set_label("componente normalizada 0–1 sobre os 808 pontos", fontsize=8.8)
    bar.ax.xaxis.set_major_formatter(FormatStrFormatter("%.2f"))
    bar.ax.tick_params(labelsize=7.5, length=2.6)
    bar.outline.set_linewidth(0.7)

    figure.text(
        0.5, 0.048,
        "ρ|lat| < 0 favorece o Norte, > 0 favorece o Sul.   "
        "ρ freq < 0 (vermelho) cancela a frequência na média equiponderada; "
        "> 0 (verde) a reforça.",
        ha="center", va="top", fontsize=8.2, color="#374151",
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "duration_variants_maps.png"
    figure.savefig(out, dpi=ARTICLE_DPI, bbox_inches="tight")
    plt.close(figure)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
