"""
Summary outputs for the threshold calibration analysis.

Produces:
  - tab_TC_event_metrics.csv — consolidated per-event metrics table
  - fig_TC_S1 — grouped bar chart: max Hs and SSH normalised by event, sorted by
                municipality then date
  - fig_TC_S2 — scatter: normalised Hs vs normalised SSH, coloured by municipality,
                marker size ∝ concurrent fraction, concurrent events highlighted
  - fig_TC_S3 — concomitance bar chart: concurrent fraction per event
  - fig_TC_S4 — heatmap: municipality × event sorted by date, colour = concurrent
                fraction (overview of all events in the test domain)
"""
from __future__ import annotations

import logging

import matplotlib.cm as cm
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

from src.preliminary_compound.config.analysis_config import CFG
from src.preliminary_compound.utils import save_fig, muni_slug
from config.plot_config import STYLE, apply_publication_style, panel_label, SECTOR_COLORS

log = logging.getLogger(__name__)


def run_summary(
    metrics_df: pd.DataFrame,
    thresholds: dict[str, dict[str, float]],
) -> None:
    """Save the consolidated metrics table and all summary figures."""
    log.info("== Summary: table + figures ==")
    apply_publication_style()

    if metrics_df.empty:
        log.warning("  No event metrics; skipping summary outputs.")
        return

    # Load sector information from events file
    events_path = CFG["events_file"]
    df_events_raw = pd.read_csv(events_path)
    df_events_raw = df_events_raw.rename(columns={
        "Disaster ID": "disaster_id",
        "Municipalities": "municipality",
        "Coastal Sectors": "coastal_sector",
    })
    # Merge sector info into metrics
    metrics_df = metrics_df.merge(
        df_events_raw[["disaster_id", "municipality", "coastal_sector"]].drop_duplicates(),
        on=["disaster_id", "municipality"],
        how="left"
    )

    # ── Table ────────────────────────────────────────────────────────────────
    _save_table(metrics_df)

    # ── Threshold summary table ───────────────────────────────────────────────
    _save_threshold_table(thresholds)

    # ── Figures ───────────────────────────────────────────────────────────────
    # Original all-sector figures
    _fig_s1_normalised_bars(metrics_df)
    _fig_s2_scatter(metrics_df)
    _fig_s3_concomitance_bars(metrics_df)
    _fig_s4_heatmap(metrics_df)
    
    # New: per-sector figures with subplots per municipality
    _fig_s1_per_sector(metrics_df)
    _fig_s3_per_sector(metrics_df)
    _fig_s4_per_sector(metrics_df)

    log.info("Summary outputs complete.")


# ── Table helpers ─────────────────────────────────────────────────────────────

def _save_table(df: pd.DataFrame) -> None:
    path = CFG["tab_dir"] / "tab_TC_event_metrics.csv"
    df.to_csv(path, index=False)
    log.info("  -> Table: %s", path)


def _save_threshold_table(thresholds: dict[str, dict[str, float]]) -> None:
    rows = []
    q = CFG["threshold_quantile"]
    for muni, th in thresholds.items():
        rows.append({
            "municipality": muni,
            "threshold_quantile": q,
            "hs_q90_m":    round(th["hs_q90"],  3),
            "ssh_q90_m":   round(th["ssh_q90"], 4),
            "hs_mean_m":   round(th["hs_mean"], 3),
            "ssh_mean_m":  round(th["ssh_mean"],4),
            "hs_std_m":    round(th["hs_std"],  3),
            "ssh_std_m":   round(th["ssh_std"], 4),
            "hs_p99_m":    round(th["hs_p99"],  3),
            "ssh_p99_m":   round(th["ssh_p99"], 4),
        })
    df = pd.DataFrame(rows).sort_values("municipality").reset_index(drop=True)
    path = CFG["tab_dir"] / "tab_TC_thresholds.csv"
    df.to_csv(path, index=False)
    log.info("  -> Table: %s", path)


# ── Figure S1: normalised max Hs and SSH per event ────────────────────────────

