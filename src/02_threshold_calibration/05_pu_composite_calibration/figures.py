"""
Visualisation for Step 2e — PU Composite Calibration.

Generates heatmaps of the composite score surface and comparison figures
between the Step 2d (CSI) and Step 2e (PU) optimal threshold pairs.

Figure inventory
----------------
fig_TC5_H1_score_heatmap.png        — Composite Score(θ) across 9×9 threshold grid
fig_TC5_H2_recall_heatmap.png       — R_pos(θ) across 9×9 threshold grid
fig_TC5_H3_burden_heatmap.png       — B(θ) across 9×9 threshold grid
fig_TC5_H4_fsoft_heatmap.png        — F_soft(θ)/P across 9×9 threshold grid
fig_TC5_S1_csi_vs_pu.png            — CSI optimal pair vs PU optimal pair comparison
fig_TC5_S2_sensitivity_weights.png  — Weight sensitivity: optimal pair stability
fig_TC5_S3_sensitivity_b_target.png — B_target sensitivity: Score vs B_target
fig_TC5_A1_qi_distribution.png      — Distribution of q_i values across all episodes
fig_TC5_A2_city_source_audit.png    — Municipality source audit (expanded/legacy/both)
                                       coloured by database origin on SC coast map
"""
from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

# ── Shared colour maps ─────────────────────────────────────────────────────────
_SCORE_CMAP  = "RdYlGn"   # diverging: red=bad, green=good
_METRIC_CMAP = "viridis"
_BURDEN_CMAP = "YlOrRd"   # low burden (yellow) → high burden (red)


# ── Internal helper: 9×9 pivot for heatmaps ──────────────────────────────────

def _pivot(df: pd.DataFrame, value_col: str) -> tuple[pd.DataFrame, list[float], list[float]]:
    """Pivot a metrics DataFrame into a matrix for heatmap plotting.

    Returns
    -------
    matrix : DataFrame (hs_pct rows × ssh_pct columns)
    hs_labels : list of str
    ssh_labels : list of str
    """
    pivot = df.pivot(index="thr_hs_pct", columns="thr_ssh_pct", values=value_col)
    # Sort ascending (q50 at top → q90 at bottom)
    pivot = pivot.sort_index(ascending=True)
    hs_labels  = [f"q{round(v*100):.0f}" for v in pivot.index]
    ssh_labels = [f"q{round(v*100):.0f}" for v in pivot.columns]
    return pivot, hs_labels, ssh_labels


def _mark_optimal(ax, df: pd.DataFrame, optimal: dict, color: str = "black") -> None:
    """Draw a rectangle around the optimal cell in a heatmap axis."""
    hs_levels  = sorted(df["thr_hs_pct"].unique())
    ssh_levels = sorted(df["thr_ssh_pct"].unique())
    hs_idx  = hs_levels.index(optimal["thr_hs_pct"])
    ssh_idx = ssh_levels.index(optimal["thr_ssh_pct"])
    rect = plt.Rectangle(
        (ssh_idx - 0.5, hs_idx - 0.5), 1, 1,
        linewidth=2.5, edgecolor=color, facecolor="none",
    )
    ax.add_patch(rect)


# ── Heatmap: generic single metric ───────────────────────────────────────────

