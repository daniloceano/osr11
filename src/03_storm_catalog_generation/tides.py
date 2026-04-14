"""
Thin tide wrapper for Step 3 — Storm Catalog Generation.

Calls the low-level FES2022 functions from Step 2c's tides.py to compute
SSH_total = zos + tide_daily_max at each coastal grid point.

Interface note (from Step 3 README §2.3):
    Step 2c's build_tide_cache() expects list[EventRecord] objects. Step 3
    does not use EventRecord objects. Instead, this module calls the
    lower-level _compute_daily_max_tides() and add_tide_to_ssh() directly.
"""
from __future__ import annotations

import logging

import pandas as pd

log = logging.getLogger(__name__)


def compute_daily_max_tides(
    lat: float,
    lon: float,
    time_index: pd.DatetimeIndex,
) -> pd.Series:
    """Compute FES2022 daily-maximum tide at a single grid point.

    Wraps Step 2c's _compute_daily_max_tides(). Evaluates FES2022 at hourly
    resolution and retains the daily maximum.

    Parameters
    ----------
    lat, lon : float
        Grid point coordinates.
    time_index : pd.DatetimeIndex
        Daily timestamps (00:00 UTC).

    Returns
    -------
    pd.Series : daily-max tide heights (m), indexed to time_index.
    """
    from src.tidal_sensitivity.tides import _compute_daily_max_tides

    return _compute_daily_max_tides(lat, lon, time_index)


def compute_ssh_total(
    ssh_series: pd.Series,
    tide_series: pd.Series,
) -> pd.Series:
    """Compute SSH_total = zos + tide_daily_max.

    Wraps Step 2c's add_tide_to_ssh().
    """
    from src.tidal_sensitivity.tides import add_tide_to_ssh

    return add_tide_to_ssh(ssh_series, tide_series)


def build_tide_cache(
    grid_points: list[tuple[float, float]],
    time_index: pd.DatetimeIndex,
) -> dict[tuple[float, float], pd.Series]:
    """Compute FES2022 daily-max tides for all grid points.

    Parameters
    ----------
    grid_points : list of (lat, lon) tuples.
    time_index : pd.DatetimeIndex
        Daily timestamps spanning the full metocean record.

    Returns
    -------
    dict mapping (lat, lon) → daily-max tide pd.Series.
    Failed grid points are logged and excluded.
    """
    n = len(grid_points)
    cache: dict[tuple[float, float], pd.Series] = {}
    failed: list[tuple[float, float, str]] = []

    for i, (lat, lon) in enumerate(grid_points):
        log.info(
            "  Tide [%d/%d] lat=%.4f, lon=%.4f (%d days)",
            i + 1, n, lat, lon, len(time_index),
        )
        try:
            tide = compute_daily_max_tides(lat, lon, time_index)
            if tide.isna().all():
                log.warning("    All-NaN tide at (%.4f, %.4f)", lat, lon)
                failed.append((lat, lon, "all_nan"))
            else:
                cache[(lat, lon)] = tide
        except Exception as exc:
            log.error(
                "    Tide computation failed at (%.4f, %.4f): %s", lat, lon, exc
            )
            failed.append((lat, lon, str(exc)))

    log.info(
        "Tide cache: %d/%d grid points computed (%d failed)",
        len(cache), n, len(failed),
    )
    if failed:
        log.warning("Failed tide grid points: %s", failed)

    return cache
