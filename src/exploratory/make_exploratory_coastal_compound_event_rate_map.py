"""Generate an exploratory coastal map of annual compound-event frequency.

The native-grid total compound-event count is divided by the documented
33-year record length (1993-01-01 through 2025-12-31). The annualized value is
then assigned to short coastline segments using the same nearest-grid-point
method and map design as the article total-count figure.

Run from the repository root:

    python src/exploratory/make_exploratory_coastal_compound_event_rate_map.py
"""
from __future__ import annotations

from datetime import date, datetime, timezone
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import cartopy.crs as ccrs
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import BoundaryNorm, ListedColormap
import numpy as np
import pandas as pd
from shapely.geometry import LineString
from shapely.ops import linemerge, unary_union

from src.figures_article.make_article_risk_figures import (
    COASTAL_COLOR_CLASSES,
    COASTAL_MAP_EXTENT,
    _draw_administrative_boundaries,
    _line_parts,
    _plot_coastline,
    _setup_article_geo_axis,
    build_coastal_compound_event_segments,
    read_coastline,
    read_ocean_hazard_data,
    read_risk_data,
)

COMPOUND_SUMMARY = (
    ROOT / "outputs/storm_catalog/compound/compound_summary.json"
)
OUTPUT_DIR = ROOT / "outputs/exploratory_coastal_compound_event_rate_map"
EXPLORATORY_DPI = 150


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def annual_rate_boundaries(values: pd.Series) -> np.ndarray:
    finite = pd.to_numeric(values, errors="coerce").dropna()
    if finite.empty:
        raise ValueError("No finite annual compound-event rates")
    step = math.ceil(
        float(finite.max()) / COASTAL_COLOR_CLASSES * 10.0
    ) / 10.0
    return (
        np.arange(COASTAL_COLOR_CLASSES + 1, dtype=float) * step
    )