def plot_metric_heatmap(
    df: pd.DataFrame,
    metric: str,
    title: str,
    cmap: str,
    output_path: Path,
    optimal: dict | None = None,
    fmt: str = ".3f",
    vmin: float | None = None,
    vmax: float | None = None,
) -> None:
    """Plot a 9×9 heatmap for one metric across the threshold grid.

    Parameters
    ----------
    df : scores DataFrame from compute_pu_scores
    metric : column name to plot
    title : figure title
    cmap : matplotlib colormap name
    output_path : where to save the figure
    optimal : optional dict with thr_hs_pct and thr_ssh_pct to mark
    fmt : cell annotation format string
    vmin, vmax : colour scale limits (None = data range)
    """
    matrix, hs_labels, ssh_labels = _pivot(df, metric)

    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(
        matrix.values,
        cmap=cmap,
        aspect="auto",
        vmin=vmin if vmin is not None else matrix.values.min(),
        vmax=vmax if vmax is not None else matrix.values.max(),
    )

    # Axis ticks
    ax.set_xticks(range(len(ssh_labels)))
    ax.set_yticks(range(len(hs_labels)))
    ax.set_xticklabels(ssh_labels, fontsize=9)
    ax.set_yticklabels(hs_labels, fontsize=9)
    ax.set_xlabel("SSH_total threshold", fontsize=11)
    ax.set_ylabel("Hₛ threshold", fontsize=11)
    ax.set_title(title, fontsize=12, pad=8)

    # Annotate cells — use luminance to pick readable text color for any cmap
    _vmin = vmin if vmin is not None else float(np.nanmin(matrix.values))
    _vmax = vmax if vmax is not None else float(np.nanmax(matrix.values))
    _norm = plt.Normalize(vmin=_vmin, vmax=_vmax)
    _cmap_obj = plt.get_cmap(cmap)
    for i in range(len(hs_labels)):
        for j in range(len(ssh_labels)):
            val = matrix.values[i, j]
            txt = f"{val:{fmt}}" if not np.isnan(val) else "—"
            rgba = _cmap_obj(_norm(val))
            # Perceived luminance (ITU-R BT.601)
            lum = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
            ax.text(j, i, txt, ha="center", va="center", fontsize=7,
                    color="black" if lum > 0.55 else "white")

    # Mark optimal pair
    if optimal is not None:
        _mark_optimal(ax, df, optimal)

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    log.info("Saved: %s", output_path.name)


# ── Composite heatmaps ────────────────────────────────────────────────────────

def plot_score_heatmap(
    df_scores: pd.DataFrame,
    optimal: dict,
    output_path: Path,
) -> None:
    """Composite Score(θ) heatmap with optimal pair marked."""
    plot_metric_heatmap(
        df=df_scores,
        metric="Score",
        title="PU Composite Score(θ)\n(higher = better)",
        cmap=_SCORE_CMAP,
        output_path=output_path,
        optimal=optimal,
        fmt=".4f",
    )


def plot_recall_heatmap(
    df_scores: pd.DataFrame,
    optimal: dict,
    output_path: Path,
) -> None:
    """R_pos(θ) heatmap."""
    plot_metric_heatmap(
        df=df_scores,
        metric="R_pos",
        title="Positive Recall R_pos(θ) = H / P\n(fraction of confirmed events captured)",
        cmap=_METRIC_CMAP,
        output_path=output_path,
        optimal=optimal,
        fmt=".3f",
        vmin=0.0, vmax=1.0,
    )


def plot_burden_heatmap(
    df_scores: pd.DataFrame,
    optimal: dict,
    output_path: Path,
) -> None:
    """Annual burden B(θ) heatmap."""
    plot_metric_heatmap(
        df=df_scores,
        metric="B",
        title="Annual Burden B(θ) = min(1, (H+U)/(Y·B_target))\n(lower = fewer detections)",
        cmap=_BURDEN_CMAP,
        output_path=output_path,
        optimal=optimal,
        fmt=".3f",
        vmin=0.0, vmax=1.0,
    )


def plot_fsoft_heatmap(
    df_scores: pd.DataFrame,
    optimal: dict,
    P: int,
    output_path: Path,
) -> None:
    """F_soft(θ)/P heatmap."""
    df = df_scores.copy()
    df["F_soft_norm"] = df["F_soft"] / max(P, 1)
    plot_metric_heatmap(
        df=df,
        metric="F_soft_norm",
        title=f"Normalised Soft Penalty F_soft(θ)/P  (P={P})\n(lower = more plausible unmatched episodes)",
        cmap=_BURDEN_CMAP,
        output_path=output_path,
        optimal=optimal,
        fmt=".3f",
    )


# ── CSI vs PU comparison bar chart ────────────────────────────────────────────

