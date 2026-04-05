"""
Part G — Supplementary statistical analyses and figures.

G1 — Descriptive statistics by municipality (table).
G2 — Scatter Hs vs SSH: one subplot per municipality (nearest coastal grid point,
     daily Hs and daily SSH, coloured by year).
G3 — Monthly seasonal cycle (median ± IQR for Hs and SSH, per municipality).
G4 — Compound co-occurrence quick-look [EDA only] (per municipality).
G5 — Top-N compound events: two-panel time series (last 10 years), quarterly
     x-axis ticks, POT-style circular markers at exceedance dates, no gridlines.
     One figure per municipality.
G6 — Marginal distributions (histograms) of Hs and SSH per municipality.

Important: quantile thresholds in G4/G5 are empirical and exploratory.
They do NOT define compound events for the final study methodology.

Design
------
All analyses (G1–G6) use the nearest coastal WAVERYS / GLORYS grid points
from the municipality–grid association table (Part E).  Domain means are NOT
used anywhere in Part G.
"""
from __future__ import annotations

import logging
import math
import re
import sys
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from scipy.stats import pearsonr

# Allow running this module directly (python statistics.py)
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.explore_test_data_south_sc.config.analysis_config import CFG
from config.plot_config import STYLE
from src.explore_test_data_south_sc.utils import save_fig

log = logging.getLogger(__name__)


def _muni_slug(name: str) -> str:
    """Convert a municipality name to a safe filename slug.

    Replaces any character that is not a letter or digit with an underscore,
    preventing path separators (e.g. "/" in "Içara/Balneário Rincão") from
    being interpreted as directory components.
    """
    return re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()


def run_additional_analyses(
    ds_wave: xr.Dataset,
    ds_gl: xr.Dataset,
    df_events: pd.DataFrame,
    grid_table: pd.DataFrame,
) -> None:
    """Part G: supplementary exploratory statistical analyses."""
    log.info("== Part G: Additional analyses ==")

    da_hs  = ds_wave[CFG["wave_var"]]
    da_zos = ds_gl[CFG["ssl_var"]]

    # ── Per-municipality daily series (all of G1–G6) ──────────────────────
    muni_series = _extract_muni_daily_series(da_hs, da_zos, grid_table)

    _g1_descriptive_stats(muni_series)
    _g2_scatter_per_municipality(muni_series)
    _g3_seasonal_cycle(muni_series)
    compound_dict = _g4_compound_quicklook(muni_series)
    _g5_top_compound_events(muni_series, compound_dict)
    _g6_distributions(muni_series)


# ── Shared helper: per-municipality daily series ──────────────────────────────

def _extract_muni_daily_series(
    da_hs: xr.DataArray,
    da_zos: xr.DataArray,
    grid_table: pd.DataFrame,
) -> dict[str, dict]:
    """Extract aligned daily Hs and SSH series for each municipality.

    WAVERYS (3-hourly) is resampled to daily mean to match GLORYS (daily).
    Only municipalities with both ``in_wave_domain`` and ``in_gl_domain``
    produce a full Hs+SSH paired series.  Municipalities with only one of the
    two flags produce a partial series.

    Returns
    -------
    dict keyed by municipality name.  Each value is a dict with:
        ``hs_all``   : np.ndarray — all finite Hs values (full period).
        ``zos_all``  : np.ndarray — all finite SSH values (full period).
        ``hs_daily`` : np.ndarray — daily Hs values aligned to ``times``.
        ``zos_daily``: np.ndarray — daily SSH values aligned to ``times``.
        ``times``    : pd.DatetimeIndex — common dates for paired series.
    """
    wave_col = "in_wave_domain" if "in_wave_domain" in grid_table.columns else "in_test_domain"
    gl_col   = "in_gl_domain"   if "in_gl_domain"   in grid_table.columns else "in_test_domain"

    series: dict[str, dict] = {}

    for _, row in grid_table.iterrows():
        muni    = row["municipality"]
        has_hs  = bool(row[wave_col])
        has_ssh = bool(row[gl_col])

        hs_all = zos_all = np.array([])
        hs_d   = zos_d  = np.array([])
        times  = pd.DatetimeIndex([])

        if has_hs:
            raw = da_hs.sel(
                latitude=row["wave_grid_lat"], longitude=row["wave_grid_lon"],
                method="nearest",
            )
            hs_daily_raw = raw.resample(time="1D").mean()
            hs_all = raw.values
            hs_all = hs_all[np.isfinite(hs_all)]

            if has_ssh:
                raw_zos = da_zos.sel(
                    latitude=row["gl_grid_lat"], longitude=row["gl_grid_lon"],
                    method="nearest",
                )
                zos_all = raw_zos.values
                zos_all = zos_all[np.isfinite(zos_all)]

                common = np.intersect1d(
                    hs_daily_raw.time.values,
                    raw_zos.time.values,
                )
                hs_c   = hs_daily_raw.sel(time=common).values
                zos_c  = raw_zos.sel(time=common).values
                valid  = np.isfinite(hs_c) & np.isfinite(zos_c)
                hs_d   = hs_c[valid]
                zos_d  = zos_c[valid]
                times  = pd.to_datetime(common)[valid]

        elif has_ssh:
            raw_zos = da_zos.sel(
                latitude=row["gl_grid_lat"], longitude=row["gl_grid_lon"],
                method="nearest",
            )
            zos_all = raw_zos.values
            zos_all = zos_all[np.isfinite(zos_all)]

        series[muni] = {
            "hs_all":    hs_all,
            "zos_all":   zos_all,
            "hs_daily":  hs_d,
            "zos_daily": zos_d,
            "times":     times,
        }

    log.info(
        "  Per-municipality series: %d municipalities | "
        "%d with paired Hs+SSH daily series",
        len(series),
        sum(len(v["times"]) > 0 for v in series.values()),
    )
    return series


