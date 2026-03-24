"""
Utility functions for the tidal sensitivity analysis.
"""
from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt

from src.preliminary_compound.utils import muni_slug  # noqa: F401
from config.plot_config import STYLE
from src.tidal_sensitivity.config.analysis_config import CFG

log = logging.getLogger(__name__)


def save_fig(fig: plt.Figure, path: Path | str) -> None:
    """Save figure to *path* (full path including extension) at publication DPI."""
    path = Path(path)
    fig.savefig(path, dpi=STYLE.dpi_export, bbox_inches="tight")
    plt.close(fig)
    log.info("  -> Figure: %s", path)


def make_output_dirs() -> None:
    """Create all output directories required by this analysis."""
    for key in (
        "output_root", "fig_dir", "fig_events_dir",
        "fig_summary_dir", "fig_comparison_dir",
        "tab_dir", "log_dir",
    ):
        CFG[key].mkdir(parents=True, exist_ok=True)