def plot_csi_vs_pu_comparison(
    optimal_pu: dict,
    csi_optimal_path: Path,
    output_path: Path,
) -> None:
    """Side-by-side bar comparison of Step 2d CSI-optimal and Step 2e PU-optimal pairs.

    Shows Hₛ and SSH_total threshold percentiles for each method.
    """
    # Load Step 2d results if available
    csi_hs = csi_ssh = None
    if csi_optimal_path.exists():
        try:
            row = pd.read_csv(csi_optimal_path).iloc[0]
            csi_hs  = float(row.get("thr_hs_pct", 0)) * 100
            csi_ssh = float(row.get("thr_ssh_pct", 0)) * 100
        except Exception:
            pass

    pu_hs  = float(optimal_pu.get("thr_hs_pct", 0)) * 100
    pu_ssh = float(optimal_pu.get("thr_ssh_pct", 0)) * 100

    fig, ax = plt.subplots(figsize=(7, 4))

    x = np.array([0, 1])
    width = 0.35

    labels = ["Hₛ threshold", "SSH_total threshold"]

    if csi_hs is not None:
        ax.bar(x - width/2, [csi_hs, csi_ssh], width, label="Step 2d (CSI)",
               color="#d62728", alpha=0.8)

    ax.bar(x + width/2, [pu_hs, pu_ssh], width, label="Step 2e (PU)",
           color="#2ca02c", alpha=0.8)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel("Threshold percentile (%)", fontsize=11)
    ax.set_ylim(40, 100)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("q%.0f"))
    ax.set_title("Optimal Threshold Pair: CSI (Step 2d) vs PU (Step 2e)", fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3)

    # Annotate with R_pos for PU
    r_pos = optimal_pu.get("R_pos", None)
    if r_pos is not None:
        ax.text(
            0.98, 0.05,
            f"PU: R_pos={r_pos:.2f}  B={optimal_pu.get('B', '—'):.2f}",
            transform=ax.transAxes, ha="right", fontsize=9,
            bbox=dict(facecolor="white", edgecolor="gray", boxstyle="round,pad=0.3"),
        )

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    log.info("Saved: %s", output_path.name)


# ── Sensitivity summary plot ───────────────────────────────────────────────────

def plot_sensitivity_weights(
    df_sens: pd.DataFrame,
    output_path: Path,
) -> None:
    """Visualise weight sensitivity: optimal pair for each weight preset."""
    if df_sens.empty:
        return

    fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True)

    for i, (col, label, ax) in enumerate(zip(
        ["thr_hs_pct", "thr_ssh_pct"],
        ["Hₛ threshold percentile", "SSH threshold percentile"],
        axes,
    )):
        vals = df_sens[col] * 100
        ax.barh(df_sens["label"], vals, color="#1f77b4", alpha=0.8)
        ax.set_xlabel(label)
        ax.set_xlim(45, 95)
        ax.axvline(90, color="gray", linestyle="--", linewidth=1, label="q90 (CSI opt.)")
        ax.legend(fontsize=8)
        ax.grid(axis="x", alpha=0.3)

    axes[0].set_ylabel("Weight preset", fontsize=11)
    fig.suptitle("Weight Sensitivity: Optimal Threshold Pair", fontsize=12)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    log.info("Saved: %s", output_path.name)


def _resolve_b_target_x_col(df: pd.DataFrame) -> str:
    """Resolve the per-municipality B_target column name from a sensitivity table.

    Checks for known column names in priority order (newest schema first) and
    returns the first one found. Raises KeyError with a clear diagnostic message
    if none of the known names are present.

    Schema history
    --------------
    Current  : b_target_per_muni          (standardised name, explicit units)
    Previous : b_target_per_municipality  (old name before schema standardisation)
    Legacy   : b_target                   (pre-2025 name, dropped n_municipalities)

    Parameters
    ----------
    df : B_target sensitivity DataFrame loaded from tab_TC5_sensitivity_b_target.csv

    Returns
    -------
    str — the column name to use as the x-axis
    """
    candidates = ["b_target_per_muni", "b_target_per_municipality", "b_target"]
    for col in candidates:
        if col in df.columns:
            if col != "b_target_per_muni":
                log.warning(
                    "B_target sensitivity table uses legacy column '%s'. "
                    "Current schema uses 'b_target_per_muni'. "
                    "Regenerate tab_TC5_sensitivity_b_target.csv to update.",
                    col,
                )
            return col

    raise KeyError(
        "B_target sensitivity table is missing the per-municipality burden column. "
        f"Expected one of {candidates}. "
        f"Available columns: {list(df.columns)}. "
        "Regenerate tab_TC5_sensitivity_b_target.csv by running:\n"
        "  python src/02_threshold_calibration/05_pu_composite_calibration/main.py --sensitivity"
    )