# ── Shared layout helper ───────────────────────────────────────────────────────

def _muni_grid_layout(n: int) -> tuple[int, int, float, float]:
    """Return (nr, nc, fig_w, fig_h) for a grid of n municipality subplots."""
    nc = min(n, 3)
    nr = math.ceil(n / nc)
    fig_w = nc * (STYLE.fig_width_single - 1.0)
    fig_h = nr * (STYLE.fig_width_single - 1.0)
    return nr, nc, fig_w, fig_h


def _hide_unused_axes(axes: np.ndarray, n: int, nr: int, nc: int) -> None:
    for ax_idx in range(n, nr * nc):
        axes[ax_idx // nc][ax_idx % nc].set_visible(False)


# ── G1: descriptive statistics ────────────────────────────────────────────────

def _g1_descriptive_stats(muni_series: dict[str, dict]) -> None:
    rows = []
    for muni, s in muni_series.items():
        hs_s  = s["hs_all"]
        zos_s = s["zos_all"]
        if len(hs_s) == 0 and len(zos_s) == 0:
            continue
        r: dict = {"municipality": muni}
        if len(hs_s) > 0:
            r.update({
                "hs_mean":   np.nanmean(hs_s),   "hs_median": np.nanmedian(hs_s),
                "hs_p75":    np.nanpercentile(hs_s, 75),
                "hs_p90":    np.nanpercentile(hs_s, 90),
                "hs_p99":    np.nanpercentile(hs_s, 99),
                "hs_max":    np.nanmax(hs_s),
            })
        if len(zos_s) > 0:
            r.update({
                "zos_mean":   np.nanmean(zos_s),   "zos_median": np.nanmedian(zos_s),
                "zos_p75":    np.nanpercentile(zos_s, 75),
                "zos_p90":    np.nanpercentile(zos_s, 90),
                "zos_p99":    np.nanpercentile(zos_s, 99),
                "zos_max":    np.nanmax(zos_s),
            })
        rows.append(r)

    if rows:
        pd.DataFrame(rows).to_csv(
            CFG["tab_dir"] / "tab_descriptive_stats_by_municipality.csv", index=False
        )
        log.info("  -> tab_descriptive_stats_by_municipality.csv")


# ── G2: scatter Hs vs SSH — one subplot per municipality ─────────────────────

def _g2_scatter_per_municipality(muni_series: dict[str, dict]) -> None:
    """G2 — Scatter of daily Hs vs SSH at the nearest coastal grid point.

    One subplot per municipality (paired series only).  Each subplot is
    coloured by year.  Pearson r and p-value annotated in the title.
    """
    paired = {m: s for m, s in muni_series.items() if len(s["times"]) > 20}
    if not paired:
        log.warning("  G2: no municipality with enough paired Hs+SSH data — skipping.")
        return

    n   = len(paired)
    nr, nc, fig_w, fig_h = _muni_grid_layout(n)
    fig, axes = plt.subplots(nr, nc, figsize=(fig_w, fig_h), squeeze=False)

    q_levels = {
        "hs":  CFG["compound_hs_quantile"]  * 100,
        "ssh": CFG["compound_zos_quantile"] * 100,
    }

    for ax_idx, (muni, s) in enumerate(paired.items()):
        ax   = axes[ax_idx // nc][ax_idx % nc]
        hs_d = s["hs_daily"]
        zd   = s["zos_daily"]
        t    = s["times"]

        r_val, p_val = pearsonr(hs_d, zd)
        q_hs  = float(np.nanpercentile(hs_d, q_levels["hs"]))
        q_zos = float(np.nanpercentile(zd,   q_levels["ssh"]))

        sc = ax.scatter(hs_d, zd, c=t.year, cmap=STYLE.cmap_sequential,
                        s=5, alpha=0.40, lw=0)
        fig.colorbar(sc, ax=ax, pad=0.01, shrink=0.85, label="Year")
        ax.axvline(q_hs,  color=STYLE.color_hs,  ls="--", lw=0.85, alpha=0.8,
                   label=f"$H_s$ q{int(q_levels['hs']):.0f}")
        ax.axhline(q_zos, color=STYLE.color_ssh, ls="--", lw=0.85, alpha=0.8,
                   label=f"SSH q{int(q_levels['ssh']):.0f}")
        ax.set_xlabel("Daily $H_s$ (m)",   fontsize=8)
        ax.set_ylabel("Daily SSH (m)",      fontsize=8)
        p_str = "p < 0.001" if p_val < 0.001 else f"p = {p_val:.3f}"
        ax.set_title(
            f"{muni}\nr = {r_val:.2f}  ({p_str})",
            fontsize=8.5,
        )
        ax.legend(fontsize=6, loc="upper left")

    _hide_unused_axes(axes, n, nr, nc)
    fig.suptitle(
        "Daily $H_s$ vs SSH — nearest coastal grid point per municipality\n"
        "(WAVERYS daily · GLORYS daily · 1993–2025)",
        fontsize=10, y=1.01,
    )
    fig.tight_layout()
    save_fig(fig, "fig_G2_scatter_Hs_SSH_per_municipality")


# ── G3: seasonal cycle — per municipality ─────────────────────────────────────

def _g3_seasonal_cycle(muni_series: dict[str, dict]) -> None:
    """G3 — Monthly seasonal cycle per municipality.

    Two multi-panel figures:
    - fig_G3a: Hs median ± IQR — one subplot per municipality.
    - fig_G3b: SSH median ± IQR — one subplot per municipality.
    """
    paired = {m: s for m, s in muni_series.items() if len(s["times"]) > 20}
    if not paired:
        log.warning("  G3: no municipality with enough paired data — skipping.")
        return

    n = len(paired)
    nr, nc, fig_w, fig_h = _muni_grid_layout(n)
    months = np.arange(1, 13)
    month_labels = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]

    fig_hs,  axes_hs  = plt.subplots(nr, nc, figsize=(fig_w, fig_h), squeeze=False)
    fig_zos, axes_zos = plt.subplots(nr, nc, figsize=(fig_w, fig_h), squeeze=False)

    for ax_idx, (muni, s) in enumerate(paired.items()):
        ax_h = axes_hs [ax_idx // nc][ax_idx % nc]
        ax_z = axes_zos[ax_idx // nc][ax_idx % nc]

        df = pd.DataFrame({
            "hs":  s["hs_daily"],
            "zos": s["zos_daily"],
            "month": s["times"].month,
        })
        hs_mon = df.groupby("month")["hs"].agg(
            median="median",
            q25=lambda x: x.quantile(0.25),
            q75=lambda x: x.quantile(0.75),
        )
        zos_mon = df.groupby("month")["zos"].agg(
            median="median",
            q25=lambda x: x.quantile(0.25),
            q75=lambda x: x.quantile(0.75),
        )

        ax_h.plot(months, hs_mon["median"].values,
                  color=STYLE.color_hs, lw=2, marker="o", ms=4)
        ax_h.fill_between(months, hs_mon["q25"].values, hs_mon["q75"].values,
                          color=STYLE.color_hs, alpha=0.18, label="IQR")
        ax_h.set_title(muni, fontsize=8.5)
        ax_h.set_ylabel("$H_s$ (m)", fontsize=8)
        ax_h.set_xticks(months)
        ax_h.set_xticklabels(month_labels, fontsize=7)
        ax_h.legend(fontsize=6)

        ax_z.plot(months, zos_mon["median"].values,
                  color=STYLE.color_ssh, lw=2, marker="o", ms=4)
        ax_z.fill_between(months, zos_mon["q25"].values, zos_mon["q75"].values,
                          color=STYLE.color_ssh, alpha=0.18, label="IQR")
        ax_z.set_title(muni, fontsize=8.5)
        ax_z.set_ylabel("SSH (m)", fontsize=8)
        ax_z.set_xticks(months)
        ax_z.set_xticklabels(month_labels, fontsize=7)
        ax_z.legend(fontsize=6)

    _hide_unused_axes(axes_hs,  n, nr, nc)
    _hide_unused_axes(axes_zos, n, nr, nc)

    fig_hs.suptitle(
        "Seasonal cycle — $H_s$ monthly median ± IQR per municipality\n"
        "(WAVERYS nearest coastal point · 1993–2025)",
        fontsize=10, y=1.01,
    )
    fig_hs.tight_layout()
    save_fig(fig_hs, "fig_G3a_seasonal_cycle_Hs_per_municipality")

    fig_zos.suptitle(
        "Seasonal cycle — SSH monthly median ± IQR per municipality\n"
        "(GLORYS nearest coastal point · 1993–2025)",
        fontsize=10, y=1.01,
    )
    fig_zos.tight_layout()
    save_fig(fig_zos, "fig_G3b_seasonal_cycle_SSH_per_municipality")


# ── G4: compound co-occurrence quick-look — per municipality ──────────────────

def _g4_compound_quicklook(
    muni_series: dict[str, dict],
) -> dict[str, dict]:
    """G4 — Compound scatter per municipality.

    Returns a dict keyed by municipality with compound mask and thresholds,
    used downstream by G5.
    """
    paired = {m: s for m, s in muni_series.items() if len(s["times"]) > 20}
    if not paired:
        log.warning("  G4: no municipality with enough paired data — skipping.")
        return {}

    n = len(paired)
    nr, nc, fig_w, fig_h = _muni_grid_layout(n)
    fig, axes = plt.subplots(nr, nc, figsize=(fig_w, fig_h), squeeze=False)

    compound_dict: dict[str, dict] = {}

    for ax_idx, (muni, s) in enumerate(paired.items()):
        ax   = axes[ax_idx // nc][ax_idx % nc]
        hs_d = s["hs_daily"]
        zd   = s["zos_daily"]
        t    = s["times"]

        q_hs  = float(np.nanpercentile(hs_d, CFG["compound_hs_quantile"]  * 100))
        q_zos = float(np.nanpercentile(zd,   CFG["compound_zos_quantile"] * 100))
        compound = (hs_d >= q_hs) & (zd >= q_zos)
        n_comp   = int(compound.sum())
        pct      = 100 * n_comp / len(hs_d)

        compound_dict[muni] = {
            "mask":  compound,
            "q_hs":  q_hs,
            "q_zos": q_zos,
            "hs":    hs_d,
            "zos":   zd,
            "times": t,
        }

        log.info(
            "  %s — compound [EDA]: Hs>=q%.0f (%.2f m) & SSH>=q%.0f (%.3f m) "
            "-> %d days (%.1f%%)",
            muni,
            CFG["compound_hs_quantile"]  * 100, q_hs,
            CFG["compound_zos_quantile"] * 100, q_zos,
            n_comp, pct,
        )

        ax.scatter(hs_d[~compound], zd[~compound],
                   color="#999999", s=4, alpha=0.25, lw=0, label="Background")
        ax.scatter(
            hs_d[compound], zd[compound],
            color=STYLE.color_highlight, s=12, alpha=0.75, lw=0,
            label=f"n = {n_comp} ({pct:.1f}%)",
        )
        ax.axvline(q_hs,  color=STYLE.color_hs,  ls="--", lw=0.85, alpha=0.8)
        ax.axhline(q_zos, color=STYLE.color_ssh, ls="--", lw=0.85, alpha=0.8)
        ax.set_xlabel("Daily $H_s$ (m)", fontsize=8)
        ax.set_ylabel("Daily SSH (m)",   fontsize=8)
        ax.set_title(
            f"{muni}\n"
            f"$H_s$\u2265q{int(CFG['compound_hs_quantile']*100)} "
            f"& SSH\u2265q{int(CFG['compound_zos_quantile']*100)}",
            fontsize=8.5,
        )
        ax.legend(fontsize=6, loc="upper left")

    _hide_unused_axes(axes, n, nr, nc)
    fig.suptitle(
        "Compound co-occurrence quick-look [EDA] — per municipality\n"
        "Empirical quantile thresholds — not a final event definition",
        fontsize=9.5, y=1.01,
    )
    fig.tight_layout()
    save_fig(fig, "fig_G4_compound_quicklook_per_municipality")

    return compound_dict


# ── G5: top compound events — per municipality ────────────────────────────────

def _g5_top_compound_events(
    muni_series: dict[str, dict],
    compound_dict: dict[str, dict],
) -> None:
    """G5 — Time series (last 10 years) with POT-style compound event markers.

    One two-panel figure per municipality.  Top-20 events across all
    municipalities saved to CSV.

    Formatting choices:
    - x-axis ticks every 3 months for readability on a 10-year span.
    - Circular scatter markers at compound-event dates (Peak-Over-Threshold
      style) instead of vertical shading lines.
    - No background gridlines.
    """
    if not compound_dict:
        log.warning("  G5: no compound data — skipping.")
        return

    # ── Save top-20 events (pooled across municipalities) ─────────────────
    all_rows = []
    for muni, cd in compound_dict.items():
        mask = cd["mask"]
        if mask.sum() == 0:
            continue
        all_rows.append(pd.DataFrame({
            "municipality": muni,
            "date":         cd["times"][mask],
            "hs_m":         cd["hs"][mask],
            "ssh_m":        cd["zos"][mask],
            "hs_ssh_sum":   cd["hs"][mask] + cd["zos"][mask],
        }))

    if all_rows:
        (pd.concat(all_rows)
           .sort_values("hs_ssh_sum", ascending=False)
           .head(20)
           .to_csv(CFG["tab_dir"] / "tab_top_compound_events_eda.csv", index=False))
        log.info(
            "  -> tab_top_compound_events_eda.csv (%d municipalities contributing)",
            len(all_rows),
        )

    # ── One figure per municipality ────────────────────────────────────────
    for muni, cd in compound_dict.items():
        hs_d     = cd["hs"]
        zd       = cd["zos"]
        t        = cd["times"]
        q_hs     = cd["q_hs"]
        q_zos    = cd["q_zos"]
        compound = cd["mask"]

        t_start  = t.max() - pd.DateOffset(years=10)
        mask_plt = t >= t_start
        t_plt    = t[mask_plt]
        hs_plt   = hs_d[mask_plt]
        zos_plt  = zd[mask_plt]
        comp_plt = compound[mask_plt]

        n_comp_plt = int(comp_plt.sum())
        t_exc  = t_plt[comp_plt]
        hs_exc = hs_plt[comp_plt]
        zos_exc= zos_plt[comp_plt]

        fig, (ax_a, ax_b) = plt.subplots(
            2, 1, figsize=(STYLE.fig_width_wide - 1, 6), sharex=True
        )

        # ── Hs panel ──────────────────────────────────────────────────────
        ax_a.plot(t_plt, hs_plt, color=STYLE.color_hs, lw=0.75, alpha=0.85)
        ax_a.axhline(q_hs, color=STYLE.color_hs, ls="--", lw=0.9, alpha=0.7,
                     label=f"q{int(CFG['compound_hs_quantile']*100)} = {q_hs:.2f} m")
        ax_a.scatter(t_exc, hs_exc, s=20, marker="o",
                     color=STYLE.color_highlight, zorder=5,
                     label=f"Compound [EDA] (n = {n_comp_plt})")
        ax_a.set_ylabel("$H_s$ (m)")
        ax_a.set_title(
            f"{muni} — daily time series (last 10 years) — compound markers [EDA]\n"
            f"Circles: $H_s$ \u2265 q{int(CFG['compound_hs_quantile']*100)} "
            f"AND SSH \u2265 q{int(CFG['compound_zos_quantile']*100)}",
            fontsize=9.5,
        )
        ax_a.legend(fontsize=8)
        ax_a.grid(False)

        # ── SSH panel ─────────────────────────────────────────────────────
        ax_b.plot(t_plt, zos_plt, color=STYLE.color_ssh, lw=0.75, alpha=0.85)
        ax_b.axhline(q_zos, color=STYLE.color_ssh, ls="--", lw=0.9, alpha=0.7,
                     label=f"q{int(CFG['compound_zos_quantile']*100)} = {q_zos:.3f} m")
        ax_b.scatter(t_exc, zos_exc, s=20, marker="o",
                     color=STYLE.color_highlight, zorder=5,
                     label=f"Compound [EDA] (n = {n_comp_plt})")
        ax_b.set_ylabel("SSH (m)")
        ax_b.legend(fontsize=8)
        ax_b.grid(False)

        ax_b.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax_b.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
        plt.setp(ax_b.xaxis.get_majorticklabels(), rotation=0, ha="center")

        fig.tight_layout()
        save_fig(fig, f"fig_G5_timeseries_compound_{_muni_slug(muni)}")


# ── G6: marginal distributions — per municipality ─────────────────────────────

def _g6_distributions(muni_series: dict[str, dict]) -> None:
    """G6 — Histograms of Hs and SSH at the nearest coastal point per municipality.

    Two multi-panel figures:
    - fig_G6a: Hs distributions — one subplot per municipality.
    - fig_G6b: SSH distributions — one subplot per municipality.
    """
    paired = {m: s for m, s in muni_series.items() if len(s["times"]) > 20}
    if not paired:
        log.warning("  G6: no municipality with enough paired data — skipping.")
        return

    n = len(paired)
    nr, nc, fig_w, fig_h = _muni_grid_layout(n)

    fig_hs,  axes_hs  = plt.subplots(nr, nc, figsize=(fig_w, fig_h), squeeze=False)
    fig_zos, axes_zos = plt.subplots(nr, nc, figsize=(fig_w, fig_h), squeeze=False)

    for ax_idx, (muni, s) in enumerate(paired.items()):
        ax_h = axes_hs [ax_idx // nc][ax_idx % nc]
        ax_z = axes_zos[ax_idx // nc][ax_idx % nc]

        hs_v  = s["hs_daily"]
        zos_v = s["zos_daily"]

        q_hs  = float(np.nanpercentile(hs_v,  CFG["compound_hs_quantile"]  * 100))
        q_zos = float(np.nanpercentile(zos_v, CFG["compound_zos_quantile"] * 100))

        ax_h.hist(hs_v, bins=40, color=STYLE.color_hs,
                  edgecolor="white", lw=0.3, alpha=0.8, density=True)
        ax_h.axvline(q_hs, color="black", ls="--", lw=1.1,
                     label=f"q{int(CFG['compound_hs_quantile']*100)} = {q_hs:.2f} m")
        ax_h.axvline(float(np.nanmedian(hs_v)), color=STYLE.color_hs, ls="-", lw=1.1,
                     label=f"Median = {np.nanmedian(hs_v):.2f} m")
        ax_h.set_xlabel("Daily $H_s$ (m)", fontsize=8)
        ax_h.set_ylabel("Density",          fontsize=8)
        ax_h.set_title(muni, fontsize=8.5)
        ax_h.legend(fontsize=6)

        ax_z.hist(zos_v, bins=40, color=STYLE.color_ssh,
                  edgecolor="white", lw=0.3, alpha=0.8, density=True)
        ax_z.axvline(q_zos, color="black", ls="--", lw=1.1,
                     label=f"q{int(CFG['compound_zos_quantile']*100)} = {q_zos:.3f} m")
        ax_z.axvline(float(np.nanmedian(zos_v)), color=STYLE.color_ssh, ls="-", lw=1.1,
                     label=f"Median = {np.nanmedian(zos_v):.3f} m")
        ax_z.set_xlabel("Daily SSH (m)", fontsize=8)
        ax_z.set_ylabel("Density",       fontsize=8)
        ax_z.set_title(muni, fontsize=8.5)
        ax_z.legend(fontsize=6)

    _hide_unused_axes(axes_hs,  n, nr, nc)
    _hide_unused_axes(axes_zos, n, nr, nc)

    fig_hs.suptitle(
        "$H_s$ distribution per municipality\n"
        "(WAVERYS nearest coastal point · daily · 1993–2025)",
        fontsize=10, y=1.01,
    )
    fig_hs.tight_layout()
    save_fig(fig_hs, "fig_G6a_distributions_Hs_per_municipality")

    fig_zos.suptitle(
        "SSH distribution per municipality\n"
        "(GLORYS nearest coastal point · daily · 1993–2025)",
        fontsize=10, y=1.01,
    )
    fig_zos.tight_layout()
    save_fig(fig_zos, "fig_G6b_distributions_SSH_per_municipality")


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

    run_additional_analyses(_ds_wave, _ds_gl, _df_events, _grid)
