"""
Per-event figures for threshold calibration.

Produces one figure per reported event with two panels (Hs top, SSH bottom),
each showing:
  - The 7-day time series in the event window
  - The q90 threshold as a horizontal dashed line
  - Exceedance periods highlighted as a coloured fill (MagicA POT, event_wise)
  - Reported event date marked with a vertical line
  - Maximum value in the window marked with a circular marker
  - A text box with key metrics (max values, thresholds, concomitance)

MagicA usage
------------
Uses magica.read_data(series).get_extremes_analyzer().peaks_over_threshold(
    threshold=q90, event_wise=True
) to identify distinct exceedance events. The contiguous exceedance periods
are then reconstructed from the raw series for shading.

Figure naming
-------------
fig_TC_event_{disaster_id:03d}_{municipality_slug}_{date:%Y%m%d}.png
"""
from __future__ import annotations

import logging
from typing import Optional

import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import magica as ma

from src.threshold_calibration.config.analysis_config import CFG
from src.threshold_calibration.events import EventRecord
from src.threshold_calibration.utils import save_fig, muni_slug
from config.plot_config import STYLE, apply_publication_style, panel_label

log = logging.getLogger(__name__)

# Colour for exceedance shading
_COLOR_EXCEED_HS  = "#d62728"   # same as STYLE.color_hs
_COLOR_EXCEED_SSH = "steelblue" # same as STYLE.color_ssh
_EXCEED_ALPHA     = 0.20
_THRESHOLD_LS     = "--"
_THRESHOLD_LW     = 1.2
_THRESHOLD_ALPHA  = 0.80
_EVENT_LINE_COLOR = "black"


def run_event_figures(
    records: list[EventRecord],
    thresholds: dict[str, dict[str, float]],
    metrics_df: pd.DataFrame,
) -> None:
    """Generate one figure per event record.

    Parameters
    ----------
    records : list of EventRecord
    thresholds : dict
        Output of thresholds.compute_thresholds().
    metrics_df : pd.DataFrame
        Output of thresholds.compute_event_metrics().
    """
    log.info("== Part TC-1: Per-event figures ==")
    apply_publication_style()

    q = CFG["threshold_quantile"]

    for rec in records:
        muni = rec.municipality
        if muni not in thresholds:
            log.warning("  No threshold for '%s', skipping figure.", muni)
            continue

        th = thresholds[muni]
        hs_thr  = th["hs_q90"]
        ssh_thr = th["ssh_q90"]

        # Metrics row for this event
        m_row = metrics_df[
            (metrics_df["disaster_id"] == rec.disaster_id) &
            (metrics_df["municipality"] == muni)
        ]
        is_concurrent = bool(m_row["is_concurrent"].values[0]) if len(m_row) else False
        n_concurrent  = int(m_row["n_concurrent"].values[0])   if len(m_row) else 0
        hs_max_norm   = float(m_row["hs_max_norm"].values[0])  if len(m_row) else np.nan
        ssh_max_norm  = float(m_row["ssh_max_norm"].values[0]) if len(m_row) else np.nan

        # ── Build figure ──────────────────────────────────────────────────────
        fig, axes = plt.subplots(
            2, 1,
            figsize=(STYLE.fig_width_double, STYLE.fig_height_default * 1.2),
            sharex=True,
        )
        ax_hs, ax_ssh = axes

        # ── Panel (a): Hs ─────────────────────────────────────────────────────
        _plot_panel(
            ax        = ax_hs,
            series    = rec.hs_window,
            threshold = hs_thr,
            event_date= rec.date,
            color     = _COLOR_EXCEED_HS,
            ylabel    = "Hₛ (m)",
            threshold_label = f"q{int(q*100)} = {hs_thr:.2f} m",
            variable  = "Hs",
        )
        panel_label(ax_hs, "a")

        # ── Panel (b): SSH ────────────────────────────────────────────────────
        _plot_panel(
            ax        = ax_ssh,
            series    = rec.ssh_window,
            threshold = ssh_thr,
            event_date= rec.date,
            color     = _COLOR_EXCEED_SSH,
            ylabel    = "SSH (m)",
            threshold_label = f"q{int(q*100)} = {ssh_thr:.3f} m",
            variable  = "SSH",
        )
        panel_label(ax_ssh, "b")
        _fmt_time_ax(ax_ssh)

        # ── Title and suptitle ────────────────────────────────────────────────
        date_str = rec.date.strftime("%d %b %Y")
        win_str  = (
            f"{rec.window_start.strftime('%d %b')}–"
            f"{rec.window_end.strftime('%d %b %Y')}"
        )
        fig.suptitle(
            f"{muni}  ·  Event {rec.disaster_id}  ·  Reported: {date_str}",
            fontsize=STYLE.font_size_title + 1,
            fontweight="bold",
            y=1.01,
        )

        # ── Concomitance annotation ───────────────────────────────────────────
        _add_metrics_box(
            fig, ax_ssh,
            hs_max_norm   = hs_max_norm,
            ssh_max_norm  = ssh_max_norm,
            n_concurrent  = n_concurrent,
            is_concurrent = is_concurrent,
            window_len    = len(rec.hs_window),
            q             = q,
        )

        # ── Shared x-label ───────────────────────────────────────────────────
        ax_ssh.set_xlabel(f"Date  ({win_str})", fontsize=STYLE.font_size_axis_label)

        fig.tight_layout()

        # ── Save ──────────────────────────────────────────────────────────────
        slug  = muni_slug(muni)
        fname = f"fig_TC_event_{rec.disaster_id:03d}_{slug}_{rec.date:%Y%m%d}"
        save_fig(fig, fname, subdir="events")

    log.info("Per-event figures complete.")


