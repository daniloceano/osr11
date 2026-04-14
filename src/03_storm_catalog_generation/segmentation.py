"""
Storm detection and episode segmentation for Step 3.

Implements the core storm catalog pipeline:
1. Compute local percentile thresholds per grid point
2. Build binary exceedance masks
3. Cluster consecutive exceedances into storm episodes (gap-tolerant)
4. Compute per-episode attributes
5. Assemble per-grid-point catalogs

The clustering algorithm replicates the _cluster_episodes() logic from
Step 2e (scoring.py) but operates on **single-variable** exceedance masks
(one for Hs, one for SSH_total) rather than compound masks.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

from .config import analysis_config as cfg
from .metrics import compute_episode_attributes

log = logging.getLogger(__name__)


def compute_local_threshold(
    series: pd.Series,
    percentile: float,
) -> float | None:
    """Compute a local percentile threshold from a time series.

    Parameters
    ----------
    series : pd.Series
        Daily values for one variable at one grid point.
    percentile : float
        Percentile fraction (e.g. 0.90 for q90).

    Returns
    -------
    float threshold, or None if the series has no finite values.
    """
    finite = series.dropna()
    if len(finite) == 0:
        return None
    return float(finite.quantile(percentile))


def build_exceedance_mask(
    series: pd.Series,
    threshold: float,
) -> pd.Series:
    """Create a boolean exceedance mask: True where series >= threshold.

    NaN values produce False (not an exceedance).
    """
    return series.ge(threshold).fillna(False)


def cluster_episodes(
    mask: pd.Series,
    max_gap_days: int | None = None,
) -> list[pd.DatetimeIndex]:
    """Group exceedance days into independent episodes.

    Replicates the _cluster_episodes() logic from Step 2e scoring.py.
    Two exceedance days belong to the same episode if the gap between them
    is at most ``max_gap_days + 1`` calendar days (i.e., at most
    ``max_gap_days`` non-exceedance days may separate them).

    Parameters
    ----------
    mask : pd.Series[bool]
        Boolean mask indexed by daily timestamps.
    max_gap_days : int
        Maximum gap tolerance. Default from config.

    Returns
    -------
    List of DatetimeIndex objects, one per episode.
    """
    if max_gap_days is None:
        max_gap_days = cfg.EPISODE_MAX_GAP_DAYS

    days = mask[mask].index.sort_values()
    if len(days) == 0:
        return []

    episodes: list[pd.DatetimeIndex] = []
    current: list[pd.Timestamp] = [days[0]]

    for d in days[1:]:
        gap = (d - current[-1]).days
        if gap <= max_gap_days + 1:
            current.append(d)
        else:
            episodes.append(pd.DatetimeIndex(current))
            current = [d]
    episodes.append(pd.DatetimeIndex(current))
    return episodes


def build_storm_catalog_for_point(
    *,
    grid_lat: float,
    grid_lon: float,
    series: pd.Series,
    threshold_pct: float,
    var_prefix: str,
    municipality: str | None = None,
) -> dict[str, Any]:
    """Build the complete storm catalog entry for one grid point and variable.

    Parameters
    ----------
    grid_lat, grid_lon : float
        Grid point coordinates.
    series : pd.Series
        Full time series (1993–2025) for the variable at this grid point.
    threshold_pct : float
        Percentile fraction (e.g. 0.90).
    var_prefix : str
        "hs" or "ssh_total" — used in event_id and field names.
    municipality : str or None
        Optional municipality label.

    Returns
    -------
    dict matching the catalog JSON schema (see README §4.1).
    """
    thr_abs = compute_local_threshold(series, threshold_pct)
    if thr_abs is None:
        log.warning(
            "NaN threshold at (%.4f, %.4f) for %s — all-NaN series",
            grid_lat, grid_lon, var_prefix,
        )
        return {
            "grid_lat": grid_lat,
            "grid_lon": grid_lon,
            "municipality": municipality,
            f"thr_{var_prefix}_pct": threshold_pct,
            f"thr_{var_prefix}_abs": None,
            "storms": [],
            "_skip_reason": "all_nan_series",
        }

    mask = build_exceedance_mask(series, thr_abs)
    episodes = cluster_episodes(mask)

    storms: list[dict] = []
    for ep_dates in episodes:
        attrs = compute_episode_attributes(
            dates=ep_dates,
            values=series,
            threshold=thr_abs,
            var_prefix=var_prefix,
            grid_lat=grid_lat,
            grid_lon=grid_lon,
        )
        storms.append(attrs)

    return {
        "grid_lat": grid_lat,
        "grid_lon": grid_lon,
        "municipality": municipality,
        f"thr_{var_prefix}_pct": threshold_pct,
        f"thr_{var_prefix}_abs": round(thr_abs, 6),
        "storms": storms,
    }
