"""Generate article figures for PU calibration and the Santa Catarina study area.

Outputs are semantic, PNG-only article figures written to
``outputs/article_figures/``. Run from the repository root with::

    python -m src.figures_article.make_article_calibration_figures
"""
from __future__ import annotations

import json
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
import numpy as np
import pandas as pd

from config.plot_config import SECTOR_COLORS, apply_publication_style
from src.figures_article.make_article_risk_figures import (
    METADATA_DIR,
    OUT_DIR,
    RISK_SHP,
    _relative,
    _save_figure,
    validate_article_figure_outputs,
)

ROOT = Path(__file__).resolve().parents[2]
SCORE_DATA = ROOT / "site/public/data/tc5_score_decomposition.json"
GRID_REFERENCE = ROOT / "outputs/preprocessing/municipality_grid_ref.csv"
EXPANDED_EVENTS = ROOT / "data/reported events/ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv"
LEGACY_EVENTS = ROOT / "data/reported events/reported_events_Karine_sc.csv"

# Requested order is explicitly WORSE -> BETTER. For metrics that are minimized
# (B and F_soft/P), reverse it so low numerical values receive the best colour.
QUALITY_COLORS_WORSE_TO_BETTER = (
    "#FDF5D0", "#FCEAA1", "#F8E070", "#F4B354",
    "#EC8439", "#E05020", "#C84232", "#AF3540",
    "#96274B", "#7C1B55", "#600F5F", "#3E0668",
)
MAXIMIZE_CMAP = ListedColormap(QUALITY_COLORS_WORSE_TO_BETTER, name="quality_worse_to_better")
MINIMIZE_CMAP = ListedColormap(tuple(reversed(QUALITY_COLORS_WORSE_TO_BETTER)), name="quality_better_to_worse")

# Dedicated Score palette requested as green -> purple, applied INVERTED so
# the panel uses the exact reversed sequence below.
SCORE_COLORS = (
    "#008000", "#33B200", "#80D900", "#CCE600",
    "#FFE600", "#FFB200", "#FF8000", "#FF4000",
    "#FF0000", "#CC0033", "#99004C", "#660066",
)
SCORE_CMAP = ListedColormap(tuple(reversed(SCORE_COLORS)), name="score_requested_reversed")

SECTOR_ORDER = ("North", "Central-north", "Central", "Central-south", "South")
# The legacy source contains two event-level sector labels for Garopaba. The
# project-wide municipality lookup classifies it as South; use that stable
# municipality classification in this methodology map.
SECTOR_OVERRIDES = {"garopaba": "South"}


def _normalise_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    return " ".join(text.casefold().strip().split())


def _score_frame() -> pd.DataFrame:
    with SCORE_DATA.open(encoding="utf-8") as handle:
        frame = pd.DataFrame(json.load(handle))
    required = {"hs_percentile", "ssh_percentile", "R_pos", "B", "term_fsoft_raw", "Score"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing score-decomposition fields: {sorted(missing)}")
    return frame


def _heatmap_panel(
    ax: plt.Axes,
    data: pd.DataFrame,
    metric: str,
    title: str,
    *,
    higher_is_better: bool,
    fmt: str,
    panel: str,
    cmap_override: ListedColormap | None = None,
) -> None:
    matrix = data.pivot(index="hs_percentile", columns="ssh_percentile", values=metric).sort_index()
    matrix = matrix.reindex(sorted(matrix.columns), axis=1)
    values = matrix.to_numpy(dtype=float)
    vmin, vmax = float(np.nanmin(values)), float(np.nanmax(values))
    norm = Normalize(vmin=vmin, vmax=vmax)
    cmap = cmap_override or (MAXIMIZE_CMAP if higher_is_better else MINIMIZE_CMAP)
    image = ax.imshow(values, cmap=cmap, norm=norm, aspect="equal", origin="upper")

    labels_x = [f"q{int(value)}" for value in matrix.columns]
    labels_y = [f"q{int(value)}" for value in matrix.index]
    ax.set_xticks(range(len(labels_x)), labels_x, rotation=45, ha="right")
    ax.set_yticks(range(len(labels_y)), labels_y)
    ax.set_xlabel(r"SSH$_{total}$ quantile")
    ax.set_ylabel(r"H$_s$ quantile")
    ax.set_title(title, fontweight="bold", pad=7)
    ax.grid(False)
    ax.text(-0.13, 1.06, f"({panel})", transform=ax.transAxes, fontweight="bold", fontsize=11)

    for row in range(values.shape[0]):
        for col in range(values.shape[1]):
            value = values[row, col]
            rgba = cmap(norm(value))
            luminance = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
            ax.text(col, row, format(value, fmt), ha="center", va="center", fontsize=5.5,
                    color="black" if luminance > 0.55 else "white")

    if 90 in matrix.index and 90 in matrix.columns:
        row = list(matrix.index).index(90)
        col = list(matrix.columns).index(90)
        ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, fill=False,
                               edgecolor="#00E5FF", linewidth=2.0))

    colorbar = ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.025)
    direction = "higher is better" if higher_is_better else "lower is better"
    colorbar.set_label(direction, fontsize=7)
    colorbar.ax.tick_params(labelsize=6)


