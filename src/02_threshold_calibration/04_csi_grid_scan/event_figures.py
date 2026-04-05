"""
Per-event time-series figures for the threshold calibration analysis (OSR11 — Step 3b).

Each figure has two stacked panels:
  (a) Hₛ — daily maximum from WAVERYS (3-hourly, resampled)
  (b) SSH_total = SSH (zos, 00:00 UTC) + FES2022 tide (daily maximum)

Both panels share the same x-axis (7-day window centred on the event date)
and display the local percentile threshold as a dashed horizontal line.  The
causal/antecedent matching window [D-2, D-1, D, D+1] is highlighted in both
panels with a translucent blue band.  A colour-coded title bar indicates
whether the event is captured (green ✓) or missed (red ✗) at the selected
threshold pair.

Figures are generated for each of the nine diagonal threshold pairs:
  (q50, q50), (q55, q55), ..., (q90, q90)
plus the optimal pair if it falls off the diagonal.  This supports the
percentile-level navigation on the results website.

Output locations
----------------
  outputs/threshold_calibration/figures/events/
      fig_TC4_E{id:03d}_{slug}_{YYYYMMDD}_hs{NN}_ssh{NN}.png

  site/public/figures/tc4_events/
      (same filenames, served by the Next.js site)

Content file
------------
  site/content/tc4Events.ts
      TypeScript array used by the Tc4EventSelector component.
      Auto-generated — do not edit by hand.
"""
from __future__ import annotations

import logging
import re
import unicodedata
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

from config.plot_config import apply_publication_style, STYLE
from src.threshold_calibration.config.analysis_config import CFG

matplotlib.use("Agg")
log = logging.getLogger(__name__)

# Diagonal percentile pairs: q50×q50 … q90×q90
_DIAGONAL_PCTS: list[float] = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90]

# Site public figures directory (relative to this file → project root → site)
_SITE_EVENTS_DIR: Path = (
    Path(__file__).resolve().parents[2] / "site" / "public" / "figures" / "tc4_events"
)
_SITE_CONTENT_FILE: Path = (
    Path(__file__).resolve().parents[2] / "site" / "content" / "tc4Events.ts"
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _muni_slug(name: str) -> str:
    """ASCII filename slug from a municipality name."""
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9]+", "_", ascii_str).strip("_").lower()


def _local_threshold(series: pd.Series, pct: float) -> float:
    finite = series.dropna()
    if finite.empty:
        return np.nan
    return float(finite.quantile(pct))


def _shade_exceedances(ax, series: pd.Series, threshold: float, color: str, alpha: float = 0.25) -> None:
    """Fill contiguous blocks above threshold."""
    if np.isnan(threshold) or not (series >= threshold).any():
        return
    times = series.index
    in_block = False
    t_start = None
    for t, exc in zip(times, series >= threshold):
        if exc and not in_block:
            t_start = t
            in_block = True
        elif not exc and in_block:
            ax.axvspan(t_start, t, color=color, alpha=alpha, linewidth=0)
            in_block = False
    if in_block:
        ax.axvspan(t_start, times[-1], color=color, alpha=alpha, linewidth=0)


def _fmt_time_ax(ax, dates) -> None:
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=7)


# ── Per-event 2-panel figure ─────────────────────────────────────────────────

