"""Exploratory Figure 3 variant with long-term mean zos point hatching.

Replicates ``outputs/article_figures/original_ocean_hazard_points.png`` and
adds hatching over valid points where long-term mean GLORYS zos is >= 0.20 m.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.path import Path as MarkerPath
import numpy as np
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.figures_article.make_article_risk_figures import (
    RISK_CMAP,
    _plot_coastline,
    _setup_map_axis,
    read_coastline,
    read_ocean_hazard_data,
)


DEFAULT_ZOS = ROOT / "outputs/monthly_quicklook_brazil_all/data/longterm_mean_zos.nc"
OUT_DIR = ROOT / "outputs" / "exploratory_original_ocean_hazard_zos_hatched_points"
FIG_DIR = OUT_DIR / "figures"
TABLE_DIR = OUT_DIR / "tables"
DEFAULT_STEM = "original_ocean_hazard_points_zos_mean_ge_0p20_point_hatching"
SAVE_EXTENSIONS = ("png", "pdf", "svg")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create Figure 3 variant with point hatching where mean zos >= threshold."
    )
    parser.add_argument("--zos", type=Path, default=DEFAULT_ZOS)
    parser.add_argument("--threshold", type=float, default=0.20)
    parser.add_argument("--stem", default=DEFAULT_STEM)
    parser.add_argument("--figure-dir", type=Path, default=FIG_DIR)
    parser.add_argument("--table-dir", type=Path, default=TABLE_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ocean_df, ocean_meta = read_ocean_hazard_data()
    coastline = read_coastline()
    zos = load_mean_zos(args.zos)
    point_df = sample_point_zos(ocean_df, zos, args.threshold)

    fig, ax = plt.subplots(figsize=(7.6, 8.2), constrained_layout=False)
    fig.subplots_adjust(left=0.075, right=0.88, top=0.93, bottom=0.105)

    values = ocean_df["Hazard_Index"]
    norm = Normalize(float(values.min()), float(values.max()))
    _setup_map_axis(ax, "Original oceanic compound-event hazard points")
    _plot_coastline(ax, coastline)

    scatter = ax.scatter(
        ocean_df["longitude"],
        ocean_df["latitude"],
        c=values,
        cmap=RISK_CMAP,
        norm=norm,
        s=20,
        edgecolors="#0f172a",
        linewidths=0.18,
        alpha=0.95,
        zorder=5,
    )
    add_point_hatching(ax, point_df.loc[point_df["zos_ge_threshold"]])
    cbar = fig.colorbar(scatter, ax=ax, orientation="vertical", fraction=0.04, pad=0.025)
    if ocean_meta["hazard_index_mode"] == "compound_count_only":
        cbar.set_label("Compound-event count", fontsize=8)
    else:
        cbar.set_label("Oceanic Hazard_Index (relative)", fontsize=8)
    cbar.ax.tick_params(labelsize=7, length=2.5)
    cbar.outline.set_linewidth(0.7)

    mode_text = {
        "read": "Hazard_Index read directly from source.",
        "computed_minmax_mean": "Hazard_Index computed as mean of min-max normalized count, overlap duration, and intensity.",
        "compound_count_only": "Fallback: only compound-event count was available.",
    }[ocean_meta["hazard_index_mode"]]
    valid_points = int(point_df["zos_valid"].sum())
    hatched_points = int(point_df["zos_ge_threshold"].sum())
    fig.text(
        0.075,
        0.035,
        (
            f"n = {len(ocean_df)} ocean grid points. {mode_text}\n"
            f"Hatching over valid points: long-term mean zos >= {args.threshold:.2f} m "
            f"({hatched_points:,}/{valid_points:,} valid points)."
        ),
        ha="left",
        va="bottom",
        fontsize=7.5,
        color="#334155",
    )
    save_figure(fig, args.stem, args.figure_dir)
    save_point_table(point_df, args.table_dir, args.stem)


def load_mean_zos(path: Path) -> xr.DataArray:
    if not path.exists():
        raise FileNotFoundError(path)
    ds = xr.open_dataset(path)
    if "zos_longterm_mean" in ds:
        da = ds["zos_longterm_mean"]
    elif len(ds.data_vars) == 1:
        da = next(iter(ds.data_vars.values()))
    else:
        raise ValueError(f"Cannot infer mean zos variable from {path}")
    return da.sortby("latitude").sortby("longitude")


def sample_point_zos(ocean_df, zos: xr.DataArray, threshold: float):
    point_lon = xr.DataArray(ocean_df["longitude"].to_numpy(), dims="point")
    point_lat = xr.DataArray(ocean_df["latitude"].to_numpy(), dims="point")
    sampled = zos.sel(longitude=point_lon, latitude=point_lat, method="nearest")

    point_df = ocean_df.copy()
    point_df["zos_longterm_mean"] = sampled.to_numpy()
    point_df["zos_sampled_longitude"] = sampled["longitude"].to_numpy()
    point_df["zos_sampled_latitude"] = sampled["latitude"].to_numpy()
    point_df["zos_sample_distance_deg"] = np.hypot(
        point_df["longitude"] - point_df["zos_sampled_longitude"],
        point_df["latitude"] - point_df["zos_sampled_latitude"],
    )
    point_df["zos_valid"] = np.isfinite(point_df["zos_longterm_mean"])
    point_df["zos_ge_threshold"] = point_df["zos_valid"] & (
        point_df["zos_longterm_mean"] >= threshold
    )
    return point_df


def add_point_hatching(ax: plt.Axes, point_df) -> None:
    if point_df.empty:
        return
    marker = MarkerPath(
        [
            (-0.95, -0.35),
            (-0.35, 0.25),
            (-0.35, -0.75),
            (0.55, 0.15),
            (0.25, -0.95),
            (0.95, -0.25),
        ],
        [
            MarkerPath.MOVETO,
            MarkerPath.LINETO,
            MarkerPath.MOVETO,
            MarkerPath.LINETO,
            MarkerPath.MOVETO,
            MarkerPath.LINETO,
        ],
    )
    ax.scatter(
        point_df["longitude"],
        point_df["latitude"],
        marker=marker,
        s=28,
        facecolors="none",
        edgecolors="#020617",
        linewidths=0.55,
        zorder=8,
    )


def save_figure(fig: plt.Figure, stem: str, figure_dir: Path) -> list[Path]:
    figure_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for ext in SAVE_EXTENSIONS:
        path = figure_dir / f"{stem}.{ext}"
        if ext == "png":
            fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
        else:
            fig.savefig(path, bbox_inches="tight", facecolor="white")
        outputs.append(path)
    plt.close(fig)
    return outputs


def save_point_table(point_df, table_dir: Path, stem: str) -> Path:
    table_dir.mkdir(parents=True, exist_ok=True)
    columns = [
        "longitude",
        "latitude",
        "Hazard_Index",
        "zos_longterm_mean",
        "zos_sampled_longitude",
        "zos_sampled_latitude",
        "zos_sample_distance_deg",
        "zos_valid",
        "zos_ge_threshold",
    ]
    path = table_dir / f"{stem}_sampled_points.csv"
    point_df.loc[:, columns].to_csv(path, index=False)
    return path


if __name__ == "__main__":
    main()
