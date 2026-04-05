"""
Summary figures for the tidal sensitivity analysis.

Produces four types of outputs:

1. tab_TS_event_metrics.csv  — full metrics table with SSH-only and SSH_total columns
2. tab_TS_tidal_thresholds.csv — q90 thresholds for SSH_total per municipality
3. fig_TS_C1_detection_comparison — grouped bar chart: SSH vs SSH_total concurrent fraction per event
4. fig_TS_C2_scatter_change — scatter of SSH-only vs SSH_total normalised maxima, coloured by detection change
5. fig_TS_C3_new_detections — bar chart of events newly detected with SSH_total
6. fig_TS_C4_tidal_contribution — horizontal bar chart of tidal contribution (tide max / SSH_total max) per event

All summary figures are available for the full SC domain.
"""
from __future__ import annotations

import logging

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config.plot_config import apply_publication_style, STYLE
from src.tidal_sensitivity.config.analysis_config import CFG
from src.tidal_sensitivity.utils import save_fig  # local save_fig (handles full paths)

matplotlib.use("Agg")
log = logging.getLogger(__name__)

# ── Colour palette ─────────────────────────────────────────────────────────────
_COLOR_SSH   = STYLE.color_ssh      # blue
_COLOR_TOTAL = "#7b2d8b"            # purple
_COLOR_NEW   = "#2ca02c"            # green  — new detections
_COLOR_LOST  = "#d62728"            # red    — lost detections
_COLOR_KEEP  = "#1f77b4"            # blue   — maintained
_COLOR_NONE  = "#cccccc"            # grey   — never detected

# ── Table outputs ─────────────────────────────────────────────────────────────

def _save_tables(metrics_df: pd.DataFrame, thresholds_total: dict) -> None:
    out = CFG["tab_dir"]

    # Main metrics table
    metrics_df.to_csv(out / "tab_TS_event_metrics.csv", index=False)
    log.info("Saved: tab_TS_event_metrics.csv  (%d rows)", len(metrics_df))

    # Tidal thresholds table
    rows = [
        {"municipality": muni, **vals}
        for muni, vals in thresholds_total.items()
    ]
    pd.DataFrame(rows).to_csv(out / "tab_TS_tidal_thresholds.csv", index=False)
    log.info("Saved: tab_TS_tidal_thresholds.csv  (%d rows)", len(rows))


# ── Figure C1: detection comparison bar chart ─────────────────────────────────

def _fig_c1_detection_comparison(df: pd.DataFrame) -> None:
    """
    Grouped bar chart: concurrent fraction using SSH-only vs SSH_total.
    One pair of bars per event, sorted by municipality then date.
    """
    valid = df.dropna(subset=["concurrent_fraction", "concurrent_fraction_total"])
    if valid.empty:
        log.warning("C1: no valid events with both SSH-only and SSH_total data.")
        return

    valid = valid.sort_values(["coastal_sector", "municipality", "date"]).reset_index(drop=True)
    x = np.arange(len(valid))
    w = 0.38

    fig, ax = plt.subplots(figsize=(max(14, len(valid) * 0.35), 5))
    bars_ssh   = ax.bar(x - w/2, valid["concurrent_fraction"],       width=w, color=_COLOR_SSH,
                        label="SSH only (q90)", alpha=0.85)
    bars_total = ax.bar(x + w/2, valid["concurrent_fraction_total"],  width=w, color=_COLOR_TOTAL,
                        label="SSH + tide (q90)", alpha=0.85)

    # Highlight new detections
    for i, row in valid.iterrows():
        if row["detection_change"] == "new":
            ax.bar(i + w/2, row["concurrent_fraction_total"], width=w,
                   color=_COLOR_NEW, alpha=0.9)
        elif row["detection_change"] == "lost":
            ax.bar(i - w/2, row["concurrent_fraction"], width=w,
                   color=_COLOR_LOST, alpha=0.9)

    labels = [
        f"{r['municipality'][:10]}\n{pd.Timestamp(r['date']).strftime('%b %y')}"
        for _, r in valid.iterrows()
    ]
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=6, rotation=60, ha="right")
    ax.set_ylabel("Concurrent fraction (fraction of 7-day window)", fontsize=9)
    ax.set_title(
        "Concurrent exceedance fraction: SSH-only vs SSH + FES2022 tide  ·  Full SC coast",
        fontsize=10
    )
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(axis="y", alpha=0.3, lw=0.5)
    fig.tight_layout()

    save_fig(fig, CFG["fig_summary_dir"] / "fig_TS_C1_detection_comparison.png")


