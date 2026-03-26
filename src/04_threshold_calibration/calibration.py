"""
Core CSI grid scan logic for threshold calibration.

This module implements the two-layer evaluation described in the
threshold calibration process document:

Layer 1 — Hits and misses (event-by-event evaluation)
------------------------------------------------------
For each observed event (date D, municipality M):
1. Identify the causal window [D-2, D-1, D, D+1 00Z].
2. Extract Hₛ(t) and SSH_total(t) at the pre-associated grid point.
3. Apply percentile thresholds computed locally at that grid point.
4. Check if the compound condition holds at any admissible timestamp.
5. Record: captured (hit) or not captured (miss).

Layer 2 — False alarms (full-series scan)
------------------------------------------
For each unique grid point associated with at least one observed event:
1. Scan the full time series for compound days (both variables exceed
   their local thresholds simultaneously).
2. Cluster consecutive compound days (gap ≤ CFG["episode_max_gap_days"])
   into independent episodes.
3. Pair each episode with the observed events at that grid point by
   checking whether any day of the episode falls within any event's
   causal window.
4. Unpaired episodes → false alarms.

Design notes
------------
- SSH_total is used throughout (zos + FES2022 tide), consistent with Step 3.
- Thresholds are computed from the FULL climatological series at each grid
  point, not seasonally. This keeps the threshold definition simple and
  consistent with the preliminary compound analysis.
- The same EventRecord objects built by src.preliminary_compound.events
  are reused; no new grid matching is performed.
- False alarms are evaluated only at grid points with at least one observed
  event. This restricts the evaluation domain to where validation data exist,
  which is the appropriate scope for this calibration.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from src.threshold_calibration.config.analysis_config import CFG
from src.threshold_calibration.windows import build_causal_window

log = logging.getLogger(__name__)


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class CaptureResult:
    """Result of the causal window check for one event × one threshold pair."""
    event_idx: int
    disaster_id: int
    municipality: str
    date: pd.Timestamp
    thr_hs_pct: float
    thr_ssh_pct: float
    captured: bool
    capture_time: pd.Timestamp | None        # first admissible timestamp where condition holds
    lag_from_event_day: int | None           # capture_time - D in days (negative = antecedent)
    hs_at_capture: float | None              # Hₛ value at capture timestamp
    ssh_total_at_capture: float | None       # SSH_total value at capture timestamp
    n_admissible: int                        # number of admissible timestamps found in data
    n_compound: int                          # number of admissible timestamps with compound hit


@dataclass
class GridScanResults:
    """Aggregated CSI grid scan results."""
    # One CaptureResult per event per threshold pair
    captures: list[CaptureResult] = field(default_factory=list)

    # Summary contingency table: one row per threshold pair
    contingency: pd.DataFrame = field(default_factory=pd.DataFrame)

    # Per-event hit/miss summary across all threshold pairs
    event_summary: pd.DataFrame = field(default_factory=pd.DataFrame)


# ── Local threshold computation ────────────────────────────────────────────────

def _local_threshold(series: pd.Series, pct: float) -> float:
    """Compute percentile threshold from the full (finite) climatological series."""
    finite = series.dropna()
    if finite.empty:
        return np.nan
    return float(finite.quantile(pct))


# ── Episode clustering (for false alarm detection) ────────────────────────────

def _cluster_episodes(
    compound_mask: pd.Series,
    max_gap_days: int,
) -> list[pd.DatetimeIndex]:
    """Group compound days into independent episodes.

    Two compound days belong to the same episode if the gap between them
    (in calendar days) is at most max_gap_days + 1. This means that a single
    non-compound day between two compound days does NOT break the episode.

    Parameters
    ----------
    compound_mask : pd.Series (bool, DatetimeIndex)
        True where both Hₛ and SSH_total exceed their thresholds.
    max_gap_days : int
        Maximum allowed gap (in days) within one episode.

    Returns
    -------
    list of pd.DatetimeIndex
        One DatetimeIndex per episode, containing its compound days.
    """
    days = compound_mask[compound_mask].index.sort_values()
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


# ── Layer 1: event-by-event hits / misses ─────────────────────────────────────

def evaluate_event(
    rec,
    ssh_total_clim: pd.Series,
    thr_hs_pct: float,
    thr_ssh_pct: float,
    time_index: pd.DatetimeIndex,
) -> CaptureResult:
    """Evaluate capture of one event at one threshold pair.

    Parameters
    ----------
    rec : EventRecord
        Event record from src.preliminary_compound.events.
    ssh_total_clim : pd.Series
        Full climatological SSH_total series at the grid point.
    thr_hs_pct, thr_ssh_pct : float
        Percentile values (e.g., 0.75) for Hₛ and SSH_total respectively.
    time_index : pd.DatetimeIndex
        Full time coordinate of the dataset.

    Returns
    -------
    CaptureResult
    """
    # Compute local thresholds from the full climatological series
    thr_hs    = _local_threshold(rec.hs_clim, thr_hs_pct)
    thr_ssh   = _local_threshold(ssh_total_clim, thr_ssh_pct)

    # Build causal window
    match_times = build_causal_window(rec.date, time_index)
    n_admissible = len(match_times)

    if n_admissible == 0 or np.isnan(thr_hs) or np.isnan(thr_ssh):
        return CaptureResult(
            event_idx=rec.event_idx,
            disaster_id=rec.disaster_id,
            municipality=rec.municipality,
            date=rec.date,
            thr_hs_pct=thr_hs_pct,
            thr_ssh_pct=thr_ssh_pct,
            captured=False,
            capture_time=None,
            lag_from_event_day=None,
            hs_at_capture=None,
            ssh_total_at_capture=None,
            n_admissible=n_admissible,
            n_compound=0,
        )

    # Check compound condition at each admissible timestamp
    n_compound = 0
    first_capture_time: pd.Timestamp | None = None
    hs_at_cap: float | None = None
    ssh_at_cap: float | None = None

    for t in match_times:
        hs_val = rec.hs_clim.get(t, np.nan)
        ssh_val = ssh_total_clim.get(t, np.nan)

        if np.isnan(hs_val) or np.isnan(ssh_val):
            continue

        both_above = (hs_val >= thr_hs) and (ssh_val >= thr_ssh)
        if both_above:
            n_compound += 1
            if first_capture_time is None:
                first_capture_time = t
                hs_at_cap = hs_val
                ssh_at_cap = ssh_val

    captured = first_capture_time is not None

    lag: int | None = None
    if first_capture_time is not None:
        D = pd.Timestamp(rec.date.year, rec.date.month, rec.date.day)
        lag = (first_capture_time - D).days

    return CaptureResult(
        event_idx=rec.event_idx,
        disaster_id=rec.disaster_id,
        municipality=rec.municipality,
        date=rec.date,
        thr_hs_pct=thr_hs_pct,
        thr_ssh_pct=thr_ssh_pct,
        captured=captured,
        capture_time=first_capture_time,
        lag_from_event_day=lag,
        hs_at_capture=hs_at_cap,
        ssh_total_at_capture=ssh_at_cap,
        n_admissible=n_admissible,
        n_compound=n_compound,
    )


def run_hits_misses(
    records: list,
    ssh_total_cache: dict,
    time_index: pd.DatetimeIndex,
    hs_percentiles: list[float],
    ssh_percentiles: list[float],
) -> tuple[list[CaptureResult], pd.DataFrame]:
    """Run Layer 1: event-by-event hit/miss evaluation for all threshold pairs.

    Parameters
    ----------
    records : list[EventRecord]
    ssh_total_cache : dict mapping (lat, lon) → SSH_total climatological Series
    time_index : pd.DatetimeIndex
    hs_percentiles, ssh_percentiles : list of float
        Percentile values to sweep.

    Returns
    -------
    (all_captures, contingency_df)
        all_captures : flat list of CaptureResult (n_records × n_pairs)
        contingency_df : DataFrame with columns [thr_hs_pct, thr_ssh_pct, H, M]
    """
    all_captures: list[CaptureResult] = []
    n_pairs = len(hs_percentiles) * len(ssh_percentiles)
    pair_idx = 0

    rows_hm: list[dict] = []

    for hs_pct in hs_percentiles:
        for ssh_pct in ssh_percentiles:
            pair_idx += 1
            if pair_idx % 9 == 1:
                log.info(
                    "  Layer 1 grid scan: pair %d/%d  (hs=q%.0f, ssh=q%.0f)",
                    pair_idx, n_pairs,
                    round(hs_pct * 100), round(ssh_pct * 100),
                )

            H = M = 0
            for rec in records:
                key = (round(float(rec.grid_lat), 6), round(float(rec.grid_lon), 6))
                ssh_total_clim = ssh_total_cache.get(key, pd.Series(dtype=float))

                result = evaluate_event(rec, ssh_total_clim, hs_pct, ssh_pct, time_index)
                all_captures.append(result)
                if result.captured:
                    H += 1
                else:
                    M += 1

            rows_hm.append({"thr_hs_pct": hs_pct, "thr_ssh_pct": ssh_pct, "H": H, "M": M})

    contingency_df = pd.DataFrame(rows_hm)
    return all_captures, contingency_df


# ── Layer 2: false alarm detection (full-series scan) ─────────────────────────

def _build_event_windows_for_point(
    records: list,
    grid_lat: float,
    grid_lon: float,
    time_index: pd.DatetimeIndex,
) -> list[list[pd.Timestamp]]:
    """Return the list of causal windows for all events at a given grid point."""
    windows = []
    key_lat = round(grid_lat, 4)
    key_lon = round(grid_lon, 4)
    for rec in records:
        if (
            round(float(rec.grid_lat), 4) == key_lat
            and round(float(rec.grid_lon), 4) == key_lon
        ):
            w = build_causal_window(rec.date, time_index)
            if w:
                windows.append(w)
    return windows


def _episode_is_paired(
    episode: pd.DatetimeIndex,
    event_windows: list[list[pd.Timestamp]],
) -> bool:
    """Return True if any day of the episode falls within any event's causal window."""
    episode_set = set(episode)
    for window in event_windows:
        if episode_set & set(window):
            return True
    return False


