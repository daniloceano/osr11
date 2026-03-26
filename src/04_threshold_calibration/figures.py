"""
Figure generation for the threshold calibration analysis (OSR11 — Step 4).

Figures produced
----------------
TC4-H1  CSI heatmap (hs_pct × ssh_pct)
TC4-H2  FAR heatmap (hs_pct × ssh_pct)
TC4-H3  POD heatmap (hs_pct × ssh_pct)
TC4-S1  Ranking scatter: POD vs FAR (bubble size = CSI)
TC4-S2  Hit/miss bar chart per event at the optimal threshold pair
TC4-S3  Capture lag distribution (D-2 / D-1 / D / D+1 00Z)
TC4-S4  CSI, FAR, POD by coastal sector at optimal pair
"""
from __future__ import annotations

import logging

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from src.threshold_calibration.config.analysis_config import CFG
from src.threshold_calibration.utils import save_fig
from config.plot_config import STYLE

log = logging.getLogger(__name__)

_PCT_LABELS = {p: f"q{round(p*100)}" for p in CFG["hs_percentiles"]}


def _pivot_metric(df_metrics: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Pivot metric values into a (hs_pct × ssh_pct) matrix for heatmap plotting."""
    return df_metrics.pivot(index="thr_hs_pct", columns="thr_ssh_pct", values=metric)


# ── TC4-H1: CSI heatmap ───────────────────────────────────────────────────────

def plot_csi_heatmap(
    df_metrics: pd.DataFrame,
    optimal: dict,
) -> plt.Figure:
    """CSI heatmap with the optimal pair highlighted."""
    pivot = _pivot_metric(df_metrics, "CSI")
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(pivot.values, aspect="auto", cmap="YlGn", vmin=0, vmax=pivot.values.max())
    cbar = fig.colorbar(im, ax=ax, shrink=0.85)
    cbar.set_label("CSI", fontsize=STYLE.label_fs)

    n_rows, n_cols = pivot.shape
    hs_labels  = [f"q{round(p*100)}" for p in pivot.index]
    ssh_labels = [f"q{round(p*100)}" for p in pivot.columns]
    ax.set_xticks(range(n_cols))
    ax.set_xticklabels(ssh_labels, fontsize=STYLE.tick_fs)
    ax.set_yticks(range(n_rows))
    ax.set_yticklabels(hs_labels, fontsize=STYLE.tick_fs)
    ax.set_xlabel("SSH_total threshold (percentile)", fontsize=STYLE.label_fs)
    ax.set_ylabel("Hₛ threshold (percentile)", fontsize=STYLE.label_fs)
    ax.set_title("TC4-H1 — CSI Grid Scan", fontsize=STYLE.title_fs, fontweight="bold")

    # Annotate values
    for i in range(n_rows):
        for j in range(n_cols):
            val = pivot.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                        fontsize=6, color="black")

    # Highlight optimal pair
    opt_i = list(pivot.index).index(optimal["thr_hs_pct"])
    opt_j = list(pivot.columns).index(optimal["thr_ssh_pct"])
    ax.add_patch(plt.Rectangle(
        (opt_j - 0.5, opt_i - 0.5), 1, 1,
        linewidth=2, edgecolor="red", facecolor="none",
    ))
    ax.text(
        opt_j, opt_i - 0.42,
        f"★ optimal\nCSI={optimal['CSI']:.2f}",
        ha="center", va="top", fontsize=6, color="red", fontweight="bold",
    )

    fig.tight_layout()
    return fig


# ── TC4-H2: FAR heatmap ───────────────────────────────────────────────────────

def plot_far_heatmap(
    df_metrics: pd.DataFrame,
    optimal: dict,
) -> plt.Figure:
    """FAR heatmap with the optimal pair highlighted."""
    pivot = _pivot_metric(df_metrics, "FAR")
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(pivot.values, aspect="auto", cmap="YlOrRd", vmin=0, vmax=1)
    cbar = fig.colorbar(im, ax=ax, shrink=0.85)
    cbar.set_label("FAR", fontsize=STYLE.label_fs)

    n_rows, n_cols = pivot.shape
    hs_labels  = [f"q{round(p*100)}" for p in pivot.index]
    ssh_labels = [f"q{round(p*100)}" for p in pivot.columns]
    ax.set_xticks(range(n_cols))
    ax.set_xticklabels(ssh_labels, fontsize=STYLE.tick_fs)
    ax.set_yticks(range(n_rows))
    ax.set_yticklabels(hs_labels, fontsize=STYLE.tick_fs)
    ax.set_xlabel("SSH_total threshold (percentile)", fontsize=STYLE.label_fs)
    ax.set_ylabel("Hₛ threshold (percentile)", fontsize=STYLE.label_fs)
    ax.set_title("TC4-H2 — FAR Grid Scan", fontsize=STYLE.title_fs, fontweight="bold")

    for i in range(n_rows):
        for j in range(n_cols):
            val = pivot.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                        fontsize=6, color="black")

    opt_i = list(pivot.index).index(optimal["thr_hs_pct"])
    opt_j = list(pivot.columns).index(optimal["thr_ssh_pct"])
    ax.add_patch(plt.Rectangle(
        (opt_j - 0.5, opt_i - 0.5), 1, 1,
        linewidth=2, edgecolor="navy", facecolor="none",
    ))
    fig.tight_layout()
    return fig


# ── TC4-H3: POD heatmap ───────────────────────────────────────────────────────

def plot_pod_heatmap(
    df_metrics: pd.DataFrame,
    optimal: dict,
) -> plt.Figure:
    """POD heatmap with the optimal pair highlighted."""
    pivot = _pivot_metric(df_metrics, "POD")
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(pivot.values, aspect="auto", cmap="Blues", vmin=0, vmax=1)
    cbar = fig.colorbar(im, ax=ax, shrink=0.85)
    cbar.set_label("POD", fontsize=STYLE.label_fs)

    n_rows, n_cols = pivot.shape
    hs_labels  = [f"q{round(p*100)}" for p in pivot.index]
    ssh_labels = [f"q{round(p*100)}" for p in pivot.columns]
    ax.set_xticks(range(n_cols))
    ax.set_xticklabels(ssh_labels, fontsize=STYLE.tick_fs)
    ax.set_yticks(range(n_rows))
    ax.set_yticklabels(hs_labels, fontsize=STYLE.tick_fs)
    ax.set_xlabel("SSH_total threshold (percentile)", fontsize=STYLE.label_fs)
    ax.set_ylabel("Hₛ threshold (percentile)", fontsize=STYLE.label_fs)
    ax.set_title("TC4-H3 — POD Grid Scan", fontsize=STYLE.title_fs, fontweight="bold")

    for i in range(n_rows):
        for j in range(n_cols):
            val = pivot.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                        fontsize=6, color="black")

    opt_i = list(pivot.index).index(optimal["thr_hs_pct"])
    opt_j = list(pivot.columns).index(optimal["thr_ssh_pct"])
    ax.add_patch(plt.Rectangle(
        (opt_j - 0.5, opt_i - 0.5), 1, 1,
        linewidth=2, edgecolor="navy", facecolor="none",
    ))
    fig.tight_layout()
    return fig


# ── TC4-S1: Ranking scatter (POD vs FAR, bubble = CSI) ───────────────────────

def plot_ranking_scatter(df_metrics: pd.DataFrame, optimal: dict) -> plt.Figure:
    """POD vs FAR scatter, bubble size proportional to CSI."""
    fig, ax = plt.subplots(figsize=(6, 5))

    sizes = (df_metrics["CSI"].fillna(0) * 400 + 10).values
    sc = ax.scatter(
        df_metrics["FAR"], df_metrics["POD"],
        s=sizes, c=df_metrics["CSI"], cmap="YlGn", vmin=0, vmax=df_metrics["CSI"].max(),
        alpha=0.7, edgecolors="gray", linewidths=0.4,
    )
    cbar = fig.colorbar(sc, ax=ax, shrink=0.85)
    cbar.set_label("CSI", fontsize=STYLE.label_fs)

    # Highlight optimal
    ax.scatter(
        optimal["FAR"], optimal["POD"],
        s=300, c="red", marker="*", zorder=5, label=(
            f"Optimal\nHs=q{round(optimal['thr_hs_pct']*100)}"
            f" / SSH=q{round(optimal['thr_ssh_pct']*100)}"
        ),
    )

    ax.set_xlabel("FAR (False Alarm Ratio)", fontsize=STYLE.label_fs)
    ax.set_ylabel("POD (Probability of Detection)", fontsize=STYLE.label_fs)
    ax.set_title("TC4-S1 — Threshold Ranking: POD vs FAR", fontsize=STYLE.title_fs, fontweight="bold")
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.axhline(0.5, color="gray", ls="--", lw=0.8, alpha=0.5)
    ax.axvline(0.5, color="gray", ls="--", lw=0.8, alpha=0.5)
    ax.legend(fontsize=7)
    fig.tight_layout()
    return fig


# ── TC4-S2: Per-event hit/miss bar chart ──────────────────────────────────────

def plot_event_hits(df_event_hits: pd.DataFrame, optimal: dict) -> plt.Figure:
    """Horizontal bar chart: one row per event, coloured by hit/miss."""
    df_opt = df_event_hits[
        (df_event_hits["thr_hs_pct"]  == optimal["thr_hs_pct"]) &
        (df_event_hits["thr_ssh_pct"] == optimal["thr_ssh_pct"])
    ].sort_values("date").reset_index(drop=True)

    n = len(df_opt)
    fig, ax = plt.subplots(figsize=(8, max(4, n * 0.22)))

    colors = ["#27ae60" if c else "#e74c3c" for c in df_opt["captured"]]
    labels = [
        f"{row['municipality'][:18]} — {row['date'].strftime('%Y-%m-%d')}"
        for _, row in df_opt.iterrows()
    ]

    ax.barh(range(n), df_opt["captured"].astype(int), color=colors, height=0.7)
    ax.set_yticks(range(n))
    ax.set_yticklabels(labels, fontsize=6)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Miss", "Hit"], fontsize=STYLE.tick_fs)
    ax.set_title(
        f"TC4-S2 — Event capture at optimal pair\n"
        f"Hₛ=q{round(optimal['thr_hs_pct']*100)} / SSH_total=q{round(optimal['thr_ssh_pct']*100)}"
        f"  →  H={int(optimal['H'])}  M={int(optimal['M'])}  F={int(optimal['F'])}",
        fontsize=STYLE.title_fs, fontweight="bold",
    )
    ax.invert_yaxis()
    fig.tight_layout()
    return fig


# ── TC4-S3: Capture lag distribution ──────────────────────────────────────────

def plot_lag_distribution(lag_summary: pd.DataFrame, optimal: dict) -> plt.Figure:
    """Bar chart: number of captures at each lag offset."""
    fig, ax = plt.subplots(figsize=(5, 4))
    colors = ["#3498db" if lag <= 0 else "#e67e22" for lag in lag_summary["lag"]]
    ax.bar(lag_summary["lag_label"], lag_summary["count"], color=colors, width=0.6)
    ax.set_xlabel("Lag relative to event day D", fontsize=STYLE.label_fs)
    ax.set_ylabel("Number of captures", fontsize=STYLE.label_fs)
    ax.set_title(
        f"TC4-S3 — Capture lag distribution\n"
        f"Optimal: Hₛ=q{round(optimal['thr_hs_pct']*100)} / SSH=q{round(optimal['thr_ssh_pct']*100)}",
        fontsize=STYLE.title_fs, fontweight="bold",
    )
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.tick_params(axis="both", labelsize=STYLE.tick_fs)
    from matplotlib.patches import Patch
    ax.legend(
        handles=[
            Patch(color="#3498db", label="Antecedent (D-2, D-1, D)"),
            Patch(color="#e67e22", label="D+1 00Z tolerance"),
        ],
        fontsize=7,
    )
    fig.tight_layout()
    return fig


# ── TC4-S4: Metrics by coastal sector ─────────────────────────────────────────

def plot_sector_metrics(df_event_hits: pd.DataFrame, optimal: dict) -> plt.Figure:
    """Grouped bar chart: POD, FAR, CSI per coastal sector at optimal pair."""
    df_opt = df_event_hits[
        (df_event_hits["thr_hs_pct"]  == optimal["thr_hs_pct"]) &
        (df_event_hits["thr_ssh_pct"] == optimal["thr_ssh_pct"])
    ]
    if "coastal_sector" not in df_opt.columns or df_opt["coastal_sector"].isna().all():
        log.warning("No coastal_sector column in event hits — skipping TC4-S4.")
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No sector data available", ha="center", va="center")
        return fig

    sectors = df_opt["coastal_sector"].dropna().unique()
    sector_rows = []
    for sec in sectors:
        sub = df_opt[df_opt["coastal_sector"] == sec]
        H = sub["captured"].sum()
        M = (~sub["captured"]).sum()
        pod = H / (H + M) if (H + M) > 0 else np.nan
        sector_rows.append({"sector": sec, "POD": pod, "H": H, "M": M})

    df_sec = pd.DataFrame(sector_rows).sort_values("sector")
    x = np.arange(len(df_sec))

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(x, df_sec["POD"], width=0.5, color="#3498db", label="POD")
    ax.set_xticks(x)
    ax.set_xticklabels(df_sec["sector"], fontsize=STYLE.tick_fs - 1, rotation=20, ha="right")
    ax.set_ylabel("POD", fontsize=STYLE.label_fs)
    ax.set_ylim(0, 1.1)
    ax.set_title(
        f"TC4-S4 — POD by coastal sector\n"
        f"Optimal: Hₛ=q{round(optimal['thr_hs_pct']*100)} / SSH=q{round(optimal['thr_ssh_pct']*100)}",
        fontsize=STYLE.title_fs, fontweight="bold",
    )
    for i, row in enumerate(df_sec.itertuples()):
        ax.text(i, (row.POD or 0) + 0.03, f"H={row.H}", ha="center", fontsize=7)
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


# ── Orchestration ─────────────────────────────────────────────────────────────

def run_figures(
    df_metrics: pd.DataFrame,
    df_event_hits: pd.DataFrame,
    lag_summary: pd.DataFrame,
    optimal: dict,
) -> None:
    """Generate and save all Step 4 figures."""
    log.info("Generating threshold calibration figures...")

    fig_h1 = plot_csi_heatmap(df_metrics, optimal)
    save_fig(fig_h1, "fig_TC4_H1_csi_heatmap", subdir="summary")

    fig_h2 = plot_far_heatmap(df_metrics, optimal)
    save_fig(fig_h2, "fig_TC4_H2_far_heatmap", subdir="summary")

    fig_h3 = plot_pod_heatmap(df_metrics, optimal)
    save_fig(fig_h3, "fig_TC4_H3_pod_heatmap", subdir="summary")

    fig_s1 = plot_ranking_scatter(df_metrics, optimal)
    save_fig(fig_s1, "fig_TC4_S1_ranking_scatter", subdir="summary")

    fig_s2 = plot_event_hits(df_event_hits, optimal)
    save_fig(fig_s2, "fig_TC4_S2_event_hits", subdir="summary")

    if not lag_summary.empty:
        fig_s3 = plot_lag_distribution(lag_summary, optimal)
        save_fig(fig_s3, "fig_TC4_S3_lag_distribution", subdir="summary")

    fig_s4 = plot_sector_metrics(df_event_hits, optimal)
    save_fig(fig_s4, "fig_TC4_S4_sector_pod", subdir="summary")

    log.info("All TC4 figures saved.")
