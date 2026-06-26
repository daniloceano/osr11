"""Exploratory Figure 3 variant with long-term mean zos hatching.

Replicates ``outputs/article_figures/fig03_original_ocean_hazard_points`` and
adds hatching over grid cells where long-term mean GLORYS zos is >= 0.20 m.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.figures_article.make_article_risk_figures import (
    RISK_CMAP,
    _plot_coastline,
    _save_figure,
    _setup_map_axis,
    read_coastline,
    read_ocean_hazard_data,
)


DEFAULT_ZOS = ROOT / "outputs/monthly_quicklook_brazil_all/data/longterm_mean_zos.nc"
DEFAULT_STEM = "fig03_original_ocean_hazard_points_zos_mean_ge_0p20_hatched"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create Figure 3 variant with hatching where mean zos >= threshold."
    )
    parser.add_argument("--zos", type=Path, default=DEFAULT_ZOS)
    parser.add_argument("--threshold", type=float, default=0.20)
    parser.add_argument("--stem", default=DEFAULT_STEM)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ocean_df, ocean_meta = read_ocean_hazard_data()
    coastline = read_coastline()
    zos = load_mean_zos(args.zos)

    fig, ax = plt.subplots(figsize=(7.6, 8.2), constrained_layout=False)
    fig.subplots_adjust(left=0.075, right=0.88, top=0.93, bottom=0.105)

    values = ocean_df["Hazard_Index"]
    norm = Normalize(float(values.min()), float(values.max()))
    _setup_map_axis(ax, "Original oceanic compound-event hazard points")
    add_zos_hatching(ax, zos, args.threshold)
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
    hatched_cells = int(np.count_nonzero(zos.values >= args.threshold))
    finite_cells = int(np.isfinite(zos.values).sum())
    fig.text(
        0.075,
        0.035,
        (
            f"n = {len(ocean_df)} ocean grid points. {mode_text}\n"
            f"Hatching: long-term mean zos >= {args.threshold:.2f} m "
            f"({hatched_cells:,}/{finite_cells:,} finite cells)."
        ),
        ha="left",
        va="bottom",
        fontsize=7.5,
        color="#334155",
    )
    _save_figure(fig, args.stem)


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


def add_zos_hatching(ax: plt.Axes, zos: xr.DataArray, threshold: float) -> None:
    lon = zos["longitude"].values
    lat = zos["latitude"].values
    mask = np.where(zos.values >= threshold, 1.0, np.nan)
    ax.contourf(
        lon,
        lat,
        mask,
        levels=[0.5, 1.5],
        colors=["none"],
        hatches=["////"],
        zorder=3,
    )


if __name__ == "__main__":
    main()
