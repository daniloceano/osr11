"""
Per-event figures for the tidal sensitivity analysis.

Each figure has three stacked panels:
  (a) Hₛ — identical to the preliminary compound figure
  (b) SSH (zos only)
  (c) SSH_total = SSH + FES2022 astronomical tide

Panel (b) shows SSH with the SSH-only q90 threshold and SSH-only POT peaks.
Panel (c) shows SSH_total with the SSH_total q90 threshold and SSH_total POT peaks.
This layout makes it easy to see how much the tide shifts the total sea-level
signal and whether it changes the exceedance status during the event window.

A comparison text box at the top of the figure summarises:
  - max Hₛ / q90 ratio in window
  - max SSH / q90 ratio  (SSH only)
  - max SSH_total / q90 ratio  (SSH + tide)
  - detected compound (SSH only)?
  - detected compound (SSH + tide)?

Files are saved to: outputs/tidal_sensitivity/figures/events/
Naming convention: fig_TS_event_{id:03d}_{municipality_slug}_{YYYYMMDD}.png
"""
from __future__ import annotations

import logging

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

from config.plot_config import apply_publication_style, STYLE
from src.tidal_sensitivity.config.analysis_config import CFG
from src.preliminary_compound.events import EventRecord
from src.preliminary_compound.utils import muni_slug
from src.tidal_sensitivity.utils import save_fig

matplotlib.use("Agg")
log = logging.getLogger(__name__)

# ── Helpers (re-used from preliminary compound) ──────────────────────────────

def _shade_exceedances(ax, series: pd.Series, threshold: float, color: str, alpha: float = 0.25) -> None:
    """Fill contiguous exceedance blocks above threshold."""
    if np.isnan(threshold):
        return
    above = series >= threshold
    if not above.any():
        return
    times = series.index
    in_block = False
    t_start = None
    for t, exc in zip(times, above):
        if exc and not in_block:
            t_start = t
            in_block = True
        elif not exc and in_block:
            ax.axvspan(t_start, t, color=color, alpha=alpha, linewidth=0)
            in_block = False
    if in_block:
        ax.axvspan(t_start, times[-1], color=color, alpha=alpha, linewidth=0)


def _mark_pot_peaks(ax, series: pd.Series, threshold: float, color: str) -> None:
    """Mark MagicA POT peaks above threshold."""
    if np.isnan(threshold):
        return
    finite = series.dropna()
    if finite.empty or (finite >= threshold).sum() < 1:
        return
    try:
        import magica as ma
        processor = ma.read_data(finite)
        ea = processor.get_extremes_analyzer()
        peaks, peak_times = ea.peaks_over_threshold(threshold=threshold, event_wise=True)
        if len(peak_times) > 0:
            ax.scatter(
                peak_times, peaks,
                color=color, zorder=6, s=40, marker="^",
                edgecolors="white", linewidths=0.6, label="POT peak",
            )
    except Exception as exc:
        log.debug("MagicA POT failed: %s", exc)


def _fmt_time_ax(ax, dates) -> None:
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=7)


# ── Per-event 3-panel figure ─────────────────────────────────────────────────

def _plot_panel(
    ax,
    series: pd.Series,
    threshold: float,
    event_date: pd.Timestamp,
    color: str,
    ylabel: str,
    max_val: float,
    max_norm: float,
    label_str: str,
) -> None:
    """Draw one time-series panel."""
    ax.plot(series.index, series.values, color=color, lw=1.4, zorder=3)
    _shade_exceedances(ax, series, threshold, color)
    _mark_pot_peaks(ax, series, threshold, color)

    if not np.isnan(threshold):
        ax.axhline(threshold, color="gray", lw=0.9, ls="--", alpha=0.8, label=f"q{int(CFG['threshold_quantile']*100)}")

    # Event date marker
    ax.axvline(pd.Timestamp(event_date), color="black", lw=1.2, ls=":", alpha=0.9)

    # Max marker
    if not np.isnan(max_val):
        max_t = series.idxmax()
        ax.scatter([max_t], [max_val], color=color, s=50, zorder=7, edgecolors="white", lw=0.8)

    ax.set_ylabel(ylabel, fontsize=8)
    ax.tick_params(axis="both", labelsize=7)
    ax.grid(True, alpha=0.3, lw=0.5)

    # Small label box
    if not np.isnan(max_norm):
        ax.text(
            0.02, 0.93, f"max/mean = {max_norm:.2f}×",
            transform=ax.transAxes, fontsize=7,
            va="top", ha="left",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="lightgray", alpha=0.8),
        )