def _fig_s1_normalised_bars(df: pd.DataFrame) -> None:
    """Grouped bar chart: normalised Hs (red) and SSH (blue) per event."""
    df = df.copy()
    df["event_label"] = df.apply(
        lambda r: f"{muni_slug(r['municipality'])[:10]}\n{pd.Timestamp(r['date']).strftime('%Y-%m')}",
        axis=1,
    )
    # Sort: municipality then date
    df = df.sort_values(["municipality", "date"]).reset_index(drop=True)

    x    = np.arange(len(df))
    w    = 0.38

    fig, ax = plt.subplots(figsize=(max(STYLE.fig_width_wide, len(df) * 0.55 + 2), 5.0))

    bars_hs  = ax.bar(x - w/2, df["hs_max_norm"],  width=w, color=STYLE.color_hs,
                      label="Hₛ_max / Hₛ_mean", alpha=0.85)
    bars_ssh = ax.bar(x + w/2, df["ssh_max_norm"], width=w, color=STYLE.color_ssh,
                      label="SSH_max / SSH_mean", alpha=0.85)

    # Horizontal line at 1.0 (= climatological mean) and at threshold
    q = CFG["threshold_quantile"]
    ax.axhline(1.0, color="0.5", lw=0.8, ls=":", label="Climatological mean (= 1)")

    ax.set_xticks(x)
    ax.set_xticklabels(df["event_label"], fontsize=7, rotation=45, ha="right")
    ax.set_ylabel("Normalised value (÷ clim. mean)", fontsize=STYLE.font_size_axis_label)
    ax.set_title(
        f"Per-event normalised Hₛ and SSH maxima in ±{CFG['event_half_window_days']}-day window",
        fontsize=STYLE.font_size_title,
    )
    ax.legend(fontsize=STYLE.font_size_legend, framealpha=STYLE.legend_framealpha)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    save_fig(fig, "fig_TC_S1_normalised_maxima_per_event", subdir="summary")


# ── Figure S2: scatter normalised Hs vs SSH ───────────────────────────────────

