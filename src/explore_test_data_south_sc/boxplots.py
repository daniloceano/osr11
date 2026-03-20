"""
Part F — Per-sector figures (map + Hs boxplot + SSH boxplot).

Generates one 1×3 figure per coastal sector:
- Left panel:   map with municipality locations, nearest WAVERYS grid points,
                and the test domain bounding box (cartopy).
- Centre panel: Hs boxplots per municipality.
- Right panel:  SSH boxplots per municipality.

Municipality ordering in boxplots: by latitude (south to north), consistent
with the orientation of the Santa Catarina coastline.

Data source per municipality:
- ``in_wave_domain``:  full WAVERYS time series at nearest coastal grid point.
- ``in_gl_domain``:    full GLORYS time series at nearest coastal grid point.
- Otherwise:           Hs only from the events spreadsheet (at event dates).

Note: ``in_wave_domain`` and ``in_gl_domain`` are separate flags because GLORYS
uses a finer ocean land-mask than WAVERYS.  A municipality can have a valid
WAVERYS coastal cell while the nearest GLORYS cell is land-masked — producing
fewer SSH municipalities than Hs municipalities in the SSH panel.  This is a
known property of the GLORYS12 ocean mask, not a data error.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

# Allow running this module directly (python boxplots.py)
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.explore_test_data_south_sc.config.analysis_config import CFG
from config.plot_config import SECTOR_COLORS, STYLE
from src.explore_test_data_south_sc.maps import _CRS, _ne
from src.explore_test_data_south_sc.utils import save_fig

log = logging.getLogger(__name__)


def run_sector_figures(
    df_events: pd.DataFrame,
    grid_table: pd.DataFrame,
    ds_wave: xr.Dataset,
    ds_gl: xr.Dataset,
) -> None:
    """Part F: generate one 1×3 figure per coastal sector."""
    log.info("== Part F: Per-sector figures ==")

    da_hs  = ds_wave[CFG["wave_var"]]
    da_zos = ds_gl[CFG["ssl_var"]]
    lat_w  = ds_wave.latitude.values
    lon_w  = ds_wave.longitude.values

    sectors = sorted(df_events["coastal_sector"].dropna().unique().tolist())

    for sector in sectors:
        log.info("  Sector: %s", sector)
        _sector_figure(
            sector, df_events, grid_table,
            da_hs, da_zos, lat_w, lon_w,
        )
        log.info(
            "    -> fig_F_%s_sector.png",
            sector.replace(" ", "_").replace("-", "_"),
        )


# ── Internal ──────────────────────────────────────────────────────────────────

def _sector_figure(
    sector: str,
    df_events: pd.DataFrame,
    grid_table: pd.DataFrame,
    da_hs: xr.DataArray,
    da_zos: xr.DataArray,
    lat_w: np.ndarray,
    lon_w: np.ndarray,
) -> None:
    color = SECTOR_COLORS.get(sector, "gray")

    sector_munis = df_events[df_events["coastal_sector"] == sector]["municipality"].unique()
    gt_sec = grid_table[grid_table["municipality"].isin(sector_munis)].copy()

    # Separate masks: in_wave_domain for Hs, in_gl_domain for SSH
    gt_wave = gt_sec[gt_sec["in_wave_domain"]].copy() if "in_wave_domain" in gt_sec.columns \
              else gt_sec[gt_sec["in_test_domain"]].copy()
    gt_gl   = gt_sec[gt_sec["in_gl_domain"]].copy()   if "in_gl_domain"   in gt_sec.columns \
              else gt_sec[gt_sec["in_test_domain"]].copy()

    # Sort south to north (ascending latitude)
    gt_sec_sorted  = gt_sec.sort_values("muni_lat",  ascending=True)
    gt_wave_sorted = gt_wave.sort_values("muni_lat", ascending=True)
    gt_gl_sorted   = gt_gl.sort_values("muni_lat",   ascending=True)
    munis_all  = gt_sec_sorted["municipality"].tolist()
    munis_wave = gt_wave_sorted["municipality"].tolist()
    munis_gl   = gt_gl_sorted["municipality"].tolist()

    # For backward compat with _map_panel (uses in_test_domain)
    if "in_wave_domain" in gt_sec_sorted.columns and "in_test_domain" not in gt_sec_sorted.columns:
        gt_sec_sorted = gt_sec_sorted.copy()
        gt_sec_sorted["in_test_domain"] = gt_sec_sorted["in_wave_domain"]

    # Extract grid time series for municipalities with valid WAVERYS coastal point
    hs_grid:  dict[str, np.ndarray] = {}
    zos_grid: dict[str, np.ndarray] = {}
    for _, row in gt_wave_sorted.iterrows():
        muni = row["municipality"]
        raw  = da_hs.sel(
            latitude=row["wave_grid_lat"], longitude=row["wave_grid_lon"],
            method="nearest",
        ).values
        hs_grid[muni] = raw[np.isfinite(raw)]
    for _, row in gt_gl_sorted.iterrows():
        muni = row["municipality"]
        raw  = da_zos.sel(
            latitude=row["gl_grid_lat"], longitude=row["gl_grid_lon"],
            method="nearest",
        ).values
        zos_grid[muni] = raw[np.isfinite(raw)]

    # Hs from events spreadsheet (fallback for municipalities without WAVERYS coastal point)
    hs_events: dict[str, np.ndarray] = {
        m: df_events.loc[df_events["municipality"] == m, "hs_m"].dropna().values
        for m in munis_all
    }

    # ── Figure layout ────────────────────────────────────────────────────
    n_all   = max(len(munis_all), 1)
    n_gl    = max(len(munis_gl),  1)
    box_w   = max(3.5, n_all * 0.9)
    fig_w   = min(22, 6 + box_w + max(2.5, n_gl * 0.9))
    fig     = plt.figure(figsize=(fig_w, 6.5))
    gs      = GridSpec(
        1, 3, figure=fig,
        width_ratios=[1.8, box_w / 4, max(2.5, n_gl * 0.9) / 4],
        wspace=0.35,
    )
    ax_map  = fig.add_subplot(gs[0, 0], projection=_CRS)
    ax_hs   = fig.add_subplot(gs[0, 1])
    ax_zos  = fig.add_subplot(gs[0, 2])

    _map_panel(ax_map, gt_sec_sorted, lat_w, lon_w, sector, color)
    _hs_panel(ax_hs, munis_all, hs_grid, hs_events, color)
    _ssh_panel(ax_zos, munis_gl, zos_grid, sector_munis, munis_all)

    safe_name = sector.replace(" ", "_").replace("-", "_")
    save_fig(fig, f"fig_F_{safe_name}_sector")


def _map_panel(
    ax: plt.Axes,
    gt_sec_sorted: pd.DataFrame,
    lat_w: np.ndarray,
    lon_w: np.ndarray,
    sector: str,
    color: str,
) -> None:
    all_lats = gt_sec_sorted["muni_lat"].dropna().tolist() + [lat_w.min(), lat_w.max()]
    all_lons = gt_sec_sorted["muni_lon"].dropna().tolist() + [lon_w.min(), lon_w.max()]
    pad = 0.35
    ax.set_extent(
        [min(all_lons) - pad, max(all_lons) + pad,
         min(all_lats) - pad, max(all_lats) + pad],
        crs=_CRS,
    )
    ax.add_feature(_ne("physical", "land",  facecolor="#f0ede8"), zorder=0)
    ax.add_feature(_ne("physical", "ocean", facecolor="#daeeff"), zorder=0)
    ax.add_feature(
        _ne("physical", "coastline", edgecolor="black", facecolor="none"),
        linewidth=0.8, zorder=3,
    )
    ax.add_feature(
        _ne("cultural", "admin_1_states_provinces_lines",
            edgecolor="dimgray", facecolor="none"),
        linewidth=0.5, zorder=3,
    )
    gl = ax.gridlines(
        draw_labels=True, linewidth=0.4, color="gray",
        alpha=0.5, linestyle="--", crs=_CRS,
    )
    gl.top_labels   = False
    gl.right_labels = False
    gl.xlabel_style = {"size": 7}
    gl.ylabel_style = {"size": 7}

    for _, row in gt_sec_sorted.iterrows():
        if pd.isna(row["muni_lat"]):
            continue
        if row["in_test_domain"]:
            ax.plot(row["muni_lon"], row["muni_lat"], "o",
                    color=color, ms=8, mec="black", mew=0.6,
                    zorder=5, transform=_CRS)
            ax.plot(row["wave_grid_lon"], row["wave_grid_lat"], "s",
                    mfc="none", mec=color, mew=1.3, ms=7,
                    zorder=4, transform=_CRS)
            ax.plot(
                [row["muni_lon"], row["wave_grid_lon"]],
                [row["muni_lat"], row["wave_grid_lat"]],
                "k--", lw=0.55, alpha=0.4, zorder=3, transform=_CRS,
            )
        else:
            ax.plot(row["muni_lon"], row["muni_lat"], "o",
                    mfc="white", mec="gray", ms=7, mew=0.9,
                    zorder=5, transform=_CRS)
        ax.text(
            row["muni_lon"] + 0.04, row["muni_lat"] + 0.04,
            row["municipality"],
            fontsize=5.5, color="black", transform=_CRS, zorder=6,
        )

    ax.add_patch(Rectangle(
        (lon_w.min(), lat_w.min()),
        lon_w.max() - lon_w.min(), lat_w.max() - lat_w.min(),
        lw=1.0, edgecolor="dimgray", facecolor="none",
        ls=":", alpha=0.8, transform=_CRS, zorder=4,
    ))
    ax.set_title(f"Sector: {sector}", fontsize=10, fontweight="bold")
    ax.legend(
        handles=[
            Line2D([0], [0], marker="o", color="w", markerfacecolor=color,
                   mec="black", ms=7, label="City (in domain)"),
            Line2D([0], [0], marker="o", color="w", markerfacecolor="white",
                   mec="gray", ms=7, label="City (outside domain)"),
            Line2D([0], [0], marker="s", color="w", markerfacecolor="none",
                   mec=color, ms=7, label="Nearest WAVERYS point"),
            Line2D([0], [0], color="dimgray", ls=":", lw=1.0, label="Test domain"),
        ],
        fontsize=6, loc="best",
    )


def _hs_panel(
    ax: plt.Axes,
    munis_all: list[str],
    hs_grid: dict[str, np.ndarray],
    hs_events: dict[str, np.ndarray],
    color: str,
) -> None:
    bp_labels:   list[str]      = []
    bp_data:     list[np.ndarray] = []
    bp_is_grid:  list[bool]     = []

    for m in munis_all:
        if m in hs_grid and len(hs_grid[m]) > 0:
            bp_labels.append(m)
            bp_data.append(hs_grid[m])
            bp_is_grid.append(True)
        elif len(hs_events.get(m, [])) > 0:
            bp_labels.append(m)
            bp_data.append(hs_events[m])
            bp_is_grid.append(False)

    if bp_data:
        bp = ax.boxplot(
            bp_data, patch_artist=True, showfliers=True,
            medianprops=dict(color="black", lw=1.4),
            flierprops=dict(marker="o", ms=2.5, alpha=0.4),
        )
        for patch, is_grid in zip(bp["boxes"], bp_is_grid):
            patch.set_facecolor(color if is_grid else "lightgray")
            patch.set_alpha(0.75)
        ax.set_xticks(range(1, len(bp_labels) + 1))
        ax.set_xticklabels(bp_labels, rotation=45, ha="right", fontsize=7.5)
        ax.set_ylabel("$H_s$ (m)", fontsize=9)
        ax.set_title("$H_s$", fontsize=10, fontweight="bold")
        ax.legend(
            handles=[
                Patch(facecolor=color,       alpha=0.75, label="Grid series (1993–2025)"),
                Patch(facecolor="lightgray", alpha=0.75, label="Events DB only"),
            ],
            fontsize=6.5, loc="upper right",
        )
    else:
        ax.text(0.5, 0.5, "No Hs data",
                transform=ax.transAxes, ha="center", va="center",
                fontsize=9, color="gray")
        ax.set_title("$H_s$", fontsize=10, fontweight="bold")


def _ssh_panel(
    ax: plt.Axes,
    munis_gl: list[str],
    zos_grid: dict[str, np.ndarray],
    sector_munis: np.ndarray,
    munis_all: list[str],
) -> None:
    """SSH boxplot panel — only municipalities with a valid GLORYS coastal point."""
    zos_labels: list[str]        = []
    zos_data:   list[np.ndarray] = []

    for m in munis_gl:
        if m in zos_grid and len(zos_grid[m]) > 0:
            zos_labels.append(m)
            zos_data.append(zos_grid[m])

    if zos_data:
        bp = ax.boxplot(
            zos_data, patch_artist=True, showfliers=True,
            medianprops=dict(color="black", lw=1.4),
            flierprops=dict(marker="o", ms=2.5, alpha=0.4),
        )
        for patch in bp["boxes"]:
            patch.set_facecolor(STYLE.color_ssh)
            patch.set_alpha(0.7)
        ax.set_xticks(range(1, len(zos_labels) + 1))
        ax.set_xticklabels(zos_labels, rotation=45, ha="right", fontsize=7.5)
        ax.set_ylabel("SSH (m)", fontsize=9)
        ax.set_title("SSH", fontsize=10, fontweight="bold")
        n_missing = len(munis_all) - len(zos_labels)
        if n_missing > 0:
            ax.text(
                0.98, 0.02,
                f"{n_missing} municipality/ies without GLORYS coastal point\n"
                "(finer GLORYS land mask — not a data error)",
                transform=ax.transAxes, fontsize=6.5, color="gray",
                ha="right", va="bottom", style="italic",
            )
    else:
        ax.text(
            0.5, 0.55,
            "No SSH grid data\nfor this sector",
            transform=ax.transAxes, ha="center", va="center",
            fontsize=9, color="gray",
        )
        ax.text(
            0.5, 0.35,
            f"All {len(sector_munis)} sector municipalities\n"
            "lack a valid GLORYS coastal grid point.\n"
            "This reflects the finer GLORYS12 ocean mask.",
            transform=ax.transAxes, ha="center", va="center",
            fontsize=7.5, color="gray", style="italic",
        )
        ax.set_title("SSH", fontsize=10, fontweight="bold")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )
    from config.plot_config import apply_publication_style
    from src.explore_test_data_south_sc.utils import make_output_dirs
    from src.explore_test_data_south_sc.io import (
        load_glorys_data, load_reported_events, load_wave_data,
    )
    from src.explore_test_data_south_sc.municipalities import (
        run_municipality_grid_association,
    )

    apply_publication_style()
    make_output_dirs()

    _ds_wave   = load_wave_data()
    _ds_gl     = load_glorys_data()
    _df_events = load_reported_events()
    _grid      = run_municipality_grid_association(_df_events, _ds_wave, _ds_gl)

    run_sector_figures(_df_events, _grid, _ds_wave, _ds_gl)
