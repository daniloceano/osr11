"""
Part D — Exploratory analysis of the reported events database.

Generates summary tables and figures from the Leal et al. (2024) dataset:
- Event counts by municipality (bar chart).
- Hs AND SSH boxplots by municipality (side-by-side, at event dates).
- Monthly event count (seasonal cycle).

Changes from the initial version
---------------------------------
- D1: Sector panel removed.  Since the analysis is restricted to the South
  sector only, a sector comparison is meaningless.
- D2: SSH (sea level from GLORYS, at event dates) added alongside Hs.
  Requires ``grid_table`` and ``ds_gl`` to be provided; if absent the SSH
  panel is silently skipped.
- D3 (Hs by sector): removed for the same reason as the D1 sector panel.

Note: at this stage the events database has already been filtered to South
sector municipalities by io.load_reported_events().
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

# Allow running this module directly (python reported_events.py)
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.explore_test_data_south_sc.config.analysis_config import CFG
from config.plot_config import STYLE
from src.explore_test_data_south_sc.utils import save_fig

log = logging.getLogger(__name__)


def run_reported_events_eda(
    df: pd.DataFrame,
    ds_gl: xr.Dataset | None = None,
    grid_table: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Part D: summary tables and exploratory figures for the events database.

    Parameters
    ----------
    df:
        Cleaned reported-events DataFrame (output of io.load_reported_events).
    ds_gl:
        GLORYS dataset.  Required for the SSH panel in D2; if None, the SSH
        panel is omitted.
    grid_table:
        Municipality–grid association table (output of Part E).  Required for
        the SSH panel in D2; if None, the SSH panel is omitted.

    Returns
    -------
    muni_count, sector_count : pd.DataFrame
        Aggregated event counts and Hs statistics per municipality and sector.
    """
    log.info("== Part D: Reported events EDA ==")

    muni_count, sector_count = _build_summary_tables(df)
    _fig_d1_event_counts(df, muni_count)
    _fig_d2_hs_ssh_by_municipality(df, ds_gl, grid_table)
    _fig_d4_monthly_seasonality(df)

    return muni_count, sector_count


# ── Summary tables ────────────────────────────────────────────────────────────