def _resolve_threshold_pct_cols(df: pd.DataFrame) -> tuple[str, str]:
    """Resolve the optimal-pair percentile column names from a sensitivity table.

    Checks for `thr_hs_pct`/`thr_ssh_pct` (fractional, 0.7=q70) and
    `hs_percentile`/`ssh_percentile` (integer, 70=q70). Returns the pair found,
    applying a /100 scale factor flag.

    Returns
    -------
    (hs_col, ssh_col) — column names to use for the optimal-pair x-axis plots.
                        Values in these columns are already in % (integer).
    """
    if "hs_percentile" in df.columns and "ssh_percentile" in df.columns:
        return "hs_percentile", "ssh_percentile"
    if "thr_hs_pct" in df.columns and "thr_ssh_pct" in df.columns:
        log.warning(
            "B_target sensitivity table uses legacy fractional columns "
            "'thr_hs_pct'/'thr_ssh_pct'. "
            "Current schema uses integer 'hs_percentile'/'ssh_percentile'. "
            "Regenerate tab_TC5_sensitivity_b_target.csv to update."
        )
        return "thr_hs_pct", "thr_ssh_pct"
    raise KeyError(
        "B_target sensitivity table is missing optimal-pair percentile columns. "
        f"Available columns: {list(df.columns)}."
    )


def plot_sensitivity_b_target(
    df_sens: pd.DataFrame,
    output_path: Path,
) -> None:
    """Plot composite Score and optimal threshold pair vs. per-municipality B_target.

    X-axis: b_target_per_muni (episodes/year/municipality)
    Left Y: composite Score
    Right Y: optimal Hₛ and SSH threshold percentiles

    Backward-compatible: resolves column names from current and legacy schemas.
    Raises KeyError with diagnostics if required columns are absent.
    """
    if df_sens.empty:
        return

    x_col = _resolve_b_target_x_col(df_sens)
    hs_col, ssh_col = _resolve_threshold_pct_cols(df_sens)

    # Scale: hs_percentile/ssh_percentile are already integer %; thr_hs/ssh_pct are fractions.
    pct_scale = 1 if hs_col == "hs_percentile" else 100

    x_vals = df_sens[x_col]

    # Annotate x-axis label with total if n_municipalities is available
    if "n_municipalities" in df_sens.columns:
        n_munis = int(df_sens["n_municipalities"].iloc[0])
        xlabel = f"Annual burden target per municipality (ep/yr/muni)\n[n={n_munis} municipalities; total = value × {n_munis}]"
    else:
        xlabel = "Annual burden target per municipality (ep/yr/muni)"

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(x_vals, df_sens["Score"], "o-", color="#2ca02c", label="Composite Score")
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel("Composite Score", fontsize=11)
    ax.set_title("Composite Score vs. Per-Municipality Annual Burden Target", fontsize=12)
    ax.grid(alpha=0.3)

    # Convert to integer percentile if using legacy fractional columns
    hs_vals  = df_sens[hs_col]  if pct_scale == 1 else df_sens[hs_col]  * 100
    ssh_vals = df_sens[ssh_col] if pct_scale == 1 else df_sens[ssh_col] * 100

    ax2 = ax.twinx()
    ax2.plot(x_vals, hs_vals,  "s--", color="#d62728", alpha=0.7, label="Hₛ threshold (q%)")
    ax2.plot(x_vals, ssh_vals, "^--", color="#ff7f0e", alpha=0.7, label="SSH threshold (q%)")
    ax2.set_ylabel("Optimal threshold percentile (%)", fontsize=10)
    ax2.set_ylim(40, 100)

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, fontsize=9, loc="lower right")

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    log.info("Saved: %s", output_path.name)


# ── q_i distribution ──────────────────────────────────────────────────────────