def count_false_alarms_for_pair(
    records: list,
    ssh_total_cache: dict,
    time_index: pd.DatetimeIndex,
    hs_pct: float,
    ssh_pct: float,
    episode_max_gap: int,
) -> int:
    """Count false alarm episodes for one threshold pair.

    An episode is a false alarm if none of its compound days fall within
    any observed event's causal window at the same grid point.

    Parameters
    ----------
    records : list[EventRecord]
    ssh_total_cache : dict
    time_index : pd.DatetimeIndex
    hs_pct, ssh_pct : float
    episode_max_gap : int

    Returns
    -------
    int — number of false alarm episodes
    """
    # Collect unique grid points
    unique_points: dict[tuple[float, float], Any] = {}
    for rec in records:
        key = (round(float(rec.grid_lat), 6), round(float(rec.grid_lon), 6))
        if key not in unique_points:
            unique_points[key] = (rec.hs_clim, ssh_total_cache.get(key, pd.Series(dtype=float)))

    total_fa = 0

    for (lat, lon), (hs_clim, ssh_total_clim) in unique_points.items():
        if hs_clim.empty or ssh_total_clim.empty:
            continue

        thr_hs  = _local_threshold(hs_clim, hs_pct)
        thr_ssh = _local_threshold(ssh_total_clim, ssh_pct)

        if np.isnan(thr_hs) or np.isnan(thr_ssh):
            continue

        # Align series
        hs_aligned    = hs_clim.reindex(time_index)
        ssh_aligned   = ssh_total_clim.reindex(time_index)

        compound_mask = (hs_aligned >= thr_hs) & (ssh_aligned >= thr_ssh)
        episodes = _cluster_episodes(compound_mask, episode_max_gap)

        if not episodes:
            continue

        # Get all event windows at this grid point
        event_windows = _build_event_windows_for_point(records, lat, lon, time_index)

        for episode in episodes:
            if not _episode_is_paired(episode, event_windows):
                total_fa += 1

    return total_fa


