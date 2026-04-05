"""
Threshold and metrics computation for the tidal sensitivity analysis.

Extends src.preliminary_compound.thresholds by computing an additional
set of metrics based on SSH_total = SSH + FES2022 tide.

The function compute_thresholds_total() mirrors compute_thresholds() from
the preliminary compound module but operates on the SSH_total series.

The function compute_event_metrics_total() produces the same columns as
compute_event_metrics() plus *_total variants so that SSH-only and
SSH_total results can be compared directly.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from src.tidal_sensitivity.config.analysis_config import CFG

log = logging.getLogger(__name__)

# ── q90 threshold computation ──────────────────────────────────────────────────

def compute_thresholds_total(
    records,
    tide_cache: dict,
) -> dict[str, dict]:
    """
    Compute q90 thresholds for SSH_total at each municipality.

    Returns
    -------
    dict : {municipality: {ssh_total_q90, ssh_total_mean, ssh_total_std, ssh_total_p99, ...}}
    """
    from src.tidal_sensitivity.tides import add_tide_to_ssh, get_tide_for_record

    q = CFG["threshold_quantile"]
    thresholds: dict[str, dict] = {}

    for rec in records:
        muni = rec.municipality
        if muni in thresholds:
            continue
        tide = get_tide_for_record(rec, tide_cache)
        ssh_total_clim = add_tide_to_ssh(rec.ssh_clim, tide)

        finite_ssh_total = ssh_total_clim.dropna()
        if finite_ssh_total.empty:
            thresholds[muni] = {k: np.nan for k in (
                "ssh_total_q90", "ssh_total_mean", "ssh_total_std", "ssh_total_p99"
            )}
            continue

        thresholds[muni] = {
            "ssh_total_q90":  float(finite_ssh_total.quantile(q)),
            "ssh_total_mean": float(finite_ssh_total.mean()),
            "ssh_total_std":  float(finite_ssh_total.std()),
            "ssh_total_p99":  float(finite_ssh_total.quantile(0.99)),
        }

    return thresholds


# ── Per-event metrics ─────────────────────────────────────────────────────────

def compute_event_metrics_total(
    records,
    thresholds_ssh: dict,
    thresholds_total: dict,
    tide_cache: dict,
) -> pd.DataFrame:
    """
    Compute per-event metrics for BOTH SSH-only and SSH_total analyses.

    Parameters
    ----------
    records : list[EventRecord]
    thresholds_ssh   : from src.preliminary_compound.thresholds.compute_thresholds()
    thresholds_total : from compute_thresholds_total() above
    tide_cache       : tidal series cache from tides.build_tide_cache()

    Returns
    -------
    DataFrame with one row per event containing:
      - All columns from the preliminary compound metrics (ssh-only)
      - Additional *_total columns for SSH_total-based metrics
      - detected_ssh, detected_total : bool, whether concurrent at q90
      - detection_change : 'new', 'lost', 'maintained', 'neither'
    """
    from src.preliminary_compound.thresholds import compute_event_metrics
    from src.tidal_sensitivity.tides import add_tide_to_ssh, get_tide_for_record

    # Re-compute SSH-only metrics using the preliminary_compound logic
    df_ssh = compute_event_metrics(records, thresholds_ssh)

    rows = []
    half = CFG["event_half_window_days"]

    for rec in records:
        muni = rec.municipality
        thr_ssh   = thresholds_ssh.get(muni, {})
        thr_total = thresholds_total.get(muni, {})

        tide = get_tide_for_record(rec, tide_cache)
        ssh_total_clim = add_tide_to_ssh(rec.ssh_clim, tide)

        # Extract window for SSH_total
        win_mask = (
            (ssh_total_clim.index >= rec.window_start) &
            (ssh_total_clim.index <= rec.window_end)
        )
        ssh_total_win = ssh_total_clim[win_mask]

        hs_q90    = thr_ssh.get("hs_q90", np.nan)
        total_q90 = thr_total.get("ssh_total_q90", np.nan)
        total_mean = thr_total.get("ssh_total_mean", np.nan)

        finite_total = ssh_total_win.dropna()
        finite_hs    = rec.hs_window.dropna()

        if finite_total.empty:
            row = dict(
                event_idx=rec.event_idx,
                ssh_total_max_window=np.nan,
                ssh_total_max_norm=np.nan,
                ssh_total_days_above=np.nan,
                n_concurrent_total=np.nan,
                concurrent_fraction_total=np.nan,
                is_concurrent_total=False,
            )
        else:
            ssh_total_max = float(finite_total.max())
            ssh_total_max_norm = (
                ssh_total_max / total_mean if total_mean and not np.isnan(total_mean) else np.nan
            )

            above_hs    = (rec.hs_window >= hs_q90).reindex(ssh_total_win.index, fill_value=False)
            above_total = ssh_total_win >= total_q90
            concurrent  = above_hs & above_total
            n_concurrent_total = int(concurrent.sum())
            window_len  = max(len(ssh_total_win), 1)

            row = dict(
                event_idx=rec.event_idx,
                ssh_total_max_window=ssh_total_max,
                ssh_total_max_norm=ssh_total_max_norm,
                ssh_total_days_above=int((ssh_total_win >= total_q90).sum()),
                n_concurrent_total=n_concurrent_total,
                concurrent_fraction_total=n_concurrent_total / window_len,
                is_concurrent_total=n_concurrent_total > 0,
            )

        rows.append(row)

    df_total = pd.DataFrame(rows)

    # Merge with SSH-only metrics
    df = df_ssh.merge(df_total, on="event_idx", how="left")

    # Detection-change column
    def _change(row) -> str:
        had = bool(row["is_concurrent"])
        has = bool(row.get("is_concurrent_total", False))
        if not had and has:
            return "new"
        if had and not has:
            return "lost"
        if had and has:
            return "maintained"
        return "neither"

    df["detection_change"] = df.apply(_change, axis=1)

    # Add coastal_sector if not already present (comes from events CSV, not EventRecord)
    if "coastal_sector" not in df.columns:
        try:
            from src.preliminary_compound.io import load_reported_events
            ev = load_reported_events()
            sector_map = ev.set_index("disaster_id")["coastal_sector"].to_dict()
            df["coastal_sector"] = df["disaster_id"].map(sector_map)
        except Exception:
            df["coastal_sector"] = None

    return df
