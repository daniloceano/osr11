r"""Generate only the PU threshold-calibration heatmap panel.

Suggested LaTeX figure block (requires ``\usepackage{graphicx}``)
-----------------------------------------------------------------
\begin{figure}[htbp]
    \centering
    \includegraphics[width=\linewidth]{outputs/article_figures/pu_composite_calibration_heatmaps.png}
    \caption{Positive-unlabeled (PU) threshold calibration across the tested
    combinations of significant wave height ($H_s$) and tide-free sea-level
    anomaly ($\mathrm{zos}$) quantiles. Panels show
    (a) positive recall ($R_{\mathrm{pos}}$), (b) detection burden ($B$),
    (c) the soft false-positive penalty ($F_{\mathrm{soft}}/P$), and
    (d) the composite score. Colors represent relative performance within each
    panel: higher values are preferred for $R_{\mathrm{pos}}$ and the composite
    score, whereas lower values are preferred for $B$ and
    $F_{\mathrm{soft}}/P$. Cell annotations report the corresponding metric
    values, and the cyan outline identifies the selected $q_{70}/q_{99}$
    threshold pair.}
    \label{fig:pu-threshold-calibration}
\end{figure}
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, Normalize
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd

from config.plot_config import apply_publication_style
from src.figures_article.calibration_common import load_optimal_pair, load_score_frame
from src.figures_article.figure_io import _save_figure, validate_article_figure_outputs

QUALITY_COLORS_WORSE_TO_BETTER = (
    "#FDF5D0", "#FCEAA1", "#F8E070", "#F4B354", "#EC8439", "#E05020",
    "#C84232", "#AF3540", "#96274B", "#7C1B55", "#600F5F", "#3E0668",
)
MAXIMIZE_CMAP = ListedColormap(QUALITY_COLORS_WORSE_TO_BETTER, name="quality_worse_to_better")
MINIMIZE_CMAP = ListedColormap(tuple(reversed(QUALITY_COLORS_WORSE_TO_BETTER)), name="quality_better_to_worse")
SCORE_COLORS = (
    "#008000", "#33B200", "#80D900", "#CCE600", "#FFE600", "#FFB200",
    "#FF8000", "#FF4000", "#FF0000", "#CC0033", "#99004C", "#660066",
)
SCORE_CMAP = ListedColormap(tuple(reversed(SCORE_COLORS)), name="score_requested_reversed")


def _heatmap_panel(
    ax,
    data,
    metric,
    title,
    *,
    higher_is_better,
    fmt,
    panel,
    show_xlabel,
    show_ylabel,
    selected_pair,
    cmap_override=None,
):
    matrix = data.pivot(index="hs_percentile", columns="ssh_percentile", values=metric).sort_index()
    matrix = matrix.reindex(sorted(matrix.columns), axis=1)
    values = matrix.to_numpy(dtype=float)
    norm = Normalize(vmin=float(np.nanmin(values)), vmax=float(np.nanmax(values)))
    cmap = cmap_override or (MAXIMIZE_CMAP if higher_is_better else MINIMIZE_CMAP)
    image = ax.imshow(values, cmap=cmap, norm=norm, aspect="equal", origin="upper")
    ax.set_xticks(range(len(matrix.columns)), [f"q{int(v)}" for v in matrix.columns], rotation=45, ha="right")
    ax.set_yticks(range(len(matrix.index)), [f"q{int(v)}" for v in matrix.index])
    ax.set_xlabel(r"zos quantile" if show_xlabel else "")
    ax.set_ylabel(r"H$_s$ quantile" if show_ylabel else "")
    ax.set_title(title, fontweight="bold", pad=7)
    ax.grid(False)
    ax.text(-0.13, 1.06, f"({panel})", transform=ax.transAxes, fontweight="bold", fontsize=11)
    for row in range(values.shape[0]):
        for col in range(values.shape[1]):
            value = values[row, col]
            rgba = cmap(norm(value))
            luminance = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
            ax.text(col, row, format(value, fmt), ha="center", va="center", fontsize=8,
                    color="black" if luminance > 0.55 else "white")
    selected_hs, selected_zos = selected_pair
    if selected_hs in matrix.index and selected_zos in matrix.columns:
        row = list(matrix.index).index(selected_hs)
        col = list(matrix.columns).index(selected_zos)
        ax.add_patch(Rectangle((col - 0.5, row - 0.5), 1, 1, fill=False,
                               edgecolor="#00E5FF", linewidth=2.0))
    colorbar = ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.025)
    # colorbar.set_label("higher is better" if higher_is_better else "lower is better", fontsize=7)
    colorbar.ax.tick_params(labelsize=8)


def generate_calibration_heatmaps(data: pd.DataFrame | None = None) -> list[str]:
    apply_publication_style()
    data = load_score_frame() if data is None else data
    selected_pair = load_optimal_pair()
    fig, axes = plt.subplots(2, 2, figsize=(9.0, 9.0), constrained_layout=True)
    fig.get_layout_engine().set(w_pad=0.02, h_pad=0.02, wspace=0.015, hspace=0.015)
    panels = (
        ("R_pos", r"Positive recall, $R_{pos}$", True, ".2f", "a", None),
        ("B", r"Detection burden, $B$", False, ".2f", "b", None),
        ("term_fsoft_raw", r"Soft penalty, $F_{soft}/P$", False, ".1f", "c", None),
        ("Score", "Composite score, $S$", True, ".2f", "d", SCORE_CMAP),
    )
    for index, (ax, args) in enumerate(zip(axes.flat, panels)):
        metric, title, higher, fmt, panel, cmap = args
        _heatmap_panel(ax, data, metric, title, higher_is_better=higher, fmt=fmt,
                       panel=panel, show_xlabel=index >= 2,
                       show_ylabel=index % 2 == 0, selected_pair=selected_pair,
                       cmap_override=cmap)
    return _save_figure(fig, "pu_composite_calibration_heatmaps")


def main() -> None:
    for path in generate_calibration_heatmaps():
        print(path)
    validate_article_figure_outputs()


if __name__ == "__main__":
    main()
