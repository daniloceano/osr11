"""
Astronomical tide estimation via FES2022 (eo-tides).

For each unique grid point (latitude, longitude) in the event records,
this module computes the FES2022 tidal prediction for the full dataset
time range (1993-2025) and caches it keyed by (lat, lon).

Time conventions
----------------
Two modes are supported:

**Snapshot mode (daily 00:00 UTC, default)**:
    The unified GLORYS12/WAVERYS dataset contains daily snapshots at
    00:00 UTC. FES2022 tides are evaluated at 00:00 UTC each day —
    matching the GLORYS snapshot time exactly. This is the original
    convention used in Steps 2 and 3.

        SSH_total(t) = zos(t, 00:00 UTC) + tide(t, 00:00 UTC)

**Daily-maximum mode (daily_max=True)**:
    FES2022 is evaluated at hourly resolution (24 values per day) and
    the daily maximum tide height is retained. This captures the highest
    tidal level occurring at any time during the civil day, regardless of
    whether it coincides with the GLORYS snapshot time. Intended for use
    in STEP 4 threshold calibration, where Hₛ is also represented as a
    daily maximum from WAVERYS.

        tide_daily_max(d) = max(tide(d 00:00 UTC), tide(d 01:00 UTC), …, tide(d 23:00 UTC))
        SSH_total(d) = zos(d, 00:00 UTC) + tide_daily_max(d)

    Note: combining the 00:00 UTC GLORYS SSH with the daily-maximum tide
    is an approximation, since the tide maximum may occur at a different
    time than the GLORYS snapshot. This is inherent to the daily-resolution
    nature of GLORYS12 (a daily ocean reanalysis with one value per day).
    Sub-daily SSH data would be required for a fully synchronised estimate.

FES2022 can be evaluated at any sub-daily frequency. For event figures,
this module also provides `compute_hourly_tides_for_window()` which
returns the full hourly tidal prediction for a 7-day window.

- tide heights in metres (consistent with zos units)
- FES2022 includes all major semi-diurnal, diurnal, and long-period
  tidal constituents; the clipped Brasil subset covers the SC coast.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from src.tidal_sensitivity.config.analysis_config import CFG

log = logging.getLogger(__name__)


def compute_tides_for_point(
    lat: float,
    lon: float,
    time_index: pd.DatetimeIndex,
) -> pd.Series:
    """
    Compute FES2022 astronomical tide height at a single (lat, lon) for a
    given time array.

    Parameters
    ----------
    lat, lon : float
        Coordinates of the grid point (decimal degrees).
    time_index : pd.DatetimeIndex
        Timestamps at which to evaluate the tide model.

    Returns
    -------
    pd.Series
        Tide heights in metres, indexed by time_index.
    """
    from eo_tides.model import model_tides  # lazy import to avoid hard dep at module load

    result = model_tides(
        x=float(lon),
        y=float(lat),
        model=[CFG["tide_model"]],
        time=time_index,
        directory=str(CFG["tide_models_dir"]),
    )
    # result is a DataFrame with MultiIndex (time, x, y) and column tide_height
    tide_series = result["tide_height"].droplevel(["x", "y"])
    tide_series.index.name = "time"
    tide_series.name = CFG["tide_var_name"]
    return tide_series


def _compute_daily_max_tides(
    lat: float,
    lon: float,
    time_index: pd.DatetimeIndex,
) -> pd.Series:
    """Compute FES2022 daily-maximum tide by evaluating at hourly resolution.

    For each calendar day in ``time_index``, FES2022 is evaluated at every
    full hour (00:00–23:00 UTC) and the maximum value is retained.

    Parameters
    ----------
    lat, lon : float
        Grid point coordinates.
    time_index : pd.DatetimeIndex
        Daily timestamps (00:00 UTC) that define the output dates.

    Returns
    -------
    pd.Series
        Daily-maximum tide heights in metres, indexed to ``time_index``.
    """
    t_start = time_index.min().normalize()
    t_end   = time_index.max().normalize() + pd.Timedelta("23h")
    hourly_index = pd.date_range(t_start, t_end, freq="h")

    log.debug(
        "    Computing hourly tides for daily-max (%d hours = %d days)",
        len(hourly_index), len(hourly_index) // 24,
    )
    tide_hourly = compute_tides_for_point(lat, lon, hourly_index)

    # Resample hourly → daily max; re-align to the input daily index
    tide_daily_max = tide_hourly.resample("D").max()
    tide_daily_max.index = tide_daily_max.index.normalize()

    # Reindex to the exact dates in time_index (daily 00:00 UTC)
    daily_norm = time_index.normalize()
    tide_out = tide_daily_max.reindex(daily_norm)
    tide_out.index = time_index
    tide_out.name = CFG["tide_var_name"]
    return tide_out


def build_tide_cache(
    records,
    daily_max: bool = False,
) -> dict[tuple[float, float], pd.Series]:
    """
    Build a cache of tidal time series for every unique grid point used
    across all event records.

    The full climatological time range is computed once per grid point
    from the event records' climatological series index.

    Parameters
    ----------
    records : list[EventRecord]
        Event records from src.preliminary_compound.events.
    daily_max : bool, optional
        If False (default), FES2022 is evaluated at 00:00 UTC each day —
        consistent with the GLORYS12 daily snapshot convention (Steps 2–3).
        If True, FES2022 is evaluated at hourly resolution and the daily
        maximum tide height is retained — intended for STEP 4 threshold
        calibration, where Hₛ is also represented as a daily maximum.

    Returns
    -------
    dict mapping (lat, lon) → tide Series over the full climatological period
    """
    mode_label = "daily max (hourly FES2022 → resample)" if daily_max else "daily 00:00 UTC snapshot"
    log.info(
        "Computing FES2022 tides for %d unique grid points  [mode: %s]...",
        len({(round(float(r.grid_lat), 6), round(float(r.grid_lon), 6)) for r in records}),
        mode_label,
    )

    # Collect unique (lat, lon) pairs and determine the full time range
    unique_points: dict[tuple[float, float], pd.DatetimeIndex] = {}
    for rec in records:
        key = (round(float(rec.grid_lat), 6), round(float(rec.grid_lon), 6))
        if key not in unique_points:
            clim_index = rec.hs_clim.index if not rec.hs_clim.empty else rec.ssh_clim.index
            unique_points[key] = clim_index

    cache: dict[tuple[float, float], pd.Series] = {}

    for i, ((lat, lon), time_idx) in enumerate(unique_points.items()):
        log.info(
            "  [%d/%d] lat=%.4f, lon=%.4f  (%d days)",
            i + 1, len(unique_points), lat, lon, len(time_idx),
        )
        try:
            if daily_max:
                tide_series = _compute_daily_max_tides(lat, lon, time_idx)
            else:
                tide_series = compute_tides_for_point(lat, lon, time_idx)
            cache[(lat, lon)] = tide_series
        except Exception as exc:
            log.warning("  FES2022 failed at (%.4f, %.4f): %s — filling with NaN", lat, lon, exc)
            cache[(lat, lon)] = pd.Series(
                np.nan, index=time_idx, name=CFG["tide_var_name"]
            )

    log.info("Tide computation complete for %d grid points.", len(cache))
    return cache


def get_tide_for_record(
    rec,
    cache: dict[tuple[float, float], pd.Series],
) -> pd.Series:
    """
    Retrieve the tidal series for an EventRecord from the cache.

    Returns the full climatological tidal series aligned to the record's
    SSH/Hs time index.
    """
    key = (round(float(rec.grid_lat), 6), round(float(rec.grid_lon), 6))
    return cache.get(key, pd.Series(dtype=float, name=CFG["tide_var_name"]))


def compute_hourly_tides_for_window(
    lat: float,
    lon: float,
    window_start: pd.Timestamp,
    window_end: pd.Timestamp,
) -> pd.Series:
    """
    Compute FES2022 tide at 1-hour resolution for a given time window.

    Used for visual overlays in event figures — shows the full tidal rhythm
    within the event window. This is NOT used for the SSH+tide computation
    (which uses daily 00:00 UTC values to match the GLORYS snapshot time).

    Parameters
    ----------
    lat, lon       : float — grid point coordinates
    window_start   : pd.Timestamp — start of the window (inclusive)
    window_end     : pd.Timestamp — end of the window (inclusive)

    Returns
    -------
    pd.Series — hourly tide heights in metres
    """
    hourly_index = pd.date_range(window_start, window_end, freq="h")
    return compute_tides_for_point(lat, lon, hourly_index)


def add_tide_to_ssh(
    ssh_series: pd.Series,
    tide_series: pd.Series,
) -> pd.Series:
    """
    Add astronomical tide to SSH to produce total sea level.

    Parameters
    ----------
    ssh_series : pd.Series  — SSH (zos) in metres
    tide_series : pd.Series — FES2022 tide in metres, same index

    Returns
    -------
    pd.Series  — SSH_total = SSH + tide, same index as ssh_series
    """
    tide_aligned = tide_series.reindex(ssh_series.index)
    total = ssh_series + tide_aligned
    total.name = CFG["ssh_total_var"]
    return total
