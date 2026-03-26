"""
Summary output generation for the threshold calibration analysis (OSR11 — Step 4).

Tables saved
------------
tab_TC4_metrics_full.csv
    Full grid scan results: one row per threshold pair.
    Columns: thr_hs_pct, thr_ssh_pct, H, M, F, POD, FAR, CSI

tab_TC4_metrics_ranked.csv
    Same as above, sorted by the optimal pair selection hierarchy
    (CSI desc → FAR asc → pct_sum desc). Includes a 'rank' column.

tab_TC4_event_hits.csv
    Per-event capture results at ALL threshold pairs (full long table).
    Useful for downstream analysis and debugging.

tab_TC4_event_hits_optimal.csv
    Per-event capture results at the OPTIMAL threshold pair only.
    The primary event-level output.

tab_TC4_lag_summary.csv
    Distribution of capture lags at the optimal threshold pair.

tab_TC4_optimal_pair.csv
    Single-row summary of the optimal threshold pair and its metrics.
    Provides a stable reference for downstream steps.

Logs
----
    log_TC4_na_warnings.txt   (municipalities with NaN thresholds)
    log_TC4_run_summary.txt   (key run metadata and results)
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.threshold_calibration.config.analysis_config import CFG
from src.threshold_calibration.figures import run_figures
from src.threshold_calibration.metrics import build_event_hit_table, capture_lag_summary

log = logging.getLogger(__name__)


def _save_csv(df: pd.DataFrame, name: str) -> None:
    path = CFG["tab_dir"] / f"{name}.csv"
    df.to_csv(path, index=False)
    log.info("  -> Table: %s", path)


def run_summary(
    df_metrics: pd.DataFrame,
    df_ranked: pd.DataFrame,
    optimal: dict,
    all_captures: list,
    df_events_meta: pd.DataFrame,
) -> None:
    """Generate all summary tables and figures for Step 4.

    Parameters
    ----------
    df_metrics : output of metrics.compute_scores()
    df_ranked  : output of metrics.rank_combinations()
    optimal    : dict — best threshold pair and its metrics
    all_captures : list[CaptureResult] from calibration.run_hits_misses()
    df_events_meta : reported events DataFrame (for sector metadata)
    """
    log.info("== Generating Step 4 summary outputs ==")

    # ── Tables ────────────────────────────────────────────────────────────────
    _save_csv(df_metrics, "tab_TC4_metrics_full")
    _save_csv(df_ranked,  "tab_TC4_metrics_ranked")

    # Full event hits table (all threshold pairs — useful for analysis)
    df_event_hits_all = build_event_hit_table(all_captures, df_events_meta)
    _save_csv(df_event_hits_all, "tab_TC4_event_hits")

    # Optimal pair event hits
    df_event_hits_opt = df_event_hits_all[
        (df_event_hits_all["thr_hs_pct"]  == optimal["thr_hs_pct"]) &
        (df_event_hits_all["thr_ssh_pct"] == optimal["thr_ssh_pct"])
    ].copy()
    _save_csv(df_event_hits_opt, "tab_TC4_event_hits_optimal")

    # Optimal pair summary row
    opt_df = pd.DataFrame([optimal])
    _save_csv(opt_df, "tab_TC4_optimal_pair")

    # Lag summary
    lag_sum = capture_lag_summary(df_event_hits_opt)
    _save_csv(lag_sum, "tab_TC4_lag_summary")

    # ── Figures ───────────────────────────────────────────────────────────────
    run_figures(df_metrics, df_event_hits_all, lag_sum, optimal)

    # ── Run log ───────────────────────────────────────────────────────────────
    _write_run_log(df_metrics, df_ranked, optimal, df_event_hits_opt, lag_sum)

    log.info("== Step 4 summary complete ==")


def _write_run_log(
    df_metrics: pd.DataFrame,
    df_ranked: pd.DataFrame,
    optimal: dict,
    df_event_hits_opt: pd.DataFrame,
    lag_sum: pd.DataFrame,
) -> None:
    """Write a human-readable run summary log."""
    path = CFG["log_dir"] / "log_TC4_run_summary.txt"
    lines = [
        "=" * 70,
        "OSR11 — Step 4: Threshold Calibration (CSI Grid Scan)",
        "=" * 70,
        "",
        "CONFIGURATION",
        f"  Sweep             : q{round(CFG['pct_start']*100)}–q{round(CFG['pct_stop']*100)} "
        f"in {round(CFG['pct_step']*100):.0f}% steps  "
        f"(pct_start/pct_stop/pct_step in analysis_config.py)",
        f"  Hₛ percentiles    : {[f'q{round(p*100)}' for p in CFG['hs_percentiles']]}",
        f"  SSH percentiles   : {[f'q{round(p*100)}' for p in CFG['ssh_total_percentiles']]}",
        f"  Total pairs       : {len(df_metrics)}",
        f"  Match window      : {CFG['match_window_offsets']} days (D-2, D-1, D, D+1 00Z)",
        f"  Episode max gap   : {CFG['episode_max_gap_days']} day",
        f"  SSH_total         : zos + FES2022 tide (instantaneous 00:00 UTC)",
        "",
        "OPTIMAL PAIR",
        f"  Hₛ threshold      : q{round(optimal['thr_hs_pct']*100)}",
        f"  SSH_total thr.    : q{round(optimal['thr_ssh_pct']*100)}",
        f"  CSI               : {optimal['CSI']:.4f}",
        f"  POD               : {optimal['POD']:.4f}",
        f"  FAR               : {optimal['FAR']:.4f}",
        f"  H (hits)          : {int(optimal['H'])}",
        f"  M (misses)        : {int(optimal['M'])}",
        f"  F (false alarms)  : {int(optimal['F'])}",
        "",
        "TOP 10 RANKED PAIRS",
    ]
    top10_cols = ["rank", "thr_hs_pct", "thr_ssh_pct", "CSI", "POD", "FAR", "H", "M", "F"]
    available = [c for c in top10_cols if c in df_ranked.columns]
    lines.append(df_ranked[available].head(10).to_string(index=False))
    lines.append("")

    if not lag_sum.empty:
        lines.append("CAPTURE LAG DISTRIBUTION (optimal pair)")
        lines.append(lag_sum[["lag_label", "count", "fraction"]].to_string(index=False))
        lines.append("")

    total_events = len(df_event_hits_opt)
    hits = int(df_event_hits_opt["captured"].sum())
    lines += [
        "EVENT-LEVEL SUMMARY (optimal pair)",
        f"  Total events      : {total_events}",
        f"  Captured (hits)   : {hits} ({100*hits/total_events:.1f}%)",
        f"  Missed            : {total_events - hits} ({100*(total_events-hits)/total_events:.1f}%)",
        "",
        "=" * 70,
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))
    log.info("  -> Run log: %s", path)
