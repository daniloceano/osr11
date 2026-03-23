"""
Threshold computation for the threshold calibration analysis.

Computes per-municipality, per-variable q90 thresholds from the full
climatological series. These initial thresholds are used for the first
exploratory calibration against reported events.

Design
------
- Threshold = q90 (90th percentile) of the full daily series at the nearest
  coastal grid point to each municipality.
- The full series (1993–2025) is used rather than a seasonal sub-sample;
  seasonal thresholds may be explored in later phases.
- NaN values are excluded from the percentile calculation.
- Normalisation reference: the same climatological series that defines the
  threshold (so threshold_normalised = quantile, always = 0.90 by construction;
  the normalised peak value is what varies between events).
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from src.threshold_calibration.config.analysis_config import CFG
from src.threshold_calibration.events import EventRecord

log = logging.getLogger(__name__)


def compute_thresholds(records: list[EventRecord]) -> dict[str, dict[str, float]]:
    """Compute q90 thresholds for each unique municipality.

    Parameters
    ----------
    records : list of EventRecord

    Returns
    -------
    dict keyed by municipality.  Each value is:
        {
            "hs_q90":        float,  # Hs threshold (m)
            "ssh_q90":       float,  # SSH threshold (m)
            "hs_mean":       float,  # Hs climatological mean
            "ssh_mean":      float,  # SSH climatological mean
            "hs_std":        float,  # Hs climatological std
            "ssh_std":       float,  # SSH climatological std
            "hs_p99":        float,  # Hs 99th percentile
            "ssh_p99":       float,  # SSH 99th percentile
        }
    """
    q = CFG["threshold_quantile"]
    thresholds: dict[str, dict[str, float]] = {}

    # Use the first record per municipality to get the full climatological series
    seen: dict[str, EventRecord] = {}
    for rec in records:
        if rec.municipality not in seen:
            seen[rec.municipality] = rec

    for muni, rec in seen.items():
        hs_vals  = rec.hs_clim.dropna().values
        ssh_vals = rec.ssh_clim.dropna().values

        thresholds[muni] = {
            "hs_q90":  float(np.nanpercentile(hs_vals,  q * 100)),
            "ssh_q90": float(np.nanpercentile(ssh_vals, q * 100)),
            "hs_mean": float(np.nanmean(hs_vals)),
            "ssh_mean":float(np.nanmean(ssh_vals)),
            "hs_std":  float(np.nanstd(hs_vals)),
            "ssh_std": float(np.nanstd(ssh_vals)),
            "hs_p99":  float(np.nanpercentile(hs_vals,  99)),
            "ssh_p99": float(np.nanpercentile(ssh_vals, 99)),
        }
        log.info(
            "  %-35s  Hs q90=%.2f m  SSH q90=%.3f m",
            muni, thresholds[muni]["hs_q90"], thresholds[muni]["ssh_q90"],
        )

    return thresholds


def compute_event_metrics(
    records: list[EventRecord],
    thresholds: dict[str, dict[str, float]],
) -> pd.DataFrame:
    """Compute per-event metrics for the consolidated table.

    Metrics
    -------
    Raw (absolute):
      - hs_max_window:      Max Hs in the 7-day window (m)
      - ssh_max_window:     Max SSH in the 7-day window (m)
      - hs_max_date:        Date of Hs maximum
      - ssh_max_date:       Date of SSH maximum

    Threshold-relative:
      - hs_days_above:      Number of days with Hs > q90 threshold in window
      - ssh_days_above:     Number of days with SSH > q90 threshold in window

    Normalised (÷ climatological mean at same grid point):
      - hs_max_norm:        hs_max_window / hs_mean
      - ssh_max_norm:       ssh_max_window / ssh_mean

    Concomitance:
      - n_concurrent:       Number of time steps with BOTH Hs>q90 AND SSH>q90
      - concurrent_fraction: n_concurrent / window_length
      - is_concurrent:      1 if any concurrent exceedance, 0 otherwise
    """
    rows = []
    for rec in records:
        muni = rec.municipality
        if muni not in thresholds:
            log.warning("No threshold for '%s', skipping metrics.", muni)
            continue

        th = thresholds[muni]
        hs_win  = rec.hs_window.dropna()
        ssh_win = rec.ssh_window.dropna()

        # Align both series to their common time index
        common_idx = hs_win.index.intersection(ssh_win.index)
        hs_aligned  = hs_win.reindex(common_idx)
        ssh_aligned = ssh_win.reindex(common_idx)

        # Raw maxima
        hs_max  = float(hs_win.max())  if len(hs_win)  > 0 else np.nan
        ssh_max = float(ssh_win.max()) if len(ssh_win) > 0 else np.nan
        hs_max_date  = hs_win.idxmax()  if len(hs_win)  > 0 else pd.NaT
        ssh_max_date = ssh_win.idxmax() if len(ssh_win) > 0 else pd.NaT

        # Days above threshold
        hs_above  = int((hs_aligned  > th["hs_q90"]).sum())
        ssh_above = int((ssh_aligned > th["ssh_q90"]).sum())

        # Normalised maxima (÷ climatological mean)
        hs_norm  = hs_max  / th["hs_mean"]  if th["hs_mean"]  > 0 else np.nan
        ssh_norm = ssh_max / th["ssh_mean"] if th["ssh_mean"] > 0 else np.nan

        # Concomitance: both above threshold simultaneously
        both_above    = (hs_aligned > th["hs_q90"]) & (ssh_aligned > th["ssh_q90"])
        n_concurrent  = int(both_above.sum())
        win_len       = len(common_idx) if len(common_idx) > 0 else 1
        concurrent_frac = n_concurrent / win_len

        rows.append({
            "event_idx":         rec.event_idx,
            "disaster_id":       rec.disaster_id,
            "municipality":      muni,
            "date":              rec.date,
            "window_start":      rec.window_start,
            "window_end":        rec.window_end,
            "grid_lat":          rec.grid_lat,
            "grid_lon":          rec.grid_lon,
            "coord_source":      rec.coord_source,
            # Thresholds
            "hs_q90":            round(th["hs_q90"],  3),
            "ssh_q90":           round(th["ssh_q90"], 4),
            # Raw maxima
            "hs_max_window":     round(hs_max,  3) if not np.isnan(hs_max)  else np.nan,
            "ssh_max_window":    round(ssh_max, 4) if not np.isnan(ssh_max) else np.nan,
            "hs_max_date":       hs_max_date,
            "ssh_max_date":      ssh_max_date,
            # Normalised maxima
            "hs_max_norm":       round(hs_norm,  3) if not np.isnan(hs_norm)  else np.nan,
            "ssh_max_norm":      round(ssh_norm, 3) if not np.isnan(ssh_norm) else np.nan,
            # Days above threshold
            "hs_days_above":     hs_above,
            "ssh_days_above":    ssh_above,
            # Concomitance
            "n_concurrent":      n_concurrent,
            "concurrent_fraction": round(concurrent_frac, 3),
            "is_concurrent":     int(n_concurrent > 0),
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["municipality", "date"]).reset_index(drop=True)
    log.info("Event metrics computed: %d rows", len(df))
    return df
