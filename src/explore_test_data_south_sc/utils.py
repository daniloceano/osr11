"""Shared plotting and I/O utilities for the south SC exploratory analysis."""
from __future__ import annotations

import logging

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from src.explore_test_data_south_sc.config.analysis_config import CFG
from config.plot_config import STYLE

log = logging.getLogger(__name__)


def make_output_dirs() -> None:
    """Create all output directories defined in CFG."""
    for key in ("fig_dir", "tab_dir", "log_dir", "meta_dir"):
        CFG[key].mkdir(parents=True, exist_ok=True)
    log.info("Output directories ready: %s", CFG["output_root"])


def save_fig(fig: plt.Figure, name: str) -> None:
    """Save figure to the figures output directory as PNG."""
    path = CFG["fig_dir"] / f"{name}.png"
    fig.savefig(path, dpi=STYLE.dpi_export, bbox_inches="tight")
    log.info("  -> Figure: %s", path.name)
    plt.close(fig)


def peaks_coincident(t1: pd.Timestamp, t2: pd.Timestamp, window_days: int) -> bool:
    """Return True if two timestamps are within *window_days* of each other."""
    return abs((t1 - t2).total_seconds()) <= window_days * 86_400


def fmt_time_ax(ax: plt.Axes, *, minor: bool = True) -> None:
    """Apply clean date formatting to a time axis (day-level precision)."""
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    if minor:
        ax.xaxis.set_minor_locator(mdates.DayLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")


def vline(
    ax: plt.Axes,
    t: pd.Timestamp,
    color: str,
    label: str | None = None,
) -> None:
    """Draw a vertical dashed line at time *t*."""
    ax.axvline(t, color=color, lw=1.3, ls="--", alpha=0.85, label=label, zorder=4)


def span(ax: plt.Axes, t_center: pd.Timestamp, window_days: int) -> None:
    """Shade the symmetric temporal window around *t_center*."""
    t0 = t_center - pd.Timedelta(days=window_days // 2)
    t1 = t_center + pd.Timedelta(days=window_days // 2)
    ax.axvspan(t0, t1, color=STYLE.color_reference_span, alpha=0.12, zorder=0)