# ── Private helpers ────────────────────────────────────────────────────────────

def _plot_panel(
    ax: plt.Axes,
    series: pd.Series,
    threshold: float,
    event_date: pd.Timestamp,
    color: str,
    ylabel: str,
    threshold_label: str,
    variable: str,
) -> None:
    """Draw a single time-series panel with threshold, exceedances, event mark."""
    times = series.index
    vals  = series.values

    # ── Exceedance shading (contiguous periods above threshold) ───────────────
    _shade_exceedances(ax, series, threshold, color)

    # ── MagicA POT: mark event-wise peaks ────────────────────────────────────
    _mark_pot_peaks(ax, series, threshold, color)

    # ── Time series line ──────────────────────────────────────────────────────
    ax.plot(times, vals, color=color, lw=STYLE.linewidth_default, zorder=3)

    # ── Threshold line ────────────────────────────────────────────────────────
    ax.axhline(
        threshold,
        color=color,
        lw=_THRESHOLD_LW,
        ls=_THRESHOLD_LS,
        alpha=_THRESHOLD_ALPHA,
        label=threshold_label,
        zorder=2,
    )

    # ── Reported event date ───────────────────────────────────────────────────
    ax.axvline(
        event_date,
        color=_EVENT_LINE_COLOR,
        lw=1.4,
        ls="-",
        alpha=0.75,
        label="Reported date",
        zorder=5,
    )

    # ── Maximum value marker ──────────────────────────────────────────────────
    finite = series.dropna()
    if len(finite) > 0:
        t_max = finite.idxmax()
        v_max = finite.max()
        ax.scatter(
            [t_max], [v_max],
            color=color, s=55, zorder=6,
            edgecolors="white", linewidths=0.8,
            label=f"Max {variable} = {v_max:.2f}",
        )

    # ── Formatting ────────────────────────────────────────────────────────────
    ax.set_ylabel(ylabel, fontsize=STYLE.font_size_axis_label)
    ax.grid(axis="y", alpha=STYLE.grid_alpha, lw=STYLE.linewidth_thin)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(
        handles, labels,
        fontsize=STYLE.font_size_legend,
        framealpha=STYLE.legend_framealpha,
        loc="upper left",
    )


def _shade_exceedances(
    ax: plt.Axes,
    series: pd.Series,
    threshold: float,
    color: str,
) -> None:
    """Fill contiguous exceedance periods with semi-transparent colour."""
    above = series > threshold
    if not above.any():
        return

    # Group consecutive True blocks
    in_block = False
    t_start  = None
    for t, flag in above.items():
        if flag and not in_block:
            t_start  = t
            in_block = True
        elif not flag and in_block:
            ax.axvspan(t_start, t, color=color, alpha=_EXCEED_ALPHA, zorder=1)
            in_block = False
    if in_block and t_start is not None:
        ax.axvspan(t_start, series.index[-1], color=color, alpha=_EXCEED_ALPHA, zorder=1)


def _mark_pot_peaks(
    ax: plt.Axes,
    series: pd.Series,
    threshold: float,
    color: str,
) -> None:
    """Use MagicA to identify event-wise POT peaks and mark them."""
    finite = series.dropna()
    if len(finite) < 2:
        return

    try:
        processor = ma.read_data(finite)
        ea        = processor.get_extremes_analyzer()
        peaks, peak_times = ea.peaks_over_threshold(
            threshold    = threshold,
            event_wise   = True,
        )
        if len(peaks) == 0:
            return
        ax.scatter(
            peak_times, peaks,
            color="none", s=90, zorder=7,
            edgecolors=color, linewidths=1.8,
            marker="o",
        )
    except Exception as exc:
        # MagicA issues should not crash the entire figure generation;
        # they are reported here and the panel is still saved without POT markers.
        log.error(
            "  MagicA POT failed for series ('%s'): %s — panel saved without POT markers.",
            series.name, exc,
        )


def _add_metrics_box(
    fig: plt.Figure,
    ax: plt.Axes,
    hs_max_norm: float,
    ssh_max_norm: float,
    n_concurrent: int,
    is_concurrent: bool,
    window_len: int,
    q: float,
) -> None:
    """Add a small text box with normalised metrics and concomitance info."""
    q_label = f"q{int(q*100)}"
    concurrent_label = "YES" if is_concurrent else "NO"
    concurrent_frac  = n_concurrent / window_len if window_len > 0 else 0.0

    text = (
        f"Hₛ_max / Hₛ_mean = {hs_max_norm:.2f}\n"
        f"SSH_max / SSH_mean = {ssh_max_norm:.2f}\n"
        f"Concurrent ({q_label}): {concurrent_label} ({n_concurrent}/{window_len} d, "
        f"{concurrent_frac:.0%})"
    )
    ax.text(
        0.99, 0.04, text,
        transform=ax.transAxes,
        fontsize=STYLE.font_size_legend,
        verticalalignment="bottom",
        horizontalalignment="right",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                  edgecolor="0.7", alpha=0.85),
        zorder=10,
    )


def _fmt_time_ax(ax: plt.Axes) -> None:
    """Apply clean date formatting to the shared x-axis (day precision)."""
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    # Use AutoDateLocator to avoid generating too many ticks
    # For a 7-day window, this will intelligently pick appropriate intervals
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3, maxticks=8))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")
