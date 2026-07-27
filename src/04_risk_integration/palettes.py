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
    """Return the green-to-red palette truncated to ``class_count`` classes."""
    if not 1 <= class_count <= len(RISK_COLORS):
        raise ValueError(
            f"class_count must be between 1 and {len(RISK_COLORS)}"
        )
    return list(RISK_COLORS[:class_count])
