"""
Central figure style configuration for the OSR11 project.

Designed for publication-quality scientific figures with a clean, minimal
aesthetic inspired by high-impact journals (Scientific Reports reference style),
adapted for digital output (PNG/SVG; no PDF generation).

Usage
-----
Apply the global style at the top of any script that produces figures::

    from .config.plot_config import apply_publication_style, STYLE
    apply_publication_style()

To override specific parameters for a single script without affecting the
global default, construct a modified FigureStyle and pass it explicitly::

    from dataclasses import replace
    apply_publication_style(replace(STYLE, dpi_export=600))

To add a panel label (a), (b), ... to an Axes::

    from .config.plot_config import panel_label
    panel_label(ax, "a")

Design principles
-----------------
- White background, no chart junk.
- Consistent sans-serif typography across all figures.
- Two canonical colours for the main physical variables (Hs and SSH).
- Sector colours defined once; imported wherever needed.
- All size values in inches (matplotlib convention).
- Primary export format is PNG at 300 dpi; SVG optional for vector output.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

if TYPE_CHECKING:
    import matplotlib.axes


# ── Sector colour palette ─────────────────────────────────────────────────────

SECTOR_COLORS: dict[str, str] = {
    "North":          "#1f77b4",
    "Central-north":  "#ff7f0e",
    "Central":        "#2ca02c",
    "Central-south":  "#d62728",
    "South":          "#9467bd",
}


# ── Style dataclass ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class FigureStyle:
    """Immutable, composable style parameters for publication-quality figures.

    All fields have sensible defaults aligned with the OSR11 visual standard.
    Use ``dataclasses.replace(STYLE, field=value)`` to derive a variant.
    """

    # ── Figure dimensions (inches) ────────────────────────────────────────────
    fig_width_single:  float = 6.5    # single-column or portrait
    fig_width_double:  float = 10.0   # two-panel landscape
    fig_width_wide:    float = 13.0   # multi-panel wide layout
    fig_height_default: float = 5.0

    # ── Export ────────────────────────────────────────────────────────────────
    dpi_screen: int = 150    # interactive / notebook rendering
    dpi_export: int = 300    # saved PNG/SVG
    export_format: str = "png"

    # ── Typography ────────────────────────────────────────────────────────────
    font_family:          str   = "sans-serif"
    font_size_base:       float = 10.0
    font_size_axis_label: float = 11.0
    font_size_tick:       float = 9.0
    font_size_title:      float = 11.0
    font_size_legend:     float = 8.5
    font_size_annotation: float = 7.5
    font_size_panel_label: float = 11.0  # (a), (b), (c) labels

    # ── Lines ─────────────────────────────────────────────────────────────────
    linewidth_default: float = 1.5
    linewidth_thin:    float = 0.8
    linewidth_thick:   float = 2.0

    # ── Grid ──────────────────────────────────────────────────────────────────
    grid_alpha:     float = 0.3
    grid_linestyle: str   = "--"
    grid_linewidth: float = 0.5

    # ── Scientific variable colours ───────────────────────────────────────────
    color_hs:              str = "#d62728"    # significant wave height (warm red)
    color_ssh:             str = "steelblue"  # sea surface height (blue)
    color_contour:         str = "steelblue"  # SSH contour lines on maps
    color_boxplot_default: str = "#4C72B0"    # default boxplot fill
    color_highlight:       str = "crimson"    # compound event highlights
    color_reference_span:  str = "gold"       # temporal window shading

    # ── Colormaps ─────────────────────────────────────────────────────────────

    crameri_tofino = ['#DBD7FE', '#98A8E1', '#5777BA', '#19253D', '#0E1615', '#374030', '#899365', '#D9E49A']
    eccharts_wave_height_10 = ['#E6F7FF', '#A6DEF7', '#4CBFE6', '#0099D1', '#007AB8', '#1AA64C', '#8CCC00', '#E6CC00', '#FF8000', '#D90000']

    colors_hs = LinearSegmentedColormap.from_list('crameri-tofino', crameri_tofino)
    colors_ssh = LinearSegmentedColormap.from_list('eccharts-wave-height-10', eccharts_wave_height_10)

    cmap_hs: str = "crameri-tofino"  # colormap for Hs spatial fields
    cmap_ssh: str = "eccharts-wave-height-10"  # colormap for SSH spatial fields
    cmap_sequential: str = "viridis"  # generic sequential (scatter colour by year)

    # ── Layout ────────────────────────────────────────────────────────────────
    legend_framealpha:  float = 0.85
    axes_spines_top:    bool  = False
    axes_spines_right:  bool  = False

    # ── Panel labels ──────────────────────────────────────────────────────────
    panel_label_prefix:     str = "("
    panel_label_suffix:     str = ")"
    panel_label_fontweight: str = "bold"


# ── Global default instance ───────────────────────────────────────────────────

STYLE = FigureStyle()

# ── Register custom colormaps ─────────────────────────────────────────────────

# Register custom colormaps with matplotlib so they can be referenced by string name
try:
    plt.colormaps.register(STYLE.colors_hs)
    plt.colormaps.register(STYLE.colors_ssh)
except (ValueError, AttributeError):
    # Already registered or using older matplotlib version
    pass


# ── Public API ────────────────────────────────────────────────────────────────

def apply_publication_style(style: FigureStyle | None = None) -> None:
    """Apply matplotlib rcParams for publication-quality figures.

    Parameters
    ----------
    style:
        FigureStyle instance. If None, uses the module-level ``STYLE`` default.
        Pass a customised instance to override specific parameters without
        altering the global default.
    """
    s = style or STYLE
    plt.rcParams.update({
        "figure.dpi":        s.dpi_screen,
        "savefig.dpi":       s.dpi_export,
        "font.family":       s.font_family,
        "font.size":         s.font_size_base,
        "axes.labelsize":    s.font_size_axis_label,
        "axes.titlesize":    s.font_size_title,
        "xtick.labelsize":   s.font_size_tick,
        "ytick.labelsize":   s.font_size_tick,
        "legend.fontsize":   s.font_size_legend,
        "legend.framealpha": s.legend_framealpha,
        "figure.facecolor":  "white",
        "axes.facecolor":    "white",
        "axes.grid":         True,
        "grid.alpha":        s.grid_alpha,
        "grid.linestyle":    s.grid_linestyle,
        "grid.linewidth":    s.grid_linewidth,
        "axes.spines.top":   s.axes_spines_top,
        "axes.spines.right": s.axes_spines_right,
        "lines.linewidth":   s.linewidth_default,
        "savefig.bbox":      "tight",
        "savefig.format":    s.export_format,
    })


def panel_label(
    ax: matplotlib.axes.Axes,
    label: str,
    style: FigureStyle | None = None,
) -> None:
    """Add a panel label — e.g. (a), (b) — to the upper-left corner of an Axes.

    Parameters
    ----------
    ax:    Target matplotlib Axes.
    label: Label character, e.g. ``"a"``, ``"b"``.
    style: FigureStyle instance (defaults to module-level ``STYLE``).
    """
    s = style or STYLE
    text = f"{s.panel_label_prefix}{label}{s.panel_label_suffix}"
    ax.text(
        0.01, 0.98, text,
        transform=ax.transAxes,
        fontsize=s.font_size_panel_label,
        fontweight=s.panel_label_fontweight,
        va="top", ha="left",
    )
