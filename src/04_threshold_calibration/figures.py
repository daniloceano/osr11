"""
Figure generation for the threshold calibration analysis (OSR11 — Step 4).

Figures produced
----------------
TC4-A1  Audit map: municipality locations vs. matched grid points (coastal geometry check)
TC4-H1  CSI heatmap (hs_pct × ssh_pct)
TC4-H2  FAR heatmap (hs_pct × ssh_pct)
TC4-H3  POD heatmap (hs_pct × ssh_pct)
TC4-S1  Ranking scatter: POD vs FAR (bubble size = CSI)
TC4-S2  Hit/miss bar chart per event at the optimal threshold pair
TC4-S3  Capture lag distribution (D-2 / D-1 / D / D+1 00Z)
TC4-S4  CSI, FAR, POD by coastal sector at optimal pair
TC4-S5  Peak Hₛ vs peak SSH_total scatter — absolute maxima within causal window,
        coloured by sector, filled = captured at optimal pair (open = missed)
TC4-M1  Municipality hit-rate heatmap (city × threshold pair)
TC4-M2  Municipality miss-rate heatmap (city × threshold pair)
TC4-M3  Municipality false-alarm heatmap (city × threshold pair)
"""
from __future__ import annotations

import logging

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from src.threshold_calibration.config.analysis_config import CFG
from src.threshold_calibration.utils import save_fig
from config.plot_config import STYLE, SECTOR_COLORS

log = logging.getLogger(__name__)

_PCT_LABELS = {p: f"q{round(p*100)}" for p in CFG["hs_percentiles"]}


# ── TC4-A1: Grid audit map ────────────────────────────────────────────────────

