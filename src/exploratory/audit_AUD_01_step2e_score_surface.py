"""Score surface of the recalibrated Step 2e sweep, with its sample support.

The 2026-07-30 recalibration scores the production detector (Hs and tide-free
zos percentiles, gated by ``max(SWL) > HAT``) over an extended 11x11 percentile
grid. The selected optimum landed at q99/q99. This diagnostic exists to make
visible WHY that is not a usable answer, and it does so by putting the two
things side by side that the score itself never shows:

  * the four terms of the composite score, panel by panel, as in the article
    figure ``pu_composite_calibration_heatmaps.png``;
  * the number of compound episodes the detector actually accepted at each
    pair, which is the sample the score was computed on.

Read-only. Nothing here selects a pair, changes the score, or writes into the
calibration outputs.

Usage:
    conda run -n osr11 python -m src.exploratory.audit_AUD_01_step2e_score_surface

Outputs:
    outputs/audit/AUD-01_step2e_score_surface/score_surface.csv
    outputs/audit/AUD-01_step2e_score_surface/summary.json
    outputs/audit/AUD-01_step2e_score_surface/figures/step2e_score_surface.png
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, LogNorm, Normalize
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd

TAB_DIR = ROOT / "outputs" / "threshold_calibration" / "tables"
SCORES = TAB_DIR / "tab_TC5_pu_metrics_full.csv"
CENSUS = TAB_DIR / "tab_TC5_detection_census.csv"
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-01_step2e_score_surface"

#: Same palette as the article calibration figure, so the two read together.
QUALITY_WORSE_TO_BETTER = (
    "#FDF5D0", "#FCEAA1", "#F8E070", "#F4B354", "#EC8439", "#E05020",
    "#C84232", "#AF3540", "#96274B", "#7C1B55", "#600F5F", "#3E0668",
)
MAXIMIZE_CMAP = ListedColormap(QUALITY_WORSE_TO_BETTER)
MINIMIZE_CMAP = ListedColormap(tuple(reversed(QUALITY_WORSE_TO_BETTER)))
SCORE_COLORS = (
    "#008000", "#33B200", "#80D900", "#CCE600", "#FFE600", "#FFB200",
    "#FF8000", "#FF4000", "#FF0000", "#CC0033", "#99004C", "#660066",
)
SCORE_CMAP = ListedColormap(tuple(reversed(SCORE_COLORS)))

#: The pair the superseded calibration selected, marked for reference.
INCUMBENT = (90, 90)


def _panel(
    ax, frame, metric, title, *, higher_is_better, fmt, panel_letter,
    show_xlabel, show_ylabel, cmap_override=None, log_scale=False,
    hatch_degenerate=True,
):
    matrix = frame.pivot(
        index="hs_percentile", columns="ssh_percentile", values=metric
    ).sort_index()
    matrix = matrix.reindex(sorted(matrix.columns), axis=1)
    values = matrix.to_numpy(dtype=float)
    finite = values[np.isfinite(values)]
    if log_scale and finite.min() > 0:
        norm = LogNorm(vmin=float(finite.min()), vmax=float(finite.max()))
    else:
        norm = Normalize(vmin=float(finite.min()), vmax=float(finite.max()))
    cmap = cmap_override or (MAXIMIZE_CMAP if higher_is_better else MINIMIZE_CMAP)
    image = ax.imshow(values, cmap=cmap, norm=norm, aspect="equal", origin="upper")

    ax.set_xticks(
        range(len(matrix.columns)),
        [f"q{int(v)}" for v in matrix.columns], rotation=45, ha="right",
    )
    ax.set_yticks(range(len(matrix.index)), [f"q{int(v)}" for v in matrix.index])
    ax.set_xlabel("zos quantile (tide-free)" if show_xlabel else "")
    ax.set_ylabel(r"H$_s$ quantile" if show_ylabel else "")
    ax.set_title(title, fontweight="bold", fontsize=10, pad=6)
    ax.grid(False)
    ax.text(
        -0.16, 1.07, f"({panel_letter})", transform=ax.transAxes,
        fontweight="bold", fontsize=11,
    )

    degenerate = frame.pivot(
        index="hs_percentile", columns="ssh_percentile", values="degenerate"
    ).sort_index().reindex(sorted(matrix.columns), axis=1).to_numpy()

    for row in range(values.shape[0]):
        for col in range(values.shape[1]):
            value = values[row, col]
            rgba = cmap(norm(value))
            luminance = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
            ax.text(
                col, row, format(value, fmt), ha="center", va="center",
                fontsize=6.5, color="black" if luminance > 0.55 else "white",
            )
            if hatch_degenerate and bool(degenerate[row, col]):
                ax.add_patch(Rectangle(
                    (col - 0.5, row - 0.5), 1, 1, fill=False,
                    edgecolor="black", hatch="///", linewidth=0.0,
                ))

    for (hs_mark, ssh_mark), colour, width in (
        (INCUMBENT, "#00E5FF", 2.0),
        (
            (
                int(frame.loc[frame["Score"].idxmax(), "hs_percentile"]),
                int(frame.loc[frame["Score"].idxmax(), "ssh_percentile"]),
            ),
            "#000000", 2.0,
        ),
    ):
        if hs_mark in matrix.index and ssh_mark in matrix.columns:
            row = list(matrix.index).index(hs_mark)
            col = list(matrix.columns).index(ssh_mark)
            ax.add_patch(Rectangle(
                (col - 0.5, row - 0.5), 1, 1, fill=False,
                edgecolor=colour, linewidth=width,
            ))

    colorbar = ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.02)
    colorbar.ax.tick_params(labelsize=7)


def main() -> None:
    for path in (SCORES, CENSUS):
        if not path.exists():
            raise FileNotFoundError(path)

    scores = pd.read_csv(SCORES)
    census = pd.read_csv(CENSUS)
    frame = census.merge(
        scores[["thr_hs_pct", "thr_ssh_pct", "U", "B", "F_soft", "Score"]],
        on=["thr_hs_pct", "thr_ssh_pct"], validate="one_to_one",
        suffixes=("", "_score"),
    )
    frame["hs_percentile"] = (frame["thr_hs_pct"] * 100).round().astype(int)
    frame["ssh_percentile"] = (frame["thr_ssh_pct"] * 100).round().astype(int)
    P = int(frame["P"].iloc[0])
    frame["term_fsoft_raw"] = frame["F_soft"] / P
    frame["H_events"] = frame["H"]

    plt.rcParams.update({"font.size": 8, "axes.titlesize": 10})
    fig, axes = plt.subplots(2, 3, figsize=(15.0, 9.6), constrained_layout=True)
    panels = (
        ("R_pos", r"(a) Positive recall $R_{pos}=H/P$", True, ".2f", "a", False, None, False),
        ("B", r"(b) Detection burden $B$", False, ".2f", "b", False, None, False),
        ("term_fsoft_raw", r"(c) Soft penalty $F_{soft}/P$", False, ".1f", "c", False, None, False),
        ("Score", r"(d) Composite score $S$", True, ".2f", "d", False, SCORE_CMAP, False),
        ("n_accepted_episodes", "(e) Compound episodes accepted\n(the sample the score is computed on)",
         True, ".0f", "e", True, None, True),
        ("H_events", f"(f) Reported events captured, H  (of P={P})",
         True, ".0f", "f", True, None, False),
    )
    for index, (ax, spec) in enumerate(zip(axes.flat, panels)):
        metric, title, higher, fmt, letter, log_scale, cmap, _ = spec
        _panel(
            ax, frame, metric, title, higher_is_better=higher, fmt=fmt,
            panel_letter=letter, show_xlabel=index >= 3,
            show_ylabel=index % 3 == 0, cmap_override=cmap, log_scale=log_scale,
        )

    best = frame.loc[frame["Score"].idxmax()]
    incumbent = frame[
        (frame["hs_percentile"] == INCUMBENT[0])
        & (frame["ssh_percentile"] == INCUMBENT[1])
    ].iloc[0]
    fig.suptitle(
        "Step 2e recalibrated on the production detector "
        "(H$_s$ $\\geq$ q$_{hs}$, zos $\\geq$ q$_{zos}$, gate max(SWL) > HAT) — "
        "Santa Catarina calibration domain, 12 grid points, "
        f"P = {P} reported events\n"
        "black outline: score optimum   ·   cyan outline: superseded q90/q90 pair"
        "   ·   hatched: fewer accepted episodes than positive events",
        fontsize=10.5, fontweight="bold",
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "figures").mkdir(exist_ok=True)
    figure_path = OUT_DIR / "figures" / "step2e_score_surface.png"
    fig.savefig(figure_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    export = frame[[
        "hs_percentile", "ssh_percentile", "n_accepted_episodes",
        "n_accepted_matched", "n_accepted_unmatched", "n_points_with_episodes",
        "n_points", "H", "M", "U", "R_pos", "B", "F_soft", "term_fsoft_raw",
        "Score", "degenerate", "episodes_per_positive",
        "min_thr_hs_abs", "median_thr_hs_abs", "median_thr_zos_abs",
    ]].sort_values(["hs_percentile", "ssh_percentile"])
    export.to_csv(OUT_DIR / "score_surface.csv", index=False)

    monotonicity = float(
        frame["Score"].corr(frame["n_accepted_episodes"], method="spearman")
    )
    summary = {
        "generated_by": "src.exploratory.audit_AUD_01_step2e_score_surface",
        "question": (
            "Does the composite score have an interior optimum once the Step 2e "
            "grid is extended beyond q90, and what sample supports the "
            "selected pair?"
        ),
        "grid": sorted(frame["hs_percentile"].unique().tolist()),
        "n_pairs": int(len(frame)),
        "P_positive_events": P,
        "spearman_score_vs_accepted_episodes": round(monotonicity, 6),
        "degeneracy_rule": (
            "A pair is flagged degenerate when it accepts fewer compound "
            "episodes over the whole calibration domain than there are "
            "positive events to recall (n_accepted_episodes < P)."
        ),
        "n_degenerate_pairs": int(frame["degenerate"].sum()),
        "score_optimum": {
            "pair": f"q{int(best['hs_percentile'])}/q{int(best['ssh_percentile'])}",
            "n_accepted_episodes": int(best["n_accepted_episodes"]),
            "H": int(best["H"]),
            "R_pos": round(float(best["R_pos"]), 6),
            "B": round(float(best["B"]), 6),
            "F_soft": round(float(best["F_soft"]), 4),
            "Score": round(float(best["Score"]), 6),
            "degenerate": bool(best["degenerate"]),
        },
        "incumbent_q90_q90": {
            "n_accepted_episodes": int(incumbent["n_accepted_episodes"]),
            "H": int(incumbent["H"]),
            "R_pos": round(float(incumbent["R_pos"]), 6),
            "B": round(float(incumbent["B"]), 6),
            "F_soft": round(float(incumbent["F_soft"]), 4),
            "Score": round(float(incumbent["Score"]), 6),
            "degenerate": bool(incumbent["degenerate"]),
        },
        "figure": "figures/step2e_score_surface.png",
    }
    (OUT_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\nFigure: {figure_path}")


if __name__ == "__main__":
    main()
