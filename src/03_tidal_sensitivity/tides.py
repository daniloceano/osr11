"""
Astronomical tide estimation via FES2022 (eo-tides).

For each unique grid point (latitude, longitude) in the event records,
this module computes the FES2022 tidal prediction for the full dataset
time range (1993-2025) and caches it keyed by (lat, lon).

Time convention
---------------
The unified GLORYS12/WAVERYS dataset contains **daily snapshots at
00:00 UTC** (not daily means). This is confirmed by inspecting the
time coordinate of metocean_sc_full_unified_waverys_grid.nc, which
shows timestamps of the form 'YYYY-MM-DDT00:00:00'.

FES2022 tides for the SSH+tide computation are therefore evaluated at
**00:00 UTC** each day — matching the GLORYS snapshot time exactly.
This avoids any phasing bias that would arise from using midnight tides
against, e.g., a 12:00 UTC snapshot.

FES2022 can be evaluated at any sub-daily frequency. For event figures,
this module also provides `compute_hourly_tides_for_window()` which
returns the full hourly tidal prediction for a 7-day window. This gives
a richer visual reference of the tidal rhythm in the event figures,
while the daily 00:00 UTC value remains what is actually summed with SSH.

Outputs
-------
    SSH_total(t) = zos(t, 00:00 UTC) + tide(t, 00:00 UTC)

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


def build_tide_cache(
    records,
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

    Returns
    -------
    dict mapping (lat, lon) → tide Series over the full climatological period
    """
    # Collect unique (lat, lon) pairs and determine the full time range
    unique_points: dict[tuple[float, float], pd.DatetimeIndex] = {}
    for rec in records:
        key = (round(float(rec.grid_lat), 6), round(float(rec.grid_lon), 6))
        if key not in unique_points:
            # Use the full climatological index from the first record at this point
            clim_index = rec.hs_clim.index if not rec.hs_clim.empty else rec.ssh_clim.index
            unique_points[key] = clim_index

    log.info("Computing FES2022 tides for %d unique grid points...", len(unique_points))
    cache: dict[tuple[float, float], pd.Series] = {}

    for i, ((lat, lon), time_idx) in enumerate(unique_points.items()):
        log.info(
            "  [%d/%d] lat=%.4f, lon=%.4f  (%d time steps)",
            i + 1, len(unique_points), lat, lon, len(time_idx),
        )
        try:
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