def _fig_s2_scatter(df: pd.DataFrame) -> None:
    """Scatter: normalised Hs vs normalised SSH, coloured by municipality."""
    munis  = sorted(df["municipality"].unique())
    colors = _muni_colormap(munis)

    fig, ax = plt.subplots(figsize=(STYLE.fig_width_single + 3.0, STYLE.fig_height_default))

    for muni in munis:
        sub = df[df["municipality"] == muni]
        # Concurrent events: larger, filled; non-concurrent: open
        concurrent    = sub[sub["is_concurrent"] == 1]
        non_concurrent = sub[sub["is_concurrent"] == 0]

        scatter_kw = dict(
            color=colors[muni],
            edgecolors=colors[muni],
            linewidths=1.2,
            zorder=4,
        )
        if not non_concurrent.empty:
            ax.scatter(
                non_concurrent["hs_max_norm"],
                non_concurrent["ssh_max_norm"],
                s=40, marker="o", facecolors="none",
                label=f"{muni} (no concom.)",
                **scatter_kw,
            )
        if not concurrent.empty:
            ax.scatter(
                concurrent["hs_max_norm"],
                concurrent["ssh_max_norm"],
                s=80, marker="o",
                label=f"{muni} (concurrent)",
                alpha=0.85,
                **scatter_kw,
            )

    # Diagonal and reference lines
    all_vals = pd.concat([df["hs_max_norm"].dropna(), df["ssh_max_norm"].dropna()])
    vmax = all_vals.max() * 1.05
    ax.axhline(1.0, color="0.7", lw=0.8, ls=":")
    ax.axvline(1.0, color="0.7", lw=0.8, ls=":")

    # Threshold line (normalised threshold ≈ q90 / mean = STYLE marker)
    q = CFG["threshold_quantile"]
    ax.set_xlabel("Hₛ_max / Hₛ_mean", fontsize=STYLE.font_size_axis_label)
    ax.set_ylabel("SSH_max / SSH_mean", fontsize=STYLE.font_size_axis_label)
    ax.set_title(
        f"Normalised maxima per event — filled = concurrent (both > q{int(q*100)})",
        fontsize=STYLE.font_size_title,
    )
    ax.legend(
        fontsize=6, framealpha=STYLE.legend_framealpha, ncol=1,
        bbox_to_anchor=(1.02, 1), loc="upper left", borderaxespad=0,
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    save_fig(fig, "fig_TC_S2_scatter_normalised_hs_ssh", subdir="summary")


# ── Figure S3: concomitance fraction bar chart ───────────────────────────────

def _fig_s3_concomitance_bars(df: pd.DataFrame) -> None:
    """Horizontal bar chart: concurrent fraction per event."""
    df = df.copy().sort_values(["municipality", "date"]).reset_index(drop=True)
    df["event_label"] = df.apply(
        lambda r: f"{r['municipality'][:18]}  {pd.Timestamp(r['date']).strftime('%Y-%m-%d')}",
        axis=1,
    )

    q = CFG["threshold_quantile"]
    fig, ax = plt.subplots(
        figsize=(STYLE.fig_width_double, max(4.0, len(df) * 0.38 + 1.5))
    )

    colors = [STYLE.color_hs if v > 0 else "0.80" for v in df["concurrent_fraction"]]
    ax.barh(
        np.arange(len(df)),
        df["concurrent_fraction"],
        color=colors, alpha=0.85,
    )
    ax.set_yticks(np.arange(len(df)))
    ax.set_yticklabels(df["event_label"], fontsize=8)
    ax.set_xlabel(f"Fraction of days with both Hₛ and SSH > q{int(q*100)}")
    ax.set_title(
        f"Concomitance fraction per event (±{CFG['event_half_window_days']}-day window)",
        fontsize=STYLE.font_size_title,
    )
    ax.axvline(0, color="0.5", lw=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Annotations on bars
    for i, (_, row) in enumerate(df.iterrows()):
        frac = row["concurrent_fraction"]
        if frac > 0.01:
            ax.text(
                frac + 0.005, i, f"{frac:.0%}",
                va="center", fontsize=7, color="black",
            )

    fig.tight_layout()
    save_fig(fig, "fig_TC_S3_concomitance_fraction_per_event", subdir="summary")


# ── Figure S4: heatmap municipality × event ──────────────────────────────────

def _fig_s4_heatmap(df: pd.DataFrame) -> None:
    """Heatmap of concurrent fraction for municipality × event date."""
    pivot = df.pivot_table(
        index="municipality",
        columns="date",
        values="concurrent_fraction",
        aggfunc="first",
    )
    if pivot.empty:
        return

    pivot.columns = [pd.Timestamp(c).strftime("%Y-%m-%d") for c in pivot.columns]

    fig, ax = plt.subplots(
        figsize=(max(STYLE.fig_width_wide, len(pivot.columns) * 0.45 + 3),
                 max(3.0, len(pivot.index) * 0.55 + 1.5))
    )

    im = ax.imshow(
        pivot.values, aspect="auto", cmap="Reds",
        vmin=0, vmax=1.0,
    )

    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=45, ha="right", fontsize=7)
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=8)

    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label(f"Concurrent fraction (both > q{int(CFG['threshold_quantile']*100)})",
                   fontsize=STYLE.font_size_legend)

    ax.set_title(
        "Concomitance heatmap — municipality × event date",
        fontsize=STYLE.font_size_title,
    )

    fig.tight_layout()
    save_fig(fig, "fig_TC_S4_heatmap_concomitance", subdir="summary")


# ── Utilities ─────────────────────────────────────────────────────────────────

def _muni_colormap(municipalities: list[str]) -> dict[str, str]:
    """Assign a distinct colour from a qualitative colormap to each municipality."""
    cmap   = cm.get_cmap("tab10", max(len(municipalities), 1))
    colors = {}
    for i, muni in enumerate(municipalities):
        rgba = cmap(i % 10)
        colors[muni] = f"#{int(rgba[0]*255):02x}{int(rgba[1]*255):02x}{int(rgba[2]*255):02x}"
    return colors


