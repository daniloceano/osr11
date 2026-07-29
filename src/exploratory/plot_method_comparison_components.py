"""Figure: hazard components under the legacy SSH_total method and the MHWS method.

Reads the side-by-side comparison produced by
:mod:`compare_methods_ssh_total_vs_mhws` and draws the three normalized hazard
components and the resulting index against latitude, one panel each, so the
behaviour of every component under the two detectors can be read directly.

The message the figure has to carry is that two components moved as intended
and one did not: frequency and intensity fall in the macrotidal north under the
new detector, while the duration component inverts — the south drops to the
domain minimum and the equatorial sector rises to the maximum — and that
inversion is large enough to raise the resulting index in the north despite the
other two falling.

Read-only. Draws from the existing comparison; recomputes nothing.

Usage:
    python -m src.exploratory.plot_method_comparison_components

Output:
    outputs/method_comparison_ssh_total_vs_mhws/figures/hazard_components_legacy_vs_mhws.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from config.plot_config import STYLE  # noqa: E402

SOURCE = (
    ROOT
    / "outputs"
    / "method_comparison_ssh_total_vs_mhws"
    / "hazard_by_point.csv"
)
OUT_DIR = (
    ROOT / "outputs" / "method_comparison_ssh_total_vs_mhws" / "figures"
)

PANELS = (
    ("Hazard_Frequency", "Frequência", "corrigiu como pretendido"),
    ("Hazard_Intensity", "Intensidade", "corrigiu como pretendido"),
    ("Hazard_Duration", "Duração", "VIÉS AMPLIFICADO: Norte/Sul 2,0× → 9,4×"),
    ("Hazard_Index", "Índice de perigo", "resultado líquido"),
)

BANDS = (
    ("RS", -36.0, -30.0),
    ("SC/PR", -30.0, -25.0),
    ("SP/RJ", -25.0, -20.0),
    ("ES/BA-S", -20.0, -15.0),
    ("BA-N", -15.0, -10.0),
    ("NE", -10.0, -5.0),
    ("N eq.", -5.0, 0.0),
    ("AP", 0.0, 7.0),
)

COLOR_LEGACY = "#8C8C8C"
COLOR_MHWS = "#B2182B"
BIN_WIDTH_DEG = 1.0


def _binned(lat: np.ndarray, value: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Mean of ``value`` in fixed-width latitude bins, for the trend line."""
    edges = np.arange(np.floor(lat.min()), np.ceil(lat.max()) + BIN_WIDTH_DEG, BIN_WIDTH_DEG)
    centres, means = [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        sel = (lat >= lo) & (lat < hi)
        if sel.sum() >= 2:
            centres.append((lo + hi) / 2)
            means.append(float(np.nanmean(value[sel])))
    return np.asarray(centres), np.asarray(means)


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(
            f"{SOURCE} not found. Run compare_methods_ssh_total_vs_mhws first."
        )
    df = pd.read_csv(SOURCE)
    lat = df["grid_lat_legacy"].to_numpy(dtype=float)

    fig, axes = plt.subplots(
        2, 2,
        figsize=(STYLE.fig_width_double, 7.4),
        sharex=True,
    )

    for ax, (field, title, verdict) in zip(axes.ravel(), PANELS):
        legacy = df[f"{field}_legacy"].to_numpy(dtype=float)
        mhws = df[f"{field}_mhws"].to_numpy(dtype=float)

        for lo, hi in [(b[1], b[2]) for b in BANDS][1::2]:
            ax.axvspan(lo, hi, color="0.94", zorder=0, linewidth=0)

        ax.scatter(lat, legacy, s=5, c=COLOR_LEGACY, alpha=0.30, linewidths=0, zorder=2)
        ax.scatter(lat, mhws, s=5, c=COLOR_MHWS, alpha=0.30, linewidths=0, zorder=2)

        cx, cy = _binned(lat, legacy)
        ax.plot(cx, cy, color=COLOR_LEGACY, lw=2.2, zorder=4,
                label="legado — SSH_total")
        cx, cy = _binned(lat, mhws)
        ax.plot(cx, cy, color=COLOR_MHWS, lw=2.2, zorder=4,
                label="novo — zos + condição MHWS")

        emphasis = field == "Hazard_Duration"
        ax.set_title(
            f"{title}  ·  {verdict}",
            fontsize=STYLE.font_size_title,
            fontweight="bold" if emphasis else "normal",
            color=COLOR_MHWS if emphasis else "black",
            pad=6,
        )
        ax.set_ylabel("componente normalizada (0–1)",
                      fontsize=STYLE.font_size_axis_label)
        ax.set_ylim(-0.03, 1.03)
        ax.tick_params(labelsize=STYLE.font_size_tick)
        ax.grid(True, alpha=0.25, linewidth=0.6)
        ax.set_axisbelow(True)

    for ax in axes[-1]:
        ax.set_xlabel("latitude (°)", fontsize=STYLE.font_size_axis_label)
    axes[0, 0].legend(loc="upper right", fontsize=STYLE.font_size_legend,
                      framealpha=0.92)
    axes[0, 0].set_xlim(-36, 7)

    # 79 % of points fall in duration under the new method; what changes is the
    # contrast, because the south collapses to the floor of the scale while the
    # equatorial sector holds. Annotated here so the panel is not misread as an
    # inversion.
    duration_ax = axes[1, 0]
    duration_ax.annotate(
        "Sul colapsa ao piso\nda escala (0,22 → 0,04)",
        xy=(-32.0, 0.04), xytext=(-34.5, 0.46),
        fontsize=STYLE.font_size_annotation + 0.5, color=COLOR_MHWS, ha="left",
        arrowprops=dict(arrowstyle="->", color=COLOR_MHWS, lw=1.2),
    )
    duration_ax.annotate(
        "setor equatorial\nse mantém alto",
        xy=(-2.0, 0.56), xytext=(-13.5, 0.82),
        fontsize=STYLE.font_size_annotation + 0.5, color=COLOR_MHWS, ha="left",
        arrowprops=dict(arrowstyle="->", color=COLOR_MHWS, lw=1.2),
    )

    fig.suptitle(
        "Componentes do perigo — método legado (SSH_total) × método MHWS",
        fontsize=STYLE.font_size_title + 1.5, fontweight="bold", y=0.995,
    )
    fig.text(
        0.5, 0.012,
        "Pontos: 808 pontos de grade nativos.  Linhas: média em faixas de 1° de latitude.  "
        "Sul à esquerda, equador à direita.\n"
        "A duração cai em 79 % dos pontos sob o método novo, mas o Sul colapsa ao piso da escala "
        "enquanto o setor equatorial se mantém: o contraste Norte/Sul\npassa de 2,0× para 9,4×, e "
        "isso eleva o índice no Norte apesar da queda de frequência e intensidade.  "
        "Ver outputs/method_comparison_ssh_total_vs_mhws/README.md",
        ha="center", va="bottom", fontsize=STYLE.font_size_annotation, color="0.25",
    )

    fig.tight_layout(rect=(0, 0.075, 1, 0.975))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "hazard_components_legacy_vs_mhws.png"
    fig.savefig(out, dpi=STYLE.dpi_export, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