def plot_qi_distribution(
    audit_df: pd.DataFrame,
    output_path: Path,
    thr_hs_pct: float | None = None,
    thr_ssh_pct: float | None = None,
) -> None:
    """Histogram of q_i values for all unmatched episodes.

    If thr_hs_pct and thr_ssh_pct are given, shows distribution for the
    optimal pair only. Otherwise uses all episodes from all pairs.
    """
    if audit_df.empty:
        log.warning("Audit table is empty — skipping q_i distribution plot.")
        return

    if thr_hs_pct is not None and thr_ssh_pct is not None:
        subset = audit_df[
            (audit_df["thr_hs_pct"] == thr_hs_pct)
            & (audit_df["thr_ssh_pct"] == thr_ssh_pct)
        ]
        title_suffix = f" (hs=q{round(thr_hs_pct*100)}, ssh=q{round(thr_ssh_pct*100)})"
    else:
        subset = audit_df
        title_suffix = " (all pairs)"

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(subset["q_i"], bins=20, range=(0, 1), color="#1f77b4", alpha=0.75, edgecolor="white")
    ax.axvline(subset["q_i"].mean(),  color="red",    linestyle="--", label=f"Mean={subset['q_i'].mean():.3f}")
    ax.axvline(subset["q_i"].median(), color="orange", linestyle=":",  label=f"Median={subset['q_i'].median():.3f}")
    ax.set_xlabel("Confidence weight qᵢ", fontsize=11)
    ax.set_ylabel("Count of unmatched episodes", fontsize=11)
    ax.set_title(f"Distribution of qᵢ weights{title_suffix}", fontsize=12)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    log.info("Saved: %s", output_path.name)


# ── City/database source audit figure ────────────────────────────────────────

def plot_city_source_audit(
    events_provenance: "pd.DataFrame",
    grid_ref_path: "Path",
    output_path: "Path",
) -> None:
    """Scatter plot of combined-event municipalities on the SC coast, coloured by source.

    Shows which municipalities come from the expanded database only, the legacy
    database only, or both — as a geographic audit of the combined positive set.
    Grid point positions are overlaid as circles; municipality centroids as stars.

    Parameters
    ----------
    events_provenance : DataFrame from load_combined_events() — columns
        [municipality, date, source, near_match_flag].
    grid_ref_path : Path to municipality_grid_ref.csv.
    output_path : where to save the figure.
    """
    from pathlib import Path as _Path

    grid_ref_path = _Path(grid_ref_path)
    if not grid_ref_path.exists():
        log.warning(
            "municipality_grid_ref.csv not found at %s — skipping city audit figure.",
            grid_ref_path,
        )
        return

    grid_ref = pd.read_csv(grid_ref_path)

    # Unique municipality → source mapping from provenance
    muni_source = (
        events_provenance.groupby("municipality")["source"]
        .agg(lambda s: "both" if "both" in s.values else
             ("expanded" if (s == "expanded").any() else "legacy"))
        .reset_index()
        .rename(columns={"source": "db_source"})
    )
    near_muni = set(
        events_provenance.loc[events_provenance["near_match_flag"], "municipality"]
    )

    # Merge with grid_ref
    merged = grid_ref.merge(muni_source, on="municipality", how="outer")
    merged["db_source"] = merged["db_source"].fillna("legacy")  # legacy-only if in grid_ref but not provenance

    source_style = {
        "expanded": {"color": "#2ca02c", "marker": "^", "label": "Expanded only (14 cities)"},
        "legacy":   {"color": "#1f77b4", "marker": "s", "label": "Legacy only (13 cities)"},
        "both":     {"color": "#d62728", "marker": "o", "label": "Both databases (9+1 cities)"},
    }

    fig, ax = plt.subplots(figsize=(5, 9))

    for src, style in source_style.items():
        subset = merged[merged["db_source"] == src]
        if subset.empty:
            continue
        ax.scatter(
            subset["muni_lon"], subset["muni_lat"],
            marker=style["marker"], color=style["color"], s=60,
            zorder=5, label=style["label"], alpha=0.85, edgecolors="k", linewidths=0.4,
        )
        # Overlay grid points as smaller unfilled circles
        coord_cols = [c for c in ["grid_lat", "grid_lon"] if c in subset.columns]
        grid_sub = subset.dropna(subset=coord_cols) if coord_cols else subset.iloc[0:0]
        if not grid_sub.empty:
            ax.scatter(
                grid_sub["grid_lon"], grid_sub["grid_lat"],
                marker="o", facecolor="none", edgecolor=style["color"],
                s=90, zorder=4, linewidths=1.2,
            )

    # Label municipalities
    for _, row in merged.iterrows():
        if pd.isna(row.get("muni_lat")):
            continue
        nm_flag = row["municipality"] in near_muni
        ax.annotate(
            ("★ " if nm_flag else "") + row["municipality"],
            xy=(row["muni_lon"], row["muni_lat"]),
            xytext=(4, 2), textcoords="offset points",
            fontsize=5.5, color="black",
        )

    ax.set_xlabel("Longitude (°W)", fontsize=10)
    ax.set_ylabel("Latitude (°S)", fontsize=10)
    ax.set_title(
        "TC5-A2 — Combined Positive-Event Set: Municipality Sources\n"
        "Stars (★) = near-match cities (±3 d cross-database)",
        fontsize=10, pad=6,
    )
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(alpha=0.25)
    ax.invert_xaxis()  # west on left

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    log.info("Saved: %s", output_path.name)


