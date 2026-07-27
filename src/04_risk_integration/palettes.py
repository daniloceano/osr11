"""Shared discrete palettes for the coastal hazard and risk products.

Keeping the class colors in one place guarantees that the article figures, the
exploratory audits, and the website legends are visually identical.
"""

from __future__ import annotations

import matplotlib
import numpy as np


#: Green-to-red palette of the integrated Risk Index; also used by the final
#: Hazard Index so both composite indices read on the same visual scale.
RISK_COLORS: tuple[str, ...] = (
    "#008000",
    "#33B200",
    "#80D900",
    "#CCE600",
    "#FFB200",
    "#FF8000",
    "#FF4000",
    "#FF0000",
)

#: Endpoints used to sample matplotlib's magma colormap for the physical
#: hazard components (reversed, so darker means more severe).
COMPONENT_COLORMAP = "magma"
COMPONENT_SAMPLE_RANGE = (0.95, 0.12)


def component_colors(class_count: int) -> list[str]:
    """Return ``class_count`` hex colors of the discrete component palette."""
    if class_count < 1:
        raise ValueError("class_count must be positive")
    colormap = matplotlib.colormaps[COMPONENT_COLORMAP]
    samples = np.linspace(*COMPONENT_SAMPLE_RANGE, class_count)
    return [matplotlib.colors.to_hex(colormap(value)) for value in samples]


def risk_colors(class_count: int = len(RISK_COLORS)) -> list[str]:
    """Return ``class_count`` colors spanning the full green-to-red palette.

    Fewer classes than the reference palette are sampled evenly rather than
    truncated, so the scale always runs from green to red.
    """
    if not 1 <= class_count <= len(RISK_COLORS):
        raise ValueError(
            f"class_count must be between 1 and {len(RISK_COLORS)}"
        )
    if class_count == len(RISK_COLORS):
        return list(RISK_COLORS)
    if class_count == 1:
        return [RISK_COLORS[-1]]
    positions = np.linspace(0, len(RISK_COLORS) - 1, class_count)
    return [RISK_COLORS[int(round(position))] for position in positions]


#: Colormap used for signed quantities (trend slopes, peak lags), sampled so
#: that cool colors are negative and warm colors are positive.
DIVERGING_COLORMAP = "RdBu_r"

#: Cyclic month palette: DJF red, MAM yellow, JJA blue, SON green, closing on
#: red in December so the scale wraps continuously.
MONTH_COLORS: tuple[str, ...] = (
    "#d73027",
    "#fc8d59",
    "#fec44f",
    "#fee090",
    "#d9ef8b",
    "#91bfdb",
    "#4575b4",
    "#313695",
    "#1a9850",
    "#66bd63",
    "#a6d96a",
    "#a50026",
)


def diverging_colors(class_count: int) -> list[str]:
    """Return ``class_count`` hex colors of the discrete diverging palette."""
    if class_count < 2:
        raise ValueError("class_count must be at least 2")
    colormap = matplotlib.colormaps[DIVERGING_COLORMAP]
    samples = np.linspace(0.06, 0.94, class_count)
    return [matplotlib.colors.to_hex(colormap(value)) for value in samples]


def palette_catalog(class_count: int = 8) -> dict[str, list[str]]:
    """Bundle the discrete palettes shared with the website legends."""
    return {
        "sequential": component_colors(class_count),
        "diverging": diverging_colors(class_count),
        "risk": risk_colors(min(class_count, len(RISK_COLORS))),
        "month": list(MONTH_COLORS),
    }
