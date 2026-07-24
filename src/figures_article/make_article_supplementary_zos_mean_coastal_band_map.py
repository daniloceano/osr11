r"""Generate the supplementary temporal-mean GLORYS ``zos`` map.

Suggested LaTeX figure block (requires ``\usepackage{graphicx}``)
-----------------------------------------------------------------
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.72\linewidth]{outputs/article_figures/supplementary_temporal_mean_zos_within_200km_coast.png}
    \caption{Temporal mean dynamic sea level from GLORYS (variable
    $\mathrm{zos}$) during 1993--2025, restricted to valid ocean grid cells
    within 200~km of the Natural Earth 10-m coastline. Colors show the mean
    $\mathrm{zos}$ in metres using six discrete intervals, with the upper
    extension representing values greater than 0.30~m. The dashed blue line
    marks the outer boundary of the 200-km coastal band, solid blue lines show
    the principal rivers, and black lines show the coastline. Dark-gray lines
    delineate international borders, lighter gray lines delineate first-order
    administrative divisions (states or provinces), and gray shading denotes
    land. Tides and total sea surface height
    ($\mathrm{SSH}_{\mathrm{total}}$) are not included.}
    \label{fig:supplementary-mean-zos-coastal-band}
\end{figure}

Run from the repository root:

    python src/figures_article/make_article_supplementary_zos_mean_coastal_band_map.py

The plotting and distance-mask implementation remains shared with the
exploratory generator so that both versions use identical scientific methods.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.exploratory.make_exploratory_zos_mean_coastal_band_map import main


if __name__ == "__main__":
    main(article_supplement=True)
