"""
Summary output generation for the threshold calibration analysis (OSR11 — Step 3b).

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

import numpy as np
import pandas as pd

from src.threshold_calibration.config.analysis_config import CFG
from src.threshold_calibration.figures import run_figures
from src.threshold_calibration.event_figures import run_event_figures
from src.threshold_calibration.metrics import build_event_hit_table, capture_lag_summary
from src.threshold_calibration.calibration import _local_threshold
from src.threshold_calibration.windows import build_causal_window

log = logging.getLogger(__name__)


def _empirical_percentile(climatology: pd.Series, values: pd.Series) -> pd.Series:
    """Return each value's local empirical percentile on a 0–100 scale."""
    finite = np.sort(climatology.dropna().to_numpy(dtype=float))
    result = pd.Series(np.nan, index=values.index, dtype=float)
    valid = values.notna()
    if finite.size and valid.any():
        result.loc[valid] = (
            np.searchsorted(finite, values.loc[valid].to_numpy(dtype=float), side="right")
            / finite.size * 100.0
        )
    return result


def build_local_threshold_audits(
    records: list,
    ssh_total_cache: dict,
    df_event_hits_opt: pd.DataFrame,
    optimal: dict,
    time_index: pd.DatetimeIndex,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build event- and grid-level proof of the local-threshold calculation.

    The values are recomputed from the same full climatological series and with
    the same helper used by the operational hit/miss and false-alarm paths.
    ``time_index`` is used only to construct the causal window; it is never used
    to truncate the climatology from which thresholds are estimated.
    """
    hs_pct = float(optimal["thr_hs_pct"])
    ssh_pct = float(optimal["thr_ssh_pct"])
    hit_by_idx = df_event_hits_opt.set_index("event_idx").to_dict("index")
    rows: list[dict] = []

    for rec in records:
        key = (round(float(rec.grid_lat), 6), round(float(rec.grid_lon), 6))
        ssh = ssh_total_cache.get(key, pd.Series(dtype=float))
        hs_finite = rec.hs_clim.dropna()
        ssh_finite = ssh.dropna()
        thr_hs = _local_threshold(rec.hs_clim, hs_pct)
        thr_ssh = _local_threshold(ssh, ssh_pct)
        window = pd.DatetimeIndex(build_causal_window(rec.date, time_index))
        hs_win = rec.hs_clim.reindex(window)
        ssh_win = ssh.reindex(window)
        valid_both = hs_win.notna() & ssh_win.notna()

        peak_hs_date = hs_win.idxmax() if hs_win.notna().any() else pd.NaT
        peak_ssh_date = ssh_win.idxmax() if ssh_win.notna().any() else pd.NaT
        peak_hs = float(hs_win.max()) if hs_win.notna().any() else np.nan
        peak_ssh = float(ssh_win.max()) if ssh_win.notna().any() else np.nan

        hs_ratio = hs_win / thr_hs if np.isfinite(thr_hs) and thr_hs != 0 else hs_win * np.nan
        ssh_ratio = ssh_win / thr_ssh if np.isfinite(thr_ssh) and thr_ssh != 0 else ssh_win * np.nan
        hs_quantile = _empirical_percentile(rec.hs_clim, hs_win)
        ssh_quantile = _empirical_percentile(ssh, ssh_win)
        joint_score = pd.concat([hs_quantile, ssh_quantile], axis=1).min(axis=1, skipna=False)
        joint_score = joint_score[valid_both]
        simultaneous_date = joint_score.idxmax() if joint_score.notna().any() else pd.NaT
        hit = hit_by_idx.get(rec.event_idx, {})

        rows.append({
            "event_idx": rec.event_idx,
            "event_identifier": f"TC4-E{int(rec.disaster_id):03d}-{int(rec.event_idx):03d}",
            "disaster_id": rec.disaster_id,
            "event_date": rec.date,
            "municipality": rec.municipality,
            "sector": hit.get("coastal_sector", ""),
            "grid_lat": float(rec.grid_lat),
            "grid_lon": float(rec.grid_lon),
            "hs_percentile_level": hs_pct,
            "local_hs_threshold_m": thr_hs,
            "ssh_total_percentile_level": ssh_pct,
            "local_ssh_total_threshold_m": thr_ssh,
            "hs_reference_start": hs_finite.index.min() if not hs_finite.empty else pd.NaT,
            "hs_reference_end": hs_finite.index.max() if not hs_finite.empty else pd.NaT,
            "ssh_total_reference_start": ssh_finite.index.min() if not ssh_finite.empty else pd.NaT,
            "ssh_total_reference_end": ssh_finite.index.max() if not ssh_finite.empty else pd.NaT,
            "n_valid_hs_observations": int(len(hs_finite)),
            "n_valid_ssh_total_observations": int(len(ssh_finite)),
            "n_valid_joint_window_observations": int(valid_both.sum()),
            "window_peak_hs_m": peak_hs,
            "window_peak_hs_date": peak_hs_date,
            "window_peak_ssh_total_m": peak_ssh,
            "window_peak_ssh_total_date": peak_ssh_date,
            "window_peak_hs_ratio": peak_hs / thr_hs if np.isfinite(thr_hs) else np.nan,
            "window_peak_ssh_total_ratio": peak_ssh / thr_ssh if np.isfinite(thr_ssh) else np.nan,
            "window_peak_hs_quantile": float(hs_quantile.get(peak_hs_date, np.nan)),
            "window_peak_ssh_total_quantile": float(ssh_quantile.get(peak_ssh_date, np.nan)),
            "max_min_quantile_date": simultaneous_date,
            "max_min_hs_m": float(hs_win.get(simultaneous_date, np.nan)),
            "max_min_ssh_total_m": float(ssh_win.get(simultaneous_date, np.nan)),
            "max_min_hs_ratio": float(hs_ratio.get(simultaneous_date, np.nan)),
            "max_min_ssh_total_ratio": float(ssh_ratio.get(simultaneous_date, np.nan)),
            "max_min_hs_quantile": float(hs_quantile.get(simultaneous_date, np.nan)),
            "max_min_ssh_total_quantile": float(ssh_quantile.get(simultaneous_date, np.nan)),
            "capture_day": hit.get("capture_time", pd.NaT),
            "hs_at_capture_m": hit.get("hs_at_capture", np.nan),
            "ssh_total_at_capture_m": hit.get("ssh_total_at_capture", np.nan),
            "captured": bool(hit.get("captured", False)),
        })

    events = pd.DataFrame(rows)
    grid_cols = [
        "grid_lat", "grid_lon", "hs_percentile_level", "local_hs_threshold_m",
        "ssh_total_percentile_level", "local_ssh_total_threshold_m",
        "hs_reference_start", "hs_reference_end", "ssh_total_reference_start",
        "ssh_total_reference_end", "n_valid_hs_observations",
        "n_valid_ssh_total_observations",
    ]
    grids = events[grid_cols].drop_duplicates(subset=["grid_lat", "grid_lon"]).copy()
    muni_by_grid = (
        events.groupby(["grid_lat", "grid_lon"])["municipality"]
        .agg(lambda values: " | ".join(sorted(set(values))))
        .rename("municipalities")
        .reset_index()
    )
    grids = muni_by_grid.merge(grids, on=["grid_lat", "grid_lon"], how="left")
    return events, grids


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
    fa_per_muni_df: pd.DataFrame | None = None,
    records: list | None = None,
    ssh_total_cache: dict | None = None,
    time_index=None,
) -> None:
    """Generate all summary tables and figures for Step 3b.

    Parameters
    ----------
    df_metrics     : output of metrics.compute_scores()
    df_ranked      : output of metrics.rank_combinations()
    optimal        : dict — best threshold pair and its metrics
    all_captures   : list[CaptureResult] from calibration.run_hits_misses()
    df_events_meta : reported events DataFrame (for sector metadata)
    fa_per_muni_df : per-municipality false alarm counts across all threshold
                     pairs (from calibration.run_false_alarms()). Optional.
    records : list[EventRecord] | None
        If provided (together with ssh_total_cache and time_index), per-event
        time-series figures are generated and site/content/tc4Events.ts is
        written.
    ssh_total_cache : dict | None
        SSH_total climatological cache, keyed by (lat, lon).
    time_index : pd.DatetimeIndex | None
        Full (clipped) time coordinate of the dataset.
    """
    log.info("== Generating Step 3b summary outputs ==")

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

    # Explicit audit of the physical local thresholds and same-day capture rule.
    df_threshold_audit = None
    if records is not None and ssh_total_cache is not None and time_index is not None:
        df_event_audit, df_grid_audit = build_local_threshold_audits(
            records, ssh_total_cache, df_event_hits_opt, optimal,
            pd.DatetimeIndex(time_index),
        )
        _save_csv(df_event_audit, "tab_TC4_event_threshold_audit")
        _save_csv(df_grid_audit, "tab_TC4_grid_threshold_audit")
        df_threshold_audit = df_event_audit

    # Optimal pair summary row
    opt_df = pd.DataFrame([optimal])
    _save_csv(opt_df, "tab_TC4_optimal_pair")

    # Lag summary
    lag_sum = capture_lag_summary(df_event_hits_opt)
    _save_csv(lag_sum, "tab_TC4_lag_summary")

    # Per-municipality false alarm counts (all threshold pairs)
    if fa_per_muni_df is not None and not fa_per_muni_df.empty:
        _save_csv(fa_per_muni_df, "tab_TC4_false_alarms_per_municipality")
    else:
        log.info("  No per-municipality FA data provided — tab_TC4_false_alarms_per_municipality not saved.")

    # ── Figures ───────────────────────────────────────────────────────────────
    # Load the municipality → grid reference table for the audit map (TC4-A1).
    # If the file does not exist, the audit figure is silently skipped.
    df_muni_ref = None
    _ref_path = CFG.get("municipality_grid_ref")
    if _ref_path is not None and Path(_ref_path).exists():
        try:
            df_muni_ref = pd.read_csv(_ref_path)
            log.info("  Loaded municipality grid reference: %d rows", len(df_muni_ref))
        except Exception as exc:
            log.warning("  Could not load municipality grid reference: %s", exc)

    run_figures(df_metrics, df_event_hits_all, lag_sum, optimal,
                df_muni_ref=df_muni_ref, df_events_meta=df_events_meta,
                df_fa_per_muni=fa_per_muni_df,
                records=records,
                ssh_total_cache=ssh_total_cache,
                df_threshold_audit=df_threshold_audit)

    # ── Per-event time-series figures ─────────────────────────────────────────
    if records is not None and ssh_total_cache is not None:
        log.info("Generating per-event time-series figures (diagonal pairs q50–q90)...")
        run_event_figures(
            records=records,
            ssh_total_cache=ssh_total_cache,
            time_index=time_index,
            df_event_hits_all=df_event_hits_all,
            df_events_meta=df_events_meta,
            optimal=optimal,
        )
    else:
        log.info(
            "Skipping per-event time-series figures — records or ssh_total_cache not provided."
        )

    # ── Run log ───────────────────────────────────────────────────────────────
    _write_run_log(df_metrics, df_ranked, optimal, df_event_hits_opt, lag_sum)

    log.info("== Step 3b summary complete ==")


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
        "OSR11 — Step 3b: Threshold Calibration (CSI Grid Scan)",
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
        f"  SSH_total         : zos (00:00 UTC) + FES2022 tide (daily maximum)",
        f"  Hₛ convention     : daily maximum (from 3-hourly WAVERYS)",
        f"  SSH convention    : 00:00 UTC snapshot (GLORYS12 is a daily product)",
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
