"""
Diagnostic figures for Step 3 — Storm Catalog Generation.

Produces QA visualizations:
- SC3-1: Annual storm count time series (domain mean)
- SC3-2: Storm duration distribution (histograms)
- SC3-3: Seasonal climatology of storm frequency
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

# Attempt to load project plot style
try:
    from config.plot_config import apply_publication_style, STYLE
    apply_publication_style()
except Exception:
    pass

# Variable display settings
_COLORS = {"hs": "#d62728", "ssh_total": "steelblue"}
_LABELS = {"hs": "Hₛ storms", "ssh_total": "SSH_total storms"}


def _flatten_catalog(catalog: list[dict]) -> pd.DataFrame:
    """Flatten a catalog JSON into a DataFrame of storms."""
    rows = []
    for entry in catalog:
        for storm in entry.get("storms", []):
            rows.append({
                "grid_lat": entry["grid_lat"],
                "grid_lon": entry["grid_lon"],
                "date_start": pd.Timestamp(storm["date_start"]),
                "date_end": pd.Timestamp(storm["date_end"]),
                "duration_days": storm["duration_days"],
                "peak_value": storm["peak_value"],
                "integrated_intensity": storm["integrated_intensity"],
            })
    return pd.DataFrame(rows)


def plot_annual_counts(
    catalog_hs: list[dict],
    catalog_ssh: list[dict],
    out_path: Path,
) -> None:
    """SC3-1: Annual storm count per variable (domain total)."""
    fig, ax = plt.subplots(figsize=(10, 4))

    for var_prefix, catalog in [("hs", catalog_hs), ("ssh_total", catalog_ssh)]:
        df = _flatten_catalog(catalog)
        if df.empty:
            continue
        df["year"] = df["date_start"].dt.year
        annual = df.groupby("year").size()
        ax.plot(
            annual.index, annual.values,
            marker="o", markersize=3, linewidth=1.2,
            color=_COLORS[var_prefix], label=_LABELS[var_prefix],
        )

    ax.set_xlabel("Year")
    ax.set_ylabel("Total storm episodes (all grid points)")
    ax.set_title("SC3-1 — Annual storm count")
    ax.legend()
    ax.grid(alpha=0.3, linestyle="--", linewidth=0.5)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    log.info("Saved figure: %s", out_path.name)


def plot_duration_distribution(
    catalog_hs: list[dict],
    catalog_ssh: list[dict],
    out_path: Path,
) -> None:
    """SC3-2: Histogram of storm durations per variable."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)

    for ax, (var_prefix, catalog) in zip(
        axes, [("hs", catalog_hs), ("ssh_total", catalog_ssh)]
    ):
        df = _flatten_catalog(catalog)
        if df.empty:
            ax.set_title(_LABELS[var_prefix])
            continue
        durations = df["duration_days"].values
        max_dur = min(int(np.percentile(durations, 99)) + 2, 30)
        bins = np.arange(0.5, max_dur + 1.5, 1)
        ax.hist(
            durations, bins=bins, color=_COLORS[var_prefix],
            alpha=0.7, edgecolor="white", linewidth=0.5,
        )
        ax.set_xlabel("Duration (days)")
        ax.set_title(_LABELS[var_prefix])
        ax.grid(alpha=0.3, linestyle="--", linewidth=0.5)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)

        med = np.median(durations)
        ax.axvline(med, color="black", linestyle="--", linewidth=1, alpha=0.6)
        ax.text(
            med + 0.3, ax.get_ylim()[1] * 0.9,
            f"median={med:.0f}d", fontsize=8, va="top",
        )

    axes[0].set_ylabel("Count")
    fig.suptitle("SC3-2 — Storm duration distribution", fontsize=11)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    log.info("Saved figure: %s", out_path.name)


def plot_seasonal_climatology(
    catalog_hs: list[dict],
    catalog_ssh: list[dict],
    out_path: Path,
) -> None:
    """SC3-3: Monthly climatology of storm frequency (domain mean)."""
    fig, ax = plt.subplots(figsize=(8, 4))

    for var_prefix, catalog in [("hs", catalog_hs), ("ssh_total", catalog_ssh)]:
        df = _flatten_catalog(catalog)
        if df.empty:
            continue
        df["month"] = df["date_start"].dt.month
        df["year"] = df["date_start"].dt.year
        # Mean annual count per month
        monthly_annual = df.groupby(["year", "month"]).size().reset_index(name="count")
        clim = monthly_annual.groupby("month")["count"].mean()
        ax.plot(
            clim.index, clim.values,
            marker="s", markersize=4, linewidth=1.5,
            color=_COLORS[var_prefix], label=_LABELS[var_prefix],
        )

    ax.set_xlabel("Month")
    ax.set_ylabel("Mean storm episodes per month (all grid points)")
    ax.set_title("SC3-3 — Seasonal storm climatology")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"])
    ax.legend()
    ax.grid(alpha=0.3, linestyle="--", linewidth=0.5)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    log.info("Saved figure: %s", out_path.name)