def make_pu_calibration_multiplot(data: pd.DataFrame) -> list[str]:
    """Create the article 2x2 PU score-component heatmap."""
    fig, axes = plt.subplots(2, 2, figsize=(10.8, 9.4), constrained_layout=True)
    panels = (
        ("R_pos", r"Positive recall, $R_{pos}$", True, ".2f", "a", None),
        ("B", r"Detection burden, $B$", False, ".2f", "b", None),
        ("term_fsoft_raw", r"Soft penalty, $F_{soft}/P$", False, ".1f", "c", None),
        ("Score", "Composite score", True, ".2f", "d", SCORE_CMAP),
    )
    for ax, (metric, title, higher_is_better, fmt, panel, cmap) in zip(axes.flat, panels):
        _heatmap_panel(ax, data, metric, title, higher_is_better=higher_is_better,
                       fmt=fmt, panel=panel, cmap_override=cmap)
    fig.suptitle(r"PU calibration across tested H$_s$ and SSH$_{total}$ quantiles", fontweight="bold")
    fig.text(0.5, -0.012, "Cyan outline: selected q90/q90 threshold pair.", ha="center", fontsize=8)
    return _save_figure(fig, "pu_composite_calibration_heatmaps")


def _study_municipalities() -> pd.DataFrame:
    expanded = pd.read_csv(EXPANDED_EVENTS, usecols=["city", "coastal_sector"]).rename(
        columns={"city": "municipality", "coastal_sector": "sector"}
    )
    legacy = pd.read_csv(LEGACY_EVENTS, usecols=["Municipalities", "Coastal Sectors"]).rename(
        columns={"Municipalities": "municipality", "Coastal Sectors": "sector"}
    )
    events = pd.concat([expanded, legacy], ignore_index=True).dropna()
    events["name_key"] = events["municipality"].map(_normalise_name)
    events["sector"] = events["sector"].astype(str).str.strip()
    for name_key, sector in SECTOR_OVERRIDES.items():
        events.loc[events["name_key"] == name_key, "sector"] = sector
    conflicts = events.groupby("name_key")["sector"].nunique()
    if (conflicts > 1).any():
        names = conflicts[conflicts > 1].index.tolist()
        raise ValueError(f"Conflicting coastal sectors for municipalities: {names}")
    return events.drop_duplicates("name_key")[["name_key", "municipality", "sector"]]


def _map_data() -> tuple[gpd.GeoDataFrame, pd.DataFrame]:
    study = _study_municipalities()
    municipalities = gpd.read_file(RISK_SHP)
    municipalities = municipalities[municipalities["SIGLA_UF"] == "SC"].copy()
    municipalities["name_key"] = municipalities["NM_MUN"].map(_normalise_name)
    # The legacy database has one combined study unit, Içara/Balneário Rincão.
    # Balneário Rincão is also present independently, so associate the combined
    # record with Içara's polygon to keep all 27 study units visible once.
    municipalities.loc[municipalities["name_key"] == "icara", "name_key"] = "icara/balneario rincao"
    municipalities = municipalities.merge(study, on="name_key", how="inner")
    municipalities = municipalities.to_crs("EPSG:4326")

    grid = pd.read_csv(GRID_REFERENCE)
    grid["name_key"] = grid["municipality"].map(_normalise_name)
    grid = grid.merge(study[["name_key", "sector"]], on="name_key", how="inner")
    grid = grid.dropna(subset=["grid_lat", "grid_lon"])
    return municipalities, grid


