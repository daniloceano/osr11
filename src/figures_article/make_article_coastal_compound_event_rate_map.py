r"""Generate the article map of annual native-grid compound-event frequency.

Suggested LaTeX figure block (requires ``\usepackage{graphicx}``)
-----------------------------------------------------------------
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.82\linewidth]{outputs/article_figures/coastal_compound_event_rate_per_year.png}
    \caption{Mean annual number of compound events detected at the native
    ocean-grid points along the Brazilian coast during 1993--2025. The total
    event count at each point was divided by the 33-year record length. For
    visualization, the Natural Earth
    10-m coastline was divided into segments no longer than 5~km, and each
    segment was assigned the count at its nearest native grid point using
    distances calculated in SIRGAS 2000 / Brazil Polyconic (EPSG:5880). Colors
    indicate discrete annual-frequency intervals (events~yr$^{-1}$), from
    light colors for lower rates to dark colors for higher rates. Gray shading
    denotes land,
    light blue denotes the ocean, dark-gray lines delimit countries, and
    lighter gray lines delimit Brazilian states.}
    \label{fig:coastal-compound-event-rate}
\end{figure}

Run from the repository root:

    python src/figures_article/make_article_coastal_compound_event_rate_map.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.figures_article.make_article_risk_figures import (
    make_coastal_compound_event_rate_map,
    read_coastline,
    read_ocean_hazard_data,
    read_risk_data,
    validate_article_figure_outputs,
)


def main() -> None:
    municipalities, _ = read_risk_data()
    ocean_grid, ocean_metadata = read_ocean_hazard_data()
    outputs = make_coastal_compound_event_rate_map(
        municipalities,
        ocean_grid,
        read_coastline(),
        ocean_metadata,
    )
    validate_article_figure_outputs()
    print("\n".join(outputs))


if __name__ == "__main__":
    main()