def main() -> None:
    if not COMPOUND_SUMMARY.exists():
        raise FileNotFoundError(COMPOUND_SUMMARY)
    summary_document = json.loads(COMPOUND_SUMMARY.read_text(encoding="utf-8"))
    catalog_summary = summary_document["summary"]
    number_of_years = float(catalog_summary["n_years"])
    if number_of_years <= 0:
        raise ValueError("The catalog record length must be positive")

    municipalities, _ = read_risk_data()
    ocean_grid, ocean_metadata = read_ocean_hazard_data()
    coastline = read_coastline()
    if coastline is None or coastline.empty:
        raise FileNotFoundError("Natural Earth coastline is unavailable")

    annual_grid = ocean_grid.copy()
    annual_grid["compound_event_count_total"] = annual_grid["compound_c"]
    annual_grid["compound_event_rate_per_year"] = (
        annual_grid["compound_event_count_total"] / number_of_years
    )
    annual_grid["compound_c"] = annual_grid["compound_event_rate_per_year"]

    segments, assignment_metadata = build_coastal_compound_event_segments(
        municipalities,
        annual_grid,
        coastline,
    )
    segments = segments.rename(
        columns={
            "compound_event_count": "compound_event_rate_per_year",
        }
    )
    boundaries = annual_rate_boundaries(
        segments["compound_event_rate_per_year"]
    )
    magma = plt.get_cmap("magma")
    cmap = ListedColormap(
        magma(np.linspace(0.95, 0.12, len(boundaries) - 1)),
        name="annual_compound_event_rate_reversed_magma",
    )
    norm = BoundaryNorm(boundaries, cmap.N, clip=True)

    fig = plt.figure(figsize=(8.4, 8.0), constrained_layout=False)
    axis = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    fig.subplots_adjust(left=0.07, right=0.965, top=0.98, bottom=0.14)
    _setup_article_geo_axis(
        axis,
        None,
        extent=COASTAL_MAP_EXTENT,
    )
    _draw_administrative_boundaries(axis)
    _plot_coastline(axis, coastline)

    class_indices = np.digitize(
        segments["compound_event_rate_per_year"].to_numpy(dtype=float),
        boundaries[1:-1],
    )
    for class_index in range(len(boundaries) - 1):
        geometries = segments.geometry[
            class_indices == class_index
        ].tolist()
        if not geometries:
            continue
        dissolved = unary_union(geometries)
        merged = (
            dissolved
            if isinstance(dissolved, LineString)
            else linemerge(dissolved)
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

    mappable = ScalarMappable(norm=norm, cmap=cmap)
    mappable.set_array([])
    fig.canvas.draw()
    map_position = axis.get_position()
    colorbar_axis = fig.add_axes(
        [
            map_position.x0,
            max(0.03, map_position.y0 - 0.09),
            map_position.width,
            0.026,
        ]
    )
    colorbar = fig.colorbar(
        mappable,
        cax=colorbar_axis,
        orientation="horizontal",
        boundaries=boundaries,
        ticks=boundaries,
        spacing="uniform",
        drawedges=True,
    )
    colorbar.set_label(
        r"Compound events year$^{-1}$",
        fontsize=10,
    )
    colorbar.ax.tick_params(labelsize=9, length=3)
    colorbar.outline.set_linewidth(0.75)

    figure_dir = OUTPUT_DIR / "figures"
    data_dir = OUTPUT_DIR / "data"
    metadata_dir = OUTPUT_DIR / "metadata"
    for directory in (figure_dir, data_dir, metadata_dir):
        directory.mkdir(parents=True, exist_ok=True)

    run_date = date.today().strftime("%Y%m%d")
    figure_path = (
        figure_dir
        / f"explore_coastal_compound_event_rate_per_year_{run_date}.png"
    )
    grid_path = data_dir / "native_grid_compound_event_rate_per_year.csv"
    metadata_path = (
        metadata_dir / "explore_coastal_compound_event_rate_metadata.json"
    )
    fig.savefig(
        figure_path,
        dpi=EXPLORATORY_DPI,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(fig)

    annual_grid[
        [
            "longitude",
            "latitude",
            "compound_event_count_total",
            "compound_event_rate_per_year",
        ]
    ].to_csv(grid_path, index=False)

    source_csv = ROOT / ocean_metadata["source_path"]
    annual_mean_check: dict[str, float | str | None] = {
        "source_field": None,
        "maximum_absolute_difference_events_per_year": None,
    }
    if source_csv.suffix.lower() == ".csv" and source_csv.exists():
        raw = pd.read_csv(source_csv)
        if "compound_count_annual_mean" in raw:
            computed = (
                pd.to_numeric(raw["compound_count_total"], errors="coerce")
                / number_of_years
            )
            reported = pd.to_numeric(
                raw["compound_count_annual_mean"],
                errors="coerce",
            )
            annual_mean_check = {
                "source_field": "compound_count_annual_mean",
                "maximum_absolute_difference_events_per_year": float(
                    np.nanmax(np.abs(computed - reported))
                ),
            }

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "figure_role": "exploratory",
        "source": ocean_metadata["source_path"],
        "catalog_summary": relative(COMPOUND_SUMMARY),
        "period": catalog_summary["period"],
        "number_of_years": number_of_years,
        "formula": (
            "compound_event_rate_per_year = "
            "compound_count_total / number_of_years"
        ),
        "annual_mean_source_check": annual_mean_check,
        "coastal_assignment": assignment_metadata,
        "colorbar": {
            "units": "events per year",
            "number_of_colors": len(boundaries) - 1,
            "boundaries": boundaries.tolist(),
            "orientation": "low rates light; high rates dark",
            "width_matches_map_axis": True,
        },
        "map_extent": list(COASTAL_MAP_EXTENT),
        "outputs": {
            "figure": relative(figure_path),
            "annualized_native_grid": relative(grid_path),
        },
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(figure_path)
    print(grid_path)
    print(metadata_path)


if __name__ == "__main__":
    main()
