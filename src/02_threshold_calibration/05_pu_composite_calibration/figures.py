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
# Convention (applied consistently across ALL Step 2e heatmaps):
#   lighter colour = better result  /  darker colour = worse result
#
# Maximize metrics (Score, Recall): higher value = better → use reversed
#   sequential colourmap so the HIGH end is LIGHT (yellow/white) and the
#   LOW end is DARK (green).  YlGn_r: 0 → dark green (bad), 1 → yellow (good).
#
# Minimize metrics (Burden B, Soft penalty F_soft/P): lower value = better →
#   use forward sequential colourmap so the LOW end is LIGHT (yellow) and the
#   HIGH end is DARK (red).  YlOrRd: 0 → yellow (good), 1 → dark red (bad).
#
# This ensures that a quick visual scan always associates "lighter cell" with
# "better result" regardless of which metric is being displayed.
_SCORE_CMAP  = "YlGn_r"   # reversed yellow→green: low score=dark green, high score=yellow (light)
_METRIC_CMAP = "YlGn_r"   # same convention for recall (maximize)
_BURDEN_CMAP = "YlOrRd"   # forward yellow→red: low burden=yellow (light/good), high=dark red (bad)


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
    """Map of combined-event municipalities on the SC coast, coloured by database source.

    Shows which municipalities come from the expanded database only, the legacy
    database only, or both — as a geographic audit of the combined positive set.
    Uses cartopy for a properly georeferenced map with coastline and land/sea features.
    Grid point positions are overlaid as circles; municipality centroids as markers.

    Falls back to a plain matplotlib scatter if cartopy is not installed, with a warning.

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

    # Merge with grid_ref (outer so municipalities without grid points appear too)
    merged = grid_ref.merge(muni_source, on="municipality", how="outer")
    merged["db_source"] = merged["db_source"].fillna("legacy")

    source_style = {
        "expanded": {"color": "#2ca02c", "marker": "^", "zorder": 6,
                     "label": "Expanded only"},
        "legacy":   {"color": "#1f77b4", "marker": "s", "zorder": 5,
                     "label": "Legacy only"},
        "both":     {"color": "#d62728", "marker": "o", "zorder": 7,
                     "label": "Both databases"},
    }

    # Determine map extent from data
    lons = merged["muni_lon"].dropna()
    lats = merged["muni_lat"].dropna()
    if lons.empty or lats.empty:
        log.warning("No valid municipality coordinates — skipping city audit figure.")
        return
    lon_buf, lat_buf = 0.6, 0.4
    lon_min = float(lons.min()) - lon_buf
    lon_max = float(lons.max()) + lon_buf
    lat_min = float(lats.min()) - lat_buf
    lat_max = float(lats.max()) + lat_buf

    # ── Try cartopy for a geographically proper map ───────────────────────────
    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
        _use_cartopy = True
    except ImportError:
        log.warning(
            "cartopy not available — TC5-A2 will be a plain scatter plot without "
            "coastline. Install cartopy (conda install -c conda-forge cartopy) for a "
            "publication-quality geographic figure."
        )
        _use_cartopy = False

    if _use_cartopy:
        proj = ccrs.PlateCarree()
        fig, ax = plt.subplots(
            figsize=(5, 10),
            subplot_kw={"projection": proj},
        )
        ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=proj)

        # ── Geographic background ─────────────────────────────────────────────
        ax.add_feature(cfeature.LAND,      facecolor="#f5f0e8", zorder=0)
        ax.add_feature(cfeature.OCEAN,     facecolor="#d6eaf8", zorder=0)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8,  zorder=1, color="#444444")
        ax.add_feature(cfeature.BORDERS,   linewidth=0.5,  zorder=1, linestyle="--",
                       edgecolor="#888888")
        ax.add_feature(cfeature.RIVERS,    linewidth=0.3,  zorder=1, alpha=0.4,
                       edgecolor="#3385cc")
        gl = ax.gridlines(
            draw_labels=True, linewidth=0.35, color="gray", alpha=0.55,
            xlocs=np.arange(lon_min, lon_max + 0.5, 1.0),
            ylocs=np.arange(lat_min, lat_max + 0.5, 1.0),
            x_inline=False, y_inline=False,
        )
        gl.top_labels   = False
        gl.right_labels = False
        gl.xlabel_style = {"fontsize": 7}
        gl.ylabel_style = {"fontsize": 7}

        def _scatter(lons_, lats_, **kw):
            ax.scatter(lons_, lats_, transform=proj, **kw)

        def _annotate(lon_, lat_, text, **kw):
            ax.annotate(text, xy=(lon_, lat_), xycoords=proj._as_mpl_transform(ax),
                        **kw)

    else:
        fig, ax = plt.subplots(figsize=(5, 9))
        ax.set_xlim(lon_max + 0.1, lon_min - 0.1)  # west on left
        ax.set_ylim(lat_min - 0.1, lat_max + 0.1)
        ax.set_xlabel("Longitude (°W)", fontsize=9)
        ax.set_ylabel("Latitude (°S)", fontsize=9)
        ax.grid(alpha=0.25)

        def _scatter(lons_, lats_, **kw):
            ax.scatter(lons_, lats_, **kw)

        def _annotate(lon_, lat_, text, **kw):
            ax.annotate(text, xy=(lon_, lat_), **kw)

    # ── Plot municipalities coloured by source ────────────────────────────────
    for src, style in source_style.items():
        subset = merged[merged["db_source"] == src].dropna(subset=["muni_lon", "muni_lat"])
        if subset.empty:
            continue

        # Count for legend label
        n = len(subset["municipality"].unique())
        label = f"{style['label']} ({n})"

        _scatter(
            subset["muni_lon"].values, subset["muni_lat"].values,
            marker=style["marker"], color=style["color"], s=55, zorder=style["zorder"],
            label=label, alpha=0.88, edgecolors="k", linewidths=0.5,
        )

        # Overlay corresponding grid points as open circles
        gp = subset.dropna(subset=["grid_lon", "grid_lat"]) \
            if "grid_lon" in subset.columns and "grid_lat" in subset.columns \
            else subset.iloc[0:0]
        if not gp.empty:
            _scatter(
                gp["grid_lon"].values, gp["grid_lat"].values,
                marker="o", facecolor="none", edgecolor=style["color"],
                s=100, zorder=style["zorder"] - 1, linewidths=1.3,
            )
            # Thin connector lines between municipality and grid point
            for _, row in gp.iterrows():
                if _use_cartopy:
                    import cartopy.crs as _ccrs_local
                    ax.plot(
                        [row["muni_lon"], row["grid_lon"]],
                        [row["muni_lat"], row["grid_lat"]],
                        color=style["color"], lw=0.5, alpha=0.4,
                        transform=_ccrs_local.PlateCarree(), zorder=2,
                    )
                else:
                    ax.plot(
                        [row["muni_lon"], row["grid_lon"]],
                        [row["muni_lat"], row["grid_lat"]],
                        color=style["color"], lw=0.5, alpha=0.4, zorder=2,
                    )

    # ── Municipality labels ───────────────────────────────────────────────────
    for _, row in merged.dropna(subset=["muni_lon", "muni_lat"]).iterrows():
        nm_flag = row["municipality"] in near_muni
        text = ("★ " if nm_flag else "") + row["municipality"]
        _annotate(
            float(row["muni_lon"]), float(row["muni_lat"]), text,
            xytext=(4, 2), textcoords="offset points",
            fontsize=5.2, color="black",
        )

    ax.set_title(
        "TC5-A2 — Combined Positive-Event Set: Municipality Sources\n"
        "Markers: ▲ expanded only | ■ legacy only | ● both\n"
        "Open circles = grid points  ·  ★ = near-match cities (±3 d)",
        fontsize=9, pad=6,
    )
    ax.legend(fontsize=8, loc="lower left" if _use_cartopy else "lower right",
              framealpha=0.9)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    log.info("Saved: %s", output_path.name)


# ── Event-level capture scatter (TC5-E1) ─────────────────────────────────────

def plot_event_capture_scatter(
    event_status_df: pd.DataFrame,
    optimal: dict,
    output_path: Path,
) -> None:
    """Scatter of peak Hₛ vs peak SSH_total within the causal window for each event.

    Each point represents one confirmed positive event from the combined event set.
    X = max Hₛ in [D-2 … D+1]; Y = max SSH_total in the same window.
    Filled markers = captured (HIT) at the PU-optimal threshold pair.
    Open markers   = missed at the optimal pair.
    Colour encodes event source: green=expanded, blue=legacy, red=both.

    Dashed reference lines show the median local threshold across all events
    (because thresholds are computed locally, individual thresholds vary).
    A light green shading marks the "above-both-thresholds" zone.

    Parameters
    ----------
    event_status_df : DataFrame from scoring.get_event_capture_status().
        Required columns: peak_hs_causal, peak_ssh_causal, captured, source,
        municipality, date, thr_hs, thr_ssh.
    optimal : dict with thr_hs_pct, thr_ssh_pct, H, M (and optionally R_pos, Score).
    output_path : where to save the figure.
    """
    from matplotlib.lines import Line2D

    df = event_status_df.dropna(subset=["peak_hs_causal"])
    if df.empty:
        log.warning("No valid peak Hs values — skipping TC5-E1 event capture scatter.")
        return

    ssh_available = df["peak_ssh_causal"].notna().any()

    opt_hs_pct  = float(optimal.get("thr_hs_pct", 0.90))
    opt_ssh_pct = float(optimal.get("thr_ssh_pct", 0.90))

    # Source → display properties (consistent with TC5-A2)
    source_style = {
        "expanded": {"color": "#2ca02c", "label": "Expanded"},
        "legacy":   {"color": "#1f77b4", "label": "Legacy"},
        "both":     {"color": "#d62728", "label": "Both databases"},
        "unknown":  {"color": "#999999", "label": "Unknown"},
    }

    if ssh_available:
        # ── Full 2-D scatter: Hs vs SSH_total ────────────────────────────────
        df2 = df.dropna(subset=["peak_ssh_causal"])
        H = int(df2["captured"].sum())
        M = len(df2) - H

        median_thr_hs  = df2["thr_hs"].median()
        median_thr_ssh = df2["thr_ssh"].median()

        fig, ax = plt.subplots(figsize=(8, 6))

        xlim_hi = df2["peak_hs_causal"].max()  * 1.10
        ylim_hi = df2["peak_ssh_causal"].max() * 1.10
        if not (np.isnan(median_thr_hs) or np.isnan(median_thr_ssh)):
            ax.fill_betweenx(
                [median_thr_ssh, ylim_hi],
                median_thr_hs, xlim_hi,
                color="#d0f0c0", alpha=0.20, zorder=0,
            )

        if not np.isnan(median_thr_hs):
            ax.axvline(
                median_thr_hs, color="dimgray", ls="--", lw=0.9, alpha=0.75, zorder=1,
                label=f"Median Hₛ q{round(opt_hs_pct*100)} = {median_thr_hs:.2f} m",
            )
        if not np.isnan(median_thr_ssh):
            ax.axhline(
                median_thr_ssh, color="dimgray", ls=":", lw=0.9, alpha=0.75, zorder=1,
                label=f"Median SSH_total q{round(opt_ssh_pct*100)} = {median_thr_ssh:.2f} m",
            )

        for src, style in source_style.items():
            df_s = df2[df2["source"] == src]
            if df_s.empty:
                continue
            miss = df_s[~df_s["captured"]]
            hit  = df_s[ df_s["captured"]]
            if not miss.empty:
                ax.scatter(
                    miss["peak_hs_causal"], miss["peak_ssh_causal"],
                    facecolors="none", edgecolors=style["color"], linewidths=1.6,
                    s=65, zorder=2,
                )
            if not hit.empty:
                ax.scatter(
                    hit["peak_hs_causal"], hit["peak_ssh_causal"],
                    facecolors=style["color"], edgecolors=style["color"], linewidths=0.7,
                    s=65, zorder=3,
                )

        src_handles = [
            Line2D([0], [0], marker="o", linestyle="none",
                   markerfacecolor=s["color"], markeredgecolor=s["color"],
                   markersize=7, label=s["label"])
            for src, s in source_style.items()
            if src in df2["source"].values
        ]
        marker_handles = [
            Line2D([0], [0], marker="o", linestyle="none",
                   markerfacecolor="dimgray", markeredgecolor="dimgray",
                   markersize=8, label="Captured ● (filled)"),
            Line2D([0], [0], marker="o", linestyle="none",
                   markerfacecolor="none", markeredgecolor="dimgray",
                   markersize=8, label="Missed ○ (open)"),
        ]
        first_legend = ax.legend(
            handles=src_handles, title="Source", fontsize=8,
            loc="upper left", framealpha=0.85,
        )
        ax.add_artist(first_legend)
        ax.legend(handles=marker_handles, fontsize=8, loc="lower right", framealpha=0.85)

        ax.set_xlabel("Peak Hₛ in causal window [D-2 … D+1] (m)", fontsize=11)
        ax.set_ylabel("Peak SSH_total in causal window (m)", fontsize=11)
        ax.set_title(
            f"TC5-E1 — Event-level capture at PU-optimal pair\n"
            f"Hₛ=q{round(opt_hs_pct*100)} / SSH_total=q{round(opt_ssh_pct*100)}"
            f"  →  H={H}  M={M}  (R_pos={H/(H+M):.2f})",
            fontsize=10, fontweight="bold",
        )

    else:
        # ── Degraded: Hs-only strip plot (SSH dimension unavailable) ─────────
        # Show peak Hs per event sorted by source then date, with q90 threshold.
        # "Captured" is approximated by Hs-only (above local thr_hs).
        df_sort = df.sort_values(["source", "date"]).reset_index(drop=True)
        df_sort["hs_above"] = df_sort["peak_hs_causal"] >= df_sort["thr_hs"].fillna(
            df_sort["thr_hs"].median()
        )

        fig, ax = plt.subplots(figsize=(10, 5))

        # Shaded zone above median Hs threshold
        median_thr_hs = df_sort["thr_hs"].median()
        if not np.isnan(median_thr_hs):
            ax.axhspan(median_thr_hs, df_sort["peak_hs_causal"].max() * 1.10,
                       color="#d0f0c0", alpha=0.25, zorder=0,
                       label="Above median Hₛ threshold")
            ax.axhline(median_thr_hs, color="dimgray", ls="--", lw=0.9, alpha=0.75, zorder=1,
                       label=f"Median Hₛ q{round(opt_hs_pct*100)} = {median_thr_hs:.2f} m")

        for src, style in source_style.items():
            df_s = df_sort[df_sort["source"] == src]
            if df_s.empty:
                continue
            below = df_s[~df_s["hs_above"]]
            above = df_s[ df_s["hs_above"]]
            if not below.empty:
                ax.scatter(
                    below.index, below["peak_hs_causal"],
                    facecolors="none", edgecolors=style["color"], linewidths=1.5,
                    s=55, zorder=2, label=f"{style['label']} — below Hₛ thr.",
                )
            if not above.empty:
                ax.scatter(
                    above.index, above["peak_hs_causal"],
                    facecolors=style["color"], edgecolors=style["color"], linewidths=0.7,
                    s=55, zorder=3, label=f"{style['label']} — above Hₛ thr.",
                )

        ax.set_xlabel("Event rank (sorted by source, then date)", fontsize=11)
        ax.set_ylabel("Peak Hₛ in causal window [D-2 … D+1] (m)", fontsize=11)
        ax.set_title(
            f"TC5-E1 — Event peak Hₛ diagnostic  [SSH dimension unavailable: eo_tides not installed]\n"
            f"Hₛ threshold q{round(opt_hs_pct*100)} shown  |  "
            f"n={len(df_sort)} combined positive events  "
            f"({int(df_sort['hs_above'].sum())} above Hₛ thr. alone)",
            fontsize=9, fontweight="bold",
        )

        ax.text(
            0.99, 0.01,
            "NOTE: Full compound capture (Hₛ ∧ SSH_total) requires eo_tides + FES2022.\n"
            "Open = below local Hₛ threshold; Filled = above Hₛ threshold (SSH not checked).",
            transform=ax.transAxes, fontsize=7, ha="right", va="bottom",
            bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="gray", alpha=0.8),
        )
        ax.legend(fontsize=8, loc="upper left", framealpha=0.85, ncol=2)

    ax.grid(alpha=0.3)
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
    event_status_df: "pd.DataFrame | None" = None,
) -> None:
    """Generate all Step 2e figures and save to cfg["fig_summary_dir"].

    Parameters
    ----------
    events_provenance : optional DataFrame from load_combined_events() provenance.
        When provided, generates the city/database source audit figure (TC5-A2).
        Loaded from tab_TC5_event_provenance.csv if not passed directly.
    event_status_df : optional DataFrame from scoring.get_event_capture_status().
        When provided, generates the event-level capture scatter (TC5-E1).
        Loaded from tab_TC5_event_capture_status.csv if not passed directly.
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

    # ── Event-level capture scatter (TC5-E1) ──────────────────────────────────
    # Attempt to load event status from disk if not passed in-memory
    _event_status = event_status_df
    if _event_status is None:
        _es_path = tab_dir / "tab_TC5_event_capture_status.csv"
        if _es_path.exists():
            _event_status = pd.read_csv(_es_path, parse_dates=["date"])

    if _event_status is not None and not _event_status.empty:
        plot_event_capture_scatter(
            _event_status, optimal,
            summary_dir / "fig_TC5_E1_event_capture.png",
        )
    else:
        log.warning(
            "Event capture status not available — skipping TC5-E1. "
            "Run with --scoring to generate tab_TC5_event_capture_status.csv."
        )

    log.info("All Step 2e figures saved to: %s", summary_dir)