def make_sc_study_area_map(
    municipalities: gpd.GeoDataFrame,
    grid: pd.DataFrame,
) -> list[str]:
    """Map study municipalities, joined ocean points, and an Orthographic inset."""
    projection = ccrs.PlateCarree()
    fig = plt.figure(figsize=(8.8, 9.5))
    ax = fig.add_axes([0.07, 0.07, 0.70, 0.86], projection=projection)
    ax.set_extent([-50.25, -47.95, -29.45, -25.75], crs=projection)
    ax.set_facecolor("#EAF3F8")

    brazil_municipalities = gpd.read_file(RISK_SHP).to_crs("EPSG:4326")
    ax.add_geometries(brazil_municipalities.geometry, crs=projection, facecolor="#F4F4F2",
                      edgecolor="#B8B8B2", linewidth=0.25, zorder=1)
    for sector in SECTOR_ORDER:
        subset = municipalities[municipalities["sector"] == sector]
        if not subset.empty:
            ax.add_geometries(subset.geometry, crs=projection,
                              facecolor=SECTOR_COLORS[sector], edgecolor="white",
                              linewidth=0.65, alpha=0.88, zorder=3)

    unique_points = grid.drop_duplicates(["grid_lat", "grid_lon"])
    for _, row in grid.iterrows():
        ax.plot([row["muni_lon"], row["grid_lon"]], [row["muni_lat"], row["grid_lat"]],
                transform=projection, color="#505050", linewidth=0.45, alpha=0.42, zorder=4)
    ax.scatter(unique_points["grid_lon"], unique_points["grid_lat"], transform=projection,
               s=24, marker="o", facecolor="white", edgecolor="black", linewidth=0.75, zorder=6)

    centroids = municipalities.to_crs("EPSG:31982").geometry.representative_point().to_crs("EPSG:4326")
    for (_, row), point in zip(municipalities.iterrows(), centroids):
        ax.text(point.x, point.y, row["municipality"], transform=projection, fontsize=4.1,
                ha="center", va="center", color="black", zorder=7,
                path_effects=[])

    gl = ax.gridlines(draw_labels=True, linewidth=0.35, color="#777777", alpha=0.5,
                      linestyle="--", x_inline=False, y_inline=False)
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {"size": 7}
    gl.ylabel_style = {"size": 7}
    ax.set_title("SC coastal study area and municipality–grid association",
                 fontsize=10.5, fontweight="bold", pad=9)

    inset_crs = ccrs.Orthographic(central_longitude=-52, central_latitude=-28)
    inset = fig.add_axes([0.10, 0.68, 0.25, 0.23], projection=inset_crs)
    inset.set_global()
    inset.set_facecolor("#DCECF4")
    inset.add_feature(cfeature.LAND.with_scale("110m"), facecolor="#C8C8C8",
                      edgecolor="#555555", linewidth=0.35, zorder=1)
    inset.add_feature(cfeature.BORDERS.with_scale("110m"), edgecolor="#666666",
                      linewidth=0.35, zorder=2)
    sc_boundary = brazil_municipalities[brazil_municipalities["SIGLA_UF"] == "SC"].dissolve()
    inset.add_geometries(sc_boundary.geometry, crs=projection, facecolor="none",
                         edgecolor="#D7191C", linewidth=2.6, zorder=4)
    inset.set_title("South America", fontsize=7.5, pad=3)

    sector_handles = [Patch(facecolor=SECTOR_COLORS[s], edgecolor="white", label=s) for s in SECTOR_ORDER]
    point_handle = Line2D([], [], marker="o", linestyle="none", markerfacecolor="white",
                          markeredgecolor="black", markersize=5, label="Nearest ocean grid point")
    line_handle = Line2D([], [], color="#505050", linewidth=0.7, label="Municipality–grid join")
    ax.legend(handles=sector_handles + [point_handle, line_handle], loc="lower left",
              fontsize=7, framealpha=0.95, title="Coastal sector", title_fontsize=7.5)
    fig.text(0.07, 0.025,
             f"Study municipalities: {len(municipalities)}; associated municipalities: {grid['name_key'].nunique()}; "
             f"unique ocean grid points: {len(unique_points)}.", fontsize=7.5, color="#333333")
    return _save_figure(fig, "santa_catarina_study_area_and_grid_points")


def main() -> None:
    apply_publication_style()
    data = _score_frame()
    municipalities, grid = _map_data()
    outputs = {
        "pu_composite_calibration_heatmaps": make_pu_calibration_multiplot(data),
        "santa_catarina_study_area_and_grid_points": make_sc_study_area_map(municipalities, grid),
    }
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "outputs": outputs,
        "inputs": {
            "score_decomposition": _relative(SCORE_DATA),
            "municipality_polygons": _relative(RISK_SHP),
            "municipality_grid_reference": _relative(GRID_REFERENCE),
            "expanded_events": _relative(EXPANDED_EVENTS),
            "legacy_events": _relative(LEGACY_EVENTS),
        },
        "heatmap_color_logic": {
            "requested_order": "worse_to_better",
            "colors": list(QUALITY_COLORS_WORSE_TO_BETTER),
            "maximize_metrics": ["R_pos", "Score"],
            "minimize_metrics_reversed": ["B", "F_soft/P"],
            "score_palette_requested": list(SCORE_COLORS),
            "score_palette_application": "reversed",
        },
        "map_counts": {
            "study_municipalities": int(len(municipalities)),
            "associated_municipalities": int(grid["name_key"].nunique()),
            "unique_grid_points": int(len(grid.drop_duplicates(["grid_lat", "grid_lon"]))),
        },
    }
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    metadata_path = METADATA_DIR / "article_calibration_figure_summary.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    validate_article_figure_outputs()
    for files in outputs.values():
        for path in files:
            print(path)
    print(_relative(metadata_path))


if __name__ == "__main__":
    main()