def make_event_timeseries_figure(
    rec,
    ssh_total_clim: pd.Series,
    hs_pct: float,
    ssh_pct: float,
    captured: bool,
) -> plt.Figure:
    """
    Generate a 2-panel time-series figure for one event at one threshold pair.

    Parameters
    ----------
    rec : EventRecord
        Event record from src.preliminary_compound.events.
    ssh_total_clim : pd.Series
        Full climatological SSH_total series for the event's grid point.
    hs_pct, ssh_pct : float
        Percentile values (e.g., 0.75 for q75).
    captured : bool
        Whether the event is captured (hit) at this threshold pair.

    Returns
    -------
    matplotlib.figure.Figure
    """
    apply_publication_style()

    # ── Extract windows ───────────────────────────────────────────────────────
    hs_win = rec.hs_window                               # D-3 to D+3 (7 days)
    win_start, win_end = hs_win.index[0], hs_win.index[-1]
    ssh_total_win = ssh_total_clim.loc[win_start:win_end]

    # SSH_total is mandatory in Step 3b — all-NaN means FES2022 tide was not computed.
    if not ssh_total_win.notna().any():
        raise RuntimeError(
            f"SSH_total is all-NaN for {rec.municipality} {rec.date.date()} — "
            "FES2022 tidal data must be available for Step 3b. "
            "Run in the 'osr11' conda environment where eo-tides is installed."
        )

    _SSH_TOTAL_COLOR = "#7b2d8b"  # purple, consistent with Step 3a

    # ── Local thresholds ──────────────────────────────────────────────────────
    thr_hs  = _local_threshold(rec.hs_clim, hs_pct)
    thr_ssh = _local_threshold(ssh_total_clim, ssh_pct)

    # ── Causal window bounds for shading [D-2, D-1, D, D+1] ─────────────────
    event_dt    = pd.Timestamp(rec.date)
    causal_lo   = event_dt - pd.Timedelta(days=2)
    causal_hi   = event_dt + pd.Timedelta(days=1, hours=12)  # extend half day for visibility

    # ── Figure layout ─────────────────────────────────────────────────────────
    fig, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    fig.subplots_adjust(hspace=0.06, left=0.09, right=0.97, top=0.87, bottom=0.12)

    for ax in axes:
        # Causal window band (below all data)
        ax.axvspan(causal_lo, causal_hi, color="#cce6ff", alpha=0.45, zorder=0,
                   label="Causal window [D-2 … D+1]")
        # Event date marker
        ax.axvline(event_dt, color="black", lw=1.2, ls=":", alpha=0.9, zorder=4)
        ax.grid(True, alpha=0.3, lw=0.5)
        ax.tick_params(axis="both", labelsize=7)

    # ── Panel (a): Hₛ ─────────────────────────────────────────────────────────
    ax_hs = axes[0]
    ax_hs.plot(hs_win.index, hs_win.values, color=STYLE.color_hs, lw=1.4, zorder=3)
    _shade_exceedances(ax_hs, hs_win, thr_hs, STYLE.color_hs)
    if not np.isnan(thr_hs):
        ax_hs.axhline(thr_hs, color="dimgray", lw=0.9, ls="--", alpha=0.85,
                      label=f"q{round(hs_pct * 100)} threshold", zorder=2)
        # Max marker
        if not hs_win.dropna().empty:
            max_t = hs_win.idxmax()
            ax_hs.scatter([max_t], [hs_win[max_t]], color=STYLE.color_hs,
                          s=50, zorder=7, edgecolors="white", lw=0.8)
    ax_hs.set_ylabel("Hₛ (m)", fontsize=8)
    ax_hs.legend(loc="upper right", fontsize=6.5, framealpha=0.85)

    # ── Panel (b): SSH_total ──────────────────────────────────────────────────
    ax_ssh = axes[1]
    ax_ssh.plot(ssh_total_win.index, ssh_total_win.values, color=_SSH_TOTAL_COLOR, lw=1.4, zorder=3)
    _shade_exceedances(ax_ssh, ssh_total_win, thr_ssh, _SSH_TOTAL_COLOR)
    if not np.isnan(thr_ssh):
        ax_ssh.axhline(thr_ssh, color="dimgray", lw=0.9, ls="--", alpha=0.85,
                       label=f"q{round(ssh_pct * 100)} threshold", zorder=2)
        if not ssh_total_win.dropna().empty:
            max_t_ssh = ssh_total_win.idxmax()
            ax_ssh.scatter([max_t_ssh], [ssh_total_win[max_t_ssh]], color=_SSH_TOTAL_COLOR,
                           s=50, zorder=7, edgecolors="white", lw=0.8)
    ax_ssh.set_ylabel("SSH_total (m)\nzos + FES2022 tide", fontsize=8, labelpad=4)
    ax_ssh.legend(loc="upper right", fontsize=6.5, framealpha=0.85)

    # ── X-axis ────────────────────────────────────────────────────────────────
    _fmt_time_ax(ax_ssh, ssh_total_win.index)

    # ── Causal window legend on panel (a) ─────────────────────────────────────
    from matplotlib.patches import Patch
    handles, labels = ax_hs.get_legend_handles_labels()
    causal_patch = Patch(facecolor="#cce6ff", alpha=0.7, label="Causal window [D-2 … D+1]")
    handles.append(causal_patch)
    ax_hs.legend(handles=handles, loc="upper left", fontsize=6.5, framealpha=0.85)

    # ── Title bar ─────────────────────────────────────────────────────────────
    hit_str    = "✓ HIT"  if captured else "✗ MISS"
    title_col  = "#2ca02c" if captured else "#d62728"
    hs_lbl     = f"q{round(hs_pct * 100)}"
    ssh_lbl    = f"q{round(ssh_pct * 100)}"
    title = (
        f"{rec.municipality}  ·  {rec.date.strftime('%d %b %Y')}"
        f"  ·  Hₛ {hs_lbl} / SSH_total {ssh_lbl}  ·  {hit_str}"
    )
    fig.suptitle(title, fontsize=9, fontweight="bold",
                 color=title_col, y=0.96, x=0.5, ha="center")

    return fig