def run_false_alarms(
    records: list,
    ssh_total_cache: dict,
    time_index: pd.DatetimeIndex,
    hs_percentiles: list[float],
    ssh_percentiles: list[float],
    episode_max_gap: int,
) -> pd.DataFrame:
    """Run Layer 2: false alarm count for all threshold pairs.

    Parameters
    ----------
    records : list[EventRecord]
    ssh_total_cache : dict
    time_index : pd.DatetimeIndex
    hs_percentiles, ssh_percentiles : list of float
    episode_max_gap : int

    Returns
    -------
    DataFrame with columns [thr_hs_pct, thr_ssh_pct, F]
    """
    n_pairs = len(hs_percentiles) * len(ssh_percentiles)
    pair_idx = 0
    rows_fa: list[dict] = []

    for hs_pct in hs_percentiles:
        for ssh_pct in ssh_percentiles:
            pair_idx += 1
            if pair_idx % 9 == 1:
                log.info(
                    "  Layer 2 false alarms: pair %d/%d  (hs=q%.0f, ssh=q%.0f)",
                    pair_idx, n_pairs,
                    round(hs_pct * 100), round(ssh_pct * 100),
                )
            F = count_false_alarms_for_pair(
                records, ssh_total_cache, time_index,
                hs_pct, ssh_pct, episode_max_gap,
            )
            rows_fa.append({"thr_hs_pct": hs_pct, "thr_ssh_pct": ssh_pct, "F": F})

    return pd.DataFrame(rows_fa)


# ── Build SSH_total cache ──────────────────────────────────────────────────────

def build_ssh_total_cache(
    records: list,
    tide_cache: dict,
) -> dict[tuple[float, float], pd.Series]:
    """Build SSH_total = SSH + FES2022 tide for each unique grid point.

    Reuses the same add_tide_to_ssh() function from the tidal sensitivity module.

    Parameters
    ----------
    records : list[EventRecord]
    tide_cache : dict mapping (lat, lon) → tide Series (from tidal_sensitivity.tides)

    Returns
    -------
    dict mapping (lat, lon) → SSH_total climatological Series
    """
    from src.tidal_sensitivity.tides import add_tide_to_ssh, get_tide_for_record

    cache: dict[tuple[float, float], pd.Series] = {}
    for rec in records:
        key = (round(float(rec.grid_lat), 6), round(float(rec.grid_lon), 6))
        if key in cache:
            continue
        tide = get_tide_for_record(rec, tide_cache)
        ssh_total = add_tide_to_ssh(rec.ssh_clim, tide)
        cache[key] = ssh_total

    log.info("SSH_total cache built for %d unique grid points.", len(cache))
    return cache