# ── Figure C2: scatter SSH vs SSH_total normalised maxima ─────────────────────

def _fig_c2_scatter_change(df: pd.DataFrame) -> None:
    """
    Scatter: SSH_max_norm (x) vs SSH_total_max_norm (y).
    Colour by detection_change. Diagonal is 1:1.
    """
    valid = df.dropna(subset=["ssh_max_norm", "ssh_total_max_norm"])
    if valid.empty:
        log.warning("C2: no valid events with joint SSH and SSH_total maxima.")
        return

    color_map = {"new": _COLOR_NEW, "lost": _COLOR_LOST,
                 "maintained": _COLOR_KEEP, "neither": _COLOR_NONE}
    label_map = {
        "new":        "New detection (SSH+tide)",
        "lost":       "Detection lost (SSH+tide)",
        "maintained": "Maintained detection",
        "neither":    "No detection in either",
    }

    fig, ax = plt.subplots(figsize=(7, 6))
    for change_type, group in valid.groupby("detection_change"):
        ax.scatter(
            group["ssh_max_norm"], group["ssh_total_max_norm"],
            c=color_map.get(change_type, _COLOR_NONE),
            label=label_map.get(change_type, change_type),
            s=55, alpha=0.85, edgecolors="white", linewidths=0.5, zorder=3,
        )

    # 1:1 diagonal
    lim_max = max(valid["ssh_max_norm"].max(), valid["ssh_total_max_norm"].max()) * 1.1
    ax.plot([0, lim_max], [0, lim_max], "k--", lw=0.8, alpha=0.5, zorder=1, label="1:1 line")
    ax.axhline(1, color="gray", lw=0.7, ls=":", alpha=0.6)
    ax.axvline(1, color="gray", lw=0.7, ls=":", alpha=0.6)

    ax.set_xlabel("max(SSH) / mean(SSH)", fontsize=9)
    ax.set_ylabel("max(SSH + tide) / mean(SSH + tide)", fontsize=9)
    ax.set_title("Normalised maxima: SSH-only vs SSH + tide\nColour = change in compound detection at q90", fontsize=9)
    ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)
    ax.grid(alpha=0.3, lw=0.5)
    fig.tight_layout()

    save_fig(fig, CFG["fig_summary_dir"] / "fig_TS_C2_scatter_ssh_vs_total.png")


# ── Figure C3: new detections summary ────────────────────────────────────────

def _fig_c3_new_detections(df: pd.DataFrame) -> None:
    """
    Summary bar chart of event counts by detection_change category,
    split by coastal sector.
    """
    categories = ["new", "maintained", "lost", "neither"]
    colors = [_COLOR_NEW, _COLOR_KEEP, _COLOR_LOST, _COLOR_NONE]
    labels_map = {
        "new":        "New (SSH+tide only)",
        "maintained": "Consistent (both)",
        "lost":       "Lost (SSH only)",
        "neither":    "Not detected",
    }

    # Overall counts
    counts_all = df["detection_change"].value_counts().reindex(categories, fill_value=0)

    # By sector
    sectors = sorted(df["coastal_sector"].dropna().unique())
    sector_counts = {
        s: df[df["coastal_sector"] == s]["detection_change"].value_counts().reindex(categories, fill_value=0)
        for s in sectors
    }

    n_groups = 1 + len(sectors)
    x = np.arange(n_groups)
    w = 0.18
    offsets = np.linspace(-0.3, 0.3, len(categories))

    fig, ax = plt.subplots(figsize=(max(8, n_groups * 1.2), 5))
    group_labels = ["All SC"] + list(sectors)

    for i, (cat, color, off) in enumerate(zip(categories, colors, offsets)):
        vals = [counts_all[cat]] + [sector_counts[s][cat] for s in sectors]
        ax.bar(x + off, vals, width=w, color=color, alpha=0.85,
               label=labels_map[cat])
        for xi, v in zip(x + off, vals):
            if v > 0:
                ax.text(xi, v + 0.05, str(v), ha="center", va="bottom", fontsize=7)

    ax.set_xticks(x)
    ax.set_xticklabels(group_labels, fontsize=9)
    ax.set_ylabel("Number of events", fontsize=9)
    ax.set_title("Impact of adding FES2022 tide on compound event detection\n(event counts by detection-change category and sector)", fontsize=9)
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(axis="y", alpha=0.3, lw=0.5)
    fig.tight_layout()

    save_fig(fig, CFG["fig_summary_dir"] / "fig_TS_C3_detection_change_by_sector.png")