def _figure_filename(rec, hs_pct: float, ssh_pct: float) -> str:
    """Return the canonical filename (without directory) for one event figure."""
    slug = _muni_slug(rec.municipality)
    return (
        f"fig_TC4_E{rec.disaster_id:03d}_{slug}_{rec.date.strftime('%Y%m%d')}"
        f"_hs{round(hs_pct * 100)}_ssh{round(ssh_pct * 100)}.png"
    )


def _save_event_figure(fig: plt.Figure, fname: str) -> None:
    """Save event figure to the outputs dir and (if available) to the site public dir."""
    outputs_path = CFG["fig_events_dir"] / fname
    fig.savefig(outputs_path, dpi=STYLE.dpi_export, bbox_inches="tight")
    log.debug("  Saved: %s", outputs_path)

    # Mirror to site/public/figures/tc4_events/ if that tree exists
    site_dir = _SITE_EVENTS_DIR
    if site_dir.parent.exists():
        site_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(site_dir / fname, dpi=STYLE.dpi_export, bbox_inches="tight")

    plt.close(fig)


# ── Batch figure generation ───────────────────────────────────────────────────

def run_event_figures(
    records: list,
    ssh_total_cache: dict,
    time_index,
    df_event_hits_all: pd.DataFrame,
    df_events_meta: pd.DataFrame,
    optimal: dict | None = None,
) -> None:
    """
    Generate 2-panel time-series figures for all events across all percentile pairs.

    Figures are generated for the nine diagonal threshold pairs (q50×q50 …
    q90×q90) plus the optimal pair if it is off the diagonal.  After all
    figures are saved, the TypeScript content file
    ``site/content/tc4Events.ts`` is written.

    Parameters
    ----------
    records : list[EventRecord]
    ssh_total_cache : dict mapping (lat, lon) → SSH_total Series
    time_index : pd.DatetimeIndex  (unused here, kept for API consistency)
    df_event_hits_all : DataFrame from metrics.build_event_hit_table()
        Must contain [event_idx, thr_hs_pct, thr_ssh_pct, captured].
    df_events_meta : DataFrame from load_reported_events()
        Used to look up coastal_sector per municipality.
    optimal : dict | None
        Optimal threshold pair dict (keys: thr_hs_pct, thr_ssh_pct).
        If provided and off-diagonal, included as an extra figure set.
    """
    # ── Build percentile-pair list ─────────────────────────────────────────
    pct_pairs: list[tuple[float, float]] = [
        (p, p) for p in _DIAGONAL_PCTS
    ]
    if optimal is not None:
        opt_pair = (float(optimal["thr_hs_pct"]), float(optimal["thr_ssh_pct"]))
        if opt_pair not in pct_pairs:
            pct_pairs.append(opt_pair)
            log.info(
                "Optimal pair (hs=q%.0f, ssh=q%.0f) is off-diagonal — added to event figures.",
                opt_pair[0] * 100, opt_pair[1] * 100,
            )

    log.info(
        "Generating event time-series figures: %d records × %d pairs = %d figures",
        len(records), len(pct_pairs), len(records) * len(pct_pairs),
    )

    # ── Sector lookup from df_events_meta ─────────────────────────────────
    sector_map: dict[str, str] = {}
    if df_events_meta is not None and "coastal_sector" in df_events_meta.columns:
        sector_map = (
            df_events_meta
            .dropna(subset=["municipality"])
            .drop_duplicates(subset=["municipality"])
            .set_index("municipality")["coastal_sector"]
            .to_dict()
        )

    n_ok = 0
    n_skip = 0

    for hs_pct, ssh_pct in pct_pairs:
        pair_label = f"hs=q{round(hs_pct*100)} / ssh=q{round(ssh_pct*100)}"
        log.info("  Pair %s …", pair_label)

        for rec in records:
            key = (round(float(rec.grid_lat), 6), round(float(rec.grid_lon), 6))
            ssh_total_clim = ssh_total_cache.get(key, pd.Series(dtype=float))

            # Look up capture status
            row = df_event_hits_all[
                (df_event_hits_all["event_idx"]   == rec.event_idx)
                & (df_event_hits_all["thr_hs_pct"]  == hs_pct)
                & (df_event_hits_all["thr_ssh_pct"] == ssh_pct)
            ]
            captured = bool(row.iloc[0]["captured"]) if not row.empty else False

            try:
                fig = make_event_timeseries_figure(rec, ssh_total_clim, hs_pct, ssh_pct, captured)
                fname = _figure_filename(rec, hs_pct, ssh_pct)
                _save_event_figure(fig, fname)
                n_ok += 1
            except Exception as exc:
                log.warning(
                    "Event figure failed: %s %s pair %s: %s",
                    rec.municipality, rec.date.date(), pair_label, exc,
                )
                n_skip += 1

    log.info("Event figures: %d saved, %d skipped.", n_ok, n_skip)

    # ── Generate TypeScript content file ──────────────────────────────────
    _write_tc4events_ts(records, df_event_hits_all, sector_map, pct_pairs, optimal)