def plot_grid_audit(
    df_ref: pd.DataFrame,
    df_events: pd.DataFrame,
) -> plt.Figure | None:
    """Map showing municipality locations and their matched WAVERYS/GLORYS12 grid points.

    This figure is intended for visual verification of the municipality → grid-point
    assignment before any quantitative analysis is performed.  It shows:

    - Municipality coastal positions (stars), coloured by coastal sector.
    - Matched grid points (circles), same colour scheme.
    - A line connecting each municipality to its matched grid point.
    - Municipalities with insufficient data coverage are marked with a grey cross.

    Parameters
    ----------
    df_ref : pd.DataFrame
        Municipality → grid reference table from
        ``outputs/preprocessing/municipality_grid_ref.csv``.
        Required columns: municipality, muni_lat, muni_lon, grid_lat, grid_lon,
        grid_dist_km, data_quality.
    df_events : pd.DataFrame
        Reported events (from load_reported_events).  Used only to attach
        coastal_sector to each municipality row.

    Returns
    -------
    plt.Figure or None if cartopy is not available.
    """
    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
    except ImportError:
        log.warning("cartopy not available — skipping TC4-A1 audit map.")
        return None

    if df_ref is None or df_ref.empty:
        log.warning("Municipality grid reference table is empty — skipping TC4-A1.")
        return None

    # ── Attach coastal sector from events metadata ─────────────────────────────
    if "coastal_sector" in df_events.columns:
        sector_map = (
            df_events[["municipality", "coastal_sector"]]
            .dropna()
            .drop_duplicates("municipality")
            .set_index("municipality")["coastal_sector"]
        )
        df_ref = df_ref.copy()
        df_ref["coastal_sector"] = df_ref["municipality"].map(sector_map)
    else:
        df_ref = df_ref.copy()
        df_ref["coastal_sector"] = "Unknown"

    # ── Map extent (SC coast + small buffer) ──────────────────────────────────
    lat_min = df_ref[["muni_lat", "grid_lat"]].min().min() - 0.4
    lat_max = df_ref[["muni_lat", "grid_lat"]].max().max() + 0.4
    lon_min = df_ref[["muni_lon", "grid_lon"]].min().min() - 0.4
    lon_max = df_ref[["muni_lon", "grid_lon"]].max().max() + 0.4

    proj = ccrs.PlateCarree()
    fig, ax = plt.subplots(
        figsize=(STYLE.fig_width_double, 8.5),
        subplot_kw={"projection": proj},
    )
    ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=proj)

    # ── Background features ───────────────────────────────────────────────────
    ax.add_feature(cfeature.LAND,        facecolor="#f5f0e8", zorder=0)
    ax.add_feature(cfeature.OCEAN,       facecolor="#d6eaf8", zorder=0)
    ax.add_feature(cfeature.COASTLINE,   linewidth=0.7,  zorder=1)
    ax.add_feature(cfeature.BORDERS,     linewidth=0.4,  zorder=1, linestyle="--")
    ax.add_feature(cfeature.RIVERS,      linewidth=0.3,  zorder=1, alpha=0.5)
    ax.gridlines(
        draw_labels=True, linewidth=0.4, color="gray", alpha=0.6,
        xlocs=np.arange(-52, -46, 1), ylocs=np.arange(-30, -25, 1),
    )

    # ── Per-row plotting ──────────────────────────────────────────────────────
    legend_sectors: dict[str, object] = {}

    for _, row in df_ref.iterrows():
        sector = row.get("coastal_sector", "Unknown") or "Unknown"
        color  = SECTOR_COLORS.get(sector, "#555555")
        ok     = (row["data_quality"] == "ok")

        # Connector line
        ax.plot(
            [row["muni_lon"], row["grid_lon"]],
            [row["muni_lat"], row["grid_lat"]],
            color=color, linewidth=0.8, alpha=0.5,
            transform=proj, zorder=2,
        )

        # Grid point (circle)
        ax.scatter(
            row["grid_lon"], row["grid_lat"],
            s=55, marker="o", color=color, edgecolors="white",
            linewidths=0.6, alpha=0.85,
            transform=proj, zorder=3,
        )

        # Municipality (star for ok, grey × for insufficient data)
        if ok:
            h = ax.scatter(
                row["muni_lon"], row["muni_lat"],
                s=90, marker="*", color=color, edgecolors="black",
                linewidths=0.4, alpha=0.95,
                transform=proj, zorder=4,
                label=sector,
            )
            if sector not in legend_sectors:
                legend_sectors[sector] = h
        else:
            ax.scatter(
                row["muni_lon"], row["muni_lat"],
                s=90, marker="x", color="gray", linewidths=1.2,
                transform=proj, zorder=4,
            )

        # Municipality name annotation (right-aligned, small font)
        ax.text(
            row["muni_lon"] + 0.04, row["muni_lat"],
            row["municipality"].split("/")[0][:18],
            fontsize=5.5, ha="left", va="center",
            transform=proj, zorder=5,
            color="#222222",
        )

    # ── Legend ────────────────────────────────────────────────────────────────
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    sector_handles = [
        Patch(facecolor=SECTOR_COLORS.get(s, "#555555"), label=s)
        for s in sorted(k for k in legend_sectors.keys() if isinstance(k, str))
    ]
    symbol_handles = [
        Line2D([0], [0], marker="*", color="w", markerfacecolor="k",
               markersize=9, label="Municipality (ok)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="k",
               markersize=7, label="Grid point matched"),
        Line2D([0], [0], marker="x", color="gray", markersize=8,
               markeredgewidth=1.5, label="Municipality (insufficient data)",
               linestyle="None"),
    ]
    ax.legend(
        handles=sector_handles + symbol_handles,
        loc="upper left", fontsize=7,
        framealpha=0.88, title="Coastal sector / Symbol",
        title_fontsize=7,
    )

    ax.set_title(
        "TC4-A1 — Municipality → Grid Point Assignment Audit\n"
        "Stars: municipality coastal position  ·  Circles: matched WAVERYS/GLORYS12 grid point",
        fontsize=STYLE.font_size_title, fontweight="bold",
    )
    fig.tight_layout()
    return fig


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
    cbar.set_label("CSI", fontsize=STYLE.font_size_axis_label)

    n_rows, n_cols = pivot.shape
    hs_labels  = [f"q{round(p*100)}" for p in pivot.index]
    ssh_labels = [f"q{round(p*100)}" for p in pivot.columns]
    ax.set_xticks(range(n_cols))
    ax.set_xticklabels(ssh_labels, fontsize=STYLE.font_size_tick)
    ax.set_yticks(range(n_rows))
    ax.set_yticklabels(hs_labels, fontsize=STYLE.font_size_tick)
    ax.set_xlabel("SSH_total threshold (percentile)", fontsize=STYLE.font_size_axis_label)
    ax.set_ylabel("Hₛ threshold (percentile)", fontsize=STYLE.font_size_axis_label)
    ax.set_title("TC4-H1 — CSI Grid Scan", fontsize=STYLE.font_size_title, fontweight="bold")

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
    cbar.set_label("FAR", fontsize=STYLE.font_size_axis_label)

    n_rows, n_cols = pivot.shape
    hs_labels  = [f"q{round(p*100)}" for p in pivot.index]
    ssh_labels = [f"q{round(p*100)}" for p in pivot.columns]
    ax.set_xticks(range(n_cols))
    ax.set_xticklabels(ssh_labels, fontsize=STYLE.font_size_tick)
    ax.set_yticks(range(n_rows))
    ax.set_yticklabels(hs_labels, fontsize=STYLE.font_size_tick)
    ax.set_xlabel("SSH_total threshold (percentile)", fontsize=STYLE.font_size_axis_label)
    ax.set_ylabel("Hₛ threshold (percentile)", fontsize=STYLE.font_size_axis_label)
    ax.set_title("TC4-H2 — FAR Grid Scan", fontsize=STYLE.font_size_title, fontweight="bold")

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
    cbar.set_label("POD", fontsize=STYLE.font_size_axis_label)

    n_rows, n_cols = pivot.shape
    hs_labels  = [f"q{round(p*100)}" for p in pivot.index]
    ssh_labels = [f"q{round(p*100)}" for p in pivot.columns]
    ax.set_xticks(range(n_cols))
    ax.set_xticklabels(ssh_labels, fontsize=STYLE.font_size_tick)
    ax.set_yticks(range(n_rows))
    ax.set_yticklabels(hs_labels, fontsize=STYLE.font_size_tick)
    ax.set_xlabel("SSH_total threshold (percentile)", fontsize=STYLE.font_size_axis_label)
    ax.set_ylabel("Hₛ threshold (percentile)", fontsize=STYLE.font_size_axis_label)
    ax.set_title("TC4-H3 — POD Grid Scan", fontsize=STYLE.font_size_title, fontweight="bold")

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
    cbar.set_label("CSI", fontsize=STYLE.font_size_axis_label)

    # Highlight optimal
    ax.scatter(
        optimal["FAR"], optimal["POD"],
        s=300, c="red", marker="*", zorder=5, label=(
            f"Optimal\nHs=q{round(optimal['thr_hs_pct']*100)}"
            f" / SSH=q{round(optimal['thr_ssh_pct']*100)}"
        ),
    )

    ax.set_xlabel("FAR (False Alarm Ratio)", fontsize=STYLE.font_size_axis_label)
    ax.set_ylabel("POD (Probability of Detection)", fontsize=STYLE.font_size_axis_label)
    ax.set_title("TC4-S1 — Threshold Ranking: POD vs FAR", fontsize=STYLE.font_size_title, fontweight="bold")
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
    ax.set_xticklabels(["Miss", "Hit"], fontsize=STYLE.font_size_tick)
    ax.set_title(
        f"TC4-S2 — Event capture at optimal pair\n"
        f"Hₛ=q{round(optimal['thr_hs_pct']*100)} / SSH_total=q{round(optimal['thr_ssh_pct']*100)}"
        f"  →  H={int(optimal['H'])}  M={int(optimal['M'])}  F={int(optimal['F'])}",
        fontsize=STYLE.font_size_title, fontweight="bold",
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
    ax.set_xlabel("Lag relative to event day D", fontsize=STYLE.font_size_axis_label)
    ax.set_ylabel("Number of captures", fontsize=STYLE.font_size_axis_label)
    ax.set_title(
        f"TC4-S3 — Capture lag distribution\n"
        f"Optimal: Hₛ=q{round(optimal['thr_hs_pct']*100)} / SSH=q{round(optimal['thr_ssh_pct']*100)}",
        fontsize=STYLE.font_size_title, fontweight="bold",
    )
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.tick_params(axis="both", labelsize=STYLE.font_size_tick)
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
    ax.set_xticklabels(df_sec["sector"], fontsize=STYLE.font_size_tick - 1, rotation=20, ha="right")
    ax.set_ylabel("POD", fontsize=STYLE.font_size_axis_label)
    ax.set_ylim(0, 1.1)
    ax.set_title(
        f"TC4-S4 — POD by coastal sector\n"
        f"Optimal: Hₛ=q{round(optimal['thr_hs_pct']*100)} / SSH=q{round(optimal['thr_ssh_pct']*100)}",
        fontsize=STYLE.font_size_title, fontweight="bold",
    )
    for i, row in enumerate(df_sec.itertuples()):
        ax.text(i, (row.POD or 0) + 0.03, f"H={row.H}", ha="center", fontsize=7)
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


# ── TC4-M1/M2/M3: Municipality spatial heatmaps ───────────────────────────────

_SECTOR_ORDER = ["North", "Central-north", "Central", "Central-south", "South"]


def _build_municipality_order(
    df_event_hits: pd.DataFrame,
    df_muni_ref: pd.DataFrame | None,
) -> list[tuple[str, str]]:
    """Return (municipality, sector) tuples in canonical coastal display order.

    Order: North → Central-north → Central → Central-south → South.
    Within each sector: sorted by latitude (northernmost = least-negative first).
    For municipalities whose events span multiple sectors, the most frequent
    sector assignment in the event database is used.

    Parameters
    ----------
    df_event_hits : full event-hits table (all threshold pairs).
    df_muni_ref   : municipality grid reference table (provides muni_lat).

    Returns
    -------
    list of (municipality, sector) tuples, length = number of unique municipalities.
    """
    # Most common sector per municipality
    sector_map: dict[str, str] = (
        df_event_hits.groupby("municipality")["coastal_sector"]
        .agg(lambda x: x.value_counts().index[0])
        .to_dict()
    )

    # Latitude from reference table (more northerly = less negative lat)
    lat_map: dict[str, float] = {}
    if df_muni_ref is not None and not df_muni_ref.empty and "muni_lat" in df_muni_ref.columns:
        lat_map = df_muni_ref.set_index("municipality")["muni_lat"].to_dict()

    def _sort_key(muni: str) -> tuple[int, float]:
        sector = sector_map.get(muni, "Unknown")
        rank = _SECTOR_ORDER.index(sector) if sector in _SECTOR_ORDER else 99
        lat = lat_map.get(muni, 0.0)
        return (rank, -lat)  # -lat: more northern first within sector

    munis_sorted = sorted(sector_map.keys(), key=_sort_key)
    return [(m, sector_map[m]) for m in munis_sorted]


def _draw_municipality_heatmap(
    matrix: np.ndarray,
    muni_order: list[tuple[str, str]],
    hs_percentiles: list[float],
    ssh_percentiles: list[float],
    title: str,
    cmap: str,
    vmin: float,
    vmax: float,
    cbar_label: str,
    optimal: dict | None = None,
) -> plt.Figure:
    """Render a (municipality × threshold-pair) heatmap.

    Parameters
    ----------
    matrix         : (n_munis × 81) array of values. NaN = no data.
    muni_order     : list of (municipality, sector) from _build_municipality_order().
    hs_percentiles : sorted list of Hₛ percentile levels (e.g. [0.50, …, 0.90]).
    ssh_percentiles: sorted list of SSH percentile levels.
    title          : figure title string.
    cmap, vmin, vmax, cbar_label : colormap parameters.
    optimal        : dict with 'thr_hs_pct' and 'thr_ssh_pct' for the optimal pair.
                     If provided, the corresponding column is highlighted.
    """
    n_munis = len(muni_order)

    # ── Figure sizing: tight vertical fit, no excess whitespace ──────────────
    # Row height chosen so municipality labels remain legible without blank rows.
    _row_h      = 0.36    # inches per municipality row
    _top_in     = 0.85    # title
    _bottom_in  = 0.95    # two-line xlabel + tick labels
    _left_in    = 3.60    # sector labels (narrow strip) + municipality name labels
    _right_in   = 1.05    # colorbar
    _axes_w_in  = 13.50   # heatmap area width

    fig_w = _left_in + _axes_w_in + _right_in
    fig_h = _top_in + n_munis * _row_h + _bottom_in

    # Convert to fractional margins
    l_frac = _left_in  / fig_w
    r_frac = 1.0 - _right_in  / fig_w
    t_frac = 1.0 - _top_in    / fig_h
    b_frac = _bottom_in / fig_h

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.subplots_adjust(left=l_frac, right=r_frac, top=t_frac, bottom=b_frac)

    im = ax.imshow(
        matrix, aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax,
        interpolation="none",
    )
    cbar = fig.colorbar(im, ax=ax, shrink=0.85, pad=0.02)
    cbar.set_label(cbar_label, fontsize=STYLE.font_size_axis_label)

    # ── X-axis: Hₛ group labels ───────────────────────────────────────────────
    n_ssh = len(ssh_percentiles)
    group_centers = [g * n_ssh + n_ssh // 2 for g in range(len(hs_percentiles))]
    ax.set_xticks(group_centers)
    ax.set_xticklabels(
        [f"Hₛ=q{round(p * 100)}" for p in hs_percentiles],
        fontsize=STYLE.font_size_tick,
    )
    ax.set_xlabel(
        "Hₛ threshold (percentile group)\n"
        "Within each group, SSH threshold varies q50 → q90 (left to right)",
        fontsize=STYLE.font_size_axis_label,
    )

    # Vertical separators between Hₛ groups
    for g in range(1, len(hs_percentiles)):
        ax.axvline(g * n_ssh - 0.5, color="gray", lw=0.7, ls="--", alpha=0.6)

    # Highlight optimal pair column
    if optimal is not None:
        try:
            opt_hs_idx  = list(hs_percentiles).index(optimal["thr_hs_pct"])
            opt_ssh_idx = list(ssh_percentiles).index(optimal["thr_ssh_pct"])
            opt_col = opt_hs_idx * n_ssh + opt_ssh_idx
            ax.axvline(opt_col - 0.5, color="red", lw=1.8, ls="-", alpha=0.9)
            ax.axvline(opt_col + 0.5, color="red", lw=1.8, ls="-", alpha=0.9)
            ax.text(
                opt_col, -1.2, "★",
                ha="center", va="top", color="red", fontsize=9,
                transform=ax.get_xaxis_transform(),
            )
        except (ValueError, KeyError):
            pass

    # ── Y-axis: municipality names ────────────────────────────────────────────
    muni_names = [m for m, _ in muni_order]
    ax.set_yticks(range(n_munis))
    ax.set_yticklabels(muni_names, fontsize=STYLE.font_size_tick - 1)
    ax.set_ylabel("")

    # ── Sector boundaries: horizontal separators + vertical sector labels ─────
    # Sector labels are drawn with fig.text() using figure-fraction coordinates
    # so they sit to the LEFT of the municipality name tick labels and are
    # rotated 90° to conserve horizontal space.
    sector_boundaries: list[int] = []
    prev_sector: str | None = None
    for i, (_muni, sector) in enumerate(muni_order):
        if sector != prev_sector:
            sector_boundaries.append(i)
            prev_sector = sector

    # x position for sector labels: a thin strip at the very left of the figure
    # (about 0.4 inches from left edge → x_fig ≈ 0.4 / fig_w)
    sector_x_fig = 0.40 / fig_w

    for k, boundary in enumerate(sector_boundaries):
        if boundary > 0:
            ax.axhline(boundary - 0.5, color="black", lw=1.1, ls="-")

        next_boundary = sector_boundaries[k + 1] if k + 1 < len(sector_boundaries) else n_munis
        mid_row = (boundary + next_boundary - 1) / 2
        sector_name = muni_order[boundary][1]
        color = SECTOR_COLORS.get(sector_name, "#333333")

        # Convert data row index → axes fraction → figure fraction
        # imshow: row 0 is at the TOP of the axes (y increases downward)
        mid_ax = 1.0 - (mid_row + 0.5) / n_munis
        mid_fig_y = b_frac + mid_ax * (t_frac - b_frac)

        fig.text(
            sector_x_fig, mid_fig_y,
            sector_name,
            ha="center", va="center",
            rotation=90,
            fontsize=STYLE.font_size_tick,
            color=color,
            fontweight="bold",
        )

    ax.set_title(title, fontsize=STYLE.font_size_title, fontweight="bold")
    return fig


def plot_city_hits_heatmap(
    df_event_hits: pd.DataFrame,
    muni_order: list[tuple[str, str]],
    optimal: dict,
) -> plt.Figure:
    """TC4-M1 — Hit-rate heatmap: municipality × threshold pair.

    Each cell shows the fraction of that municipality's reported events that
    were captured (hit) at the given (Hₛ, SSH_total) threshold pair.  Values
    range from 0 (all events missed) to 1 (all events captured).

    Municipality rows are ordered by coastal sector (North → South) and by
    latitude within each sector.  Hₛ groups of nine SSH levels are separated
    by vertical dashed lines; the optimal pair is marked with ★.

    Parameters
    ----------
    df_event_hits : full event-hits table (all threshold pairs).
    muni_order    : from _build_municipality_order().
    optimal       : dict with 'thr_hs_pct' and 'thr_ssh_pct'.
    """
    hs_pcts  = sorted(df_event_hits["thr_hs_pct"].unique())
    ssh_pcts = sorted(df_event_hits["thr_ssh_pct"].unique())
    pairs    = [(hs, ssh) for hs in hs_pcts for ssh in ssh_pcts]
    pair_idx = {p: i for i, p in enumerate(pairs)}

    # Compute hit_rate per (municipality, pair)
    hr = (
        df_event_hits
        .groupby(["municipality", "thr_hs_pct", "thr_ssh_pct"])["captured"]
        .mean()
        .reset_index()
    )

    muni_names = [m for m, _ in muni_order]
    muni_row   = {m: i for i, m in enumerate(muni_names)}
    matrix     = np.full((len(muni_names), len(pairs)), np.nan)

    for _, row in hr.iterrows():
        i = muni_row.get(row["municipality"])
        j = pair_idx.get((row["thr_hs_pct"], row["thr_ssh_pct"]))
        if i is not None and j is not None:
            matrix[i, j] = row["captured"]

    return _draw_municipality_heatmap(
        matrix=matrix,
        muni_order=muni_order,
        hs_percentiles=hs_pcts,
        ssh_percentiles=ssh_pcts,
        title=(
            "TC4-M1 — Hit Rate per Municipality × Threshold Pair\n"
            "Fraction of reported events captured within the causal window [D-2, D+1 00Z]"
        ),
        cmap="YlGn",
        vmin=0.0,
        vmax=1.0,
        cbar_label="Hit rate  (H / n_events)",
        optimal=optimal,
    )


def plot_city_misses_heatmap(
    df_event_hits: pd.DataFrame,
    muni_order: list[tuple[str, str]],
    optimal: dict,
) -> plt.Figure:
    """TC4-M2 — Miss-rate heatmap: municipality × threshold pair.

    Each cell shows the fraction of that municipality's events that were missed
    (1 − hit_rate) at the given threshold pair.  High values (dark orange/red)
    indicate municipalities where the compound condition consistently fails to
    match reported disasters regardless of threshold choice.

    Parameters
    ----------
    df_event_hits : full event-hits table (all threshold pairs).
    muni_order    : from _build_municipality_order().
    optimal       : dict with 'thr_hs_pct' and 'thr_ssh_pct'.
    """
    hs_pcts  = sorted(df_event_hits["thr_hs_pct"].unique())
    ssh_pcts = sorted(df_event_hits["thr_ssh_pct"].unique())
    pairs    = [(hs, ssh) for hs in hs_pcts for ssh in ssh_pcts]
    pair_idx = {p: i for i, p in enumerate(pairs)}

    mr = (
        df_event_hits
        .groupby(["municipality", "thr_hs_pct", "thr_ssh_pct"])["captured"]
        .mean()
        .reset_index()
    )
    mr["miss_rate"] = 1.0 - mr["captured"]

    muni_names = [m for m, _ in muni_order]
    muni_row   = {m: i for i, m in enumerate(muni_names)}
    matrix     = np.full((len(muni_names), len(pairs)), np.nan)

    for _, row in mr.iterrows():
        i = muni_row.get(row["municipality"])
        j = pair_idx.get((row["thr_hs_pct"], row["thr_ssh_pct"]))
        if i is not None and j is not None:
            matrix[i, j] = row["miss_rate"]

    return _draw_municipality_heatmap(
        matrix=matrix,
        muni_order=muni_order,
        hs_percentiles=hs_pcts,
        ssh_percentiles=ssh_pcts,
        title=(
            "TC4-M2 — Miss Rate per Municipality × Threshold Pair\n"
            "Fraction of reported events not captured (1 − hit rate)"
        ),
        cmap="YlOrRd",
        vmin=0.0,
        vmax=1.0,
        cbar_label="Miss rate  (M / n_events)",
        optimal=optimal,
    )


def plot_city_false_alarms_heatmap(
    df_fa_per_muni: pd.DataFrame,
    muni_order: list[tuple[str, str]],
    optimal: dict,
) -> plt.Figure:
    """TC4-M3 — False alarm heatmap: municipality × threshold pair.

    Each cell shows the number of false alarm episodes at that municipality's
    grid point for the given threshold pair.  A false alarm episode is a
    compound exceedance cluster in the validated period that does NOT overlap
    with any observed event's causal window at the same grid point.

    Note: municipalities that share the same WAVERYS/GLORYS12 grid point will
    have identical false alarm counts (they observe the same oceanographic signal).

    Parameters
    ----------
    df_fa_per_muni : per-municipality false alarm table with columns
                     [thr_hs_pct, thr_ssh_pct, municipality, F].
    muni_order     : from _build_municipality_order().
    optimal        : dict with 'thr_hs_pct' and 'thr_ssh_pct'.
    """
    if df_fa_per_muni is None or df_fa_per_muni.empty:
        log.warning("No per-municipality false alarm data — skipping TC4-M3.")
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No per-municipality false alarm data.\nRe-run with --all to generate.",
                ha="center", va="center", fontsize=10, color="gray")
        ax.set_title("TC4-M3 — False Alarms per Municipality (data not available)",
                     fontsize=STYLE.font_size_title, fontweight="bold")
        return fig

    hs_pcts  = sorted(df_fa_per_muni["thr_hs_pct"].unique())
    ssh_pcts = sorted(df_fa_per_muni["thr_ssh_pct"].unique())
    pairs    = [(hs, ssh) for hs in hs_pcts for ssh in ssh_pcts]
    pair_idx = {p: i for i, p in enumerate(pairs)}

    muni_names = [m for m, _ in muni_order]
    muni_row   = {m: i for i, m in enumerate(muni_names)}
    matrix     = np.full((len(muni_names), len(pairs)), np.nan)

    for _, row in df_fa_per_muni.iterrows():
        i = muni_row.get(row["municipality"])
        j = pair_idx.get((row["thr_hs_pct"], row["thr_ssh_pct"]))
        if i is not None and j is not None:
            matrix[i, j] = row["F"]

    vmax = float(np.nanpercentile(matrix, 99)) if not np.all(np.isnan(matrix)) else 1.0

    return _draw_municipality_heatmap(
        matrix=matrix,
        muni_order=muni_order,
        hs_percentiles=hs_pcts,
        ssh_percentiles=ssh_pcts,
        title=(
            "TC4-M3 — False Alarm Count per Municipality × Threshold Pair\n"
            "Episodes in validated period not paired with any observed event at that grid point"
        ),
        cmap="Reds",
        vmin=0.0,
        vmax=vmax,
        cbar_label="False alarm episodes (F)",
        optimal=optimal,
    )


# ── Orchestration ─────────────────────────────────────────────────────────────

# ── TC4-S5: Peak Hₛ × peak SSH_total scatter ─────────────────────────────────

def plot_peak_scatter(
    records: list,
    ssh_total_cache: dict,
    df_event_hits: pd.DataFrame,
    optimal: dict,
) -> plt.Figure:
    """Scatter of absolute peak Hₛ vs peak SSH_total within the causal window.

    Each point represents one reported event. X = maximum Hₛ found in
    [D-2, D-1, D, D+1 00Z]; Y = maximum SSH_total in the same window.
    Points are coloured by coastal sector.  Filled circles indicate
    events captured at the optimal threshold pair; open circles are missed.

    Dashed reference lines show the **median** of the local percentile
    thresholds across all grid points (i.e. the median Hₛ q{N} and SSH_total
    q{N} values used in the calibration).  Because thresholds are computed
    locally at each municipality's grid point, individual events may have
    threshold values that differ from these reference lines.

    Parameters
    ----------
    records : list[EventRecord]
    ssh_total_cache : dict mapping (lat, lon) → SSH_total climatological Series
    df_event_hits : DataFrame from metrics.build_event_hit_table() (all pairs)
    optimal : dict with 'thr_hs_pct', 'thr_ssh_pct', 'H', 'M'

    Returns
    -------
    matplotlib.figure.Figure
    """
    from matplotlib.lines import Line2D
    from config.plot_config import apply_publication_style

    apply_publication_style()

    opt_hs_pct  = float(optimal["thr_hs_pct"])
    opt_ssh_pct = float(optimal["thr_ssh_pct"])

    # Capture-status lookup keyed by event_idx
    df_opt = df_event_hits[
        (df_event_hits["thr_hs_pct"]  == opt_hs_pct)
        & (df_event_hits["thr_ssh_pct"] == opt_ssh_pct)
    ].copy()
    capture_map: dict[int, bool] = dict(zip(df_opt["event_idx"], df_opt["captured"]))
    sector_map: dict[int, str]   = {}
    if "coastal_sector" in df_opt.columns:
        sector_map = dict(zip(df_opt["event_idx"], df_opt["coastal_sector"].fillna("")))

    # ── Collect per-event peak values and local thresholds ────────────────────
    # SSH_total (zos + FES2022 tide) is mandatory in Step 4.
    rows = []

    for rec in records:
        key = (round(float(rec.grid_lat), 6), round(float(rec.grid_lon), 6))
        ssh_total_clim = ssh_total_cache.get(key, pd.Series(dtype=float))

        if not ssh_total_clim.notna().any():
            raise RuntimeError(
                f"SSH_total is all-NaN for grid point {key} "
                f"(municipality: {rec.municipality}) — FES2022 tidal data is mandatory "
                "for Step 4 figures. Run in the 'osr11' conda environment."
            )

        # Causal window [D-2 … D+1]
        win_start = rec.date - pd.Timedelta(days=2)
        win_end   = rec.date + pd.Timedelta(days=1)

        hs_causal  = rec.hs_clim.loc[win_start:win_end]
        ssh_causal = ssh_total_clim.loc[win_start:win_end]

        peak_hs  = float(hs_causal.max())  if hs_causal.notna().any()  else np.nan
        peak_ssh = float(ssh_causal.max()) if ssh_causal.notna().any() else np.nan

        # Local thresholds (same computation as Layer 1)
        thr_hs = (
            float(rec.hs_clim.dropna().quantile(opt_hs_pct))
            if rec.hs_clim.notna().any() else np.nan
        )
        thr_ssh = (
            float(ssh_total_clim.dropna().quantile(opt_ssh_pct))
            if ssh_total_clim.notna().any() else np.nan
        )

        rows.append({
            "municipality": rec.municipality,
            "peak_hs":  peak_hs,
            "peak_ssh": peak_ssh,
            "thr_hs":   thr_hs,
            "thr_ssh":  thr_ssh,
            "captured": capture_map.get(rec.event_idx, False),
            "sector":   sector_map.get(rec.event_idx, ""),
        })

    df_plot = pd.DataFrame(rows)
    df_plot = df_plot.dropna(subset=["peak_hs", "peak_ssh"])

    # Median reference thresholds
    median_thr_hs  = df_plot["thr_hs"].median()
    median_thr_ssh = df_plot["thr_ssh"].median()

    # ── Figure ────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 7))

    # Light shading of "above both median thresholds" zone
    xlim_hi = df_plot["peak_hs"].max() * 1.08 if not df_plot.empty else 1.0
    ylim_hi = df_plot["peak_ssh"].max() * 1.08 if not df_plot.empty else 1.0
    if (
        not np.isnan(median_thr_hs)
        and not np.isnan(median_thr_ssh)
        and xlim_hi > median_thr_hs
        and ylim_hi > median_thr_ssh
    ):
        ax.fill_betweenx(
            [median_thr_ssh, ylim_hi],
            median_thr_hs, xlim_hi,
            color="#d0f0c0", alpha=0.25, zorder=0,
            label="Above both median thresholds",
        )

    # Reference lines
    if not np.isnan(median_thr_hs):
        ax.axvline(
            median_thr_hs, color="dimgray", ls="--", lw=1.0, alpha=0.75, zorder=1,
            label=f"Median Hₛ q{round(opt_hs_pct * 100)} = {median_thr_hs:.2f} m",
        )
    if not np.isnan(median_thr_ssh):
        ax.axhline(
            median_thr_ssh, color="dimgray", ls=":", lw=1.0, alpha=0.75, zorder=1,
            label=f"Median SSH_total q{round(opt_ssh_pct * 100)} = {median_thr_ssh:.2f} m",
        )

    # ── Scatter: misses first (below), hits on top ────────────────────────────
    for sector, color in SECTOR_COLORS.items():
        df_s = df_plot[df_plot["sector"] == sector]
        if df_s.empty:
            continue
        miss = df_s[~df_s["captured"]]
        hit  = df_s[ df_s["captured"]]
        if not miss.empty:
            ax.scatter(
                miss["peak_hs"], miss["peak_ssh"],
                facecolors="none", edgecolors=color, linewidths=1.5,
                s=72, zorder=2,
            )
        if not hit.empty:
            ax.scatter(
                hit["peak_hs"], hit["peak_ssh"],
                facecolors=color, edgecolors=color, linewidths=0.8,
                s=72, zorder=3,
            )

    # ── Legend: sector colours + marker type ─────────────────────────────────
    marker_handles = [
        Line2D([0], [0], marker="o", linestyle="none",
               markerfacecolor="dimgray", markeredgecolor="dimgray",
               markersize=8, label="Captured ● (filled)"),
        Line2D([0], [0], marker="o", linestyle="none",
               markerfacecolor="none", markeredgecolor="dimgray",
               markersize=8, label="Missed ○ (open)"),
    ]
    sector_handles = [
        Line2D([0], [0], marker="o", linestyle="none",
               markerfacecolor=color, markeredgecolor=color,
               markersize=8, label=sector)
        for sector, color in SECTOR_COLORS.items()
        if not df_plot[df_plot["sector"] == sector].empty
    ]
    ax.legend(
        handles=marker_handles + sector_handles,
        fontsize=7.5, loc="upper left", framealpha=0.9,
    )

    # ── Axes ─────────────────────────────────────────────────────────────────
    hs_label  = "Peak Hₛ in causal window [D-2 … D+1 00Z] (m)"
    ssh_label = "Peak SSH_total = zos + tide in causal window [D-2 … D+1 00Z] (m)"
    ax.set_xlabel(hs_label, fontsize=STYLE.font_size_axis_label)
    ax.set_ylabel(ssh_label, fontsize=STYLE.font_size_axis_label)
    ax.set_title(
        f"TC4-S5 — Absolute peak values within causal window — filled = captured\n"
        f"Optimal pair: Hₛ q{round(opt_hs_pct * 100)} / SSH_total q{round(opt_ssh_pct * 100)}"
        f"  ·  {int(optimal['H'])} hits  ·  {int(optimal['M'])} misses",
        fontsize=STYLE.font_size_title, fontweight="bold",
    )
    ax.tick_params(axis="both", labelsize=STYLE.font_size_tick)
    ax.grid(True, alpha=0.3, lw=0.5)
    fig.tight_layout()
    return fig


def run_figures(
    df_metrics: pd.DataFrame,
    df_event_hits: pd.DataFrame,
    lag_summary: pd.DataFrame,
    optimal: dict,
    df_muni_ref: pd.DataFrame | None = None,
    df_events_meta: pd.DataFrame | None = None,
    df_fa_per_muni: pd.DataFrame | None = None,
    records: list | None = None,
    ssh_total_cache: dict | None = None,
) -> None:
    """Generate and save all Step 4 figures.

    Parameters
    ----------
    df_metrics      : output of metrics.compute_scores()
    df_event_hits   : per-event capture results (all threshold pairs)
    lag_summary     : capture lag distribution at optimal pair
    optimal         : dict — best threshold pair and its metrics
    df_muni_ref     : municipality→grid reference table (optional).
                      If provided (and cartopy is available), the TC4-A1 audit
                      map is generated.
    df_events_meta  : reported events DataFrame (for sector metadata in audit map).
    df_fa_per_muni  : per-municipality false alarm counts (all threshold pairs),
                      as produced by calibration.run_false_alarms(). Optional;
                      if None, TC4-M3 is generated with a placeholder message.
    records : list[EventRecord] | None
        Required for TC4-S5 (peak scatter). If None, TC4-S5 is skipped.
    ssh_total_cache : dict | None
        Required for TC4-S5. Mapping (lat, lon) → SSH_total Series.
    """
    log.info("Generating threshold calibration figures...")

    # ── TC4-A1: Grid audit map ─────────────────────────────────────────────
    if df_muni_ref is not None and df_events_meta is not None:
        fig_a1 = plot_grid_audit(df_muni_ref, df_events_meta)
        if fig_a1 is not None:
            save_fig(fig_a1, "fig_TC4_A1_grid_audit", subdir="summary")
    else:
        log.info("  Skipping TC4-A1 (municipality grid reference not provided).")

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

    # ── TC4-S5: Peak scatter ───────────────────────────────────────────────
    if records is not None and ssh_total_cache is not None:
        fig_s5 = plot_peak_scatter(records, ssh_total_cache, df_event_hits, optimal)
        save_fig(fig_s5, "fig_TC4_S5_peak_scatter", subdir="summary")
    else:
        log.info("  Skipping TC4-S5 (records or ssh_total_cache not provided).")

    # ── TC4-M1/M2/M3: Municipality spatial heatmaps ────────────────────────
    muni_order = _build_municipality_order(df_event_hits, df_muni_ref)

    fig_m1 = plot_city_hits_heatmap(df_event_hits, muni_order, optimal)
    save_fig(fig_m1, "fig_TC4_M1_city_hit_rate", subdir="summary")

    fig_m2 = plot_city_misses_heatmap(df_event_hits, muni_order, optimal)
    save_fig(fig_m2, "fig_TC4_M2_city_miss_rate", subdir="summary")

    fig_m3 = plot_city_false_alarms_heatmap(df_fa_per_muni, muni_order, optimal)
    save_fig(fig_m3, "fig_TC4_M3_city_false_alarms", subdir="summary")

    log.info("All TC4 figures saved.")