# ── Figure C4: tidal fraction of total sea level ─────────────────────────────

def _fig_c4_tidal_fraction(df: pd.DataFrame, tide_cache: dict, records: list) -> None:
    """
    Horizontal bar chart showing, for each event, the fraction of SSH_total
    max attributable to the tidal signal.
    """
    rows = []
    for rec in records:
        row = df[df["event_idx"] == rec.event_idx]
        if row.empty:
            continue
        r = row.iloc[0]

        key = (round(float(rec.grid_lat), 6), round(float(rec.grid_lon), 6))
        tide = tide_cache.get(key)
        if tide is None:
            continue

        tide_win = tide.reindex(rec.ssh_window.index)
        tide_max_win = float(tide_win.abs().max()) if not tide_win.dropna().empty else np.nan
        total_max = float(r.get("ssh_total_max_window", np.nan))

        if np.isnan(tide_max_win) or np.isnan(total_max) or total_max == 0:
            continue

        rows.append({
            "label": f"{rec.municipality[:14]}\n{rec.date.strftime('%b %Y')}",
            "tidal_fraction": min(abs(tide_max_win / total_max), 1.5),
            "detection_change": r.get("detection_change", "neither"),
        })

    if not rows:
        return

    rows_df = pd.DataFrame(rows).sort_values("tidal_fraction", ascending=True)
    colors = [
        {"new": _COLOR_NEW, "lost": _COLOR_LOST, "maintained": _COLOR_KEEP}.get(c, _COLOR_NONE)
        for c in rows_df["detection_change"]
    ]

    fig, ax = plt.subplots(figsize=(7, max(5, len(rows_df) * 0.28)))
    ax.barh(rows_df["label"], rows_df["tidal_fraction"], color=colors, alpha=0.85, height=0.7)
    ax.axvline(0.5, color="gray", lw=0.8, ls="--", alpha=0.6, label="|tide| = 50% of total max")
    ax.set_xlabel("Tidal fraction of max SSH_total  (|tide_max| / SSH_total_max)", fontsize=8)
    ax.set_title("Relative tidal contribution during each event window\n(colour = detection-change category)", fontsize=9)
    ax.legend(fontsize=8)
    ax.grid(axis="x", alpha=0.3, lw=0.5)
    fig.tight_layout()

    save_fig(fig, CFG["fig_summary_dir"] / "fig_TS_C4_tidal_fraction.png")


# ── Main entry point ──────────────────────────────────────────────────────────

def run_summary(
    metrics_df: pd.DataFrame,
    thresholds_total: dict,
    tide_cache: dict,
    records: list,
) -> None:
    """Save tables and generate all summary figures."""
    apply_publication_style()

    _save_tables(metrics_df, thresholds_total)

    log.info("Generating summary figures...")
    _fig_c1_detection_comparison(metrics_df)
    _fig_c2_scatter_change(metrics_df)
    _fig_c3_new_detections(metrics_df)
    _fig_c4_tidal_fraction(metrics_df, tide_cache, records)

    log.info("Summary complete.")
