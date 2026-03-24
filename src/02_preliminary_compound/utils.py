"""Shared plotting and I/O utilities for the threshold calibration analysis."""
from __future__ import annotations

import logging
import re
import unicodedata

import matplotlib.pyplot as plt

from src.preliminary_compound.config.analysis_config import CFG
from config.plot_config import STYLE

log = logging.getLogger(__name__)


def make_output_dirs() -> None:
    """Create all output directories defined in CFG."""
    for key in ("fig_dir", "fig_events_dir", "fig_summary_dir", "tab_dir", "log_dir"):
        CFG[key].mkdir(parents=True, exist_ok=True)
    log.info("Output directories ready: %s", CFG["output_root"])


def save_fig(fig: plt.Figure, name: str, subdir: str = "figures") -> None:
    """Save figure to the specified output subdirectory as PNG.

    Parameters
    ----------
    fig : matplotlib Figure
    name : str
        Filename without extension.
    subdir : str
        One of 'figures' (main), 'events', 'summary'. Controls the output path.
    """
    if subdir == "events":
        path = CFG["fig_events_dir"] / f"{name}.png"
    elif subdir == "summary":
        path = CFG["fig_summary_dir"] / f"{name}.png"
    else:
        path = CFG["fig_dir"] / f"{name}.png"

    fig.savefig(path, dpi=STYLE.dpi_export, bbox_inches="tight")
    log.info("  -> Figure: %s", path)
    plt.close(fig)


def muni_slug(name: str) -> str:
    """Convert a municipality name to a safe ASCII filename slug.

    Strips accents via Unicode NFKD decomposition before removing non-alphanumeric
    characters, so accented letters map to their ASCII base form.

    Examples
    --------
    'Içara/Balneário Rincão' -> 'icara_balneario_rincao'
    'Araranguá'              -> 'ararangua'
    """
    # Decompose accented characters and drop the combining marks
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9]+", "_", ascii_str).strip("_").lower()