# ── Per-sector figures ────────────────────────────────────────────────────────

def _fig_s1_per_sector(df: pd.DataFrame) -> None:
    """Generate S1 figure (normalised maxima bars) per sector with subplots per municipality."""
    if "coastal_sector" not in df.columns:
        log.warning("  No sector information; skipping per-sector S1 figures.")
        return
    
    sectors = sorted(df["coastal_sector"].dropna().unique())
    
    for sector in sectors:
        sector_df = df[df["coastal_sector"] == sector].copy()
        if sector_df.empty:
            continue
        
        municipalities = sorted(sector_df["municipality"].unique())
        n_munis = len(municipalities)
        
        # Create subplots: one per municipality
        n_cols = min(2, n_munis)
        n_rows = (n_munis + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(
            n_rows, n_cols,
            figsize=(STYLE.fig_width_wide * 0.9, 3.5 * n_rows),
            squeeze=False
        )
        
        q = CFG["threshold_quantile"]
        w = 0.38
        
        for idx, muni in enumerate(municipalities):
            row = idx // n_cols
            col = idx % n_cols
            ax = axes[row, col]
            
            muni_df = sector_df[sector_df["municipality"] == muni].copy()
            muni_df = muni_df.sort_values("date").reset_index(drop=True)
            muni_df["event_label"] = muni_df["date"].apply(
                lambda d: pd.Timestamp(d).strftime('%Y-%m-%d')
            )
            
            x = np.arange(len(muni_df))
            
            ax.bar(x - w/2, muni_df["hs_max_norm"], width=w, 
                   color=STYLE.color_hs, label="Hₛ / mean", alpha=0.85)
            ax.bar(x + w/2, muni_df["ssh_max_norm"], width=w,
                   color=STYLE.color_ssh, label="SSH / mean", alpha=0.85)
            
            ax.axhline(1.0, color="0.5", lw=0.8, ls=":", alpha=0.7)
            ax.set_xticks(x)
            ax.set_xticklabels(muni_df["event_label"], fontsize=7, rotation=45, ha="right")
            ax.set_ylabel("Normalised value", fontsize=9)
            ax.set_title(muni, fontsize=10, fontweight="bold")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.grid(axis="y", alpha=0.3)
            
            if idx == 0:
                ax.legend(fontsize=8, framealpha=0.9, loc="upper left")
        
        # Hide unused subplots
        for idx in range(n_munis, n_rows * n_cols):
            row = idx // n_cols
            col = idx % n_cols
            axes[row, col].axis("off")
        
        sector_slug = sector.lower().replace(" ", "_").replace("-", "_")
        fig.suptitle(
            f"Normalised Hₛ and SSH maxima — {sector} Sector",
            fontsize=STYLE.font_size_title + 1,
            fontweight="bold",
            y=0.998
        )
        fig.tight_layout(rect=[0, 0, 1, 0.99])
        save_fig(fig, f"fig_TC_S1_normalised_maxima_{sector_slug}_sector", subdir="summary")


def _fig_s3_per_sector(df: pd.DataFrame) -> None:
    """Generate S3 figure (concomitance bars) per sector with subplots per municipality."""
    if "coastal_sector" not in df.columns:
        log.warning("  No sector information; skipping per-sector S3 figures.")
        return
    
    sectors = sorted(df["coastal_sector"].dropna().unique())
    q = CFG["threshold_quantile"]
    
    for sector in sectors:
        sector_df = df[df["coastal_sector"] == sector].copy()
        if sector_df.empty:
            continue
        
        municipalities = sorted(sector_df["municipality"].unique())
        n_munis = len(municipalities)
        
        # Create subplots: one per municipality
        n_cols = min(2, n_munis)
        n_rows = (n_munis + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(
            n_rows, n_cols,
            figsize=(STYLE.fig_width_wide * 0.9, 3.0 * n_rows),
            squeeze=False
        )
        
        for idx, muni in enumerate(municipalities):
            row = idx // n_cols
            col = idx % n_cols
            ax = axes[row, col]
            
            muni_df = sector_df[sector_df["municipality"] == muni].copy()
            muni_df = muni_df.sort_values("date").reset_index(drop=True)
            muni_df["event_label"] = muni_df["date"].apply(
                lambda d: pd.Timestamp(d).strftime('%Y-%m-%d')
            )
            
            y = np.arange(len(muni_df))
            colors = [STYLE.color_hs if v > 0 else "0.80" 
                      for v in muni_df["concurrent_fraction"]]
            
            ax.barh(y, muni_df["concurrent_fraction"], color=colors, alpha=0.85)
            ax.set_yticks(y)
            ax.set_yticklabels(muni_df["event_label"], fontsize=7)
            ax.set_xlabel("Concurrent fraction", fontsize=9)
            ax.set_title(muni, fontsize=10, fontweight="bold")
            ax.axvline(0, color="0.5", lw=0.5)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.set_xlim([0, 1.0])
            
            # Annotations
            for i, (_, event_row) in enumerate(muni_df.iterrows()):
                frac = event_row["concurrent_fraction"]
                if frac > 0.01:
                    ax.text(frac + 0.02, i, f"{frac:.0%}", va="center", 
                            fontsize=6, color="black")
        
        # Hide unused subplots
        for idx in range(n_munis, n_rows * n_cols):
            row = idx // n_cols
            col = idx % n_cols
            axes[row, col].axis("off")
        
        sector_slug = sector.lower().replace(" ", "_").replace("-", "_")
        fig.suptitle(
            f"Concomitance Fraction (both > q{int(q*100)}) — {sector} Sector",
            fontsize=STYLE.font_size_title + 1,
            fontweight="bold",
            y=0.998
        )
        fig.tight_layout(rect=[0, 0, 1, 0.99])
        save_fig(fig, f"fig_TC_S3_concomitance_{sector_slug}_sector", subdir="summary")


def _fig_s4_per_sector(df: pd.DataFrame) -> None:
    """Generate S4 figure (heatmap) per sector."""
    if "coastal_sector" not in df.columns:
        log.warning("  No sector information; skipping per-sector S4 figures.")
        return
    
    sectors = sorted(df["coastal_sector"].dropna().unique())
    q = CFG["threshold_quantile"]
    
    for sector in sectors:
        sector_df = df[df["coastal_sector"] == sector].copy()
        if sector_df.empty:
            continue
        
        pivot = sector_df.pivot_table(
            index="municipality",
            columns="date",
            values="concurrent_fraction",
            aggfunc="first",
        )
        if pivot.empty:
            continue
        
        pivot.columns = [pd.Timestamp(c).strftime("%Y-%m-%d") for c in pivot.columns]
        
        fig, ax = plt.subplots(
            figsize=(max(8, len(pivot.columns) * 0.4 + 2),
                     max(3.0, len(pivot.index) * 0.5 + 1))
        )
        
        im = ax.imshow(
            pivot.values, aspect="auto", cmap="Reds",
            vmin=0, vmax=1.0, interpolation="nearest"
        )
        
        ax.set_xticks(np.arange(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns, rotation=45, ha="right", fontsize=7)
        ax.set_yticks(np.arange(len(pivot.index)))
        ax.set_yticklabels(pivot.index, fontsize=9)
        
        cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
        cbar.set_label(f"Concurrent fraction\n(both > q{int(q*100)})",
                       fontsize=9)
        
        ax.set_title(
            f"Concomitance Heatmap — {sector} Sector",
            fontsize=STYLE.font_size_title,
            fontweight="bold"
        )
        
        fig.tight_layout()
        sector_slug = sector.lower().replace(" ", "_").replace("-", "_")
        save_fig(fig, f"fig_TC_S4_heatmap_{sector_slug}_sector", subdir="summary")
