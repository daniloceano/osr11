"""
Verification metrics and optimal pair selection for the CSI grid scan.

Metrics computed
----------------
For each threshold pair (thr_hs_pct, thr_ssh_pct):

    POD = H / (H + M)          Probability of Detection (hit rate)
    FAR = F / (H + F)          False Alarm Ratio
    CSI = H / (H + M + F)      Critical Success Index

Where:
    H = hits   (observed events captured by the causal window rule)
    M = misses (observed events not captured)
    F = false alarms (compound episodes not paired with any observed event)

Optimal pair selection hierarchy
---------------------------------
1. Highest CSI
2. Lowest FAR (tiebreaker for near-equal CSI)
3. Highest percentile sum (most restrictive pair, second tiebreaker)

References
----------
- NOAA / Space Weather Prediction Center — Forecast Verification Glossary
- Green et al. (2025) — comprehensive review of compound flooding literature
  (nhess.copernicus.org/articles/25/747/2025/)
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


def compute_scores(
    contingency: pd.DataFrame,
    false_alarms: pd.DataFrame,
) -> pd.DataFrame:
    """Merge H/M and F counts and compute POD, FAR, CSI for each threshold pair.

    Parameters
    ----------
    contingency : DataFrame with columns [thr_hs_pct, thr_ssh_pct, H, M]
    false_alarms : DataFrame with columns [thr_hs_pct, thr_ssh_pct, F]

    Returns
    -------
    DataFrame with columns:
        thr_hs_pct, thr_ssh_pct,
        H, M, F,
        POD, FAR, CSI
    """
    df = contingency.merge(false_alarms, on=["thr_hs_pct", "thr_ssh_pct"], how="left")
    df["F"] = df["F"].fillna(0).astype(int)

    # POD = H / (H + M)
    total_obs = df["H"] + df["M"]
    df["POD"] = np.where(total_obs > 0, df["H"] / total_obs, np.nan)

    # FAR = F / (H + F)
    total_det = df["H"] + df["F"]
    df["FAR"] = np.where(total_det > 0, df["F"] / total_det, np.nan)

    # CSI = H / (H + M + F)
    total_hmf = df["H"] + df["M"] + df["F"]
    df["CSI"] = np.where(total_hmf > 0, df["H"] / total_hmf, np.nan)

    return df


def rank_combinations(df_metrics: pd.DataFrame) -> pd.DataFrame:
    """Return df_metrics sorted by (CSI desc, FAR asc, percentile sum desc).

    Parameters
    ----------
    df_metrics : output of compute_scores()

    Returns
    -------
    DataFrame sorted by the optimal pair selection hierarchy, with a
    'rank' column added (1 = best).
    """
    df = df_metrics.copy()
    df["pct_sum"] = df["thr_hs_pct"] + df["thr_ssh_pct"]
    df = df.sort_values(
        by=["CSI", "FAR", "pct_sum"],
        ascending=[False, True, False],
    ).reset_index(drop=True)
    df.insert(0, "rank", range(1, len(df) + 1))
    return df


def select_optimal_pair(df_metrics: pd.DataFrame) -> dict:
    """Identify and return the optimal threshold pair.

    Parameters
    ----------
    df_metrics : output of compute_scores()

    Returns
    -------
    dict with keys: thr_hs_pct, thr_ssh_pct, H, M, F, POD, FAR, CSI
    """
    ranked = rank_combinations(df_metrics)
    best = ranked.iloc[0]
    log.info(
        "Optimal pair: hs=q%.0f / ssh=q%.0f → CSI=%.3f  FAR=%.3f  POD=%.3f  H=%d M=%d F=%d",
        best["thr_hs_pct"] * 100,
        best["thr_ssh_pct"] * 100,
        best["CSI"],
        best["FAR"],
        best["POD"],
        best["H"],
        best["M"],
        best["F"],
    )
    return best.to_dict()


def build_event_hit_table(
    all_captures: list,
    df_events_meta: pd.DataFrame,
) -> pd.DataFrame:
    """Build per-event hit/miss table at the optimal threshold pair.

    Parameters
    ----------
    all_captures : list[CaptureResult] from calibration.run_hits_misses()
    df_events_meta : reported events DataFrame (for sector and other metadata)

    Returns
    -------
    DataFrame with one row per event, columns:
        event_idx, disaster_id, municipality, date,
        thr_hs_pct, thr_ssh_pct,
        captured, lag_from_event_day,
        hs_at_capture, ssh_total_at_capture,
        capture_time, coastal_sector
    """
    rows = [
        {
            "event_idx":           c.event_idx,
            "disaster_id":         c.disaster_id,
            "municipality":        c.municipality,
            "date":                c.date,
            "thr_hs_pct":          c.thr_hs_pct,
            "thr_ssh_pct":         c.thr_ssh_pct,
            "captured":            c.captured,
            "lag_from_event_day":  c.lag_from_event_day,
            "hs_at_capture":       c.hs_at_capture,
            "ssh_total_at_capture": c.ssh_total_at_capture,
            "capture_time":        c.capture_time,
            "n_admissible":        c.n_admissible,
            "n_compound":          c.n_compound,
        }
        for c in all_captures
    ]
    df = pd.DataFrame(rows)

    # Add coastal sector if available
    if df_events_meta is not None and "coastal_sector" in df_events_meta.columns:
        sector_map = (
            df_events_meta
            .dropna(subset=["disaster_id"])
            .drop_duplicates(subset=["disaster_id"])
            .set_index("disaster_id")["coastal_sector"]
            .to_dict()
        )
        df["coastal_sector"] = df["disaster_id"].map(sector_map)

    return df


def capture_lag_summary(df_event_hits: pd.DataFrame) -> pd.DataFrame:
    """Summarise how many captures occurred at each lag offset.

    Parameters
    ----------
    df_event_hits : output of build_event_hit_table() for the optimal pair,
                    restricted to hits (captured == True).

    Returns
    -------
    DataFrame with columns [lag, count, fraction]
    """
    captured = df_event_hits[df_event_hits["captured"]].copy()
    counts = (
        captured["lag_from_event_day"]
        .value_counts()
        .sort_index()
        .reset_index()
    )
    counts.columns = ["lag", "count"]
    counts["fraction"] = counts["count"] / counts["count"].sum()
    label_map = {-2: "D-2", -1: "D-1", 0: "D", 1: "D+1 00Z"}
    counts["lag_label"] = counts["lag"].map(label_map).fillna(counts["lag"].astype(str))
    return counts