def _build_summary_tables(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    muni_count = (
        df.groupby("municipality")
        .agg(
            n_events       =("disaster_id", "count"),
            coastal_sector =("coastal_sector", "first"),
            hs_mean        =("hs_m", "mean"),
            hs_median      =("hs_m", "median"),
            hs_max         =("hs_m", "max"),
            wspd_mean      =("wspd_ms", "mean"),
        )
        .reset_index()
        .sort_values("n_events", ascending=False)
    )
    muni_count.to_csv(CFG["tab_dir"] / "tab_events_by_municipality.csv", index=False)
    log.info("  -> tab_events_by_municipality.csv")

    sector_count = (
        df.groupby("coastal_sector")
        .agg(
            n_events         =("disaster_id", "count"),
            n_municipalities =("municipality", "nunique"),
            hs_mean          =("hs_m", "mean"),
            hs_max           =("hs_m", "max"),
        )
        .reset_index()
        .sort_values("n_events", ascending=False)
    )
    sector_count.to_csv(CFG["tab_dir"] / "tab_events_by_sector.csv", index=False)
    log.info("  -> tab_events_by_sector.csv")

    return muni_count, sector_count


# ── Figures ───────────────────────────────────────────────────────────────────

def _fig_d1_event_counts(
    df: pd.DataFrame,
    muni_count: pd.DataFrame,
) -> None:
    """D1 — Horizontal bar chart of event counts by municipality (South sector only)."""
    mc   = muni_count.sort_values("n_events", ascending=True)
    fig, ax = plt.subplots(figsize=(STYLE.fig_width_single + 1, max(4, len(mc) * 0.45)))
    bars = ax.barh(mc["municipality"], mc["n_events"],
                   color=STYLE.color_boxplot_default, edgecolor="white", lw=0.4)
    ax.set_xlabel("Number of events")
    ax.set_title(
        "Declared coastal disasters by municipality\n"
        "Santa Catarina — South sector (1998–2023)",
        fontsize=10,
    )
    ax.tick_params(axis="y", labelsize=8)
    for bar, val in zip(bars, mc["n_events"]):
        ax.text(val + 0.05, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=7.5)
    plt.tight_layout()
    save_fig(fig, "fig_D1_events_by_municipality")


def _fig_d2_hs_ssh_by_municipality(
    df: pd.DataFrame,
    ds_gl: xr.Dataset | None,
    grid_table: pd.DataFrame | None,
) -> None:
    """D2 — Hs boxplots by municipality; SSH at event dates if grid_table is available."""
    muni_order = (
        df.groupby("municipality")["hs_m"].median()
        .sort_values(ascending=False).index.tolist()
    )

    has_ssh = ds_gl is not None and grid_table is not None
    ssh_at_events: dict[str, np.ndarray] = {}

    if has_ssh:
        da_zos = ds_gl[CFG["ssl_var"]]
        for muni in muni_order:
            row = grid_table[grid_table["municipality"] == muni]
            if row.empty or not bool(row.iloc[0]["in_gl_domain"]):
                ssh_at_events[muni] = np.array([])
                continue
            gl_lat = float(row.iloc[0]["gl_grid_lat"])
            gl_lon = float(row.iloc[0]["gl_grid_lon"])
            da     = da_zos.sel(latitude=gl_lat, longitude=gl_lon, method="nearest")
            event_dates = df.loc[df["municipality"] == muni, "date"].dropna()
            vals = []
            for dt in event_dates:
                try:
                    v = float(da.sel(time=dt.strftime("%Y-%m-%d"), method="nearest").values)
                    if np.isfinite(v):
                        vals.append(v)
                except Exception:
                    pass
            ssh_at_events[muni] = np.array(vals)
        log.info(
            "  D2 SSH at event dates: %d/%d municipalities with data",
            sum(len(v) > 0 for v in ssh_at_events.values()), len(muni_order),
        )

    ncols = 2 if has_ssh else 1
    fig_w = (STYLE.fig_width_double if has_ssh else STYLE.fig_width_single + 1)
    fig, axes = plt.subplots(1, ncols, figsize=(fig_w, max(4.5, len(muni_order) * 0.5)))
    if ncols == 1:
        axes = [axes]

    # ── Hs panel ──────────────────────────────────────────────────────────
    ax_hs = axes[0]
    data_hs = [df.loc[df["municipality"] == m, "hs_m"].dropna().values for m in muni_order]
    bp = ax_hs.boxplot(
        data_hs, vert=False, patch_artist=True, showfliers=True,
        medianprops=dict(color="black", lw=1.5),
        flierprops=dict(marker="o", ms=3, alpha=0.45),
    )
    for patch in bp["boxes"]:
        patch.set_facecolor(STYLE.color_hs)
        patch.set_alpha(0.65)
    ax_hs.set_yticks(range(1, len(muni_order) + 1))
    ax_hs.set_yticklabels(muni_order, fontsize=8)
    ax_hs.set_xlabel("$H_s$ at event date (m)")
    ax_hs.set_title(
        "$H_s$ — reported events\n(WAVERYS value at event date · ordered by median)",
        fontsize=9.5,
    )

    # ── SSH panel (optional) ──────────────────────────────────────────────
    if has_ssh:
        ax_ssh = axes[1]
        data_ssh = [ssh_at_events.get(m, np.array([])) for m in muni_order]
        nonempty = [d for d in data_ssh if len(d) > 0]
        if nonempty:
            bp2 = ax_ssh.boxplot(
                data_ssh, vert=False, patch_artist=True, showfliers=True,
                medianprops=dict(color="black", lw=1.5),
                flierprops=dict(marker="o", ms=3, alpha=0.45),
            )
            for patch in bp2["boxes"]:
                patch.set_facecolor(STYLE.color_ssh)
                patch.set_alpha(0.65)
        ax_ssh.set_yticks(range(1, len(muni_order) + 1))
        ax_ssh.set_yticklabels(muni_order, fontsize=8)
        ax_ssh.set_xlabel("SSH at event date (m)")
        ax_ssh.set_title(
            "SSH — GLORYS at event date\n(nearest coastal grid point)",
            fontsize=9.5,
        )
        n_ssh = sum(len(v) > 0 for v in ssh_at_events.values())
        if n_ssh < len(muni_order):
            ax_ssh.text(
                0.98, 0.02,
                f"SSH available: {n_ssh}/{len(muni_order)} municipalities\n"
                "(others outside GLORYS coastal domain)",
                transform=ax_ssh.transAxes, fontsize=7, color="gray",
                ha="right", va="bottom", style="italic",
            )

    fig.suptitle(
        "Reported coastal disasters — Santa Catarina, South sector (1998–2023)",
        fontsize=11, y=1.01,
    )
    plt.tight_layout()
    save_fig(fig, "fig_D2_Hs_SSH_boxplot_by_municipality")


def _fig_d4_monthly_seasonality(df: pd.DataFrame) -> None:
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly = df.dropna(subset=["date"]).groupby(df["date"].dt.month).size()

    fig, ax = plt.subplots(figsize=(STYLE.fig_width_single + 1.5, 4))
    ax.bar(monthly.index, monthly.values,
           color=STYLE.color_boxplot_default, edgecolor="white", lw=0.5)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(month_names)
    ax.set_xlabel("Month")
    ax.set_ylabel("Number of events")
    ax.set_title(
        "Monthly distribution of reported coastal disasters\n"
        "South sector — Santa Catarina",
        fontsize=10,
    )
    plt.tight_layout()
    save_fig(fig, "fig_D4_monthly_seasonality")


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

    run_reported_events_eda(_df_events, ds_gl=_ds_gl, grid_table=_grid)