def make_event_figure(
    rec: EventRecord,
    thresholds_ssh: dict,
    thresholds_total: dict,
    tide_series: pd.Series,
    metrics_row: "pd.Series",
) -> None:
    """
    Generate and save the 3-panel tidal sensitivity figure for one event.

    Parameters
    ----------
    rec              : EventRecord from 02_preliminary_compound
    thresholds_ssh   : SSH-only threshold dict for this municipality
    thresholds_total : SSH_total threshold dict for this municipality
    tide_series      : Full tidal series (same index as SSH) for this grid point
    metrics_row      : One row from the combined metrics DataFrame
    """
    from src.tidal_sensitivity.tides import add_tide_to_ssh

    muni = rec.municipality
    date = rec.date

    thr_ssh   = thresholds_ssh.get(muni, {})
    thr_total = thresholds_total.get(muni, {})

    hs_q90        = thr_ssh.get("hs_q90", np.nan)
    ssh_q90       = thr_ssh.get("ssh_q90", np.nan)
    ssh_total_q90 = thr_total.get("ssh_total_q90", np.nan)

    # SSH_total window
    tide_win = tide_series.reindex(rec.ssh_window.index)
    ssh_total_win = add_tide_to_ssh(rec.ssh_window, tide_win)

    # Normalised maxima
    hs_max_norm    = float(metrics_row.get("hs_max_norm", np.nan))
    ssh_max_norm   = float(metrics_row.get("ssh_max_norm", np.nan))
    total_max_norm = float(metrics_row.get("ssh_total_max_norm", np.nan))

    detected_ssh   = bool(metrics_row.get("is_concurrent", False))
    detected_total = bool(metrics_row.get("is_concurrent_total", False))
    change_label   = str(metrics_row.get("detection_change", "neither"))

    change_color_map = {
        "new":        "#2ca02c",  # green — gained detection
        "lost":       "#d62728",  # red   — lost detection
        "maintained": "#1f77b4",  # blue  — consistent
        "neither":    "#7f7f7f",  # grey  — no detection in either
    }
    header_color = change_color_map.get(change_label, "#7f7f7f")

    apply_publication_style()
    fig, axes = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    fig.subplots_adjust(hspace=0.06, left=0.09, right=0.97, top=0.87, bottom=0.10)

    # ── Panel (a): Hₛ ──────────────────────────────────────────────────────────
    hs_max = float(rec.hs_window.max()) if not rec.hs_window.empty else np.nan
    _plot_panel(axes[0], rec.hs_window, hs_q90, date,
                STYLE.color_hs, "Hₛ (m)", hs_max, hs_max_norm, "")

    # ── Panel (b): SSH (zos only) ─────────────────────────────────────────────
    ssh_max = float(rec.ssh_window.max()) if not rec.ssh_window.empty else np.nan
    _plot_panel(axes[1], rec.ssh_window, ssh_q90, date,
                STYLE.color_ssh, "SSH (m)", ssh_max, ssh_max_norm, "")

    # ── Panel (c): SSH_total = SSH + tide ──────────────────────────────────────
    total_max = float(ssh_total_win.max()) if not ssh_total_win.empty else np.nan
    _plot_panel(axes[2], ssh_total_win, ssh_total_q90, date,
                "#7b2d8b",  # purple for SSH_total
                "SSH + tide (m)", total_max, total_max_norm, "")

    # Overlay hourly FES2022 tide curve on panel (c) — visual reference of tidal rhythm
    try:
        from src.tidal_sensitivity.tides import compute_hourly_tides_for_window
        win_start = rec.ssh_window.index[0]
        win_end   = rec.ssh_window.index[-1]
        tide_hourly = compute_hourly_tides_for_window(
            float(rec.grid_lat), float(rec.grid_lon), win_start, win_end
        )
        axes[2].plot(
            tide_hourly.index, tide_hourly.values,
            color="#2ca02c", lw=0.8, ls="--", alpha=0.6, zorder=2,
            label="Tide hourly (FES2022)",
        )
        axes[2].legend(loc="upper right", fontsize=7, framealpha=0.8)
    except Exception as exc:
        log.debug("Hourly tide overlay failed: %s", exc)
        # Fall back to daily tide if hourly computation fails
        if not tide_win.dropna().empty:
            axes[2].plot(tide_win.index, tide_win.values,
                         color="#2ca02c", lw=0.9, ls="--", alpha=0.7, zorder=2,
                         label="Tide daily (FES2022)")
            axes[2].legend(loc="upper right", fontsize=7, framealpha=0.8)

    _fmt_time_ax(axes[2], ssh_total_win.index)

    # ── Header title ──────────────────────────────────────────────────────────
    compound_str_ssh   = "✓ detected" if detected_ssh   else "✗ not detected"
    compound_str_total = "✓ detected" if detected_total else "✗ not detected"
    change_str = {
        "new": "NEW detection with tide",
        "lost": "detection LOST with tide",
        "maintained": "consistent detection",
        "neither": "not detected in either",
    }.get(change_label, change_label)

    title = (
        f"{muni}  ·  {date.strftime('%d %b %Y')}  ·  "
        f"SSH-only: {compound_str_ssh}  |  SSH+tide: {compound_str_total}  →  {change_str}"
    )
    fig.suptitle(title, fontsize=9, fontweight="bold",
                 color=header_color, y=0.96, x=0.5, ha="center")

    # ── Save ──────────────────────────────────────────────────────────────────
    slug = muni_slug(muni)
    fname = CFG["fig_events_dir"] / f"fig_TS_event_{rec.disaster_id:03d}_{slug}_{date.strftime('%Y%m%d')}.png"
    save_fig(fig, fname)


def run_event_figures(records, thresholds_ssh, thresholds_total, metrics_df, tide_cache):
    """Generate 3-panel tidal sensitivity figures for all events."""
    from src.tidal_sensitivity.tides import get_tide_for_record

    log.info("Generating %d tidal sensitivity event figures...", len(records))
    n_ok, n_skip = 0, 0

    for rec in records:
        row = metrics_df[metrics_df["event_idx"] == rec.event_idx]
        if row.empty:
            n_skip += 1
            continue
        tide = get_tide_for_record(rec, tide_cache)
        try:
            make_event_figure(rec, thresholds_ssh, thresholds_total, tide, row.iloc[0])
            n_ok += 1
        except Exception as exc:
            log.warning("Event figure failed for %s %s: %s", rec.municipality, rec.date, exc)
            n_skip += 1

    log.info("Event figures: %d saved, %d skipped.", n_ok, n_skip)