# ── Main entry point ──────────────────────────────────────────────────────────

def run_all_figures(
    df_scores: pd.DataFrame,
    df_ranked: pd.DataFrame,
    optimal: dict,
    audit_df: pd.DataFrame,
    cfg: dict,
    events_provenance: "pd.DataFrame | None" = None,
) -> None:
    """Generate all Step 2e figures and save to cfg["fig_summary_dir"].

    Parameters
    ----------
    events_provenance : optional DataFrame from load_combined_events() provenance.
        When provided, generates the city/database source audit figure (TC5-A2).
        Loaded from tab_TC5_event_provenance.csv if not passed directly.
    """
    fig_dir     = Path(cfg["fig_dir"])
    summary_dir = Path(cfg["fig_summary_dir"])
    tab_dir     = Path(cfg["tab_dir"])
    fig_dir.mkdir(parents=True, exist_ok=True)
    summary_dir.mkdir(parents=True, exist_ok=True)

    P = int(df_scores["H"].max() + df_scores["M"].max())  # evaluable positive events

    # ── Score heatmaps ─────────────────────────────────────────────────────────
    plot_score_heatmap(
        df_scores, optimal,
        summary_dir / "fig_TC5_H1_score_heatmap.png",
    )
    plot_recall_heatmap(
        df_scores, optimal,
        summary_dir / "fig_TC5_H2_recall_heatmap.png",
    )
    plot_burden_heatmap(
        df_scores, optimal,
        summary_dir / "fig_TC5_H3_burden_heatmap.png",
    )
    plot_fsoft_heatmap(
        df_scores, optimal, P,
        summary_dir / "fig_TC5_H4_fsoft_heatmap.png",
    )

    # ── CSI vs PU comparison ───────────────────────────────────────────────────
    csi_opt_path = Path(cfg.get("optimal_pair_file", "nonexistent.csv"))
    plot_csi_vs_pu_comparison(
        optimal, csi_opt_path,
        summary_dir / "fig_TC5_S1_csi_vs_pu.png",
    )

    # ── Sensitivity figures ────────────────────────────────────────────────────
    w_path = tab_dir / "tab_TC5_sensitivity_weights.csv"
    b_path = tab_dir / "tab_TC5_sensitivity_b_target.csv"

    if w_path.exists():
        df_w = pd.read_csv(w_path)
        plot_sensitivity_weights(df_w, summary_dir / "fig_TC5_S2_sensitivity_weights.png")

    if b_path.exists():
        df_b = pd.read_csv(b_path)
        plot_sensitivity_b_target(df_b, summary_dir / "fig_TC5_S3_sensitivity_b_target.png")

    # ── q_i distribution at optimal pair ─────────────────────────────────────
    if not audit_df.empty:
        plot_qi_distribution(
            audit_df,
            summary_dir / "fig_TC5_A1_qi_distribution.png",
            thr_hs_pct=optimal.get("thr_hs_pct"),
            thr_ssh_pct=optimal.get("thr_ssh_pct"),
        )

    # ── City/database source audit ────────────────────────────────────────────
    # Attempt to load provenance from disk if not passed in-memory
    _provenance = events_provenance
    if _provenance is None:
        _prov_path = tab_dir / "tab_TC5_event_provenance.csv"
        if _prov_path.exists():
            _provenance = pd.read_csv(_prov_path, parse_dates=["date"])

    if _provenance is not None:
        _grid_ref_path = Path(cfg.get(
            "municipality_grid_ref",
            Path(cfg["output_root"]).parents[0] / "preprocessing/municipality_grid_ref.csv",
        ))
        plot_city_source_audit(
            _provenance, _grid_ref_path,
            summary_dir / "fig_TC5_A2_city_source_audit.png",
        )

    log.info("All Step 2e figures saved to: %s", summary_dir)