# ── TypeScript content file generation ───────────────────────────────────────

def _pt_br_month(month: int) -> str:
    """Return abbreviated month name in Brazilian Portuguese."""
    return [
        "", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
        "Jul", "Ago", "Set", "Out", "Nov", "Dez",
    ][month]


def _write_tc4events_ts(
    records: list,
    df_event_hits_all: pd.DataFrame,
    sector_map: dict[str, str],
    pct_pairs: list[tuple[float, float]],
    optimal: dict | None,
) -> None:
    """Write ``site/content/tc4Events.ts`` from the batch figure run.

    The file is consumed by the Tc4EventSelector React component.
    """
    # Only the diagonal pairs go into the site selector
    diagonal_pcts = [int(round(p * 100)) for p in _DIAGONAL_PCTS]

    # Deduplicate records by (event_idx) — one entry per unique event record
    seen: set[int] = set()
    entries: list[str] = []

    for rec in records:
        if rec.event_idx in seen:
            continue
        seen.add(rec.event_idx)

        slug   = _muni_slug(rec.municipality)
        sector = sector_map.get(rec.municipality, "")
        date_str = rec.date.strftime("%Y%m%d")
        label = (
            f"{rec.municipality} \u2014 "
            f"{rec.date.day:02d} {_pt_br_month(rec.date.month)} {rec.date.year}"
        )

        # Build capturedAt for diagonal pairs only
        captured_parts: list[str] = []
        for pct_int in diagonal_pcts:
            pct_float = pct_int / 100.0
            row = df_event_hits_all[
                (df_event_hits_all["event_idx"]   == rec.event_idx)
                & (df_event_hits_all["thr_hs_pct"]  == pct_float)
                & (df_event_hits_all["thr_ssh_pct"] == pct_float)
            ]
            captured_val = bool(row.iloc[0]["captured"]) if not row.empty else False
            captured_parts.append(f'"{pct_int}": {"true" if captured_val else "false"}')

        captured_at_str = "{ " + ", ".join(captured_parts) + " }"

        # Determine if captured at optimal pair
        captured_opt = False
        if optimal is not None:
            opt_row = df_event_hits_all[
                (df_event_hits_all["event_idx"]   == rec.event_idx)
                & (df_event_hits_all["thr_hs_pct"]  == float(optimal["thr_hs_pct"]))
                & (df_event_hits_all["thr_ssh_pct"] == float(optimal["thr_ssh_pct"]))
            ]
            captured_opt = bool(opt_row.iloc[0]["captured"]) if not opt_row.empty else False

        entries.append(
            f'  {{\n'
            f'    label: "{label}",\n'
            f'    sector: "{sector}",\n'
            f'    disasterId: {rec.disaster_id},\n'
            f'    date: "{date_str}",\n'
            f'    slug: "{slug}",\n'
            f'    capturedOptimal: {"true" if captured_opt else "false"},\n'
            f'    capturedAt: {captured_at_str},\n'
            f'  }}'
        )

    opt_hs_pct  = int(round(optimal["thr_hs_pct"]  * 100)) if optimal else "null"
    opt_ssh_pct = int(round(optimal["thr_ssh_pct"] * 100)) if optimal else "null"

    ts_content = (
        "// AUTO-GENERATED — do not edit by hand.\n"
        "// Regenerate with: python src/02_threshold_calibration/04_csi_grid_scan/main.py --summary\n"
        "// or:              python src/02_threshold_calibration/04_csi_grid_scan/main.py --timeseries\n"
        "\n"
        "export type Tc4EventEntry = {\n"
        "  label: string;\n"
        "  sector: string;\n"
        "  disasterId: number;\n"
        "  date: string;           // 'YYYYMMDD'\n"
        "  slug: string;\n"
        "  capturedOptimal: boolean;\n"
        "  capturedAt: Record<string, boolean>;  // '50', '55', …, '90'\n"
        "};\n"
        "\n"
        f"export const TC4_OPTIMAL_HS_PCT  = {opt_hs_pct};\n"
        f"export const TC4_OPTIMAL_SSH_PCT = {opt_ssh_pct};\n"
        "\n"
        "export const tc4Events: Tc4EventEntry[] = [\n"
        + ",\n".join(entries)
        + "\n];\n"
    )

    _SITE_CONTENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    _SITE_CONTENT_FILE.write_text(ts_content, encoding="utf-8")
    log.info("  -> tc4Events.ts: %s (%d entries)", _SITE_CONTENT_FILE, len(entries))
